import json
import time
from pathlib import Path
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from src.api.schemas import StyleRequest, StyleResponse
from src.agent.graph import create_agent
from src.agent.nodes import init_stores
from src.ingestion.embedder import Embedder
from src.ingestion.pipeline import load_scraped_products, run_ingestion
from src.storage.vector_store import VectorStore
from src.storage.document_store import DocumentStore
from src.storage.bm25_store import BM25Store
from src.query.cache import SemanticCache

_agent = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global _agent

    import sys
    print("[API] Initializing stores...", flush=True)
    embedder = Embedder()
    print("[API] Embedder ready", flush=True)
    vector_store = VectorStore()
    print("[API] VectorStore ready", flush=True)
    doc_store = DocumentStore()
    print("[API] DocumentStore ready", flush=True)

    bm25_store = BM25Store()
    all_products = doc_store.get_all_products()
    if all_products:
        bm25_store.add_documents(
            doc_ids=[p["id"] for p in all_products],
            texts=[
                f"{p['name']} {p['color']} {p['category']} {p['sub_category']} {p['description']}"
                for p in all_products
            ],
        )
        print(f"[API] BM25 index built with {len(all_products)} products", flush=True)
    else:
        print("[API] WARNING: No products in database. Run ingestion first.", flush=True)

    cache = SemanticCache()

    _agent = create_agent(
        embedder=embedder,
        vector_store=vector_store,
        doc_store=doc_store,
        bm25_store=bm25_store,
        cache=cache,
    )

    print("[API] Agent ready!", flush=True)
    yield
    print("[API] Shutting down...", flush=True)


app = FastAPI(
    title="Quickeee Luxury Stylist Concierge",
    description="AI-powered fashion recommendation engine",
    version="1.0.0",
    lifespan=lifespan,
)


@app.post("/api/v1/style-me", response_model=StyleResponse)
async def style_me(request: StyleRequest):
    if not request.prompt.strip():
        raise HTTPException(status_code=400, detail="Prompt cannot be empty")

    print(f"\n{'='*60}")
    print(f"[API] New request: {request.prompt}")
    print(f"{'='*60}")

    start_time = time.time()

    initial_state = {
        "user_query": request.prompt,
        "rewritten_query": "",
        "query_embedding": [],
        "extracted_filters": {},
        "vector_results": [],
        "bm25_results": [],
        "merged_results": [],
        "reranked_results": [],
        "context_str": "",
        "response": {},
        "agent_reasoning": [],
        "cache_hit": False,
        "cached_response": None,
    }

    try:
        result = _agent.invoke(initial_state)
    except Exception as e:
        print(f"[API] ERROR in agent: {type(e).__name__}: {e}")
        raise HTTPException(status_code=500, detail=f"Agent error: {type(e).__name__}: {str(e)}")

    elapsed = time.time() - start_time
    print(f"[API] Response generated in {elapsed:.2f}s")

    response = result["response"]

    return StyleResponse(
        recommended_items=response.get("recommended_items", []),
        total_price=response.get("total_price", 0),
        currency=response.get("currency", "INR"),
        stylist_note=response.get("stylist_note", ""),
        agent_reasoning=response.get("agent_reasoning", []),
    )


STATIC_DIR = Path(__file__).parent / "static"


@app.get("/")
async def root():
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/health")
async def health():
    return {"status": "ok"}


app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")
