const API_URL = import.meta.env.VITE_API_URL || '/api'

async function parseError(response) {
  try {
    const data = await response.json()
    return data.detail || response.statusText
  } catch {
    return response.statusText || 'Request failed'
  }
}

export async function ingestVideo(url) {
  const response = await fetch(`${API_URL}/ingest`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ url }),
  })

  if (!response.ok) {
    throw new Error(await parseError(response))
  }

  return response.json()
}

export async function queryVideo(videoId, query) {
  const response = await fetch(`${API_URL}/query`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ video_id: videoId, query }),
  })

  if (!response.ok) {
    throw new Error(await parseError(response))
  }

  return response.json()
}
