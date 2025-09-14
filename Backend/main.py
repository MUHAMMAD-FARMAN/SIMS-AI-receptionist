# main.py
"""
FastAPI backend that uses Qdrant server-side BM25 + Gemini dense vectors.
- Qdrant will compute BM25 sparse vectors (if collection was ingested with models.Document(..., model='Qdrant/bm25'))
- The endpoint '/query' asks Qdrant to run a hybrid query via Query API (prefetch + FusionQuery)
Fallback: if server-side hybrid throws (no inference support), we fall back to dense-only search.
"""

import os
import asyncio
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from qdrant_client import QdrantClient, models
import google.generativeai as genai
from tenacity import retry, wait_exponential, stop_after_attempt
from fastapi.middleware.cors import CORSMiddleware

load_dotenv()

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
QDRANT_URL = os.getenv("QDRANT_URL")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")

if not GOOGLE_API_KEY or not QDRANT_URL or not QDRANT_API_KEY:
    raise SystemExit("Set GOOGLE_API_KEY, QDRANT_URL and QDRANT_API_KEY in .env")

# Config
COLLECTION_NAME = "hospital-rag-data-hybrid"  # must match ingestion
DENSE_VECTOR_NAME = "dense"
SPARSE_VECTOR_NAME = "bm25"
VECTOR_SIZE = 3072
EMBEDDING_MODEL = "models/gemini-embedding-001"
LLM_MODEL = "gemini-1.5-flash"

# Init clients
genai.configure(api_key=GOOGLE_API_KEY)
qdrant = QdrantClient(url=QDRANT_URL, api_key=QDRANT_API_KEY)
llm = genai.GenerativeModel(LLM_MODEL)

app = FastAPI(title="RAG API (Qdrant BM25 + Gemini)")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])


class QueryRequest(BaseModel):
    query: str


@retry(wait=wait_exponential(multiplier=1, min=2, max=8), stop=stop_after_attempt(4))
async def get_dense_embedding(text: str):
    resp = await asyncio.to_thread(genai.embed_content, model=EMBEDDING_MODEL, content=text, task_type="RETRIEVAL_DOCUMENT")
    return resp["embedding"]


async def get_llm_answer(prompt: str):
    try:
        resp = await asyncio.to_thread(llm.generate_content, prompt, stream=False)
        return resp.text if hasattr(resp, "text") else ""
    except Exception as e:
        print("LLM generation failed:", e)
        return "I don't have enough information to answer that."


@app.post("/query")
async def query_endpoint(req: QueryRequest):
    q = req.query.strip()
    if not q:
        raise HTTPException(status_code=400, detail="Empty query")

    try:
        # 1) compute dense embedding locally (Gemini)
        # lowercase the query text
        q = q.lower()
        query_dense = await get_dense_embedding(q)

        # 2) Build prefetch list:
        #    - dense prefetch: use the dense vector and tell Qdrant to search the 'dense' named vector
        #    - sparse prefetch: send a Document to Qdrant and let it compute BM25 sparse query on the server
        prefetchs = [
            models.Prefetch(
                query=query_dense,
                using=DENSE_VECTOR_NAME,
                limit=50
            ),
            models.Prefetch(
                query=models.Document(text=q, model="Qdrant/bm25"),
                using=SPARSE_VECTOR_NAME,
                limit=50
            ),
        ]

        # 3) Ask Qdrant to fuse results server-side using RRF fusion
        fusion_query = models.FusionQuery(fusion=models.Fusion.RRF)

        try:
            # query_points will run the prefetches and fuse results on the server.
            result = qdrant.query_points(
                collection_name=COLLECTION_NAME,
                prefetch=prefetchs,
                query=fusion_query,
                with_payload=True,
                limit=6
            )
            points = result.points if hasattr(result, "points") else result
        except Exception as e:
            # If server-side hybrid is not supported by this Qdrant cluster, fallback to dense-only search
            print("Server-side hybrid query failed (maybe cluster has no inference support):", e)
            print("Falling back to dense-only Qdrant search.")
            hits = qdrant.search(
                collection_name=COLLECTION_NAME,
                query_vector=query_dense,
                limit=6,
                with_payload=True,
                vector_name=DENSE_VECTOR_NAME
            )
            points = hits

        # 4) Build context for LLM
        context_parts = []
        sources = []
        for p in points:
            payload_text = "N/A"
            try:
                if p.payload and "text" in p.payload:
                    payload_text = p.payload.get("text")
                else:
                    payload_text = str(p.payload)
            except Exception:
                payload_text = "N/A"
            context_parts.append(f"Content: {payload_text}")
            sources.append({"id": p.id, "text": payload_text})
        context = "\n\n".join(context_parts)

        if not context.strip():
            return {"query": q, "answer": "I don't have enough information to answer that.", "sources": []}

        # 5) Ask LLM (Gemini) to answer using the retrieved context
        full_prompt = (
            "You are a helpful assistant. Use the following context to answer the question. "
            "If the answer is not in the context, say 'I don't have enough information to answer that.'\n\n"
            f"Context:\n{context}\n\nQuestion: {q}\n\nAnswer:"
        )
        answer = await get_llm_answer(full_prompt)

        # return {"query": q, "answer": answer, "sources": sources}
        return {"answer": answer}

    except Exception as e:
        print("Error in /query:", e)
        raise HTTPException(status_code=500, detail=str(e))
