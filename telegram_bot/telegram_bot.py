from langchain_huggingface import ChatHuggingFace, HuggingFaceEndpoint
from langchain_nvidia_ai_endpoints import ChatNVIDIA
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters
from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import START, MessagesState, StateGraph
from dotenv import load_dotenv
from pinecone import Pinecone
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_pinecone import PineconeVectorStore
from handlers import start_handler, call_bot_handler, error_handler
from profile_manager import user_prefs, update_user_profile
import os
import time
import asyncio

load_dotenv()

# Constants and configuration
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
NVIDIA_API_KEY = os.getenv("NVIDIA_API_KEY")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
INDEX_NAME = "langchain-test-index"
MODEL_NAME = "sentence-transformers/all-mpnet-base-v2"

# Setup workflow for LangChain
workflow = StateGraph(state_schema=MessagesState)

# Initialize Pinecone and Vector Store
Pinecone(api_key=PINECONE_API_KEY)
model_kwargs = {'device': 'cpu'}
encode_kwargs = {'normalize_embeddings': False}
embeddings = HuggingFaceEmbeddings(model_name=MODEL_NAME, model_kwargs=model_kwargs, encode_kwargs=encode_kwargs)
vector_store = PineconeVectorStore(index_name=INDEX_NAME, embedding=embeddings)

chat_model = HuggingFaceEndpoint(
    repo_id="HuggingFaceH4/zephyr-7b-beta",
    #  repo_id="nvidia/Llama-3.1-Nemotron-70B-Instruct-HF",
    task="text-generation",
    max_new_tokens=512,
    do_sample=False,
    repetition_penalty=1.03,
    streaming=True,
)
huggingface_llm = ChatHuggingFace(llm=chat_model, disable_streaming=False)
nvidia_llm = ChatNVIDIA(model="nv-mistralai/mistral-nemo-12b-instruct", api_key=NVIDIA_API_KEY)

def retrieve_from_vector_store(query: str, top_k: int = 2):
    results = vector_store.similarity_search(query, k=top_k)
    return results

# Define the function that generates responses using LangChain
async def call_model(state: MessagesState):
    user_input = state["messages"][-1].content
    retrieved_docs = retrieve_from_vector_store(user_input)
    retrieved_context = "\n".join([res.page_content for res in retrieved_docs])
    system_prompt = (
        "You are a women's fitness coach named Mabel. You are very bubbly and talk in short bursts."
        f"Here is some information on the user:\n {str(user_prefs)} "
        f"You may use the following as contextual information.\n {retrieved_context}"
        "The most important thing for you to do is to be natural and focus on creating a humanlike connection with your client"
    )
    messages = [SystemMessage(content=system_prompt)] + state["messages"]

    response = huggingface_llm.invoke(messages)
    if not response.content:
        response.content = "Response unavailable"
    try:
        print("getting response from nvidia llm")
        response = await asyncio.wait_for(nvidia_llm.invoke(messages), timeout=8)
    except asyncio.TimeoutError:
        print("Getting response from hugging face llm")
        response = await huggingface_llm.invoke(messages)()
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
        ai_msg = app.invoke(messages, config={"configurable": {"thread_id": str(update.message.chat_id)}})

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
