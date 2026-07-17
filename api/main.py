from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import time
# Import the pipeline tools 
from app.ingest import extract_video_id, get_transcript_chunks
from app.embed_store import build_index, load_index
from app.router_agent import route_question
from app.retriever import search_transcript
from app.qa_chain import generate_answer

# Initialize the API
app = FastAPI(title="TubeRAG API", description="YouTube Video Knowledge Engine")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------
# Pydantic Models (Strict Data Validation for Inputs/Outputs)
# ---------------------------------------------------------
class IngestRequest(BaseModel):
    url: str

class IngestResponse(BaseModel):
    video_id: str
    message: str
    chunks_processed: int

class QueryRequest(BaseModel):
    video_id: str
    query: str

class QueryResponse(BaseModel):
    answer: str
    classification: str

# ---------------------------------------------------------
# Endpoints
# ---------------------------------------------------------

@app.post("/ingest", response_model=IngestResponse)
def ingest_video(request: IngestRequest):
    """Takes a YouTube URL, chunks it, and saves it to the vector database."""
    try:
        vid_id = extract_video_id(request.url)
        
        # SMART FIX: Check if we ALREADY processed this video in the database
        existing_collection = load_index(vid_id)
        if existing_collection and existing_collection.count() > 0:
            return IngestResponse(
                video_id=vid_id, 
                message="Video already exists in database. Skipped YouTube download.",
                chunks_processed=existing_collection.count()
            )

        # If it's a new video, proceed to Stage 1: Get Chunks from YouTube
        chunks = get_transcript_chunks(request.url)
        
        if not chunks:
            raise HTTPException(status_code=400, detail="Could not get transcript. Captions may be disabled.")
            
        # Stage 2: Embed and Store
        build_index(chunks, vid_id)
        
        return IngestResponse(
            video_id=vid_id, 
            message="Successfully ingested and embedded video.",
            chunks_processed=len(chunks)
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/query", response_model=QueryResponse)
def query_video(request: QueryRequest):
    """Takes a video ID and a question, routes it, and generates an answer."""

    start_time = time.time()
    try:
        # Stage 5: Agent Classification
        category = route_question(request.query)
        
        if category == "VAGUE":
            return QueryResponse(
                answer="Your question is too vague. Can you be more specific?",
                classification=category
            )
        elif category == "OUT_OF_SCOPE":
            return QueryResponse(
                answer="This question seems unrelated to the video's content.",
                classification=category
            )
            
        # Stage 3: Retrieval (Only runs if ANSWERABLE)
        # Note: We use top_k=3 to keep it fast and focused
        chunks = search_transcript(request.video_id, request.query, top_k=3)
        if not chunks:
            return QueryResponse(
                answer="I couldn't find any relevant information in this video.",
                classification=category
            )
            
        # Stage 4: Generate Final Answer
        final_answer = generate_answer(request.query, chunks)
        end_time = time.time() # Stop the stopwatch!
        total_seconds = end_time - start_time
        print(f"Total API Response Time: {total_seconds:.2f} seconds")
        
        return QueryResponse(
            answer=final_answer,
            classification=category
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
    
    

    
    
    