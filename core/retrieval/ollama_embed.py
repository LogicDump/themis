"""Integração e gateway de embeddings locais com metadados de proveniência."""
from __future__ import annotations

import json
import logging
import os
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any, Sequence

from core.retrieval.vector_store import (
    EMBEDDING_DIM,
    EMBEDDING_MODEL_NAME,
    EMBEDDING_MODEL_VERSION,
)

logger = logging.getLogger(__name__)


def format_doc_text(text: str) -> str:
    """Protocolo canônico do EmbeddingGemma para documentos."""
    return f"title: none | text: {text}"


def format_query_text(query: str) -> str:
    """Protocolo canônico do EmbeddingGemma para queries de busca."""
    return f"task: search result | query: {query}"


def get_active_embedding_backend() -> str:
    """Retorna o backend de embedding ativo: 'onnx' (padrão) ou 'ollama'."""
    return os.environ.get("THEMIS_EMBEDDING_BACKEND", "onnx").strip().lower()


def generate_embedding_ollama(
    text: str,
    *,
    is_query: bool = False,
    model: str = EMBEDDING_MODEL_NAME,
    ollama_url: str = "http://127.0.0.1:11434",
    timeout: int = 30,
) -> list[float] | None:
    """Gera um embedding vetorial usando embeddinggemma:300m via Ollama HTTP API."""
    formatted = format_query_text(text) if is_query else format_doc_text(text)
    payload = {
        "model": model,
        "input": formatted,
        "truncate": False,
    }
    req = urllib.request.Request(
        f"{ollama_url.rstrip('/')}/api/embed",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            embs = data.get("embeddings", [])
            if embs and len(embs) > 0:
                return embs[0]
            return None
    except Exception:
        return None


def generate_embedding_with_meta(
    text: str,
    *,
    is_query: bool = False,
    model: str = EMBEDDING_MODEL_NAME,
    ollama_url: str = "http://127.0.0.1:11434",
    timeout: int = 30,
    backend: str | None = None,
) -> tuple[list[float] | None, dict[str, Any]]:
    """Gera embedding e retorna o vetor juntamente com os metadados de modelo/backend/quantização."""
    chosen_backend = (backend or get_active_embedding_backend()).lower()

    if chosen_backend == "ollama":
        res = generate_embedding_ollama(text, is_query=is_query, model=model, ollama_url=ollama_url, timeout=timeout)
        if res is not None:
            return res, {
                "model": model,
                "backend": "ollama",
                "model_version": EMBEDDING_MODEL_VERSION,
                "quantization": "q4_k_m",
                "dim": len(res),
            }
        # Fallback ONNX
        try:
            from core.retrieval.onnx_embed import generate_embedding_onnx
            res_onnx = generate_embedding_onnx(text, is_query=is_query)
            if res_onnx is not None:
                return res_onnx, {
                    "model": model,
                    "backend": "onnx",
                    "model_version": EMBEDDING_MODEL_VERSION,
                    "quantization": "int8",
                    "dim": len(res_onnx),
                }
        except Exception:
            pass
        return None, {}

    # Padrão: ONNX INT8 local
    try:
        from core.retrieval.onnx_embed import generate_embedding_onnx
        emb = generate_embedding_onnx(text, is_query=is_query)
        if emb is not None:
            return emb, {
                "model": model,
                "backend": "onnx",
                "model_version": EMBEDDING_MODEL_VERSION,
                "quantization": "int8",
                "dim": len(emb),
            }
    except Exception as exc:
        logger.debug(f"ONNX embedding indisponível, tentando fallback Ollama: {exc}")

    # Fallback Ollama
    res = generate_embedding_ollama(text, is_query=is_query, model=model, ollama_url=ollama_url, timeout=timeout)
    if res is not None:
        return res, {
            "model": model,
            "backend": "ollama",
            "model_version": EMBEDDING_MODEL_VERSION,
            "quantization": "q4_k_m",
            "dim": len(res),
        }
    return None, {}


def generate_embedding(
    text: str,
    *,
    is_query: bool = False,
    model: str = EMBEDDING_MODEL_NAME,
    ollama_url: str = "http://127.0.0.1:11434",
    timeout: int = 30,
    backend: str | None = None,
) -> list[float] | None:
    """Gera um embedding vetorial simples."""
    vec, _meta = generate_embedding_with_meta(
        text,
        is_query=is_query,
        model=model,
        ollama_url=ollama_url,
        timeout=timeout,
        backend=backend,
    )
    return vec
