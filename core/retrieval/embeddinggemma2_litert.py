"""EmbeddingGemma 2 Text 270M with pinned LiteRT artifact and isolated vector space.

No silent fallback across CPU/GPU after an index has been created.
No copying of legacy EmbeddingGemma 1 embeddings.
"""
from __future__ import annotations

import hashlib
import logging
import math
import os
import threading
from pathlib import Path
from typing import Sequence

MODEL = "embeddinggemma2:text-270m"
VERSION = "2-text-270m-9be6e8b-chunk600-v1"
DIM = 768
QUANTIZATION = "litertlm-quantized"
BACKEND_GPU = "litert-webgpu"
BACKEND_CPU = "litert-cpu"
HF_REPO = "litert-community/embeddinggemma-2-text-270m-litert-lm"
HF_REVISION = "9be6e8b90982095dc05c2bd162e4b954ee4dbac7"
FILENAME = "embeddinggemma-2-text-270m.litertlm"
SHA256 = "2d079ee2f6f066b1f368e8d7c819f55214eaef1d0513b312321901f30ab286fb"
MAX_CHARS = 600
_LOG = logging.getLogger(__name__)
_LOCK = threading.RLock()
_ENGINE = None
_ENGINE_BACKEND = None
_ENGINE_PATH = None


def model_path() -> Path:
    override = os.environ.get("THEMIS_EMBEDDINGGEMMA2_MODEL_PATH")
    if override:
        return Path(override).expanduser().resolve()
    from core.runtime_paths import themis_data_root
    return themis_data_root() / "models" / "embeddinggemma-2-text-270m" / FILENAME


def ensure_model() -> Path:
    path = model_path()
    if path.is_file():
        if hashlib.sha256(path.read_bytes()).hexdigest() != SHA256:
            raise RuntimeError("EmbeddingGemma 2: artefato local com SHA256 divergente")
        return path
    if os.environ.get("THEMIS_EMBEDDINGGEMMA2_OFFLINE") == "1":
        raise FileNotFoundError(f"Modelo EmbeddingGemma 2 ausente: {path}")
    from huggingface_hub import hf_hub_download
    path.parent.mkdir(parents=True, exist_ok=True)
    downloaded = hf_hub_download(
        repo_id=HF_REPO, filename=FILENAME, revision=HF_REVISION,
        local_dir=str(path.parent),
    )
    if Path(downloaded).resolve() != path.resolve():
        raise RuntimeError("Caminho do modelo EmbeddingGemma 2 inesperado")
    if hashlib.sha256(path.read_bytes()).hexdigest() != SHA256:
        raise RuntimeError("Download EmbeddingGemma 2 com SHA256 divergente")
    return path


def _desired_backend(required: str | None) -> list[str]:
    setting = (required or os.environ.get("THEMIS_EMBEDDINGGEMMA2_DEVICE") or "auto").lower()
    if setting in ("gpu", BACKEND_GPU):
        return [BACKEND_GPU]
    if setting in ("cpu", BACKEND_CPU):
        return [BACKEND_CPU]
    if setting == "auto":
        return [BACKEND_GPU, BACKEND_CPU]
    raise ValueError("THEMIS_EMBEDDINGGEMMA2_DEVICE deve ser auto, cpu ou gpu")


def _get_engine(required: str | None = None):
    global _ENGINE, _ENGINE_BACKEND, _ENGINE_PATH
    with _LOCK:
        options = _desired_backend(required)
        if _ENGINE is not None and _ENGINE_BACKEND in options and _ENGINE_PATH == model_path():
            return _ENGINE, _ENGINE_BACKEND
        path = ensure_model()
        from litert_lm import Backend, EmbeddingEngine
        last_error = None
        for mode in options:
            if _ENGINE is not None and mode == _ENGINE_BACKEND and _ENGINE_PATH == path:
                return _ENGINE, mode
            try:
                candidate = EmbeddingEngine(
                    str(path), backend=Backend.GPU() if mode == BACKEND_GPU else Backend.CPU()
                )
                candidate.__enter__()
                prior = _ENGINE
                _ENGINE, _ENGINE_BACKEND, _ENGINE_PATH = candidate, mode, path
                if prior is not None:
                    prior.__exit__(None, None, None)
                return candidate, mode
            except Exception as exc:
                last_error = exc
                _LOG.warning("EmbeddingGemma 2: backend %s indisponível: %s", mode, exc)
        raise RuntimeError(f"EmbeddingGemma 2 não iniciou backend solicitado: {last_error}")


def active_signature(required: str | None = None) -> dict[str, object]:
    _engine, mode = _get_engine(required)
    return {"model": MODEL, "model_version": VERSION, "backend": mode,
            "quantization": QUANTIZATION, "dim": DIM}


def _chunks(text: str) -> list[str]:
    text = " ".join(text.split())
    if not text:
        return []
    parts = []
    while text:
        if len(text) <= MAX_CHARS:
            parts.append(text)
            break
        at = text.rfind(" ", 0, MAX_CHARS + 1)
        if at < MAX_CHARS // 3:
            at = MAX_CHARS
        parts.append(text[:at].strip())
        text = text[at:].strip()
    return parts


def embed_many(
    texts: Sequence[str], *, is_query: bool = False, required_backend: str | None = None,
) -> tuple[list[list[float] | None], dict[str, object]]:
    with _LOCK:
        engine, mode = _get_engine(required_backend)
        result = []
        for source in texts:
            chunks = _chunks(source or "")
            if not chunks:
                result.append(None)
                continue
            prompt = "task: search query | text: " if is_query else "task: search result | text: "
            total = [0.0] * DIM
            weight_sum = 0
            for chunk in chunks:
                vector = engine.compute_embedding(prompt + chunk).embedding
                if len(vector) != DIM or not all(math.isfinite(v) for v in vector):
                    raise RuntimeError("EmbeddingGemma 2 retornou vetor inválido")
                weight = len(chunk)
                for i, value in enumerate(vector):
                    total[i] += float(value) * weight
                weight_sum += weight
            norm = math.sqrt(sum((v / weight_sum) ** 2 for v in total))
            if norm < 1e-12:
                raise RuntimeError("EmbeddingGemma 2 retornou vetor nulo")
            result.append([(v / weight_sum) / norm for v in total])
        return result, {"model": MODEL, "model_version": VERSION, "backend": mode,
                        "quantization": QUANTIZATION, "dim": DIM}


def embed_query(text: str, *, required_backend: str | None = None):
    values, signature = embed_many([text], is_query=True, required_backend=required_backend)
    return values[0], signature
