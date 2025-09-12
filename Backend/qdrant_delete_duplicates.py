import os
from collections import defaultdict
from qdrant_client import QdrantClient
from qdrant_client.http import models
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# --- Configuration ---
QDRANT_URL = os.getenv("QDRANT_URL")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")
QDRANT_COLLECTION_NAME = "hospital-rag-data"

# Check for required environment variables
if not all([QDRANT_URL, QDRANT_API_KEY]):
    raise ValueError("Missing one or more required environment variables: QDRANT_URL, QDRANT_API_KEY")

# Initialize the Qdrant client
client = QdrantClient(
    url=QDRANT_URL,
    api_key=QDRANT_API_KEY
)

# --- Main Functions ---
def delete_duplicate_points(client: QdrantClient, collection_name: str):
    """
    Finds and deletes duplicate points in a Qdrant collection based on their text payload.
    
    Args:
        client (QdrantClient): The Qdrant client instance.
        collection_name (str): The name of the collection to clean.
    """
    print(f"Starting duplicate removal for collection '{collection_name}'...")
    
    # Step 1: Check if the collection exists
    try:
        collection_exists = client.collection_exists(collection_name=collection_name)
        if not collection_exists:
            print(f"Error: Collection '{collection_name}' not found. Exiting.")
            return
    except Exception as e:
        print(f"Error checking for collection existence: {e}")
        return

    # Step 2: Scroll through the collection to get all points
    # We'll use a dictionary to store points by their text content
    points_by_text = defaultdict(list)
    try:
        all_points = client.scroll(
            collection_name=collection_name,
            limit=100,  # Scroll limit, can be adjusted
            with_vectors=False,
            with_payload=True
        )

        for points, _ in all_points:
            for point in points:
                if "text" in point.payload:
                    text_content = point.payload["text"]
                    points_by_text[text_content].append(point.id)

        print(f"Found a total of {len(points_by_text)} unique text entries.")

    except Exception as e:
        print(f"Error scrolling through the collection: {e}")
        return

    # Step 3: Identify and collect IDs of duplicate points
    duplicate_ids_to_delete = []
    for text_content, point_ids in points_by_text.items():
        if len(point_ids) > 1:
            # Keep the first point, delete the rest
            duplicate_ids_to_delete.extend(point_ids[1:])
            print(f"Found {len(point_ids) - 1} duplicates for text: '{text_content[:50]}...'")

    if not duplicate_ids_to_delete:
        print("No duplicate points found.")
        return

    # Step 4: Delete the identified duplicates in batches
    # We will use a batch size of 100 to avoid timeouts
    batch_size = 100
    for i in range(0, len(duplicate_ids_to_delete), batch_size):
        batch_ids = duplicate_ids_to_delete[i:i + batch_size]
        try:
            client.delete(
                collection_name=collection_name,
                points_selector=models.PointIdsSelector(point_ids=batch_ids)
            )
            print(f"Deleted batch of {len(batch_ids)} duplicate points.")
        except Exception as e:
            print(f"Error deleting batch starting at index {i}: {e}")
            return # Exit on error to prevent partial deletion

    print(f"\nSuccessfully deleted a total of {len(duplicate_ids_to_delete)} duplicate points.")
    
    # Optional: Print the new count of points in the collection
    try:
        count_result = client.count(collection_name=collection_name)
        print(f"The collection now contains {count_result.count} total points.")
    except Exception as e:
        print(f"Could not get final point count: {e}")


if __name__ == "__main__":
    print("Starting Qdrant duplicate removal script...")
    delete_duplicate_points(client, QDRANT_COLLECTION_NAME)
