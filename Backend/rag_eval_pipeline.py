import os
import json
import random
import asyncio
import google.generativeai as genai
from tqdm import tqdm
from typing import List, Dict
from qdrant_client import QdrantClient
from qdrant_client.http.models import ScoredPoint
from qdrant_client.http.models import Distance, VectorParams
from fastembed import SparseTextEmbedding
import numpy as np

# -------------------------
# CONFIG
# -------------------------
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
QDRANT_URL = os.getenv("QDRANT_URL")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")

COLLECTION_NAME = "hospital-rag-eval"
VECTOR_SIZE = 3072
DATASET_DIR = "beir_dataset"
os.makedirs(DATASET_DIR, exist_ok=True)

genai.configure(api_key=GOOGLE_API_KEY)
llm = genai.GenerativeModel("gemini-1.5-flash")

qdrant = QdrantClient(url=QDRANT_URL, api_key=QDRANT_API_KEY)

# SPLADE model (500MB load)
sparse_model = SparseTextEmbedding(model_name="splade")

# -------------------------
# 1. Synthetic Query Generation
# -------------------------
async def generate_queries_for_chunk(doc_id: str, text: str, num_q: int = 3) -> List[Dict]:
    prompt = f"Generate {num_q} realistic user questions that could be answered by this passage:\n\n{text}"
    response = await asyncio.to_thread(llm.generate_content, prompt)
    if not hasattr(response, "text"):
        return []
    questions = [q.strip("-• \n") for q in response.text.split("\n") if q.strip()]
    return [{"query": q, "doc_id": doc_id} for q in questions[:num_q]]

async def build_dataset(chunks: List[str], num_q: int = 3):
    corpus, queries, qrels = {}, {}, {}

    tasks = []
    for i, chunk in enumerate(chunks):
        doc_id = f"doc{i}"
        corpus[doc_id] = {"_id": doc_id, "text": chunk}
        tasks.append(generate_queries_for_chunk(doc_id, chunk, num_q))

    results = await asyncio.gather(*tasks)

    q_idx = 0
    for res in results:
        for pair in res:
            qid = f"q{q_idx}"
            queries[qid] = {"_id": qid, "text": pair["query"]}
            qrels[qid] = {pair["doc_id"]: 1}
            q_idx += 1

    # Save BEIR-style dataset
    with open(os.path.join(DATASET_DIR, "corpus.jsonl"), "w", encoding="utf-8") as f:
        for doc in corpus.values():
            f.write(json.dumps(doc) + "\n")

    with open(os.path.join(DATASET_DIR, "queries.jsonl"), "w", encoding="utf-8") as f:
        for q in queries.values():
            f.write(json.dumps(q) + "\n")

    with open(os.path.join(DATASET_DIR, "qrels.txt"), "w", encoding="utf-8") as f:
        for qid, doc_dict in qrels.items():
            for doc_id, rel in doc_dict.items():
                f.write(f"{qid} 0 {doc_id} {rel}\n")

    return corpus, queries, qrels

# -------------------------
# 2. Qdrant Setup
# -------------------------
def setup_collection():
    qdrant.recreate_collection(
        collection_name=COLLECTION_NAME,
        vectors_config={
            "dense": VectorParams(size=VECTOR_SIZE, distance=Distance.COSINE),
            "sparse": VectorParams(size=sparse_model.dimensions, distance=Distance.DOT),
        }
    )
    print(f"Collection '{COLLECTION_NAME}' created.")

def upload_corpus(corpus: Dict[str, Dict]):
    from google.generativeai import embed_content

    points = []
    for doc_id, doc in tqdm(corpus.items(), desc="Uploading docs"):
        # Dense
        dense = embed_content(model="models/gemini-embedding-001", content=doc["text"], task_type="RETRIEVAL_DOCUMENT")["embedding"]
        # Sparse
        sparse = sparse_model.encode([doc["text"]])[0]

        points.append({
            "id": doc_id,
            "vector": {"dense": dense, "sparse": sparse},
            "payload": {"text": doc["text"]}
        })
    qdrant.upsert(collection_name=COLLECTION_NAME, points=points)

# -------------------------
# 3. Evaluation
# -------------------------
def search_dense(query: str, top_k: int = 5) -> List[str]:
    dense = genai.embed_content(model="models/gemini-embedding-001", content=query, task_type="RETRIEVAL_QUERY")["embedding"]
    hits = qdrant.search(collection_name=COLLECTION_NAME, query_vector=("dense", dense), limit=top_k, with_payload=False)
    return [h.id for h in hits]

def search_hybrid_bm25(query: str, top_k: int = 5) -> List[str]:
    dense = genai.embed_content(model="models/gemini-embedding-001", content=query, task_type="RETRIEVAL_QUERY")["embedding"]
    hits = qdrant.query_points(
        collection_name=COLLECTION_NAME,
        prefetch=[
            {"query": {"dense": dense}, "weight": 0.5},
            {"query": {"sparse": sparse_model.encode([query])[0]}, "weight": 0.5},
        ],
        limit=top_k
    ).points
    return [h.id for h in hits]

def eval_pipeline(queries: Dict[str, Dict], qrels: Dict[str, Dict], search_fn, name: str):
    k = 5
    correct, total = 0, 0
    for qid, q in queries.items():
        results = search_fn(q["text"], top_k=k)
        gold = set(qrels[qid].keys())
        if any(doc_id in gold for doc_id in results):
            correct += 1
        total += 1
    print(f"{name} Recall@{k}: {correct/total:.3f}")

# -------------------------
# MAIN
# -------------------------
if __name__ == "__main__":
    # Load your hospital chunks (replace with actual file read)
    hospital_chunks = [
        "Hospital visiting hours are from 9am to 5pm every day.",
        "Emergency services are available 24/7 at the hospital.",
        "To book an appointment, please call the reception desk or use the online portal."
    ]

    # Step 1: Build dataset
    corpus, queries, qrels = asyncio.run(build_dataset(hospital_chunks, num_q=2))

    # Step 2: Setup Qdrant collection
    setup_collection()
    upload_corpus(corpus)

    # Step 3: Evaluate
    eval_pipeline(queries, qrels, search_dense, "Dense Only")
    eval_pipeline(queries, qrels, search_hybrid_bm25, "Hybrid (Dense+SPLADE)")
