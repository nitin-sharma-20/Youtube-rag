import os
from groq import Groq
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv("GROQ_API_KEY")

if not api_key:
    raise ValueError("GROQ_API_KEY is not set in the .env file!")

client = Groq(api_key=api_key)

def route_question(query: str) -> str:
    """
    Acts as an intelligent router using Llama 3. Classifies the user's question.
    """
    prompt = f"""
You are an intelligent routing agent for a YouTube video Q&A system.
Your job is to analyze the user's question and classify it into exactly ONE of the following three categories:

1. ANSWERABLE: The question is specific and likely to be answered by the contents of a technical video, tutorial, or lecture.
2. VAGUE: The question is too short or lacks context to search a database effectively (e.g., "what is it?", "tell me more", "why?").
3. OUT_OF_SCOPE: The question is a general knowledge question clearly unrelated to a specific video's content (e.g., "what is the capital of France?", "write a poem").

Output ONLY the exact category name (ANSWERABLE, VAGUE, or OUT_OF_SCOPE). Do not output any other text or punctuation.

USER QUESTION: {query}
"""
    
    completion = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.0
    )
    
    category = completion.choices[0].message.content.strip().upper()
    
    if category not in ["ANSWERABLE", "VAGUE", "OUT_OF_SCOPE"]:
        category = "ANSWERABLE" 
        
    return category

# --- Testing Block ---
if __name__ == "__main__":
    test_queries = ["Where does Lance Martin work?", "What is it?", "What is the capital of France?"]
    for q in test_queries:
        print(f"\nQuestion: {q}")
        print(f"Agent Decision: {route_question(q)}")