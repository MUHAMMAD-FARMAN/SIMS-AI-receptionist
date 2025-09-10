import os
import re
from qdrant_client import QdrantClient
from qdrant_client.http import models
from qdrant_client.models import Distance, VectorParams
from dotenv import load_dotenv
import google.generativeai as genai # Corrected import to get the top-level functions

# Load environment variables from .env file
load_dotenv()

# --- Configuration ---
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
QDRANT_URL = os.getenv("QDRANT_URL")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")

# Check for required environment variables
if not all([GOOGLE_API_KEY, QDRANT_URL, QDRANT_API_KEY]):
    raise ValueError("Missing one or more required environment variables: GOOGLE_API_KEY, QDRANT_URL, QDRANT_API_KEY")

# --- Initialize Clients ---
# Initialize the Gemini embedding model configuration
genai.configure(api_key=GOOGLE_API_KEY)

# Initialize the Qdrant client
client = QdrantClient(
    url=QDRANT_URL,
    api_key=QDRANT_API_KEY
)

# --- Main Functions ---
def get_text_chunks(file_path: str):
    """
    Reads a text file line by line and returns a list of chunks.
    This assumes each line is a pre-formatted, semantically-rich chunk.
    
    Args:
        file_path (str): The path to the input text file.
        
    Returns:
        A list of text strings, or an empty list if the file is not found.
    """
    if not os.path.exists(file_path):
        print(f"Error: The file '{file_path}' was not found.")
        return []
        
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            chunks = [line.strip() for line in f.readlines() if line.strip()]
        return chunks
    except Exception as e:
        print(f"Error reading file '{file_path}': {e}")
        return []

def create_embeddings(text_chunks: list):
    """
    Generates embeddings for a list of text chunks using the Gemini embedding model.
    
    Args:
        text_chunks (list): A list of text strings to embed.
        
    Returns:
        A list of embeddings (list of floats).
    """
    if not text_chunks:
        return []

    print(f"Generating embeddings for {len(text_chunks)} chunks...")
    try:
        embeddings = genai.embed_content(
            model="models/gemini-embedding-001",
            content=text_chunks,
            task_type="RETRIEVAL_DOCUMENT"
        )
        # The embedding model returns a special object, so we extract the list of floats
        return [e['embedding'] for e in embeddings['embeddings']]
    except Exception as e:
        print(f"An error occurred while generating embeddings: {e}")
        return []

def upload_to_qdrant(collection_name: str, chunks: list, embeddings: list):
    """
    Creates a new collection in Qdrant and uploads the chunks and embeddings.
    
    Args:
        collection_name (str): The name of the Qdrant collection.
        chunks (list): The list of original text chunks.
        embeddings (list): The list of vector embeddings.
    """
    # Create the collection if it doesn't exist
    try:
        client.recreate_collection(
            collection_name=collection_name,
            vectors_config=VectorParams(size=768, distance=Distance.COSINE)
        )
        print(f"Collection '{collection_name}' created or recreated successfully.")
    except Exception as e:
        print(f"Error creating collection: {e}")
        return

    # Prepare points for upserting
    points = [
        models.PointStruct(
            id=i,  # Use an index as a unique ID
            vector=embedding,
            payload={"text": chunk}
        )
        for i, (chunk, embedding) in enumerate(zip(chunks, embeddings))
    ]

    # Upload the points to the collection in batches for efficiency
    try:
        client.upsert(
            collection_name=collection_name,
            points=points
        )
        print(f"Successfully uploaded {len(points)} points to Qdrant collection '{collection_name}'.")
    except Exception as e:
        print(f"Error uploading points to Qdrant: {e}")

if __name__ == "__main__":
    # Define the file to read and the Qdrant collection name
    input_file = "hospital_chunks.txt"
    qdrant_collection_name = "hospital-rag-data"

    print("Starting Qdrant ingestion process...")
    
    # Get the text chunks from the file
    chunks = get_text_chunks(input_file)
    if not chunks:
        print("No chunks to process. Exiting.")
    else:
        # Generate the embeddings
        embeddings = create_embeddings(chunks)
        if embeddings:
            # Upload the data to Qdrant
            upload_to_qdrant(qdrant_collection_name, chunks, embeddings)
        else:
            print("Failed to generate embeddings. Exiting.")
