import os
import re
import time
import json
import numpy as np
from typing import List, Dict
from qdrant_client import QdrantClient
from qdrant_client.http import models
from qdrant_client.models import (
    VectorParams,
    SparseVectorParams,
    Distance,
    PointStruct,
    SparseVector,
    PointVectors,
)
from sklearn.feature_extraction.text import TfidfVectorizer
from tqdm import tqdm
from dotenv import load_dotenv
import google.generativeai as genai 
from fastembed import SparseTextEmbedding
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

def create_dense_embeddings(text_chunks: List[str], cache_file: str) -> List[List[float]]:
    # (Your existing caching logic — simplified here)
    embeddings = load_embeddings_locally(cache_file)
    if embeddings is not None and len(embeddings) == len(text_chunks):
        return embeddings

    embeddings = []
    print(f"Generating dense embeddings for {len(text_chunks)} chunks...")
    for i, chunk in enumerate(text_chunks):
        try:
            emb = create_embedding_with_retry(chunk)
            embeddings.append(emb)
            print(f" Dense embedding {i+1}/{len(text_chunks)}")
        except Exception as e:
            print(f"  Error embedding chunk {i}: {e}")
            embeddings.append(None)  # keep positions aligned
    # Save only successful embeddings if desired
    save_embeddings_locally(embeddings, cache_file)
    return embeddings


def create_sparse_vectors_tfidf(text_chunks: List[str]):
    """
    Build a TF-IDF model on all chunks and return a list of sparse vectors in Qdrant format:
      [{"indices": [...], "values": [...]}, ...]
    This is a simple and practical approach for sparse lexical signal.
    """
    print("Fitting TF-IDF to produce sparse vectors...")
    vectorizer = TfidfVectorizer( norm='l2', dtype=np.float32)
    X = vectorizer.fit_transform(text_chunks)  # scipy.sparse csr_matrix

    sparse_vectors = []
    for i in range(X.shape[0]):
        row = X.getrow(i)
        nz = row.nonzero()
        indices = nz[1].tolist()
        values = row.data.tolist()
        sparse_vectors.append({"indices": indices, "values": values})
    print("Sparse vectors created.")
    return sparse_vectors


def ensure_hybrid_collection(client: QdrantClient, collection_name: str, dense_dim: int,
                             dense_name: str = "dense", sparse_name: str = "sparse",
                             distance: Distance = Distance.COSINE):
    """
    Create or recreate a collection that supports named dense + sparse vectors.
    If collection exists and has sparse config, this is a no-op.
    """
    if client.collection_exists(collection_name=collection_name):
        info = client.get_collection(collection_name=collection_name)
        # If sparse config already present, return
        cfg = getattr(info, "config", None)
        if cfg and getattr(cfg.params, "sparse_vectors", None):
            print(f"Collection '{collection_name}' already supports sparse vectors.")
            return

        # Otherwise recreate (drop & create) so new sparse config is included
        print(f"Recreating collection '{collection_name}' with hybrid (dense + sparse) config...")
        client.delete_collection(collection_name=collection_name)

    print(f"Creating collection '{collection_name}' with dense_dim={dense_dim} ...")
    client.create_collection(
        collection_name=collection_name,
        vectors_config={
            dense_name: VectorParams(size=dense_dim, distance=distance)
        },
        sparse_vectors_config={
            sparse_name: SparseVectorParams()
        }
    )
    print("Collection created.")

def add_sparse_vectors_to_existing_collection(client: QdrantClient, collection_name: str,
                                              sparse_vectors: List[Dict], ids: List[int],
                                              sparse_name: str = "sparse", batch_size: int = 256):
    """
    If collection already exists with a sparse vector config, call update_vectors to add sparse vectors.
    Uses models.PointVectors objects.
    """
    assert len(sparse_vectors) == len(ids)
    total = len(ids)
    for start in range(0, total, batch_size):
        end = min(start + batch_size, total)
        pts = []
        for i in range(start, end):
            sv = sparse_vectors[i]
            pts.append(models.PointVectors(id=ids[i], vector={sparse_name: SparseVector(indices=sv["indices"], values=sv["values"])}))
        client.update_vectors(collection_name=collection_name, points=pts)
        print(f"Updated sparse vectors for ids {start}..{end-1}.")


def upload_hybrid_to_qdrant(client: QdrantClient, collection_name: str, chunks: List[str],
                            dense_embeddings: List[List[float]], sparse_vectors: List[Dict],
                            batch_size: int = 64,
                            dense_name: str = "dense", sparse_name: str = "sparse"):
    """
    Upload points with both named dense and sparse vectors.
    Points are PointStructs where 'vector' can be a dict {dense_name: [...], sparse_name: SparseVector(...)}
    """
    assert len(chunks) == len(dense_embeddings) == len(sparse_vectors)

    total = len(chunks)
    for start in range(0, total, batch_size):
        end = min(start + batch_size, total)
        batch_points = []
        for i in range(start, end):
            emb = dense_embeddings[i]
            sp = sparse_vectors[i]
            if emb is None:
                # skip or handle failed dense embedding
                continue
            sv = SparseVector(indices=sp["indices"], values=sp["values"])
            vec = {dense_name: emb, sparse_name: sv}
            p = PointStruct(id=i, vector=vec, payload={"text": chunks[i]})
            batch_points.append(p)

        if not batch_points:
            continue

        try:
            client.upsert(collection_name=collection_name, points=batch_points)
            print(f"Uploaded points {start}..{end-1} ({len(batch_points)} points).")
            time.sleep(0.2)
        except Exception as e:
            print(f"Upload error for batch {start}-{end}: {e}")
            raise

if __name__ == "__main__":
    # Define the file to read and the Qdrant collection name
    input_file = "hospital_chunks.txt"
    embedding_cache_file = "embeddings_cache.json"
    qdrant_collection_name = "hospital-rag-data"
    DENSE_VECTOR_NAME = "dense"
    SPARSE_VECTOR_NAME = "sparse"
    VECTOR_SIZE = 3072 # Gemini embedding dim; verify
    BATCH_SIZE = 64
    RECREATE_COLLECTION = False # set True ONCE if you need to recreate collection with sparse support
    SPARSE_MODEL_NAME = "prithivida/Splade_PP_en_v1" # SPLADE++ model supported by FastEmbed
   
    print("Starting Qdrant ingestion process...")
    
    # Get the text chunks from the file
    chunks = get_text_chunks(input_file)
    if not chunks:
        print("No chunks to process. Exiting.")
    else:
         # 1) Create dense embeddings (Gemini)
        dense_embeddings = create_dense_embeddings(chunks, embedding_cache_file)

        # 2) Build sparse vectors (TF-IDF)
        sparse_vectors = create_sparse_vectors_tfidf(chunks)

        # 3) Create or ensure collection supports hybrid
        # Use first embedding to get dim (fallback safe value)
        first_emb = next((e for e in dense_embeddings if e), None)
        if first_emb is None:
            raise SystemExit("No dense embeddings produced.")
        dense_dim = len(first_emb)

        ensure_hybrid_collection(client, qdrant_collection_name, dense_dim=dense_dim)

        if dense_embeddings and sparse_vectors:
            # Upload the data to Qdrant
            upload_hybrid_to_qdrant(client,qdrant_collection_name, chunks, dense_embeddings, sparse_vectors)
        else:
            print("Failed to generate or load embeddings. Exiting.")