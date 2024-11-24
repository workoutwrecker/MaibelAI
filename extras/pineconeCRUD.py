import os
import time
from dotenv import load_dotenv

from pinecone import Pinecone, ServerlessSpec
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_pinecone import PineconeVectorStore

load_dotenv()

# Load the Pinecone API key from environment variables
pinecone_api_key = os.environ["PINECONE_API_KEY"]
pc = Pinecone(api_key=pinecone_api_key)

# Define the index name
index_name = "langchain-test-index"  # change if desired

# Check existing indexes
existing_indexes = [index_info["name"] for index_info in pc.list_indexes()]

# Create an index if it does not exist
if index_name not in existing_indexes:
    pc.create_index(
        name=index_name,
        dimension=768,  # Update this if you're using a different model
        metric="cosine",
        spec=ServerlessSpec(cloud="aws", region="us-east-1"),
    )
    # Wait until the index is ready
    while not pc.describe_index(index_name).status["ready"]:
        time.sleep(1)

# Connect to the index
index = pc.Index(index_name)

FILE_PATHS = [
    # commented files have already been added.
    # "C:/Users/ethan/PycharmMy_Projects/OpenAI_Assistant/in_house_coaching.txt",
    # "C:/Users/ethan/PycharmMy_Projects/OpenAI_Assistant/workout_routine.txt",
    # "C:/Users/ethan/PycharmMy_Projects/OpenAI_Assistant/women's_health.txt"
    # "C:/Users/ethan/PycharmMy_Projects/OpenAI_Assistant/coach_background.txt",
]

# Initialize Embeddings
model_name = "sentence-transformers/all-mpnet-base-v2"
model_kwargs = {'device': 'cpu'}
encode_kwargs = {'normalize_embeddings': False}
embeddings = HuggingFaceEmbeddings(
    model_name=model_name,
    model_kwargs=model_kwargs,
    encode_kwargs=encode_kwargs
)

# Create or Use Existing Index
vector_store = PineconeVectorStore(index_name=index_name, embedding=embeddings)

from langchain_core.documents import Document
from uuid import uuid4
# Now need to convert text in files to documents with metadata
documents = []

# Add Files to Pinecone
for file_path in FILE_PATHS:
    with open(file_path, "r") as file:
        text = file.read()
        document = Document(
            page_content=text,
            # metadata={"source": "tweet"}
            )
        documents.append(document)
        print(f"Added: {file_path}")

uuids = [str(uuid4()) for _ in range(len(documents))]
vector_store.add_documents(documents=documents, ids=uuids)