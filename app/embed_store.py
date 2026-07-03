import os
import chromadb
from typing import List, Dict, Any
from sentence_transformers import SentenceTransformer

# ---------------------------------------------------------
# 1. Module-level Singletons (Load once, use many times)
# ---------------------------------------------------------

# Set up Persistent ChromaDB. It automatically saves files to tuberag/data/chroma_db
DB_PATH = os.path.join(os.getcwd(), "data", "chroma_db")
chroma_client = chromadb.PersistentClient(path=DB_PATH)

# Load the BAAI/bge-base-en-v1.5 model once. 
MODEL_NAME = "BAAI/bge-base-en-v1.5"
print(f"Loading embedding model {MODEL_NAME}... (This takes a few seconds)")
embedding_model = SentenceTransformer(MODEL_NAME)
print("Model loaded successfully.")

# ---------------------------------------------------------
# 2. Functions
# ---------------------------------------------------------

def build_index(chunks: List[Dict[str, Any]], video_id: str):
    """
    Creates a Chroma collection for the video and embeds all chunks into it.
    """
    # get_or_create prevents errors if it already exists
    collection = chroma_client.get_or_create_collection(name=video_id)
    
    # If we already have data in this collection, skip the heavy embedding!
    if collection.count() > 0:
        print(f"Collection {video_id} already contains {collection.count()} chunks. Skipping embedding.")
        return collection
    
    print(f"Embedding {len(chunks)} chunks for video {video_id}. This might take a minute or two...")
    
    # Extract just the text strings and metadata dictionaries from our chunks
    texts = [chunk["text"] for chunk in chunks]
    metadatas = [chunk["metadata"] for chunk in chunks]
    
    # Create unique IDs for each chunk: "videoID_0", "videoID_1", etc.
    ids = [f"{video_id}_{i}" for i in range(len(chunks))]
    
    # Generate the embeddings!
    # Note: As per your plan, documents/passages do NOT need a prefix. 
    # We will only use the prefix later when the user types a query.
    embeddings = embedding_model.encode(texts, show_progress_bar=True).tolist()
    
    # Add everything to the Chroma database (saves to disk automatically)
    collection.add(
        embeddings=embeddings,
        documents=texts,
        metadatas=metadatas,
        ids=ids
    )
    
    print(f"Successfully embedded and saved {len(chunks)} chunks to disk.")
    return collection

def load_index(video_id: str):
    """
    Retrieves the existing collection from disk without re-embedding anything.
    """
    try:
        collection = chroma_client.get_collection(name=video_id)
        print(f"Loaded existing index for {video_id} with {collection.count()} chunks.")
        return collection
    except Exception:
        print(f"No existing index found for video {video_id}.")
        return None

# ---------------------------------------------------------
# 3. Standalone Testing Block
# ---------------------------------------------------------
if __name__ == "__main__":
    from ingest import get_transcript_chunks, extract_video_id
    
    test_url = "https://www.youtube.com/watch?v=sVcwVQRHIc8" # 40 min LangChain tutorial
    vid_id = extract_video_id(test_url)
    
    # 1. Fetch chunks (re-using your Stage 1 code)
    print("\n--- Step 1: Fetching chunks ---")
    my_chunks = get_transcript_chunks(test_url)
    
    if my_chunks:
        # 2. Build Index (This will take a minute on the first run)
        print("\n--- Step 2: Building Index ---")
        build_index(my_chunks, vid_id)
        
        # 3. Test Instant Loading
        print("\n--- Step 3: Testing Instant Load ---")
        load_index(vid_id)