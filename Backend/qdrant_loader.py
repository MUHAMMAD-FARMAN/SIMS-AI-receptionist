# File: qdrant_loader.py
"""
Ingestion script that creates a Qdrant collection (named dense + sparse vectors) and uploads
both dense embeddings from Gemini and sparse embeddings from FastEmbed (SPLADE).

Usage:
  - Set environment variables in a .env file: GOOGLE_API_KEY, QDRANT_URL, QDRANT_API_KEY
  - Prepare a newline-separated text file of document chunks (default: hospital_chunks.txt)
  - Run: python qdrant_loader.py

Requirements:
  pip install qdrant-client fastembed google-generativeai tenacity python-dotenv tqdm

Note: If your existing collection does not support named sparse vectors you must set
RECREATE_COLLECTION = True to recreate it (this will DELETE existing data!).
"""

import os
import time
import json
from typing import List
from dotenv import load_dotenv
from tenacity import retry, wait_exponential, stop_after_attempt
from qdrant_client import QdrantClient, models
from qdrant_client.models import VectorParams, SparseVectorParams, Distance
import google.generativeai as genai
from fastembed import SparseTextEmbedding
from tqdm import tqdm

# --- CONFIG ---
load_dotenv()
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
QDRANT_URL = os.getenv("QDRANT_URL")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")

INPUT_FILE = "hospital_chunks.txt"  # newline-separated chunks
COLLECTION_NAME = "hospital-rag-data"
DENSE_VECTOR_NAME = "dense"
SPARSE_VECTOR_NAME = "sparse"
VECTOR_SIZE = 3072  # Gemini embedding dim; verify
BATCH_SIZE = 15
RECREATE_COLLECTION = True  # set True ONCE if you need to recreate collection with sparse support
SPARSE_MODEL_NAME = "prithivida/Splade_PP_en_v1"  # SPLADE++ model supported by FastEmbed

if not GOOGLE_API_KEY or not QDRANT_URL or not QDRANT_API_KEY:
    raise SystemExit("Set GOOGLE_API_KEY, QDRANT_URL and QDRANT_API_KEY in .env")

# Init
genai.configure(api_key=GOOGLE_API_KEY)
EMBEDDING_MODEL = "models/gemini-embedding-001"
qdrant_client = QdrantClient(url=QDRANT_URL, api_key=QDRANT_API_KEY)

# FastEmbed sparse model (SPLADE)
sparse_encoder = SparseTextEmbedding(model_name=SPARSE_MODEL_NAME)

# retry wrapper for Gemini embedding
@retry(wait=wait_exponential(multiplier=1, min=4, max=10), stop=stop_after_attempt(5))
def create_dense_embedding(text: str) -> List[float]:
    resp = genai.embed_content(model=EMBEDDING_MODEL, content=text, task_type="RETRIEVAL_DOCUMENT")
    return resp["embedding"]

def load_chunks(file_path: str) -> List[str]:
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Chunks file not found: {file_path}")
    with open(file_path, "r", encoding="utf-8") as f:
        # assume one chunk per line; normalize by stripping and lowercasing
        chunks = [line.strip().lower() for line in f if line.strip()]
    return chunks

def ensure_hybrid_collection(recreate: bool = False):
    # if recreate=True -> delete and recreate (DANGEROUS: will erase data)
    exists = False
    try:
        cols = qdrant_client.get_collections()
        exists = COLLECTION_NAME in [c.name for c in cols.collections]
    except Exception as e:
        print("Warning: couldn't fetch collections list:", e)

    if exists and not recreate:
        # Check if sparse config exists
        info = qdrant_client.get_collection(collection_name=COLLECTION_NAME)
        cfg = getattr(info, "config", None)
        sparse_present = False
        if cfg and getattr(cfg.params, "sparse_vectors", None):
            sparse_present = True
        if sparse_present:
            print("Collection exists and already supports sparse vectors. OK.")
            return
        else:
            raise SystemExit("Collection exists but doesn't support sparse vectors. Set RECREATE_COLLECTION=True to recreate it (data loss).")

    if exists and recreate:
        print("Deleting existing collection (recreate=True) ...")
        qdrant_client.delete_collection(collection_name=COLLECTION_NAME)

    print("Creating collection with named dense + sparse vectors...")
    qdrant_client.create_collection(
        collection_name=COLLECTION_NAME,
        vectors_config={
            DENSE_VECTOR_NAME: VectorParams(size=VECTOR_SIZE, distance=Distance.COSINE)
        },
        sparse_vectors_config={
            SPARSE_VECTOR_NAME: SparseVectorParams()
        }
    )
    print("Collection created.")


def embed_sparse_chunks(chunks: List[str]):
    """Use FastEmbed SPLADE model to get sparse embeddings. Returns list of dicts {indices, values}.
    The FastEmbed model returns SparseEmbedding objects with `indices` and `values`.
    """
    print("Encoding sparse vectors with FastEmbed (SPLADE)...")
    sparse_list = []
    # FastEmbed's embed returns a generator; collecting into list
    for sparse_emb in tqdm(list(sparse_encoder.embed(chunks)), desc="sparse embed"):
        # sparse_emb has .indices and .values
        sparse_list.append({"indices": list(map(int, sparse_emb.indices)), "values": [float(v) for v in sparse_emb.values]})
    return sparse_list


def upload_hybrid(chunks: List[str], dense_embeddings: List[List[float]], sparse_vectors: List[dict], batch_size: int = BATCH_SIZE):
    assert len(chunks) == len(dense_embeddings) == len(sparse_vectors)
    total = len(chunks)
    print(f"Uploading {total} points in batches of {batch_size}...")
    for start in range(0, total, batch_size):
        end = min(start + batch_size, total)
        batch = []
        for i in range(start, end):
            dense = dense_embeddings[i]
            sp = sparse_vectors[i]
            vec = {
                DENSE_VECTOR_NAME: dense,
                SPARSE_VECTOR_NAME: models.SparseVector(indices=sp["indices"], values=sp["values"])
            }
            p = models.PointStruct(id=i, vector=vec, payload={"text": chunks[i]})
            batch.append(p)
        qdrant_client.upsert(collection_name=COLLECTION_NAME, points=batch)
        print(f"Uploaded batch {start}-{end-1}")
        time.sleep(0.2)


if __name__ == "__main__":
    chunks = load_chunks(INPUT_FILE)
    if not chunks:
        print("No chunks found. Exiting.")
        raise SystemExit(0)

    ensure_hybrid_collection(recreate=RECREATE_COLLECTION)

    # Dense embeddings - use cache on disk to avoid reembedding
    dense_cache = "embeddings_cache.json"
    dense_embeddings = []
    if os.path.exists(dense_cache):
        with open(dense_cache, "r", encoding="utf-8") as f:
            dense_embeddings = json.load(f)
        if len(dense_embeddings) != len(chunks):
            print("Dense cache length mismatch; regenerating dense embeddings.")
            dense_embeddings = []

    if not dense_embeddings:
        print("Generating dense embeddings (Gemini)... this may take a while.")
        for c in tqdm(chunks, desc="dense embed"):
            emb = create_dense_embedding(c)
            dense_embeddings.append(emb)
        with open(dense_cache, "w", encoding="utf-8") as f:
            json.dump(dense_embeddings, f)

    # Sparse embeddings via fastembed (SPLADE)
    sparse_vectors = embed_sparse_chunks(chunks)

    # Upload both
    upload_hybrid(chunks, dense_embeddings, sparse_vectors)

    print("Done uploading.")
