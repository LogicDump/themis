"""Recognizer e-SAJ/TJSP validado para o carimbo de conferência documental."""
from __future__ import annotations
import re

FINGERPRINT = "esaj.tjsp.jus.br/pastadigital/pg/abrirConferenciaDocumento.do"
PATTERN = re.compile(r"informe\s+o\s+processo\s+(\d{7}-\d{2}\.\d{4}\.\d\.\d{2}\.\d{4})\s+e\s+c[óo]digo", re.I)

def resolve_page_one(text: str) -> dict | None:
    if FINGERPRINT.lower() not in text.lower():
        return None
    matches = list(PATTERN.finditer(text))
    numbers = {match.group(1) for match in matches}
    if len(numbers) != 1:
        return None
    match = matches[0]
    return {"process_id": match.group(1), "source_type": "esaj_tjsp", "method": "conference_stamp", "page": 1,
            "confidence": "HIGH", "anchor": text[max(0, match.start()-110):match.end()+45]}
