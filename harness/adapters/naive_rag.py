"""
Naive-RAG baseline.

Chunks conversation turns, embeds with sentence-transformers all-MiniLM-L6-v2,
stores in a simple in-memory vector store, and does cosine-similarity retrieval.

This is the "naive RAG" baseline that every memory tool must beat. It uses
semantic search but no memory-specific techniques (no fact extraction, no
temporal reasoning, no consolidation).
"""

import time
try:
    import numpy as np
    HAVE_NUMPY = True
except ImportError:
    HAVE_NUMPY = False
from typing import Optional
from harness.adapter import MemoryAdapter, AdapterResult

try:
    from sentence_transformers import SentenceTransformer
    HAVE_ST = True
except ImportError:
    HAVE_ST = False


class NaiveRAGAdapter(MemoryAdapter):
    """Baseline: chunk → embed → cosine-similarity retrieval."""

    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        self.chunks = []
        self.embeddings = []
        self.model_name = model_name
        self.model = None
        if HAVE_ST:
            self.model = SentenceTransformer(model_name)

    def add(self, conversation_turns: list[dict]) -> AdapterResult:
        t0 = time.perf_counter()
        for turn in conversation_turns:
            content = turn.get("content", "")
            if not content.strip():
                continue
            self.chunks.append({
                "content": content,
                "timestamp": turn.get("timestamp", "unknown"),
                "role": turn.get("role", "unknown")
            })

        if self.model and HAVE_ST:
            texts = [c["content"] for c in self.chunks]
            self.embeddings = self.model.encode(texts, normalize_embeddings=True)

        elapsed = time.perf_counter() - t0
        return AdapterResult(success=True, elapsed_sec=elapsed)

    def await_ingest(self, timeout_sec: float = 60.0) -> AdapterResult:
        return AdapterResult(success=True, elapsed_sec=0.0)

    def search(self, query: str, k: int = 5) -> AdapterResult:
        t0 = time.perf_counter()
        if not self.chunks or not self.model or not HAVE_ST or not HAVE_NUMPY:
            return AdapterResult(success=True, elapsed_sec=0.0, metadata={"excerpts": []})

        query_emb = self.model.encode([query], normalize_embeddings=True)
        scores = np.dot(self.embeddings, query_emb.T).flatten()
        top_k = np.argsort(scores)[::-1][:k]
        excerpts = [self.chunks[i]["content"] for i in top_k]
        elapsed = time.perf_counter() - t0
        return AdapterResult(success=True, elapsed_sec=elapsed, metadata={"excerpts": excerpts})

    def export(self) -> AdapterResult:
        return AdapterResult(success=True, elapsed_sec=0.0, metadata={
            "chunks": len(self.chunks),
            "model": self.model_name,
            "embedding_dim": len(self.embeddings[0]) if self.embeddings else 0
        })

    def wipe(self) -> AdapterResult:
        self.chunks = []
        self.embeddings = []
        return AdapterResult(success=True, elapsed_sec=0.0)
