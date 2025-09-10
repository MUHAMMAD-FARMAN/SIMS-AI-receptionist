import os
from qdrant_client import QdrantClient
from dotenv import load_dotenv

load_dotenv()

QDRANT_URL = os.getenv("QDRANT_URL")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")

if not QDRANT_URL or not QDRANT_API_KEY:
    print("Please set QDRANT_URL and QDRANT_API_KEY in your .env file.")
else:
    try:
        client = QdrantClient(
            url=QDRANT_URL,
            api_key=QDRANT_API_KEY,
            timeout=10 # Set a short timeout for the test
        )
        
        # This is a simple request that should not fail due to a write timeout
        # It will raise an exception if the URL or API key is wrong
        client.get_collections()
        print("Successfully connected to Qdrant!")
    except Exception as e:
        print(f"Failed to connect to Qdrant. Error: {e}")
        

