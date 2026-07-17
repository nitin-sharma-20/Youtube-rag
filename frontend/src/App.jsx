import { useState } from 'react'
import { ingestVideo, queryVideo } from './api'
import './App.css'

function formatAnswer(data) {
  if (data.classification !== 'ANSWERABLE') {
    return `*(Agent Decision: ${data.classification})*\n\n${data.answer}`
  }
  return data.answer
}

function App() {
  const [youtubeUrl, setYoutubeUrl] = useState('')
  const [videoId, setVideoId] = useState(null)
  const [chatHistory, setChatHistory] = useState([])
  const [query, setQuery] = useState('')
  const [ingestStatus, setIngestStatus] = useState(null)
  const [ingestError, setIngestError] = useState(null)
  const [isIngesting, setIsIngesting] = useState(false)
  const [isQuerying, setIsQuerying] = useState(false)
  const [queryError, setQueryError] = useState(null)

  async function handleIngest(event) {
    event.preventDefault()
    setIngestError(null)
    setIngestStatus(null)

    if (!youtubeUrl.trim()) {
      setIngestError('Please enter a URL first.')
      return
    }

    setIsIngesting(true)
    try {
      const data = await ingestVideo(youtubeUrl.trim())
      setVideoId(data.video_id)
      setChatHistory([])
      setIngestStatus(`Success! Embedded ${data.chunks_processed} chunks.`)
    } catch (error) {
      setIngestError(
        error instanceof TypeError
          ? 'Could not connect to the backend API. Is it running?'
          : error.message,
      )
    } finally {
      setIsIngesting(false)
    }
  }

  async function handleQuery(event) {
    event.preventDefault()
    if (!query.trim() || !videoId || isQuerying) return

    const userMessage = query.trim()
    setQuery('')
    setQueryError(null)
    setChatHistory((prev) => [...prev, { role: 'user', content: userMessage }])
    setIsQuerying(true)

    try {
      const data = await queryVideo(videoId, userMessage)
      const answer = formatAnswer(data)
      setChatHistory((prev) => [...prev, { role: 'assistant', content: answer }])
    } catch (error) {
      setQueryError(
        error instanceof TypeError
          ? 'Could not connect to the backend API.'
          : error.message,
      )
    } finally {
      setIsQuerying(false)
    }
  }

  return (
    <div className="app">
      <aside className="sidebar">
        <h2>1. Load Video</h2>
        <form className="ingest-form" onSubmit={handleIngest}>
          <label htmlFor="youtube-url">YouTube URL</label>
          <input
            id="youtube-url"
            type="url"
            placeholder="https://www.youtube.com/watch?v=..."
            value={youtubeUrl}
            onChange={(event) => setYoutubeUrl(event.target.value)}
            disabled={isIngesting}
          />
          <button type="submit" disabled={isIngesting}>
            {isIngesting ? 'Processing...' : 'Process Video'}
          </button>
        </form>

        {isIngesting && (
          <p className="status status-loading">
            Processing transcript and generating embeddings. This may take a minute.
          </p>
        )}
        {ingestStatus && <p className="status status-success">{ingestStatus}</p>}
        {ingestError && <p className="status status-error">{ingestError}</p>}
      </aside>

      <main className="main">
        <header className="hero">
          <h1>TubeRAG: YouTube Knowledge Engine</h1>
          <p>Ask questions about any YouTube video using RAG.</p>
        </header>

        {!videoId ? (
          <div className="empty-state">
            Paste a YouTube URL in the sidebar to get started.
          </div>
        ) : (
          <section className="chat-section">
            <div className="chat-header">
              <h2>2. Ask Questions</h2>
              <p className="video-id">Currently chatting with video ID: {videoId}</p>
            </div>

            <div className="chat-history">
              {chatHistory.length === 0 && (
                <p className="chat-placeholder">
                  Ask a specific question about this video.
                </p>
              )}
              {chatHistory.map((message, index) => (
                <div key={`${message.role}-${index}`} className={`message message-${message.role}`}>
                  <span className="message-role">{message.role === 'user' ? 'You' : 'Assistant'}</span>
                  <div className="message-content">{message.content}</div>
                </div>
              ))}
              {isQuerying && (
                <div className="message message-assistant">
                  <span className="message-role">Assistant</span>
                  <div className="message-content thinking">Thinking...</div>
                </div>
              )}
            </div>

            {queryError && <p className="status status-error">{queryError}</p>}

            <form className="chat-form" onSubmit={handleQuery}>
              <input
                type="text"
                placeholder="Ask a specific question about this video..."
                value={query}
                onChange={(event) => setQuery(event.target.value)}
                disabled={isQuerying}
              />
              <button type="submit" disabled={isQuerying || !query.trim()}>
                Send
              </button>
            </form>
          </section>
        )}
      </main>
    </div>
  )
}

export default App
