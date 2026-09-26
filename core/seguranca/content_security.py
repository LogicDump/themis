"""Detecção textual conservadora para conteúdo documental não confiável.

O resultado descreve sinais e cuidado operacional; nunca conclui intenção,
ataque real, valor probatório ou consequência jurídica.
"""
from __future__ import annotations

import hashlib
import re
import unicodedata
from typing import Any

DETECTOR_VERSION = "content-security/0.1"
TRUST = "untrusted_external_content"

SIGNALS: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("IGNORE_PREVIOUS_INSTRUCTIONS", (r"\bignore (?:all |any |the )?(?:previous|prior) instructions?\b", r"\bignore (?:as )?instru[cç][oõ]es (?:anteriores|pr[eé]vias)\b")),
    ("OVERRIDE_SYSTEM_INSTRUCTIONS", (r"\b(?:override|replace|change) (?:the )?(?:system|developer) (?:prompt|instructions?)\b", r"\b(?:substitua|altere|ignore) (?:o )?(?:prompt|instru[cç][oõ]es) (?:do )?sistema\b")),
    ("REQUEST_SYSTEM_PROMPT", (r"\b(?:reveal|show|print|provide) (?:the )?(?:system|developer) prompt\b", r"\b(?:revele|mostre|exiba|forne[cç]a) (?:o )?prompt (?:do )?sistema\b")),
    ("REQUEST_SECRET_OR_CREDENTIAL", (r"\b(?:reveal|show|send|provide) (?:(?:all|the) )?(?:secrets?|credentials?|api ?keys?|passwords?)\b", r"\b(?:revele|mostre|envie|forne[cç]a) (?:(?:os|as) )?(?:segredos?|credenciais|chaves? (?:de )?api|senhas?)\b")),
    ("EXECUTE_TOOL_OR_COMMAND", (r"\b(?:execute|run|call|invoke|use) (?:the )?(?:tool|command|terminal|shell)\b", r"\b(?:execute|rode|chame|invoque|use) (?:a )?(?:ferramenta|comando|terminal|shell)\b")),
    ("ACCESS_UNRELATED_FILES", (r"\b(?:read|open|access) (?:all |the )?(?:files?|filesystem|system files?)\b", r"\b(?:leia|abra|acesse) (?:todos )?(?:os )?(?:arquivos?|sistema de arquivos)\b")),
    ("EXFILTRATE_DATA", (r"\b(?:send|upload|exfiltrate|forward) (?:the )?(?:data|files?|contents?) (?:to|via)\b", r"\b(?:envie|fa[cç]a upload|exfiltre|encaminhe) (?:os )?(?:dados|arquivos?|conte[uú]do) (?:para|por)\b")),
    ("MODEL_OR_AGENT_DIRECTIVE", (r"\b(?:chatgpt|claude|assistant|ai model|agent),?\s+(?:ignore|follow|do|you must)\b", r"\b(?:chatgpt|claude|assistente|agente|modelo),?\s+(?:ignore|siga|fa[cç]a|voc[eê] deve)\b")),
)

EVIDENTIARY_MARKER = re.compile(r"\b(?:a instru[cç][aã]o dizia|o invasor enviou|exemplo\s*:|transcri[cç][aã]o\s*:|cita[cç][aã]o\s*:|o texto continha)\b", re.I)
DESCRIPTIVE_MARKER = re.compile(r"\b(?:artigo acad[eê]mico|pesquisa acad[eê]mica|laudo t[eé]cnico|explica|analisa|descreve|conceito de prompt injection)\b", re.I)


def _normalized(text: str) -> str:
    return re.sub(r"\s+", " ", unicodedata.normalize("NFKC", text)).strip()


def _fingerprint(normalized_text: str) -> str:
    return hashlib.sha256(normalized_text.encode("utf-8")).hexdigest()


def _local_context(text: str, spans: list[tuple[int, int]]) -> str:
    if not spans:
        return "unknown"
    windows = [text[max(0, start - 180):min(len(text), end + 180)] for start, end in spans]
    for window in windows:
        if EVIDENTIARY_MARKER.search(window) and ("'" in window or '"' in window or "“" in window):
            return "quoted_or_evidentiary"
    if any(DESCRIPTIVE_MARKER.search(window) for window in windows):
        return "descriptive"
    return "ambiguous"


def _execution_risk(signals: list[str]) -> str:
    if not signals:
        return "low"
    high_impact = {"OVERRIDE_SYSTEM_INSTRUCTIONS", "REQUEST_SYSTEM_PROMPT", "REQUEST_SECRET_OR_CREDENTIAL", "EXECUTE_TOOL_OR_COMMAND", "ACCESS_UNRELATED_FILES", "EXFILTRATE_DATA"}
    return "high" if len(set(signals) & high_impact) >= 2 else "medium"


def analyze_text(text: str) -> dict[str, Any]:
    """Return derived metadata only; text itself is never altered or retained."""
    value = _normalized(text)
    matches = [(rule_id, match) for rule_id, patterns in SIGNALS for pattern in patterns for match in [re.search(pattern, value, re.I)] if match]
    signals = sorted({rule_id for rule_id, _ in matches})
    context = _local_context(value, [(match.start(), match.end()) for _, match in matches])
    return {
        "trust": TRUST,
        "signals": signals,
        "context": context,
        "execution_risk": _execution_risk(signals),
        "detector_version": DETECTOR_VERSION,
        "analysis_status": "complete",
        "content_fingerprint": _fingerprint(value),
    }


def unavailable() -> dict[str, Any]:
    """Fail-safe metadata when analysis cannot run; content remains untrusted."""
    return {
        "trust": TRUST,
        "signals": [],
        "context": "unknown",
        "execution_risk": "medium",
        "detector_version": DETECTOR_VERSION,
        "analysis_status": "unavailable",
    }


def is_current(metadata: Any, text: str) -> bool:
    """Only complete metadata for this exact normalized text is reusable."""
    if not isinstance(metadata, dict): return False
    return (metadata.get("trust") == TRUST and metadata.get("detector_version") == DETECTOR_VERSION
            and metadata.get("analysis_status") == "complete" and isinstance(metadata.get("signals"), list)
            and metadata.get("context") in {"unknown", "quoted_or_evidentiary", "descriptive", "instructional", "ambiguous"}
            and metadata.get("execution_risk") in {"low", "medium", "high"}
            and metadata.get("content_fingerprint") == _fingerprint(_normalized(text)))


def analyze_document(page_security: list[dict[str, Any]]) -> dict[str, Any]:
    """Summarize page metadata without retaining page text or detected secrets."""
    if not page_security:
        return {
            "trust": TRUST,
            "signals": [],
            "context": "unknown",
            "execution_risk": "medium",
            "detector_version": DETECTOR_VERSION,
            "analysis_status": "unavailable",
            "pages_analyzed": 0,
        }
    signals = sorted({signal for item in page_security for signal in item.get("signals", [])})
    risks = {"low": 1, "medium": 2, "high": 3}
    contexts = {item.get("context", "unknown") for item in page_security}
    return {
        "trust": TRUST,
        "signals": signals,
        "context": contexts.pop() if len(contexts) == 1 else "ambiguous",
        "execution_risk": max(page_security, key=lambda item: risks.get(item.get("execution_risk"), 2)).get("execution_risk", "medium"),
        "detector_version": DETECTOR_VERSION,
        "analysis_status": "unavailable" if any(item.get("analysis_status") == "unavailable" for item in page_security) else "complete",
        "pages_analyzed": len(page_security),
    }
