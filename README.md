# Bounce — AI Career Counselor

An AI-powered career counseling chatbot for adult students at LaGuardia Community College, built with LangGraph, ChromaDB, and React.

## Stack

| Layer | Tech |
|-------|------|
| Frontend | React + Vite + Tailwind CSS + Framer Motion |
| Backend | FastAPI + LangGraph + LangChain |
| AI Model | Gemini 3 Flash (via `langchain-google-genai`) |
| Vector Store | ChromaDB (O*NET career data) |
| Observability | LangSmith tracing |

## Architecture

```
User message
    │
    ▼
Router (LangGraph)
    ├── intake_node  → ChromaDB search (k=3) → LLM → career suggestions
    └── detail_node  → ChromaDB search (k=1, deep) → LLM → career details
```

The router sends general conversation to `intake` and routes to `detail` when the user asks for more information about a specific career.

## Setup

### Requirements
- Python 3.11+
- Node 18+
- Google API Key (Gemini)
- LangSmith API Key (optional, for tracing)

### Backend

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Create backend/.env
cp backend/.env.example backend/.env
# Fill in your API keys

# Vectorize career data (run once)
python backend/vectorize_onet.py

# Start API server
uvicorn backend.main:app --reload --port 8001
```

### Frontend

```bash
cd frontend
npm install
npm run dev
# → http://localhost:5173
```

### LangGraph Studio (optional)

```bash
pip install "langgraph-cli[inmem]"
langgraph dev
# → https://smith.langchain.com/studio/?baseUrl=http://127.0.0.1:2024
```

## Environment Variables

Create `backend/.env`:

```env
GOOGLE_API_KEY=your_google_api_key
LANGCHAIN_TRACING_V2=true
LANGCHAIN_API_KEY=your_langsmith_key
LANGCHAIN_PROJECT=rag-pdf-gemini
```

## Features

- Empathetic intake conversation with career matching from O*NET data
- Proactive career suggestions after 2 exchanges
- Deep-dive career detail on demand
- CV upload (PDF/TXT) for personalized recommendations
- 20-message conversation memory window
- Markdown rendering for structured career comparisons
- LangSmith tracing for every conversation
