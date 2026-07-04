from typing import List, Dict, Any
from app.embed_store import load_index, embedding_model

def search_transcript(video_id: str, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
    """
    Searches the saved transcript chunks for the most relevant matches to the query.
    """
    # 1. Load the existing database for this video
    collection = load_index(video_id)
    if not collection:
        raise ValueError(f"No database found for video {video_id}. Run embed_store first.")
        
    # 2. Embed the user's question
    # CRITICAL: bge-base requires this exact prefix for user queries to get the best results!
    query_prefix = "Represent this sentence for searching relevant passages: "
    full_query = query_prefix + query
    
    # Generate the math vector for the query (no progress bar needed for a single sentence)
    query_embedding = embedding_model.encode([full_query]).tolist()
    
    # 3. Ask ChromaDB for the top_k closest matches
    results = collection.query(
        query_embeddings=query_embedding,
        n_results=top_k
    )
    
    # 4. Format the messy ChromaDB output into a clean, easy-to-read list
    formatted_results = []
    
    # Chroma returns lists of lists. Since we only asked 1 question, we grab the first list [0]
    if results['documents'] and results['documents'][0]:
        docs = results['documents'][0]
        metas = results['metadatas'][0]
        distances = results['distances'][0]
        
        for i in range(len(docs)):
            formatted_results.append({
                "text": docs[i],
                "start_time": metas[i]["start_time"],
                "distance": distances[i] # Lower distance means a closer mathematical match
            })
            
    return formatted_results

# ---------------------------------------------------------
# Standalone Testing Block
# ---------------------------------------------------------
if __name__ == "__main__":
    from app.ingest import extract_video_id
    
    # We are using the LangChain tutorial video you already embedded in Stage 2
    test_url = "https://www.youtube.com/watch?v=sVcwVQRHIc8" 
    vid_id = extract_video_id(test_url)
    
    # Test Questions
    questions = [
        "What is retrieval augmented generation?",
        "Why is most of the world's data private?"
    ]
    
    for q in questions:
        print(f"\n======================================")
        print(f"QUESTION: {q}")
        print(f"======================================")
        
        try:
            matches = search_transcript(vid_id, q, top_k=3)
            for i, match in enumerate(matches):
                print(f"\n--- Result #{i+1} (Timestamp: {match['start_time']:.2f}s) ---")
                print(match['text'])
        except Exception as e:
            print(f"Failed: {e}")