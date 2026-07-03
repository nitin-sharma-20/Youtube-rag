import re
from typing import List, Dict, Any
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api._errors import TranscriptsDisabled, NoTranscriptFound

def extract_video_id(url: str) -> str:
    """Extracts the YouTube video ID using simple string splitting."""
    
    # 1. Handle short mobile links (like https://youtu.be/sVcwVQRHIc8)
    if "youtu.be/" in url:
        # Cut the string in half at "youtu.be/" and keep the right side (index 1)
        right_side = url.split("youtu.be/")[1]
        
        # If there's extra stuff at the end (like ?t=50s), cut at the "?" and keep the left side (index 0)
        clean_id = right_side.split("?")[0]
        return clean_id
        
    # 2. Handle standard desktop links (like https://www.youtube.com/watch?v=sVcwVQRHIc8&t=2111s)
    elif "v=" in url:
        # Cut the string in half at "v=" and keep the right side
        right_side = url.split("v=")[1]
        
        # If there's extra stuff at the end (like &t=2111s), cut at the "&" and keep the left side
        clean_id = right_side.split("&")[0]
        return clean_id
        
    # 3. If neither pattern exists, raise an error
    else:
        raise ValueError(f"Could not extract video ID from URL: {url}")

def get_transcript_chunks(url: str, chunk_size: int = 500) -> List[Dict[str, Any]]:
    """
    Fetches transcript and chunks it into ~500 character blocks,
    preserving the earliest timestamp for each chunk.
    """
    video_id = extract_video_id(url)
    
    try:
        # Fetch the transcript (defaults to English if available)
        api = YouTubeTranscriptApi()
        transcript = api.fetch(video_id)
    except (TranscriptsDisabled, NoTranscriptFound) as e:
        # Handle the failure case gracefully!
        print(f"Error: Captions are disabled or not found for video {url}")
        return []
    except Exception as e:
        print(f"Error fetching transcript: {str(e)}")
        return []

    chunks = []
    current_chunk_text = ""
    current_chunk_start = None
    
    # with open("fetched.txt", "w", encoding="utf-8") as file:
    #     file.write(str(transcript))

    for entry in transcript:
        text = entry.text.replace('\n', ' ').strip()
        start = entry.start    

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
        "https://www.youtube.com/watch?v=ZpF6IE0rdxA"
    ]

    for url in test_urls:
        print(f"\n--- Testing URL: {url} ---")
        try:
            chunks = get_transcript_chunks(url)
            if not chunks:
                print("No chunks returned (graceful failure).")
                continue
            
            # Print the first 2 chunks to verify
            
            print(f"Successfully created {len(chunks)} chunks.")
            for i, chunk in enumerate(chunks[:2]):
                print(f"Chunk {i+1} [Start: {chunk['metadata']['start_time']:.2f}s]:")
                print(f"{chunk['text']}\n")
                
        except Exception as e:
            print(f"Unexpected crash: {e}")