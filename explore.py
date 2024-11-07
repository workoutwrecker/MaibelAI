from langchain_nvidia_ai_endpoints import ChatNVIDIA
import os
import logging
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from telegram.ext import Application, CommandHandler, MessageHandler, filters
from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import START, MessagesState, StateGraph
from dotenv import load_dotenv
from pinecone import Pinecone
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_pinecone import PineconeVectorStore
import re

# Load environment variables
load_dotenv()

# Setup logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

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

user_prefs = {}

def retrieve_from_vector_store(query: str, top_k: int = 2):
    results = vector_store.similarity_search(query, k=top_k)
    return results

llm = ChatNVIDIA(model="meta/llama-3.1-70b-instruct", api_key=NVIDIA_API_KEY)

# Define the function that generates responses using LangChain
def call_model(state: MessagesState):
    user_input = state["messages"][-1].content
    retrieved_docs = retrieve_from_vector_store(user_input)
    retrieved_context = "\n".join([res.page_content for res in retrieved_docs])
    system_prompt = (
        "You are a women's fitness coach named Mabel. You are very bubbly and talk in short bursts. "
        f"Here is some information on the user:\n {str(user_prefs)} "
        f"You must embody the following:\n {retrieved_context}"
    )
    messages = [SystemMessage(content=system_prompt)] + state["messages"]
    response = llm.invoke(messages)
    if not response.content:
        response.content = "Response unavailable"
    return {"messages": response}

def escaped_string(text: str) -> str:
    special_chars = ['_', '*', '[', ']', '(', ')', '~', '`', '>', '#', '+', '-', '=', '{', '}', '.', '!', "'"]
    for char in special_chars:
        text = text.replace(char, f'\\{char}')
    return text

# Update user_prefs with collected profile information
async def update_user_profile(update: Update, context) -> None:
    global user_prefs
    if "profile_stage" not in context.user_data:
        # Set initial stage to ask for age
        context.user_data["profile_stage"] = "ask_age"

    # Get user's reply
    user_input = update.message.text

    # Check the current stage and ask the next question accordingly
    if context.user_data["profile_stage"] == "ask_age":
        user_prefs["age"] = user_input
        context.user_data["profile_stage"] = "ask_gender"
        await update.message.reply_text(
            "Please select your gender.",
            reply_markup=ReplyKeyboardMarkup(
                [[KeyboardButton("Female"), KeyboardButton("Male"), KeyboardButton("Other")]],
                one_time_keyboard=True,
                resize_keyboard=True
            )
        )
    elif context.user_data["profile_stage"] == "ask_gender":
        user_prefs["gender"] = user_input
        context.user_data["profile_stage"] = "ask_workouts_per_week"
        await update.message.reply_text(
            "How many workouts do you do per week?",
            reply_markup=ReplyKeyboardMarkup(
                [[KeyboardButton("1-2"), KeyboardButton("3-4"), KeyboardButton("5+")]],
                one_time_keyboard=True,
                resize_keyboard=True
            )
        )
    elif context.user_data["profile_stage"] == "ask_workouts_per_week":
        user_prefs["workouts_per_week"] = user_input
        context.user_data["profile_stage"] = "ask_goal"
        await update.message.reply_text(
            "What is your fitness goal? Choose one:",
            reply_markup=ReplyKeyboardMarkup(
                [[KeyboardButton("Lose weight"), KeyboardButton("Get stronger")],
                 [KeyboardButton("Build muscle"), KeyboardButton("Mix")]],
                one_time_keyboard=True,
                resize_keyboard=True
            )
        )
    elif context.user_data["profile_stage"] == "ask_goal":
        user_prefs["goal"] = user_input
        context.user_data["profile_stage"] = "profile_complete"
        await update.message.reply_text(
            "Thank you! Your profile is complete. You can now ask me anything related to fitness!",
            reply_markup=ReplyKeyboardRemove()
        )
    else:
        await handle_message(update, context)  # Process any general messages

# Telegram Bot Functions
async def start(update: Update, context) -> None:
    user = update.effective_user
    msg = "! I'm a bot powered by AI. Ask me anything related to women's fitness or just chat!"
    final_msg = f"Hi {user.mention_markdown_v2()}{escaped_string(msg)}"
    await update.message.reply_text(
        final_msg,
        parse_mode="MarkdownV2"
    )
    context.user_data["profile_stage"] = "ask_age"
    await update.message.reply_text(
        "To start, please enter your age.",
        reply_markup=ReplyKeyboardMarkup(
            [[KeyboardButton("18-24"), KeyboardButton("25-34"), KeyboardButton("35-44"), KeyboardButton("45+")]],
            one_time_keyboard=True,
            resize_keyboard=True
        )
    )

async def call_bot(update: Update, context) -> None:
    link = "https://th.bing.com/th/id/OIP._M8xq8ZqE859erXkR0SD8QHaEo?w=289&h=180&c=7&r=0&o=5&dpr=1.3&pid=1.7"
    msg = f"Here's the link to get on a call with me right now!\n{link}"
    await update.message.reply_text(
        escaped_string(msg),
        parse_mode="MarkdownV2"
    )

async def handle_message(update: Update, context) -> None:
    if context.user_data.get("profile_stage") != "profile_complete":
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

async def error_handler(update: Update, context) -> None:
    logger.error(msg="Exception while handling an update:", exc_info=context.error)
    if update.message:
        await update.message.reply_text("Sorry, an error occurred while processing your request.")

# Add the function to the workflow
workflow.add_node("model", call_model)
workflow.add_edge(START, "model")

# Simple memory management
memory = MemorySaver()
app = workflow.compile(checkpointer=memory)

def main() -> None:
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    application.add_handler(CommandHandler('start', start))
    application.add_handler(CommandHandler('call', call_bot))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    application.add_error_handler(error_handler)
    application.run_polling(poll_interval=1.0)

if __name__ == '__main__':
    main()
