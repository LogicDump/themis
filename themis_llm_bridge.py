"""Process-local bridge between the Agent Plugin context and dashboard routes.

The dashboard plugin is imported separately from ``register(ctx)``.  Keep only
the host-owned LLM facade in this registry; never retain the full context or
credentials.
"""
from __future__ import annotations

import os
import threading
from pathlib import Path
from typing import Any

_LOCK = threading.RLock()
_RUNTIMES: dict[tuple[str, str], Any] = {}


def _home(value: str | os.PathLike[str] | None = None) -> str:
    raw = value if value is not None else os.environ.get("HERMES_HOME")
    if not raw:
        return "<unset>"
    return str(Path(raw).expanduser().resolve())


def runtime_key(*, profile_name: str | None = None, hermes_home: str | os.PathLike[str] | None = None) -> tuple[str, str]:
    profile = str(profile_name or os.environ.get("HERMES_PROFILE") or "default").strip() or "default"
    return (_home(hermes_home), profile)


def register_runtime(ctx: Any) -> tuple[str, str]:
    """Register the host LLM when present; minimal probes may omit it."""
    llm = getattr(ctx, "llm", None)
    key = runtime_key(
        profile_name=getattr(ctx, "profile_name", None),
        hermes_home=os.environ.get("HERMES_HOME"),
    )
    if llm is None:
        return key
    with _LOCK:
        _RUNTIMES[key] = llm

    def unload() -> None:
        with _LOCK:
            # A replacement from a newer plugin generation must survive an
            # older generation's unload callback.
            if _RUNTIMES.get(key) is llm:
                _RUNTIMES.pop(key, None)

    ctx.on_unload(unload)
    return key


def unregister_runtime(*, profile_name: str | None = None, hermes_home: str | os.PathLike[str] | None = None) -> None:
    with _LOCK:
        _RUNTIMES.pop(runtime_key(profile_name=profile_name, hermes_home=hermes_home), None)


def _request_value(request: Any, names: tuple[str, ...]) -> Any:
    scope = getattr(request, "scope", {}) or {}
    for name in names:
        value = scope.get(name)
        if value is not None:
            return value
    state = getattr(request, "state", None)
    for name in names:
        value = getattr(state, name, None)
        if value is not None:
            return value
    app_state = getattr(getattr(request, "app", None), "state", None)
    for name in names:
        value = getattr(app_state, name, None)
        if value is not None:
            return value
    return None


def resolve_runtime(request: Any = None) -> Any | None:
    """Resolve the request's profile runtime without falling across profiles."""
    profile = _request_value(request, ("profile_name", "profile")) if request is not None else None
    home = _request_value(request, ("hermes_home", "home")) if request is not None else None
    key = runtime_key(profile_name=profile, hermes_home=home)
    with _LOCK:
        runtime = _RUNTIMES.get(key)
        if runtime is not None:
            return runtime
        # In a single-profile process there is no ambiguity; a multi-profile
        # process must fail closed rather than borrow another profile's LLM.
        if profile is None and home is None and len(_RUNTIMES) == 1:
            return next(iter(_RUNTIMES.values()))
    return None


def clear_for_tests() -> None:
    with _LOCK:
        _RUNTIMES.clear()
