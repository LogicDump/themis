"""Módulo de retrieval híbrido e vetorial do Jurídico."""
from __future__ import annotations

from core.retrieval.vector_store import VectorStore
from core.retrieval.hybrid_retrieval import search_hybrid, ensure_process_embeddings

__all__ = ["VectorStore", "search_hybrid", "ensure_process_embeddings"]
