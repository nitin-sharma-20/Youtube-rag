import os
from typing import List, Dict, Any
from dotenv import load_dotenv
from supadata import Supadata

# Load the API key from .env
load_dotenv()

def extract_video_id(url: str) -> str:
    """Extracts the YouTube video ID using simple string splitting."""
    
    # 1. Handle short mobile links (like https://youtu.be/sVcwVQRHIc8)
    if "youtu.be/" in url:
        right_side = url.split("youtu.be/")[1]
        clean_id = right_side.split("?")[0]
        return clean_id
        
    # 2. Handle standard desktop links (like https://www.youtube.com/watch?v=sVcwVQRHIc8)
    elif "v=" in url:
        right_side = url.split("v=")[1]
        clean_id = right_side.split("&")[0]
        return clean_id
        
    # 3. If neither pattern exists, raise an error
    else:
        raise ValueError(f"Could not extract video ID from URL: {url}")

def get_transcript_chunks(url: str, chunk_size: int = 500) -> List[Dict[str, Any]]:
    """
    Fetches transcript using the official Supadata SDK to bypass YouTube rate limits,
    and chunks it into ~500 character blocks, preserving the earliest timestamp.
    """
    video_id = extract_video_id(url)
    api_key = os.getenv("SUPADATA_API_KEY")
    
    if not api_key:
        print("Error: SUPADATA_API_KEY is not set in your .env file!")
        return []
    
    try:
        print(f"Fetching transcript for {video_id} via Supadata SDK...")
        
        # Initialize the official SDK client
        client = Supadata(api_key=api_key)
        
        # Use the new unified transcript method, passing the full URL directly
        transcript_response = client.transcript(url=url) 
        
        # The SDK returns the segments inside the .content attribute
        transcript_data = transcript_response.content
        
    except Exception as e:
        print(f"Error fetching transcript from Supadata: {str(e)}")
        return []

    chunks = []
    current_chunk_text = ""
    current_chunk_start = None

    for entry in transcript_data:
        # Use getattr() to safely extract the text and timestamp from the Python object
        text = getattr(entry, 'text', '').replace('\n', ' ').strip()
        start = getattr(entry, 'start', getattr(entry, 'offset', 0))

        if not text:
            continue

        # If this is the start of a new chunk, record the timestamp
        if current_chunk_start is None:
            current_chunk_start = start

        # Append text to the current chunk
        if current_chunk_text:
            current_chunk_text += f" {text}"
        else:
            current_chunk_text = text

        # If we hit our chunk size limit, save it and reset
        if len(current_chunk_text) >= chunk_size:
            chunks.append({
                "text": current_chunk_text,
                "metadata": {"start_time": current_chunk_start}
            })
            current_chunk_text = ""
            current_chunk_start = None

    # Catch any remaining text in the final chunk
    if current_chunk_text:
        chunks.append({
            "text": current_chunk_text,
            "metadata": {"start_time": current_chunk_start}
        })

    return chunks

# --- Standalone Testing Block ---
if __name__ == "__main__":
    # Test cases defined in your plan
    test_urls = [
        "https://www.youtube.com/watch?v=sVcwVQRHIc8"
    ]

    for url in test_urls:
        print(f"\n--- Testing URL: {url} ---")
        try:
            chunks = get_transcript_chunks(url)
            if not chunks:
                print("No chunks returned (graceful failure).")
                continue
            
            # Print the first 2 chunks to verify
            print(f"Successfully created {len(chunks)} chunks using Supadata!")
            for i, chunk in enumerate(chunks[:2]):
                print(f"Chunk {i+1} [Start: {chunk['metadata']['start_time']:.2f}s]:")
                print(f"{chunk['text']}\n")
                
        except Exception as e:
            print(f"Unexpected crash: {e}")