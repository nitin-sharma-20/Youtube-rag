import os
from typing import List, Dict, Any
from dotenv import load_dotenv
from groq import Groq

# Load the API key from the .env file
load_dotenv()
api_key = os.getenv("GROQ_API_KEY")

if not api_key:
    raise ValueError("GROQ_API_KEY is not set in the .env file!")

# Initialize the Groq client
client = Groq(api_key=api_key)

def generate_answer(query: str, retrieved_chunks: List[Dict[str, Any]]) -> str:
    """
    Takes the user's question and the chunks we found in the database,
    and asks Llama 3 (via Groq) to construct a final answer.
    """
    
    # 1. Format the chunks into a readable text block
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

    # 3. Call Groq using the open-source Llama 3 model
    completion = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "user", "content": prompt}
        ],
        temperature=0.0 # Set to 0 so it doesn't get "creative" and hallucinate
    )
    return completion.choices[0].message.content

def generate_out_of_scope_answer(query: str) -> str:
    """
    Answers a question using general world knowledge, but explicitly
    informs the user that this topic is not covered in the video.
    """
    prompt = f"""
You are a helpful assistant. The user is asking a question that is NOT covered in the YouTube video they are watching.

INSTRUCTIONS:
1. Start your response with a clear disclaimer, for example: "This topic isn't covered in the video, but here's what I know:"
2. Then answer the question using your general knowledge.
3. Keep the answer concise and accurate.

USER QUESTION:
{query}
"""
    completion = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3
    )
    return completion.choices[0].message.content

# --- Testing Block ---
if __name__ == "__main__":
    from app.retriever import search_transcript
    from app.ingest import extract_video_id
    
    test_url = "https://www.youtube.com/watch?v=sVcwVQRHIc8"
    vid_id = extract_video_id(test_url)
    
    q1 = "Where does Lance Martin work?"
    print(f"\n[Test 1] Question: {q1}")
    chunks1 = search_transcript(vid_id, q1, top_k=3)
    answer1 = generate_answer(q1, chunks1)
    print(f"ANSWER:\n{answer1}\n")