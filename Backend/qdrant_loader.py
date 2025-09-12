import os
import re
import time
import json
from qdrant_client import QdrantClient
from qdrant_client.http import models
from qdrant_client.models import Distance, VectorParams
from dotenv import load_dotenv
import google.generativeai as genai 
from tenacity import retry, stop_after_attempt, wait_exponential

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
    api_key=QDRANT_API_KEY,
    timeout=300
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

def save_embeddings_locally(embeddings: list, file_path: str):
    """Saves embeddings to a local JSON file."""
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(embeddings, f)
        print(f"Embeddings successfully saved to '{file_path}'.")
    except Exception as e:
        print(f"Error saving embeddings to file: {e}")

def load_embeddings_locally(file_path: str):
    """Loads embeddings from a local JSON file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            embeddings = json.load(f)
        print(f"Embeddings successfully loaded from '{file_path}'.")
        return embeddings
    except FileNotFoundError:
        print(f"Local embeddings file '{file_path}' not found. Will generate new embeddings.")
        return None
    except Exception as e:
        print(f"Error loading embeddings from file: {e}")
        return None

@retry(wait=wait_exponential(multiplier=1, min=4, max=10), stop=stop_after_attempt(5))
def create_embedding_with_retry(chunk):
    """Generates a single embedding with retry logic."""
    return genai.embed_content(
        model="models/gemini-embedding-001",
        content=chunk,
        task_type="RETRIEVAL_DOCUMENT"
    )['embedding']


def create_embeddings(text_chunks: list, cache_file: str):
    """
    Generates or loads embeddings for a list of text chunks.
    
    Args:
        text_chunks (list): A list of text strings to embed.
        cache_file (str): The path to the local cache file.
        
    Returns:
        A list of embeddings (list of floats).
    """
    # Attempt to load embeddings from a local file first
    embeddings = load_embeddings_locally(cache_file)
    if embeddings is not None:
        # Check if the number of chunks matches the number of cached embeddings
        if len(embeddings) == len(text_chunks):
            return embeddings
        else:
            print("Warning: Number of cached embeddings does not match text chunks. Regenerating.")
            embeddings = None
    
    # If loading failed or the cache is invalid, generate new embeddings
    if embeddings is None:
        print(f"Generating embeddings for {len(text_chunks)} chunks...")
        embeddings = []
        for i, chunk in enumerate(text_chunks):
            try:
                embedding = create_embedding_with_retry(chunk)
                embeddings.append(embedding)
                print(f"Embedding generated for chunk {i+1}/{len(text_chunks)}.")
            except Exception as e:
                print(f"An error occurred while generating embedding for chunk {i+1}: {e}")
                continue
                
        if len(embeddings) != len(text_chunks):
            print("Warning: Some embeddings failed to generate.")
        
        # Save the newly generated embeddings to a local file
        if embeddings:
            save_embeddings_locally(embeddings, cache_file)
            
    return embeddings


def upload_to_qdrant(collection_name: str, chunks: list, embeddings: list, batch_size: int = 10):
    """
    Creates a new collection in Qdrant and uploads the chunks and embeddings in batches.
    
    Args:
        collection_name (str): The name of the Qdrant collection.
        chunks (list): The list of original text chunks.
        embeddings (list): The list of vector embeddings.
        batch_size (int): The number of points to upload in each batch.
    """
    # Note: The 'recreate_collection' method is deprecated, but it's safe to use for now.
    # For future projects, you should use client.collection_exists() and client.create_collection().
    try:
        client.recreate_collection(
            collection_name=collection_name,
            vectors_config=VectorParams(size=3072, distance=Distance.COSINE)
        )
        print(f"Collection '{collection_name}' created or recreated successfully.")
    except Exception as e:
        print(f"Error creating collection: {e}")
        return

    # Prepare all points
    points = [
        models.PointStruct(
            id=i,  # Use an index as a unique ID
            vector=embedding,
            payload={"text": chunk}
        )
        for i, (chunk, embedding) in enumerate(zip(chunks, embeddings))
    ]

    # Upload points in batches
    num_points = len(points)
    for i in range(0, num_points, batch_size):
        batch = points[i:i + batch_size]
        try:
            client.upsert(
                collection_name=collection_name,
                points=batch
            )
            print(f"Successfully uploaded batch {i//batch_size + 1} ({len(batch)} points) to Qdrant.")
            time.sleep(2)  # Add a small delay between batches
        except Exception as e:
            print(f"Error uploading batch starting at index {i}: {e}")
            return # Stop if a batch fails to prevent further issues

if __name__ == "__main__":
    # Define the file to read and the Qdrant collection name
    input_file = "hospital_chunks.txt"
    embedding_cache_file = "embeddings_cache.json"
    qdrant_collection_name = "hospital-rag-data"

    print("Starting Qdrant ingestion process...")
    
    # Get the text chunks from the file
    chunks = get_text_chunks(input_file)
    if not chunks:
        print("No chunks to process. Exiting.")
    else:
        # Generate or load the embeddings
        embeddings = create_embeddings(chunks, embedding_cache_file)
        if embeddings:
            # Upload the data to Qdrant
            upload_to_qdrant(qdrant_collection_name, chunks, embeddings)
        else:
            print("Failed to generate or load embeddings. Exiting.")
