import os
from typing import List, Dict, Any
from dotenv import load_dotenv
from google import genai

# Load the API key from the .env file
load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    raise ValueError("GEMINI_API_KEY is not set in the .env file!")

# Initialize the modern Gemini client
client = genai.Client(api_key=api_key)

def generate_answer(query: str, retrieved_chunks: List[Dict[str, Any]]) -> str:
    """
    Takes the user's question and the chunks we found in the database,
    and asks Gemini to construct a final answer.
    """
    
    # 1. Format the chunks into a readable text block for Gemini
    context_text = ""
    for i, chunk in enumerate(retrieved_chunks):
        timestamp = chunk["start_time"]
        text = chunk["text"]
        context_text += f"\n--- Chunk {i+1} (Timestamp: {timestamp:.2f}s) ---\n{text}\n"

    # 2. Build the strict prompt template
    prompt = f"""
You are a helpful assistant answering questions based ONLY on the provided YouTube video transcript chunks.

INSTRUCTIONS:
1. Use the provided context to answer the user's question.
2. If the context contains the answer, you must cite the timestamp in your response (e.g., "At 45.2s, the video explains...").
3. If the context does NOT contain the answer, you MUST explicitly say: "I couldn't find this in the video." Do not make up an answer.

CONTEXT CHUNKS:
{context_text}

USER QUESTION: 
{query}
"""

    # 3. Call Gemini using the new modern SDK
    response = client.models.generate_content(
        model='gemini-3.5-flash',
        contents=prompt
    )
    return response.text

# ---------------------------------------------------------
# Standalone Testing Block
# ---------------------------------------------------------
if __name__ == "__main__":
    from app.retriever import search_transcript
    from app.ingest import extract_video_id
    
    test_url = "https://www.youtube.com/watch?v=sVcwVQRHIc8"
    vid_id = extract_video_id(test_url)
    
    # Test 1: In-video question (Should give a cited answer)
    q1 = "Where does Lance Martin work?"
    print(f"\n[Test 1] Question: {q1}")
    chunks1 = search_transcript(vid_id, q1, top_k=3)
    answer1 = generate_answer(q1, chunks1)
    print(f"ANSWER:\n{answer1}\n")
    
    # Test 2: Out-of-scope question (The hallucination test)
    q2 = "What is the capital of France?"
    print(f"\n[Test 2] Question: {q2}")
    chunks2 = search_transcript(vid_id, q2, top_k=3)
    answer2 = generate_answer(q2, chunks2)
    print(f"ANSWER:\n{answer2}\n")