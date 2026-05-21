# Quickeee - Luxury Stylist Concierge

An AI-powered fashion concierge that scrapes premium clothing brands, builds a RAG pipeline, and recommends styled outfits using an agentic LLM workflow.

## Features

- Scrapes H&M and Myntra for 100+ fashion products
- Hybrid search: Vector (ChromaDB) + BM25 keyword + metadata filtering
- Cross-encoder reranking (BGE-reranker-v2-m3)
- LangGraph agentic workflow with HyDE query rewriting
- Semantic cache for token optimization
- Single FastAPI endpoint: `POST /api/v1/style-me`

## Tech Stack

All open-source and free:
- **Scraping**: Playwright
- **Embeddings**: BGE-M3 (1024-dim)
- **Vector DB**: ChromaDB
- **Document Store**: SQLite
- **BM25**: rank-bm25
- **Reranker**: BGE-reranker-v2-m3
- **LLM**: Groq + Llama 3.3 70B (free tier)
- **Agent**: LangGraph
- **API**: FastAPI

## Setup

### 1. Install dependencies

```bash
pip install -r requirements.txt
playwright install chromium
```

### 2. Configure environment

Create a `.env` file:

```
GROQ_API_KEY=your_groq_api_key_here
GROQ_MODEL=llama-3.3-70b-versatile
```

Get your free Groq API key at https://console.groq.com

### 3. Run scrapers

```bash
python -m src.scraper.run_scrapers
```

This scrapes H&M and Myntra, saving products to `data/scraped/`.

### 4. Run ingestion pipeline

```bash
python -m src.ingestion.pipeline
```

This cleans, chunks, embeds, and stores products in ChromaDB + SQLite + BM25.

### 5. Start the API

```bash
uvicorn src.api.main:app --reload --port 8000
```

## Usage

### API Endpoint

**POST** `/api/v1/style-me`

```bash
curl -X POST http://localhost:8000/api/v1/style-me \
  -H "Content-Type: application/json" \
  -d '{"prompt": "I have dark navy chinos, what t-shirt should I wear for a summer yacht party?"}'
```

### Response

```json
{
  "recommended_items": [
    {
      "name": "Slim Fit Cotton T-shirt",
      "category": "tops",
      "color": "white",
      "price": 799.0,
      "image_url": "https://...",
      "source": "h&m"
    },
    {
      "name": "Chino Shorts Regular Fit",
      "category": "bottoms",
      "color": "beige",
      "price": 1299.0,
      "image_url": "https://...",
      "source": "myntra"
    }
  ],
  "total_price": 2098.0,
  "currency": "INR",
  "stylist_note": "The white cotton tee pairs beautifully with navy chinos — a classic nautical palette perfect for a summer yacht party.",
  "agent_reasoning": [
    "Cache MISS - proceeding with full pipeline",
    "Rewrote query using HyDE",
    "Extracted filters: {\"category\": null, \"color\": \"navy\"}",
    "Hybrid search returned 25 candidates",
    "Reranked to top 5 results",
    "Assembled context from 5 products",
    "Generated recommendation with llama-3.3-70b-versatile"
  ]
}
```

### Swagger UI

Visit `http://localhost:8000/docs` for interactive API documentation.

## Running Tests

```bash
python -m pytest tests/ -v
```

## Architecture

See [ARCHITECTURE.md](ARCHITECTURE.md) for detailed system design, database schema, state management, and Mermaid flowchart.

## Project Structure

```
quickee/
  src/
    config.py           # Central configuration
    scraper/            # Playwright scrapers (H&M + Myntra)
    ingestion/          # Clean -> chunk -> dedupe -> embed pipeline
    storage/            # ChromaDB, SQLite, BM25 wrappers
    query/              # HyDE rewriter, filter builder, hybrid search, reranker, cache
    agent/              # LangGraph state machine
    api/                # FastAPI endpoint
  data/                 # Scraped JSON, ChromaDB, SQLite
  tests/                # Unit tests
  ARCHITECTURE.md       # System design docs
```
