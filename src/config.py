import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# Paths
BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "data"
SCRAPED_DIR = DATA_DIR / "scraped"
CHROMA_DIR = DATA_DIR / "chroma"
SQLITE_PATH = DATA_DIR / "quickee.db"

# Ensure directories exist
SCRAPED_DIR.mkdir(parents=True, exist_ok=True)
CHROMA_DIR.mkdir(parents=True, exist_ok=True)

# Groq
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
GROQ_FAST_MODEL = os.getenv("GROQ_FAST_MODEL", "llama-3.1-8b-instant")

# HuggingFace Inference API (for cloud deployment)
HF_API_TOKEN = os.getenv("HF_API_TOKEN", "")
USE_HF_API = bool(HF_API_TOKEN)

# Embedding mode: "onnx" (local, no API), "api" (HF Inference), "local" (sentence-transformers)
# On Render free tier, use "onnx" to avoid external API calls for embeddings
EMBEDDING_MODE = os.getenv("EMBEDDING_MODE", "onnx" if not HF_API_TOKEN else "api")

# Embedding
EMBEDDING_MODEL = "BAAI/bge-m3"
EMBEDDING_DIM = 384 if EMBEDDING_MODE == "onnx" else 1024

# Reranker mode: "api" (HF Inference), "local" (sentence-transformers), "skip" (no reranking)
RERANKER_MODEL = "BAAI/bge-reranker-v2-m3"
RERANKER_MODE = os.getenv("RERANKER_MODE", "api" if HF_API_TOKEN else ("skip" if EMBEDDING_MODE == "onnx" else "local"))

# Chunking
CHUNK_SIZE = 512
CHUNK_OVERLAP = 50

# Search
VECTOR_SEARCH_K = 20
BM25_SEARCH_K = 20
RERANK_TOP_K = 5

# Cache TTL (seconds)
CACHE_TTL = 3600
