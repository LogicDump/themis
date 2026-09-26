"""Geração de embeddings locais via ONNX Runtime (EmbeddingGemma INT8)."""
from __future__ import annotations

import logging
import os
import threading
import gc
from pathlib import Path
from typing import Sequence

from core.runtime_paths import embeddinggemma_onnx_model_path, embeddinggemma_tokenizer_path

logger = logging.getLogger(__name__)

_LOCK = threading.Lock()
_SESSION = None
_TOKENIZER = None
_WARMUP_LOCK = threading.Lock()
_WARMUP_THREAD: threading.Thread | None = None
_SESSION_USE_LOCK = threading.RLock()
_LIFECYCLE_LOCK = threading.Lock()
_IDLE_UNLOAD_TIMER: threading.Timer | None = None
_LIFECYCLE_GENERATION = 0
EMBEDDING_IDLE_TTL_SECONDS = 90


def format_doc_text(text: str) -> str:
    """Protocolo canônico do EmbeddingGemma para documentos."""
    return f"title: none | text: {text}"


def format_query_text(query: str) -> str:
    """Protocolo canônico do EmbeddingGemma para queries de busca."""
    return f"task: search result | query: {query}"


def _get_onnx_session_and_tokenizer(
    model_path: Path | str | None = None,
    tokenizer_path: Path | str | None = None,
):
    global _SESSION, _TOKENIZER
    if _SESSION is not None and _TOKENIZER is not None:
        return _SESSION, _TOKENIZER
    with _LOCK:
        if _SESSION is not None and _TOKENIZER is not None:
            return _SESSION, _TOKENIZER

        import onnxruntime as ort
        from tokenizers import Tokenizer

        m_path = Path(model_path or embeddinggemma_onnx_model_path()).resolve()
        t_path = Path(tokenizer_path or embeddinggemma_tokenizer_path()).resolve()

        if not m_path.is_file():
            raise FileNotFoundError(f"Modelo ONNX não encontrado em: {m_path}")
        if not t_path.is_file():
            raise FileNotFoundError(f"Tokenizer não encontrado em: {t_path}")

        tokenizer = Tokenizer.from_file(str(t_path))
        tokenizer.enable_truncation(max_length=512)
        tokenizer.enable_padding(length=512, pad_id=0, pad_token="<pad>")

        opts = ort.SessionOptions()
        num_threads = int(os.environ.get("THEMIS_ONNX_THREADS", "4"))
        opts.intra_op_num_threads = num_threads
        opts.graph_optimization_level = ort.GraphOptimizationLevel.ORT_ENABLE_ALL

        avail_providers = ort.get_available_providers()
        chosen_providers = []
        if "CUDAExecutionProvider" in avail_providers:
            chosen_providers.append("CUDAExecutionProvider")
        if "DmlExecutionProvider" in avail_providers:
            chosen_providers.append("DmlExecutionProvider")
        if "CPUExecutionProvider" in avail_providers:
            chosen_providers.append("CPUExecutionProvider")

        session = ort.InferenceSession(
            str(m_path),
            sess_options=opts,
            providers=chosen_providers or ["CPUExecutionProvider"],
        )

        _SESSION = session
        _TOKENIZER = tokenizer
        return _SESSION, _TOKENIZER


def warmup_onnx_async() -> bool:
    """Load EmbeddingGemma in a background thread; the session stays resident."""
    global _WARMUP_THREAD
    if _SESSION is not None and _TOKENIZER is not None:
        return False
    with _WARMUP_LOCK:
        if _SESSION is not None and _TOKENIZER is not None:
            return False
        if _WARMUP_THREAD is not None and _WARMUP_THREAD.is_alive():
            return False

        def _load() -> None:
            try:
                _get_onnx_session_and_tokenizer()
                logger.info("EmbeddingGemma ONNX carregado em background")
            except Exception:
                logger.exception("Falha no warm-up de EmbeddingGemma ONNX")

        _WARMUP_THREAD = threading.Thread(target=_load, name="themis-embeddinggemma-warmup", daemon=True)
        _WARMUP_THREAD.start()
        return True


def request_embedding_warmup() -> str:
    """Cancel idle eviction and ensure loading starts without blocking caller."""
    global _IDLE_UNLOAD_TIMER, _LIFECYCLE_GENERATION
    with _LIFECYCLE_LOCK:
        _LIFECYCLE_GENERATION += 1
        timer = _IDLE_UNLOAD_TIMER
        _IDLE_UNLOAD_TIMER = None
        if timer is not None:
            timer.cancel()
    if _SESSION is not None and _TOKENIZER is not None:
        return "READY"
    warmup_onnx_async()
    return "LOADING"


def cancel_embedding_unload() -> bool:
    """Cancel idle eviction without starting model loading if unloaded."""
    global _IDLE_UNLOAD_TIMER, _LIFECYCLE_GENERATION
    with _LIFECYCLE_LOCK:
        _LIFECYCLE_GENERATION += 1
        timer = _IDLE_UNLOAD_TIMER
        _IDLE_UNLOAD_TIMER = None
        if timer is not None:
            timer.cancel()
            return True
    return False


def schedule_embedding_unload() -> None:
    """Evict the model after the Pesquisa tab has been idle for 90 seconds."""
    global _IDLE_UNLOAD_TIMER, _LIFECYCLE_GENERATION
    with _LIFECYCLE_LOCK:
        _LIFECYCLE_GENERATION += 1
        generation = _LIFECYCLE_GENERATION
        if _IDLE_UNLOAD_TIMER is not None:
            _IDLE_UNLOAD_TIMER.cancel()
        timer = threading.Timer(EMBEDDING_IDLE_TTL_SECONDS, _unload_if_idle, args=(generation,))
        timer.name = "themis-embeddinggemma-idle-unload"
        timer.daemon = True
        _IDLE_UNLOAD_TIMER = timer
        timer.start()


def _unload_if_idle(generation: int) -> None:
    global _SESSION, _TOKENIZER, _IDLE_UNLOAD_TIMER
    # Do not release native resources while an embedding inference uses them.
    with _SESSION_USE_LOCK:
        with _LIFECYCLE_LOCK:
            if generation != _LIFECYCLE_GENERATION or _IDLE_UNLOAD_TIMER is None:
                return
            _IDLE_UNLOAD_TIMER = None
            with _LOCK:
                old_session, old_tokenizer = _SESSION, _TOKENIZER
                _SESSION = None
                _TOKENIZER = None
        close = getattr(old_session, "close", None)
        if callable(close):
            close()
        del old_session, old_tokenizer
        gc.collect()
        logger.info("EmbeddingGemma ONNX descarregado após ociosidade")


def generate_embedding_onnx(
    text: str,
    *,
    is_query: bool = False,
    model_path: Path | str | None = None,
    tokenizer_path: Path | str | None = None,
) -> list[float] | None:
    """Gera um embedding vetorial usando EmbeddingGemma ONNX INT8."""
    cleaned = (text or "").strip()
    if not cleaned:
        return None

    try:
        import numpy as np

        with _SESSION_USE_LOCK:
            session, tokenizer = _get_onnx_session_and_tokenizer(model_path, tokenizer_path)
            formatted = format_query_text(cleaned) if is_query else format_doc_text(cleaned)
            encoding = tokenizer.encode(formatted)
            input_ids = np.array([encoding.ids], dtype=np.int64)
            attention_mask = np.array([encoding.attention_mask], dtype=np.int64)
            outputs = session.run(None, {"input_ids": input_ids, "attention_mask": attention_mask})
        token_embs = outputs[0]  # [1, 512, 768]

        mask_expanded = np.expand_dims(attention_mask, -1).astype(np.float32)
        sum_embs = np.sum(token_embs * mask_expanded, axis=1)
        sum_mask = np.clip(mask_expanded.sum(axis=1), a_min=1e-9, a_max=None)
        mean_pooled = sum_embs / sum_mask

        norm = np.clip(np.linalg.norm(mean_pooled, axis=1, keepdims=True), a_min=1e-9, a_max=None)
        normalized = (mean_pooled / norm)[0]
        return [float(x) for x in normalized]
    except Exception as exc:
        logger.warning(f"Falha ao gerar embedding ONNX: {exc}")
        return None


def generate_embeddings_batch_onnx(
    texts: Sequence[str],
    *,
    is_query: bool = False,
    model_path: Path | str | None = None,
    tokenizer_path: Path | str | None = None,
) -> list[list[float] | None]:
    """Gera embeddings em lote usando EmbeddingGemma ONNX INT8."""
    if not texts:
        return []

    try:
        import numpy as np

        with _SESSION_USE_LOCK:
            session, tokenizer = _get_onnx_session_and_tokenizer(model_path, tokenizer_path)
            formatted_list = [format_query_text(t) if is_query else format_doc_text(t) for t in texts]
            encodings = tokenizer.encode_batch(formatted_list)
            input_ids = np.array([e.ids for e in encodings], dtype=np.int64)
            attention_mask = np.array([e.attention_mask for e in encodings], dtype=np.int64)
            outputs = session.run(None, {"input_ids": input_ids, "attention_mask": attention_mask})
        token_embs = outputs[0]

        mask_expanded = np.expand_dims(attention_mask, -1).astype(np.float32)
        sum_embs = np.sum(token_embs * mask_expanded, axis=1)
        sum_mask = np.clip(mask_expanded.sum(axis=1), a_min=1e-9, a_max=None)
        mean_pooled = sum_embs / sum_mask

        norms = np.clip(np.linalg.norm(mean_pooled, axis=1, keepdims=True), a_min=1e-9, a_max=None)
        normalized = mean_pooled / norms

        return [[float(x) for x in vec] for vec in normalized]
    except Exception as exc:
        logger.warning(f"Falha ao gerar embeddings em batch ONNX: {exc}")
        return [generate_embedding_onnx(t, is_query=is_query, model_path=model_path, tokenizer_path=tokenizer_path) for t in texts]
