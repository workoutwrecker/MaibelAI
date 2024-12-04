import os
import asyncio
import pytz
from datetime import time as datetime_time
from langchain_huggingface import ChatHuggingFace, HuggingFaceEndpoint
from langchain_nvidia_ai_endpoints import ChatNVIDIA
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackQueryHandler
from langchain_core.messages import HumanMessage, SystemMessage, trim_messages
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import START, MessagesState, StateGraph
from dotenv import load_dotenv

from handlers import start_handler, call_bot_handler, setup_handler, checkin_handler, leaderboard_handler, \
id_handler, save_handler, profile_handler, error_handler, leaderboard
from profile.main_mgmt import update_user_profile
from profile.mgmt_utils import check_user_info
from pinecone_vs import VectorStoreManager
from challenge import start_challenge, check_challenge_progress

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
nemo_llm = HuggingFaceEndpoint(
    repo_id="nvidia/Llama-3.1-Nemotron-70B-Instruct-HF", # Need PRO subscription
    task="text-generation",
    max_new_tokens=1024,
    do_sample=False,
    repetition_penalty=1.03,
    streaming=True,
)
zephyr_hf_llm = ChatHuggingFace(llm=zephyr_llm, disable_streaming=False)
nemo_hf_llm = ChatHuggingFace(llm=nemo_llm, disable_streaming=False)
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


async def call_model(state: MessagesState, config):
    context = config["configurable"].get("context")
    user_info = context.user_data.get("user_info", {})
    trimmed_state = trim_messages(state['messages'], strategy="last", token_counter=len, 
                                  max_tokens=21, start_on="human", end_on=("human"), include_system=False) # Gets context of last 21 messages
    user_input = trimmed_state[-1].content

    retrieved_docs = pinecone_vs.retrieve_from_vector_store(user_input, 1)
    retrieved_context = "\n".join([res.page_content for res in retrieved_docs])    
    system_prompt = (
        "You are a women's fitness coach named Mabel. You are very bubbly and talk in short bursts."
        f"User Information:\n {str(user_info)}"
        f"You may use the following as contextual information.\n {retrieved_context}"
    )
    messages = [SystemMessage(content=system_prompt)] + trimmed_state

    async def get_nemo_response():
        return await nemo_nvidia_llm.ainvoke(messages)

    async def get_zephyr_response():
        # await asyncio.sleep(12)
        return await zephyr_hf_llm.ainvoke(messages)
    
    await context.bot.send_chat_action(chat_id=config["configurable"]["thread_id"], action="typing")
    try:
        # Create tasks for each coroutine
        nemo_task = asyncio.create_task(get_nemo_response())
        zephyr_task = asyncio.create_task(get_zephyr_response())
        done, pending = await asyncio.wait([zephyr_task], return_when=asyncio.FIRST_COMPLETED, timeout=25)

        for task in done: response = task.result(); break
        for task in pending: task.cancel()

    except asyncio.TimeoutError:
        # If neither task completes within 25 seconds, return fallback response
        print("Both tasks took too long. Returning fallback response.")
        response.content = "Response took too long. Sorry about that. Please try again."

    if not response.content: response.content = "Response unavailable. Sorry😛. Error te-0"

    return {"messages": response}


async def handle_message(update: Update, context) -> None:
    if update.message.animation:
        gif_file_id = update.message.animation.file_id
        await update.message.reply_text(f"Received a GIF! File ID: {gif_file_id}")
        return
    missing_nutrition, missing_profile = check_user_info(context)
    if "callbackquery" not in context.user_data: await start_handler(update, context); return # New User
    elif missing_nutrition or missing_profile:
        await update.message.reply_text(
            f"Missing\nNutrition: {missing_nutrition}\nProfile: {missing_profile}.\nType '/setup' to fill in these details"
        ); return
    else:
        prompt = update.message.text
        messages = {"messages": [HumanMessage(content=prompt)]}
        config = {"configurable": {"thread_id": str(update.message.chat_id), "context": context}}

        ai_msg = await app.ainvoke(messages, config)

        ai_messages = ai_msg['messages']
        for index in range(len(ai_messages) - 1, -1, -1): # Extract the latest AI message
            cur_message = ai_messages[index]
            if type(cur_message).__name__ == "AIMessage":
                await update.message.reply_text(cur_message.content); break
            

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
    application.add_handler(CommandHandler('setup', setup_handler))
    application.add_handler(CommandHandler('checkin', checkin_handler))
    application.add_handler(CommandHandler('lb', leaderboard_handler))
    application.add_handler(CommandHandler('id', id_handler))
    application.add_handler(CommandHandler('save', save_handler))
    application.add_handler(CommandHandler('profile', profile_handler))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND | filters.ANIMATION, handle_message))
    application.add_handler(CallbackQueryHandler(update_user_profile))
    application.add_error_handler(error_handler)

    # application.add_handler(CommandHandler('challenge', start_challenge))
    # application.job_queue.run_repeating(check_challenge_progress, interval=3600, first=0)


    #TODO: Schedule leaderboard per minute using application.job_queue



    application.run_polling(poll_interval=1.0)

if __name__ == '__main__':
    main()
