import { useState, useRef, useEffect } from 'react'
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
  const chatBottomRef = useRef(null)

  useEffect(() => {
    chatBottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [chatHistory, isQuerying])

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
      setIngestStatus(`Embedded ${data.chunks_processed} chunks.`)
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

  function handleKeyDown(e) {
    if (e.key === 'Enter' && !e.shiftKey) {
      handleQuery(e)
    }
  }

  return (
    <div className="app">
      {/* ── TOP NAVBAR ── */}
      <nav className="navbar">
        <div className="navbar-brand">
            <span className="brand-name">TubeRAG</span>
        </div>
        {videoId && (
          <div className="navbar-vid-badge">
            <span className="vid-dot" />
            <span className="vid-label">LIVE: {videoId}</span>
          </div>
        )}
      </nav>

      {/* ── HERO SECTION ── */}
      <section className="hero">
        <h1 className="hero-title">Chat with any<br />YouTube video</h1>
        <p className="hero-subtitle">
          Paste a video link · process the transcript · ask anything
        </p>

        {/* URL input row */}
        <form className="url-form" onSubmit={handleIngest} id="ingest-form">
          <div className="url-input-wrap">
            <span className="url-icon">🔗</span>
            <input
              id="youtube-url"
              type="url"
              className="url-input"
              placeholder="https://www.youtube.com/watch?v=..."
              value={youtubeUrl}
              onChange={(e) => setYoutubeUrl(e.target.value)}
              disabled={isIngesting}
              aria-label="YouTube URL"
            />
            <button
              type="submit"
              className="url-submit"
              disabled={isIngesting}
              aria-label="Process video"
            >
              {isIngesting ? (
                <span className="spin-icon">⟳</span>
              ) : (
                <span>↑</span>
              )}
            </button>
          </div>
        </form>

        {/* Status messages under input */}
        {isIngesting && (
          <p className="status status-loading">
            ▌ Processing transcript &amp; generating embeddings…
          </p>
        )}
        {ingestStatus && (
          <p className="status status-success">✔ {ingestStatus}</p>
        )}
        {ingestError && (
          <p className="status status-error">✖ {ingestError}</p>
        )}
      </section>

      {/* ── CHAT SECTION ── */}
      <section className="chat-section">
        {!videoId ? (
          <div className="empty-state">
            <div className="empty-icon">▶</div>
            <p>Paste a YouTube URL above to get started.</p>
          </div>
        ) : (
          <div className="chat-container">
            <div className="chat-history" id="chat-history">
              {chatHistory.length === 0 && (
                <p className="chat-placeholder">
                  Ask a specific question about this video…
                </p>
              )}
              {chatHistory.map((message, index) => (
                <div
                  key={`${message.role}-${index}`}
                  className={`message message-${message.role}`}
                >
                  <span className="message-role">
                    {message.role === 'user' ? '[ YOU ]' : '[ AI ]'}
                  </span>
                  <div className="message-content">{message.content}</div>
                </div>
              ))}
              {isQuerying && (
                <div className="message message-assistant">
                  <span className="message-role">[ AI ]</span>
                  <div className="message-content thinking">
                    <span className="blink">█</span> Thinking…
                  </div>
                </div>
              )}
              {queryError && (
                <p className="status status-error">✖ {queryError}</p>
              )}
              <div ref={chatBottomRef} />
            </div>

            {/* Chat input row */}
            <form className="chat-form" onSubmit={handleQuery} id="chat-form">
              <input
                type="text"
                className="chat-input"
                placeholder="Ask a specific question about this video…"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                onKeyDown={handleKeyDown}
                disabled={isQuerying}
                aria-label="Your question"
              />
              <button
                type="submit"
                className="chat-submit"
                disabled={isQuerying || !query.trim()}
                aria-label="Send message"
              >
                SEND ↵
              </button>
            </form>
          </div>
        )}
      </section>
    </div>
  )
}

export default App
