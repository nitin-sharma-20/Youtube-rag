import os
from google import genai
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    raise ValueError("GEMINI_API_KEY is not set in the .env file!")

client = genai.Client(api_key=api_key)

def route_question(query: str) -> str:
    """
    Acts as an intelligent router. Classifies the user's question before we 
    waste time searching the database.
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
    
    response = client.models.generate_content(
        model='gemini-3.5-flash',
        contents=prompt
    )
    
    # Clean the response to ensure we just get the raw word
    category = response.text.strip().upper()
    
    # Safety fallback: if the AI accidentally outputs weird text, default to trying to answer it
    if category not in ["ANSWERABLE", "VAGUE", "OUT_OF_SCOPE"]:
        category = "ANSWERABLE" 
        
    return category

# ---------------------------------------------------------
# Standalone Testing Block
# ---------------------------------------------------------
if __name__ == "__main__":
    
    test_queries = [
        "Where does Lance Martin work?",      # Should route to ANSWERABLE
        "What is it?",                        # Should route to VAGUE
        "What is the capital of France?"      # Should route to OUT_OF_SCOPE
    ]
    
    for q in test_queries:
        print(f"\nQuestion: {q}")
        classification = route_question(q)
        print(f"Agent Decision: {classification}")
        
        # This simulates the logic we will use in your FastAPI app tomorrow
        if classification == "ANSWERABLE":
            print("-> Action: Proceeding to ChromaDB search...")
        elif classification == "VAGUE":
            print("-> Action: Skipping DB. Asking user to be more specific.")
        elif classification == "OUT_OF_SCOPE":
            print("-> Action: Skipping DB. Telling user this is unrelated to the video.")