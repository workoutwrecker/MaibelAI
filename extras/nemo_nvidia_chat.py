from langchain_nvidia_ai_endpoints import ChatNVIDIA
from langchain_core.messages import (
    HumanMessage
)
import os
import time
from dotenv import load_dotenv
from pinecone import Pinecone
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_pinecone import PineconeVectorStore
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import START, MessagesState, StateGraph

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

def retrieve_from_vector_store(query: str, top_k: int = 2):
    results = vector_store.similarity_search(query, k=top_k)
    return results

# Tools
def get_link(topic: list) -> str:
    """Get link for specific actions like getting website, contact, and voice call links

    Args:
        topic: list. Can add 'website', 'contact' and 'voice_call'.
    """

llm = ChatNVIDIA(model="meta/llama-3.1-70b-instruct", api_key=NVIDIA_API_KEY)
# llm = ChatNVIDIA(model="meta/llama-3.1-70b-instruct", api_key=NVIDIA_API_KEY).bind_tools([get_link])

def update_prefs(user_prefs: dict):
    # Get intent of user and update accordingly
    return user_prefs

def call_model(state: MessagesState):
    user_input = state["messages"][-1].content # Latest human msg

    # Retrieve relevant data from the vector store
    retrieved_docs = retrieve_from_vector_store(user_input)
    retrieved_context = "\n".join([res.page_content for res in retrieved_docs])

    # Include context within user prompt
    prompt_with_context = (
        f"You are a bubbly women’s fitness coach named Mabel. Speak in short bursts.\n"
        f"{retrieved_context}\n\nUser Input: {user_input}"
    )
    messages = [HumanMessage(content=prompt_with_context)]

    # Stream the response in chunks
    for chunk in llm.stream(messages):
        print(chunk.content, end='', flush=True)

def return_message(response):
    tool_call = response.tool_calls
    if not tool_call:
        return {"messages": response}
    else:
        tool_call = tool_call[0]
        tool_name = tool_call.get("name", "")
        match (tool_name):
            case "get_link":
                tool_args = tool_call.get("args", "")
                topics = tool_args.get("topic", [])
                links = {
                    "website": "https://www.mabelloh.com/",
                    "contact": "https://instagram.com/mabesloh",
                    "voice_call": "https://th.bing.com/th/id/OIP._M8xq8ZqE859erXkR0SD8QHaEo?w=289&h=180&c=7&r=0&o=5&dpr=1.3&pid=1.7",
                }
                cur_links = []
                for index, topic in enumerate(topics):
                    link = links.get(topic, "Unavailable")
                    cur_links.append(f"{index + 1}: {link}")
                if (len(topics) > 1):
                    topics_content = f"Here are the links you requested!\n" + "\n".join(cur_links)
                else:
                    topics_content = f"Here is the link!\n {cur_links[0]}"
        response.content = topics_content
        return {"messages": response}

# Define the node and edge
workflow.add_node("model", call_model)
workflow.add_edge(START, "model")

# Add simple in-memory checkpointer
memory = MemorySaver()
app = workflow.compile(checkpointer=memory)

def do_thread(prompt):
    messages = {"messages": [HumanMessage(content=prompt)]}
    app.invoke(messages, config={"configurable": {"thread_id": "1"}})
    
while True:
    exit_keywords = ["q", "quit", "exit"]
    prompt = input("\nEnter Prompt: ")
    if prompt in exit_keywords:
        break
    do_thread(prompt)


