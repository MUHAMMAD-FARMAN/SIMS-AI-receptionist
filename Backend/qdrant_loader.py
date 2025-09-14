# qdrant_loader.py
"""
Create a Qdrant collection with dense + BM25 sparse vectors and upload points.

Requirements:
  pip install qdrant-client google-generativeai tenacity python-dotenv tqdm
Notes:
  - This code asks Qdrant to compute BM25 sparse vectors server-side by sending
    models.Document(text=..., model="Qdrant/bm25"). That requires Qdrant Cloud
    or a Qdrant server with FastEmbed/Cloud inference enabled.
"""

import os
import json
import time
from dotenv import load_dotenv
from tenacity import retry, wait_exponential, stop_after_attempt
from qdrant_client import QdrantClient, models
from qdrant_client.models import VectorParams, SparseVectorParams, Distance, Modifier
import google.generativeai as genai
from tqdm import tqdm

load_dotenv()

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
QDRANT_URL = os.getenv("QDRANT_URL")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")

if not GOOGLE_API_KEY or not QDRANT_URL or not QDRANT_API_KEY:
    raise SystemExit("Set GOOGLE_API_KEY, QDRANT_URL and QDRANT_API_KEY in .env")

# Config - change as needed
INPUT_FILE = "hospital_chunks.txt"   # one chunk per line
COLLECTION_NAME = "hospital-rag-data-hybrid"
DENSE_VECTOR_NAME = "dense"
SPARSE_VECTOR_NAME = "bm25"          # name Qdrant will use for BM25 sparse vectors
VECTOR_SIZE = 3072                   # Gemini dense dim
BATCH_SIZE = 64

# Init clients
genai.configure(api_key=GOOGLE_API_KEY)
EMBEDDING_MODEL = "models/gemini-embedding-001"
client = QdrantClient(url=QDRANT_URL, api_key=QDRANT_API_KEY)


@retry(wait=wait_exponential(multiplier=1, min=2, max=10), stop=stop_after_attempt(5))
def create_dense_embedding(text: str):
    resp = genai.embed_content(model=EMBEDDING_MODEL, content=text, task_type="RETRIEVAL_DOCUMENT")
    return resp["embedding"]


def read_chunks(path):
    if not os.path.exists(path):
        raise FileNotFoundError(f"{path} not found")
    with open(path, "r", encoding="utf-8") as f:
        return [line.strip().lower() for line in f if line.strip()]


def ensure_hybrid_collection(recreate=False):
    """
    Create collection with both dense and sparse (BM25) configs.
    If recreate=True, existing collection will be deleted (data loss).
    """
    try:
        cols = client.get_collections()
        names = [c.name for c in cols.collections]
    except Exception:
        names = []

    if COLLECTION_NAME in names:
        print(f"Collection {COLLECTION_NAME} already exists.")
        return

    # create collection with named dense + sparse BM25
    print(f"Creating collection {COLLECTION_NAME} with '{DENSE_VECTOR_NAME}' + '{SPARSE_VECTOR_NAME}'...")
    client.create_collection(
        collection_name=COLLECTION_NAME,
        vectors_config={
            DENSE_VECTOR_NAME: VectorParams(size=VECTOR_SIZE, distance=Distance.COSINE)
        },
        # set sparse modifier to IDF so BM25/IDF weighting is used
        sparse_vectors_config={
            SPARSE_VECTOR_NAME: SparseVectorParams(modifier=Modifier.IDF)
        },
    )
    print("Collection created.")


def upload_points(chunks, dense_vectors):
    """
    Upload points where sparse vector is declared as models.Document; Qdrant will
    compute BM25 sparse vectors server-side (requires Cloud / FastEmbed).
    """
    assert len(chunks) == len(dense_vectors)
    total = len(chunks)
    for start in range(0, total, BATCH_SIZE):
        end = min(start + BATCH_SIZE, total)
        batch = []
        for i in range(start, end):
            # build vector value with dense list and server-side document for BM25
            vec = {
                DENSE_VECTOR_NAME: dense_vectors[i],
                SPARSE_VECTOR_NAME: models.Document(text=chunks[i], model="Qdrant/bm25")
            }
            point = models.PointStruct(
                id=i,
                vector=vec,
                payload={"text": chunks[i]}
            )
            batch.append(point)
        client.upsert(collection_name=COLLECTION_NAME, points=batch)
        print(f"Uploaded points {start}-{end-1}")
        time.sleep(0.15)


def main():
    chunks = read_chunks(INPUT_FILE)
    if not chunks:
        print("No chunks found. Exiting.")
        return

    ensure_hybrid_collection(recreate=True)

    dense_cache = "embeddings_cache.json"
    dense_vectors = []
    if os.path.exists(dense_cache):
        with open(dense_cache, "r", encoding="utf-8") as f:
            dense_vectors = json.load(f)
        if len(dense_vectors) != len(chunks):
            print("Dense cache length mismatch. Regenerating.")
            dense_vectors = []

    if not dense_vectors:
        print("Generating dense embeddings (Gemini)...")
        for c in tqdm(chunks, desc="dense embed"):
            emb = create_dense_embedding(c)
            dense_vectors.append(emb)
        with open(dense_cache, "w", encoding="utf-8") as f:
            json.dump(dense_vectors, f)

    print("Uploading points (dense + ask Qdrant to compute BM25)...")
    upload_points(chunks, dense_vectors)
    print("Done.")


if __name__ == "__main__":
    main()
