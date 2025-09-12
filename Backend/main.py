import os
import asyncio
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from qdrant_client import QdrantClient
from qdrant_client.http.models import Distance, VectorParams
from qdrant_client.http.models import PointStruct, SearchRequest
import google.generativeai as genai
from contextlib import asynccontextmanager
from tenacity import retry, stop_after_attempt, wait_exponential

# Load environment variables from .env file
load_dotenv()

# --- Configuration ---
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
QDRANT_URL = os.getenv("QDRANT_URL")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")

if not GOOGLE_API_KEY:
    raise ValueError("GOOGLE_API_KEY environment variable not set.")

if not QDRANT_URL or not QDRANT_API_KEY:
    raise ValueError("QDRANT_URL and QDRANT_API_KEY environment variables must be set.")

# Initialize Gemini and Qdrant
genai.configure(api_key=GOOGLE_API_KEY)
llm_model = genai.GenerativeModel("gemini-1.5-flash")
embedding_model = "models/gemini-embedding-001"

qdrant_client = QdrantClient(url=QDRANT_URL, api_key=QDRANT_API_KEY)
COLLECTION_NAME = "hospital-rag-data"
VECTOR_SIZE = 3072 

# Pydantic model for the request body
class QueryRequest(BaseModel):
    query: str

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Handles application startup and shutdown events.
    Checks for and creates the Qdrant collection on startup.
    """
    print("Checking for Qdrant collection...")
    try:
        # Check if the collection already exists
        collections = qdrant_client.get_collections()
        if COLLECTION_NAME not in [c.name for c in collections.collections]:
            print(f"Collection '{COLLECTION_NAME}' not found. Creating it.")
            qdrant_client.create_collection(
                collection_name=COLLECTION_NAME,
                vectors_config=VectorParams(size=VECTOR_SIZE, distance=Distance.COSINE),
            )
            print(f"Collection '{COLLECTION_NAME}' created.")
        else:
            print(f"Collection '{COLLECTION_NAME}' already exists.")
    except Exception as e:
        print(f"Could not connect to Qdrant or create collection: {e}")
        # Allow the app to start even if Qdrant is not immediately available
    
    # This `yield` signals that the startup tasks are complete
    yield
    
    # Any cleanup code would go here
    print("Application shutdown complete.")

# Create the FastAPI app with the new lifespan handler
app = FastAPI(
    title="Resume RAG Backend",
    description="A FastAPI backend for a RAG system using Gemini and Qdrant.",
    version="1.0.0",
    lifespan=lifespan
)

@retry(wait=wait_exponential(multiplier=1, min=4, max=10), stop=stop_after_attempt(5))
async def get_embedding(text: str):
    """Generates an embedding for a given text using the Gemini API."""
    try:
        response = await asyncio.to_thread(
            genai.embed_content,
            model=embedding_model,
            content=text,
            task_type="RETRIEVAL_DOCUMENT"
        )
        return response["embedding"]
    except Exception as e:
        print(f"Error generating embedding: {e}")
        raise

async def get_llm_response(prompt: str, context: str):
    """Generates a response using the Gemini LLM with context."""
    full_prompt = (
        f"You are a helpful assistant. Use the following context to answer the question. "
        f"If the answer is not in the context, say 'I don't have enough information to answer that.'.\n\n"
        f"Context: {context}\n\nQuestion: {prompt}\n\nAnswer:"
    )
    try:
        response = await asyncio.to_thread(
            llm_model.generate_content,
            full_prompt,
            # tools=[{"google_search": {}}],  # Use search grounding
            stream=False,
        )
        # Check if the response contains citations
        citations = []
        if hasattr(response, 'candidates') and response.candidates and hasattr(response.candidates[0].content, 'parts'):
            for part in response.candidates[0].content.parts:
                if hasattr(part, 'text'):
                    text = part.text
                if hasattr(part, 'grounding_metadata') and hasattr(part.grounding_metadata, 'grounding_attributions'):
                    for attribution in part.grounding_metadata.grounding_attributions:
                        if hasattr(attribution, 'web'):
                            citations.append({
                                'title': attribution.web.title,
                                'uri': attribution.web.uri,
                            })
        
        # Get the text from the response
        text_response = response.text if response and hasattr(response, 'text') else "No response from LLM."
        
        return {"answer": text_response, "citations": citations}

    except Exception as e:
        print(f"Error generating LLM response: {e}")
        return {"answer": "I don't have enough information to answer that.", "citations": []}


@app.post("/query")
async def process_query(req: QueryRequest):
    """
    Accepts a query, performs a similarity search in Qdrant,
    and uses the retrieved context to answer with Gemini.
    """
    print(f"Received query: {req.query}")
    try:
        # Generate embedding for the user's query
        query_vector = await get_embedding(req.query)

        # Search the Qdrant collection
        search_result = qdrant_client.search(
            collection_name=COLLECTION_NAME,
            query_vector=query_vector,
            limit=6,  # Retrieve top 3 results
            with_payload=True
        )

        # Extract relevant context from the search results
        context = ""
        for hit in search_result:
            # Check if payload has 'text' which is the key used in qdrant_loader
            if hit.payload and 'text' in hit.payload:
                context += f"Content: {hit.payload.get('text')}\n\n"
            else:
                context += f"Content: N/A\n\n"
        
        if not context or "N/A" in context:
            return {"answer": "I don't have enough information to answer that.", "sources": []}

        # Generate LLM response with the retrieved context
        llm_response = await get_llm_response(req.query, context)
        
        return {
            "query": req.query,
            "answer": llm_response["answer"],
            "sources": [{"text": hit.payload.get('text', 'N/A')} for hit in search_result]
        }
    except Exception as e:
        print(f"An error occurred: {e}")
        raise HTTPException(status_code=500, detail=str(e))
