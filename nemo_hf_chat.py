from langchain_huggingface import ChatHuggingFace, HuggingFaceEndpoint
from langchain_core.messages import (
    HumanMessage,
    SystemMessage,
)
import os
import time
from dotenv import load_dotenv
from pinecone import Pinecone
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_pinecone import PineconeVectorStore
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import START, MessagesState, StateGraph
from langchain_core.callbacks.streaming_stdout import StreamingStdOutCallbackHandler

load_dotenv()

workflow = StateGraph(state_schema=MessagesState)

pinecone_api_key = os.environ["PINECONE_API_KEY"]
pc = Pinecone(api_key=pinecone_api_key)

index_name = "langchain-test-index"
model_name = "sentence-transformers/all-mpnet-base-v2"
model_kwargs = {'device': 'cpu'}
encode_kwargs = {'normalize_embeddings': False}
embeddings = HuggingFaceEmbeddings(
    model_name=model_name,
    model_kwargs=model_kwargs,
    encode_kwargs=encode_kwargs
)

vector_store = PineconeVectorStore(index_name=index_name, embedding=embeddings)


callbacks = [StreamingStdOutCallbackHandler()]
llm = HuggingFaceEndpoint(
    repo_id="HuggingFaceH4/zephyr-7b-beta",
    #  repo_id="nvidia/Llama-3.1-Nemotron-70B-Instruct-HF",
    task="text-generation",
    max_new_tokens=512,
    do_sample=False,
    repetition_penalty=1.03,
    streaming=True,
    callbacks=callbacks,
    # temperature=
)

def retrieve_from_vector_store(query: str, top_k: int = 2):
    results = vector_store.similarity_search(
        query,
        k=top_k,
        # filter={"source": "tweet"}
    )
    return results

chat_model = ChatHuggingFace(llm=llm, disable_streaming=False)

# Define the function that calls the model
def call_model(state: MessagesState):
    # Get the latest human message
    user_input = state["messages"][-1].content

    # Retrieve relevant data from the vector store
    retrieved_docs = retrieve_from_vector_store(user_input)

    # Create a prompt with retrieved documents for context
    retrieved_context = "\n".join([res.page_content for res in retrieved_docs])

    system_prompt = (
        "You are a womens fitness coach named Mabel. You are very bubly and you talk in short bursts"
        "You must embody the following:\n" + retrieved_context
    )
    messages = [SystemMessage(content=system_prompt)] + state["messages"]
    response = chat_model.invoke(messages)
    return {"messages": response}

# Define the node and edge
workflow.add_node("model", call_model)
workflow.add_edge(START, "model")

# Add simple in-memory checkpointer
memory = MemorySaver()
app = workflow.compile(checkpointer=memory)

def do_thread(prompt):
    messages = {"messages": [HumanMessage(content=prompt)]}
    ai_msg = app.invoke(messages, config={"configurable": {"thread_id": "1"}})

    ai_messages = ai_msg['messages']
    for index in range(len(ai_messages) - 1, -1, -1): #extract last AIMessage content
        cur_message = ai_messages[index]
        message_type = str(type(cur_message).__name__)
        if message_type == "AIMessage":
            print(cur_message.content)
            break
    
while True:
    exit_keywords = ["q", "quit", "exit"]
    prompt = input("Enter Prompt: ")
    if prompt in exit_keywords:
        break
    do_thread(prompt)
