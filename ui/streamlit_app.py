import streamlit as st
import requests

# Set the URL of our FastAPI backend
API_URL = "http://127.0.0.1:8000"

# Configure the web page
st.set_page_config(page_title="TubeRAG", page_icon="🎥", layout="centered")
st.title("🎥 TubeRAG: YouTube Knowledge Engine")
st.markdown("Ask questions about any YouTube video using RAG!")

# Initialize session state variables to remember things between button clicks
if "video_id" not in st.session_state:
    st.session_state.video_id = None
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# ---------------------------------------------------------
# Sidebar: Video Ingestion
# ---------------------------------------------------------
with st.sidebar:
    st.header("1. Load Video")
    youtube_url = st.text_input("YouTube URL:")
    
    if st.button("Process Video", type="primary"):
        if not youtube_url:
            st.warning("Please enter a URL first.")
        else:
            with st.spinner("Processing transcript & generating embeddings... This may take a minute."):
                try:
                    # Call the /ingest endpoint on our FastAPI server
                    response = requests.post(f"{API_URL}/ingest", json={"url": youtube_url})
                    
                    if response.status_code == 200:
                        data = response.json()
                        st.session_state.video_id = data["video_id"]
                        st.session_state.chat_history = [] # Clear old chat history for a new video
                        st.success(f"Success! Embedded {data['chunks_processed']} chunks.")
                    else:
                        st.error(f"Error: {response.text}")
                except Exception as e:
                    st.error("Could not connect to the backend API. Is it running?")

# ---------------------------------------------------------
# Main Chat Interface: Asking Questions
# ---------------------------------------------------------
if st.session_state.video_id:
    st.header(f"2. Ask Questions")
    st.caption(f"Currently chatting with video ID: {st.session_state.video_id}")
    
    # Draw all past messages in the chat history
    for message in st.session_state.chat_history:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # User input box at the bottom
    if user_query := st.chat_input("Ask a specific question about this video..."):
        
        # Display the user's question instantly
        st.session_state.chat_history.append({"role": "user", "content": user_query})
        with st.chat_message("user"):
            st.markdown(user_query)
            
        # Call the backend API for the AI's answer
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                try:
                    # Call the /query endpoint
                    response = requests.post(
                        f"{API_URL}/query", 
                        json={
                            "video_id": st.session_state.video_id,
                            "query": user_query
                        }
                    )
                    
                    if response.status_code == 200:
                        data = response.json()
                        answer = data["answer"]
                        
                        # If the Agent blocked it, show the user why!
                        if data["classification"] != "ANSWERABLE":
                            answer = f"*(Agent Decision: {data['classification']})*\n\n" + answer
                            
                        st.markdown(answer)
                        st.session_state.chat_history.append({"role": "assistant", "content": answer})
                    else:
                        st.error(f"API Error: {response.text}")
                except Exception as e:
                    st.error("Could not connect to the backend API.")
else:
    st.info("👈 Please paste a YouTube URL in the sidebar to get started!")