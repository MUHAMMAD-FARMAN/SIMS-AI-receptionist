# -----------------------------------------------------------------------------
# File: main.py
"""
FastAPI backend that performs hybrid search using Gemini dense embeddings and
FastEmbed SPLADE sparse vectors already uploaded to Qdrant by qdrant_loader.py.

Requirements:
  pip install qdrant-client fastembed google-generativeai fastapi uvicorn

Run:
  uvicorn main:app --reload --port 8000

Notes:
 - This code expects the collection to have named vectors: 'dense' and 'sparse'.
 - The sparse model is loaded at startup for query-time sparse encoding.
"""

import os
import asyncio
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from qdrant_client import QdrantClient, models
from qdrant_client.models import VectorParams, SparseVectorParams, Distance
import google.generativeai as genai
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from tenacity import retry, wait_exponential, stop_after_attempt
from fastembed import SparseTextEmbedding

load_dotenv()
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
QDRANT_URL = os.getenv("QDRANT_URL")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")

if not GOOGLE_API_KEY or not QDRANT_URL or not QDRANT_API_KEY:
    raise SystemExit("Set GOOGLE_API_KEY, QDRANT_URL and QDRANT_API_KEY in .env")

# Config
COLLECTION_NAME = "hospital-rag-data"
DENSE_VECTOR_NAME = "dense"
SPARSE_VECTOR_NAME = "sparse"
VECTOR_SIZE = 3072
SPARSE_MODEL_NAME = "prithivida/Splade_PP_en_v1"
EMBEDDING_MODEL = "models/gemini-embedding-001"

# Init clients and models
genai.configure(api_key=GOOGLE_API_KEY)
qdrant_client = QdrantClient(url=QDRANT_URL, api_key=QDRANT_API_KEY)

# Load sparse encoder at startup
sparse_encoder = SparseTextEmbedding(model_name=SPARSE_MODEL_NAME)

# Simple LLM wrapper
llm_model = genai.GenerativeModel("gemini-1.5-flash")

# FastAPI app
app = FastAPI(title="RAG Hybrid API")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

class QueryRequest(BaseModel):
    query: str

@retry(wait=wait_exponential(multiplier=1, min=4, max=10), stop=stop_after_attempt(5))
async def get_embedding(text: str):
    return await asyncio.to_thread(genai.embed_content, model=EMBEDDING_MODEL, content=text, task_type="RETRIEVAL_DOCUMENT")

async def compute_sparse_query(text: str):
    # fastembed returns generator, collect first result
    sparse_gen = sparse_encoder.embed([text])
    sparse_list = list(sparse_gen)
    if not sparse_list:
        return None
    se = sparse_list[0]
    return models.SparseVector(indices=list(map(int, se.indices)), values=[float(v) for v in se.values])

# Simple RRF fusion (same idea as before)
RRF_K = 60

def reciprocal_rank_fusion(lists_of_ids, k=RRF_K):
    agg = {}
    for id_list in lists_of_ids:
        for rank, _id in enumerate(id_list):
            score = 1.0 / (k + rank + 1)
            agg[_id] = agg.get(_id, 0.0) + score
    return [i for i, s in sorted(agg.items(), key=lambda kv: kv[1], reverse=True)]

@app.post("/query")
async def query_endpoint(req: QueryRequest):
    try:
        q = req.query
        dense_resp = await asyncio.to_thread(genai.embed_content, model=EMBEDDING_MODEL, content=q, task_type="RETRIEVAL_DOCUMENT")
        query_vector = dense_resp["embedding"]

        # dense search
        dense_hits = qdrant_client.search(collection_name=COLLECTION_NAME, query_vector=query_vector, limit=20, with_payload=True, vector_name=DENSE_VECTOR_NAME)

        # sparse query
        try:
            sparse_vec = await asyncio.to_thread(compute_sparse_query, q)
            named_sparse = models.NamedSparseVector(name=SPARSE_VECTOR_NAME, vector=sparse_vec)
            sparse_hits = qdrant_client.search(collection_name=COLLECTION_NAME, query_vector=named_sparse, limit=50, with_payload=True)
        except Exception as e:
            print("Sparse query failed:", e)
            sparse_hits = []

        # fuse
        dense_ids = [h.id for h in dense_hits]
        sparse_ids = [h.id for h in sparse_hits]
        fused = reciprocal_rank_fusion([dense_ids, sparse_ids])[:6]

        # build final hits preserving payloads
        id_map = {h.id: h for h in dense_hits}
        for h in sparse_hits:
            if h.id not in id_map:
                id_map[h.id] = h
        final_hits = [id_map[i] for i in fused if i in id_map]

        # build context
        context = "\n\n".join([h.payload.get("text", str(h.payload)) for h in final_hits])
        if not context.strip():
            return {"answer": "I don't have enough information to answer that.", "sources": []}

        # call LLM
        full_prompt = f"You are a helpful assistant. Use the following context to answer the question:\n\nContext: {context}\n\nQuestion: {q}\n\nAnswer:"
        llm_out = await asyncio.to_thread(llm_model.generate_content, full_prompt, stream=False)
        answer = llm_out.text if hasattr(llm_out, "text") else ""

        return {"query": q, "answer": answer, "sources": [{"id": h.id, "text": h.payload.get("text", "")} for h in final_hits]}

    except Exception as e:
        print("Error in /query:", e)
        raise HTTPException(status_code=500, detail=str(e))
