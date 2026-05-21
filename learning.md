# Quickeee - Learnings & Post-Mortem

A record of every mistake, discovery, and architectural decision made while building the Quickeee Luxury Stylist Concierge. Written to prevent repeating the same mistakes and to document the reasoning behind key trade-offs.

---

## 1. Render Free Tier: DNS Resolution Blocks External Embedding APIs

### The Problem
After a successful build and deploy on Render, every `POST /api/v1/style-me` request returned a 500 error. The root cause was a DNS resolution failure:

```
socket.gaierror: [Errno -5] No address associated with hostname
```

Render's free tier could not resolve `api-inference.huggingface.co`. This broke both:
- **Embedder** (BGE-M3 via HuggingFace Inference API)
- **Reranker** (BGE-reranker-v2-m3 via HuggingFace Inference API)

### Why It Happened
The original design spec called for BGE-M3 (1024-dim) embeddings via `sentence-transformers` locally. But `sentence-transformers` requires `torch` (~2GB), which exceeds Render free tier memory. The workaround was to call HuggingFace's Inference API instead - but Render's free tier network couldn't reach it.

### The Fix
Switched to **local ONNX embeddings** using ChromaDB's built-in `DefaultEmbeddingFunction` (all-MiniLM-L6-v2, 384-dim). This model:
- Runs via `onnxruntime` (already a ChromaDB dependency, ~50MB)
- Needs zero external API calls
- Is small enough for Render free tier memory
- Required re-ingesting all 200 products with the new 384-dim vectors

For the reranker, added a **graceful try/catch fallback** - if the HF API is unreachable, results are returned without reranking (BM25 + vector ordering is preserved).

### Lesson
**Never assume external APIs are reachable from your deployment environment.** Always design with a local fallback for critical path operations (embedding, reranking). Test the full request pipeline on the actual deployment platform, not just the build step.

---

## 2. Render Health Checks: The Missing Root Endpoint

### The Problem
Render's automatic health check sends `HEAD /` to verify the service is alive. Our FastAPI app only had `/health` and `/api/v1/style-me` routes. The root `/` returned 404, which shows in logs as:

```
INFO: 127.0.0.1:36934 - "HEAD / HTTP/1.1" 404 Not Found
```

### The Fix
Added a simple `GET /` root endpoint returning `{"service": "Quickeee Luxury Stylist Concierge", "status": "ok"}`.

### Lesson
**Always include a root health check endpoint** when deploying to PaaS platforms (Render, Railway, Fly.io). They all probe `/` by default. A 404 won't immediately kill your service, but it can cause Render to mark it unhealthy over time and trigger restarts.

---

## 3. FastAPI Version Conflicts on Python 3.12+

### The Problem
The initial deploy failed because Render defaulted to Python 3.12, and there was a version conflict between FastAPI and its dependencies on newer Python versions.

### The Fix
- Pinned `PYTHON_VERSION=3.10.14` in `render.yaml`
- Added `.python-version` file
- Pinned exact FastAPI version in `render_requirements.txt`

### Lesson
**Pin your Python version explicitly** in deployment configs. Don't rely on platform defaults. Free tier platforms often upgrade Python versions without notice.

---

## 4. Two Requirements Files: Local vs. Deploy

### The Decision
Maintaining two separate requirements files was intentional:
- `requirements.txt` - Full local stack (sentence-transformers, torch, playwright, pytest)
- `render_requirements.txt` - Lightweight deploy stack (no ML models, no test deps, no scraper deps)

### Why
Render free tier has ~512MB RAM and limited build time. `torch` alone is ~2GB. The scrapers and test framework aren't needed in production. The deploy requirements include only runtime dependencies.

### Lesson
**Separate your dev/deploy dependencies** when targeting constrained environments. A `render_requirements.txt` that only includes API runtime deps keeps builds fast and memory usage low.

---

## 5. Embedding Dimension Mismatch is Silent & Fatal

### The Problem
When switching from BGE-M3 (1024-dim) to MiniLM (384-dim), ChromaDB doesn't warn you about dimension mismatches at query time - it simply crashes or returns garbage results. If the stored vectors are 1024-dim and you query with a 384-dim vector, the HNSW index fails silently or throws an opaque error.

### The Fix
After changing the embedding model, we had to:
1. Delete the entire `data/chroma/` directory
2. Re-run the ingestion pipeline with the new embedder
3. Verify vector count matches (`200 vectors`)

### Lesson
**When you change the embedding model, you MUST re-ingest all data.** There is no migration path for vector dimension changes. Treat your embedding model choice as a schema decision - changing it is a breaking migration.

---

## 6. ChromaDB Telemetry Noise

### The Issue
Every startup logs:
```
Failed to send telemetry event ClientStartEvent: capture() takes 1 positional argument but 3 were given
```

This is a known ChromaDB + posthog compatibility issue. It's harmless but clutters logs.

### Mitigation
We already set `anonymized_telemetry=False` in `VectorStore.__init__`. The error still appears because ChromaDB attempts telemetry before the setting takes effect. This is a ChromaDB bug, not ours.

### Lesson
**Disable telemetry explicitly** in all third-party libraries for production deployments. Read their logs carefully - "Failed to send telemetry" is noise, but "Failed to resolve hostname" is a real bug.

---

## 7. Groq Model Selection: llama-3.3-70b-versatile

### The Decision
We use `llama-3.3-70b-versatile` on Groq's free tier. This was chosen over smaller models because:
- Fashion recommendation requires nuanced understanding of color theory, fabric pairing, and occasion-appropriate styling
- 70B models reliably output structured JSON
- Groq's free tier is generous enough for demo usage (30 req/min)

### Caveat
Groq's free tier has rate limits. For production, you'd need to add retry logic with exponential backoff, or switch to a self-hosted model.

---

## 8. HyDE (Hypothetical Document Embeddings) Query Rewriting

### What We Learned
Using the LLM to rewrite user queries as hypothetical product descriptions significantly improves retrieval quality. Example:

- **User query**: "summer yacht party outfit"
- **HyDE rewrite**: "A lightweight cotton polo shirt in white or light blue, slim fit, breathable fabric suitable for warm outdoor marine settings..."

The rewritten query embeds much closer to actual product descriptions in vector space than the original natural language query.

### Trade-off
This adds one extra LLM call per uncached query. The semantic cache mitigates this - identical queries skip the entire pipeline.

---

## 9. Hybrid Search is Worth the Complexity

### Why Both Vector + BM25
- **Vector search** (ChromaDB): Great for semantic matches ("yacht party" -> "nautical themed clothing")
- **BM25 keyword search**: Great for exact matches ("navy blue t-shirt" -> products with "navy" and "blue" in the text)
- Neither alone is sufficient. A user who says "blue Adidas t-shirt" needs exact keyword matching for "Adidas" and semantic matching for the style context.

### The merge strategy
Results from both searches are deduplicated by chunk ID and merged. The cross-encoder reranker then scores all candidates against the original query to produce the final top-5.

---

## 10. Scraper Fragility: Myntra & Flipkart

### What Happened
- **Myntra**: Heavy JS rendering, product data loaded via XHR. Scraper needed to intercept network requests rather than parse DOM. Works but fragile - any Myntra frontend update breaks it.
- **Flipkart**: Initially attempted but abandoned. Flipkart's anti-bot measures (CAPTCHAs, IP blocking) made reliable scraping impractical without proxy rotation.
- **H&M**: Semi-structured API endpoints behind their frontend. Most reliable of the three.

### Lesson
**Scrapers are the most fragile component in the system.** Design the rest of the pipeline to be scraper-agnostic - the ingestion pipeline accepts a standard `Product` schema regardless of source. Adding a new source is just writing a new scraper that outputs the same schema.

---

## 11. The "All Free" Constraint Shapes Everything

### Constraint
No paid APIs. Everything must be open-source or have a free tier.

### How It Shaped Decisions
| Decision | Paid Alternative | Our Free Choice |
|---|---|---|
| Embeddings | OpenAI text-embedding-3 | BGE-M3 (local) / MiniLM (ONNX) |
| LLM | GPT-4o | Groq + Llama 3.3 70B (free tier) |
| Vector DB | Pinecone | ChromaDB (local) |
| Reranker | Cohere rerank-v3 | BGE-reranker-v2-m3 (local/API) |
| Hosting | AWS/GCP | Render free tier |

### Trade-offs Accepted
- Lower embedding quality (MiniLM-L6-v2 vs BGE-M3 vs OpenAI)
- Rate-limited LLM (Groq free tier: 30 req/min)
- Ephemeral hosting (Render free tier spins down after inactivity)
- No GPU for local models (ONNX on CPU only)

---

## 12. Key Architecture Decisions Summary

1. **LangGraph over raw function chains**: Gives us state management, conditional routing (cache hit/miss), and agent reasoning traces for free
2. **ChromaDB over FAISS**: Persistent storage, metadata filtering, built-in ONNX embeddings
3. **SQLite over PostgreSQL**: Zero config, file-based, sufficient for 200 products
4. **Semantic cache in SQLite**: Simple SHA-256 hash with TTL, saves Groq API calls on repeated queries
5. **Single endpoint design**: `POST /api/v1/style-me` - simple, stateless, demo-friendly
6. **ONNX for deployment**: Avoid torch dependency, use chromadb's bundled onnxruntime for embeddings

---

## What We'd Do Differently Next Time

1. **Start with ONNX embeddings** instead of assuming HF API would be reachable everywhere
2. **Add a `/` root endpoint from day one** for health checks
3. **Test the full API flow on Render** before considering the deploy "done" (not just the build)
4. **Add structured error responses** instead of letting FastAPI return raw 500s with stack traces
5. **Add retry logic with backoff** for all external API calls (Groq, HuggingFace)
6. **Consider pre-computing embeddings at build time** rather than at runtime, to avoid cold-start latency
