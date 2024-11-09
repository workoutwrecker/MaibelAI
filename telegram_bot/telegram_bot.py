import os
import time
import asyncio
from langchain_huggingface import ChatHuggingFace, HuggingFaceEndpoint
from langchain_nvidia_ai_endpoints import ChatNVIDIA
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters
from langchain_core.messages import HumanMessage, SystemMessage, trim_messages
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import START, MessagesState, StateGraph
from dotenv import load_dotenv

from handlers import start_handler, call_bot_handler, error_handler
from telegram_bot.profile_mgmt import user_prefs, update_user_profile
from pinecone_vs import VectorStoreManager

load_dotenv()

# Constants and configuration
NVIDIA_API_KEY = os.getenv("NVIDIA_API_KEY")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

# Setup workflow for LangChain
workflow = StateGraph(state_schema=MessagesState)

zephyr_llm = HuggingFaceEndpoint(
    repo_id="HuggingFaceH4/zephyr-7b-beta",
    task="text-generation",
    max_new_tokens=1024,
    do_sample=False,
    repetition_penalty=1.03,
    streaming=True,
)
zephyr_hf_llm = ChatHuggingFace(llm=zephyr_llm, disable_streaming=False)
nemo_nvidia_llm = ChatNVIDIA(model="meta/llama-3.1-70b-instruct", api_key=NVIDIA_API_KEY)
pinecone_vs = VectorStoreManager()

# def updateState(config):
# Channels without reducers are not overrided but appended to.
#     current_state = app.get_state(config).values
#     print("\n-----------------\n")
#     print("Current State: ", current_state)
#     trimmed_state = trim_messages(current_state['messages'], strategy="last", token_counter=len, 
#                                   max_tokens=2, start_on="human", end_on=("ai"), include_system=False)
#     print("\n-----------------\n")
#     print("Trimmed State: ", trimmed_state)
#     app.update_state(config, {"messages": trimmed_state})


# Define the function that generates responses using LangChain
async def call_model(state: MessagesState):
    trimmed_state = trim_messages(state['messages'], strategy="last", token_counter=len, 
                                  max_tokens=21, start_on="human", end_on=("human"), include_system=False)
    user_input = trimmed_state[-1].content
    retrieved_docs = pinecone_vs.retrieve_from_vector_store(user_input, 1)
    retrieved_context = "\n".join([res.page_content for res in retrieved_docs])
    system_prompt = (
        "You are a women's fitness coach named Mabel. You are very bubbly and talk in short bursts."
        f"User Information:\n {str(user_prefs)} "
        f"You may use the following as contextual information.\n {retrieved_context}"
    )
    messages = [SystemMessage(content=system_prompt)] + trimmed_state

    async def get_nemo_response():
        return await nemo_nvidia_llm.ainvoke(messages)

    async def get_zephyr_response():
        await asyncio.sleep(8)
        return await zephyr_hf_llm.ainvoke(messages)

    try:
        # Create tasks for each coroutine
        nemo_task = asyncio.create_task(get_nemo_response())
        zephyr_task = asyncio.create_task(get_zephyr_response())
        done, pending = await asyncio.wait([nemo_task, zephyr_task], return_when=asyncio.FIRST_COMPLETED, timeout=25)

        for task in done:
            response = task.result()
            break
        for task in pending:
            task.cancel()

    except asyncio.TimeoutError:
        # If neither task completes within 25 seconds, return fallback response
        print("Both tasks took too long. Returning fallback response.")
        response.content = "Response took too long. Sorry about that. Please try again."

    if not response.content:
        response.content = "Response unavailable. Sorry😛. Error te-0"

    return {"messages": response}


async def handle_message(update: Update, context) -> None:
    if "profile_stage" not in context.user_data:
        await start_handler(update, context)
        return
    elif context.user_data["profile_stage"] != "profile_complete":
        await update_user_profile(update, context)
    else:
        prompt = update.message.text
        messages = {"messages": [HumanMessage(content=prompt)]}
        config = {"configurable": {"thread_id": str(update.message.chat_id)}}
        
        ai_msg = await app.ainvoke(messages, config)

        ai_messages = ai_msg['messages']
        for index in range(len(ai_messages) - 1, -1, -1): # Extract the latest AI message
            cur_message = ai_messages[index]
            if type(cur_message).__name__ == "AIMessage":
                await update.message.reply_text(cur_message.content)
                break

# Add the function to the workflow
workflow.add_node("model", call_model)
workflow.add_edge(START, "model")

# Simple memory management
memory = MemorySaver()
app = workflow.compile(checkpointer=memory)

def main() -> None:
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    application.add_handler(CommandHandler('start', start_handler))
    application.add_handler(CommandHandler('call', call_bot_handler))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    application.add_error_handler(error_handler)
    application.run_polling(poll_interval=1.0)

if __name__ == '__main__':
    main()
