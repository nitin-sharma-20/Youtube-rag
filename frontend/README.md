# TubeRAG Frontend

React UI for the TubeRAG YouTube Q&A app.

## Development

1. Start the FastAPI backend from the repo root:

```bash
uvicorn api.main:app --reload --host 127.0.0.1 --port 8000
```

2. Install dependencies and start the dev server:

```bash
cd frontend
npm install
npm run dev
```

Open http://localhost:5173. API requests are proxied to `http://127.0.0.1:8000` via `/api`.

## Production build

```bash
npm run build
npm run preview
```

Set `VITE_API_URL` when the API is hosted at a different origin.
