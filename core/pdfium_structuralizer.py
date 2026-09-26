"""Deterministic PDFium Structuralizer for Readable Markdown V2."""
from __future__ import annotations

import base64
import ctypes
import hashlib
import io
from html.parser import HTMLParser
import re
import json
import unicodedata
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from difflib import SequenceMatcher
from enum import Enum
from pathlib import Path
from statistics import median
from typing import Any

import pypdfium2 as pdfium
import pypdfium2.raw as pdfium_raw


@dataclass
class LineInfo:
    text: str
    bbox: tuple[float, float, float, float]
    font_size: float
    is_bold: bool
    is_italic: bool
    y_top: float
    y_bottom: float
    x_left: float
    x_right: float
    raw_line_id: int = 0
    # Set only while merging physical PDF blocks.  It preserves a geometric
    # paragraph restart inside one semantic list item.
    paragraph_start: bool = False


@dataclass(frozen=True)
class GlyphRun:
    """A transient horizontal run derived from PDFium character boxes.

    This intentionally has no representation in ``structure_json``.  It is
    available only to offline geometry diagnostics while a PDFium text page is
    open; the canonical textual contract remains line-based.
    """

    raw_line_id: int
    text: str
    bbox: tuple[float, float, float, float]
    gap_before: float | None = None
    gap_before_normalized: float | None = None


class FlowKind(str, Enum):
    """Closed set of semantic flows allowed to participate in continuity.

    PDFium physical blocks are only a transport detail.  A continuation is
    meaningful only after both sides have been assigned to one of these
    conservative kinds; a generic prose merge must never bridge them.
    """

    PROSE = "PROSE"
    LIST_ITEM = "LIST_ITEM"
    HEADING = "HEADING"
    QUOTE = "QUOTE"
    FIELD = "FIELD"
    FURNITURE = "FURNITURE"
    TABLE = "TABLE"
    UNKNOWN = "UNKNOWN"


@dataclass
class TypedFlowNode:
    """AST node built before Markdown serialization.

    ``children`` is used by ListItem for its Paragraph nodes.  Keeping the
    physical lines on every node makes source-line identity and bbox
    derivation additive rather than reconstructing provenance from Markdown.
    """

    kind: FlowKind
    lines: list[LineInfo]
    children: list["TypedFlowNode"] = field(default_factory=list)
    reason: str = ""

    @property
    def source_line_ids(self) -> list[int]:
        return [line.raw_line_id for line in self.lines]

    @property
    def bbox(self) -> tuple[float, float, float, float]:
        return (
            min(line.bbox[0] for line in self.lines),
            min(line.bbox[1] for line in self.lines),
            max(line.bbox[2] for line in self.lines),
            max(line.bbox[3] for line in self.lines),
        )


@dataclass(frozen=True)
class LineFlowMetrics:
    """Robust local geometry for one reading flow/column."""
    line_height: float
    baseline: float
    baseline_mad: float
    left_edge: float
    right_edge: float
    column_width: float
    left_tolerance: float
    right_tolerance: float


# Specific forensic repair patterns for PT-BR text corrupted by ToUnicode replacement chars
# Handles both literal \ufffd and stripped variants where \ufffd was dropped.
REPAIR_PATTERNS = [
    # Ordinals & court headers
    (r"(\d+)\s*[\ufffdºª]?\s*([vV][aA][rR][aA]|[cC][âa][mM][aA][rR][aA]|[tT][uU][rR][mM][aA])\b", r"\1ª \2"),
    (r"\b(\d{1,3})\s*[\ufffdºª]\b", r"\1º"),
    (r"\b[nN][\ufffdºª.]?\s*(\d+)", r"nº \1"),
    (r"\b[nN][\ufffdºª]\b", r"nº"),
    (r"\b[mM][mM][\ufffdºª.]?\s*([jJ][uU][iI][zZ][aA]?)\b", r"MM. \1"),
    (r"\b[fF][lL][sS][\ufffdºª.]?\s*(\d+)", r"fls. \1"),
    (r"\b[fF][oO][lL][hH][aA][sS]?\s*[\ufffdºª.]?\s*(\d+)", r"fls. \1"),
    (r"\b[àa]s?\s*[\ufffdºª]?\s*(\d{1,2}[hH]\d{0,2})\b", r"às \1"),
    (r"\s+[\ufffd\s]+\s*(SP|RJ|MG|RS|PR|SC|BA|GO|PE|CE|PA|AM|ES|DF)\b", r" - \1"),
    (r"[\ufffd\s]+presen[cç\ufffd][aã\ufffd]\b", r" à presença"),

    # Court, Jurisdictions & Bodies
    (r"\bEXCELENT[\ufffdI]?SSIM([OA])\b", r"EXCELENTÍSSIM\1"),
    (r"\bexcelent[\ufffdI]?ssim([oa])\b", r"excelentíssim\1"),
    (r"\bEXCEL[\ufffdE]?NCIA(S?)\b", r"EXCELÊNCIA\1"),
    (r"\bexcel[\ufffdE]?ncia(s?)\b", r"excelência\1"),
    (r"\bS[\ufffdA]?O PAULO\b", r"SÃO PAULO"),
    (r"\bS[\ufffda]?o Paulo\b", r"São Paulo"),
    (r"\bSANTO ANDR[\ufffdE]?\b", r"SANTO ANDRÉ"),
    (r"\bSanto Andr[\ufffde]?\b", r"Santo André"),
    (r"\bTRIBUNAL DE JUSTI[\ufffdC]?A\b", r"TRIBUNAL DE JUSTIÇA"),
    (r"\bTribunal de Justi[\ufffdc]?a\b", r"Tribunal de Justiça"),
    (r"\bPODER JUDICI[\ufffdA]?RIO\b", r"PODER JUDICIÁRIO"),
    (r"\bPoder Judici[\ufffda]?rio\b", r"Poder Judiciário"),
    (r"\bMINIST[\ufffdE]?RIO P[\ufffdU]?BLICO\b", r"MINISTÉRIO PÚBLICO"),
    (r"\bMinist[\ufffde]?rio P[\ufffdu]?blico\b", r"Ministério Público"),
    (r"\bDI[\ufffdA]?RIO\b", r"DIÁRIO"),
    (r"\bDi[\ufffda]?rio\b", r"Diário"),
    (r"\bELETR[\ufffdO]?NICO\b", r"ELETRÔNICO"),
    (r"\bEletr[\ufffdo]?nico\b", r"Eletrônico"),
    (r"\b[\ufffdO]?RG[\ufffdA]?O\b", r"ÓRGÃO"),
    (r"\b[\ufffdo]?rg[\ufffda]?o\b", r"órgão"),

    # Action types, proceedings, branches
    (r"\bC[\ufffdI]?VEL\b", r"CÍVEL"),
    (r"\bc[\ufffdi]?vel\b", r"cível"),
    (r"\bC[\ufffdI]?VEIS\b", r"CÍVEIS"),
    (r"\bc[\ufffdi]?veis\b", r"cíveis"),
    (r"\bFAM[\ufffdI]?LIA\b", r"FAMÍLIA"),
    (r"\bfam[\ufffdi]?lia\b", r"família"),
    (r"\bSUCESS[\ufffdO]?ES\b", r"SUCESSÕES"),
    (r"\bsucess[\ufffdo]?es\b", r"sucessões"),
    (r"\bSUCESS[\ufffdA]?O\b", r"SUCESSÃO"),
    (r"\bsucess[\ufffda]?o\b", r"sucessão"),
    (r"\bDECIS[\ufffdA]?O\b", r"DECISÃO"),
    (r"\bdecis[\ufffda]?o\b", r"decisão"),
    (r"\bINTIMA[\ufffdC]?[\ufffdA]?O\b", r"INTIMAÇÃO"),
    (r"\bintima[\ufffdc]?[\ufffda]?o\b", r"intimação"),
    (r"\bINTIMA[\ufffdC]?[\ufffdO]?ES\b", r"INTIMAÇÕES"),
    (r"\bintima[\ufffdc]?[\ufffdo]?es\b", r"intimações"),
    (r"\bPUBLICA[\ufffdC]?[\ufffdA]?O\b", r"PUBLICAÇÃO"),
    (r"\bpublica[\ufffdc]?[\ufffda]?o\b", r"publicação"),
    (r"\bPUBLICA[\ufffdC]?[\ufffdO]?ES\b", r"PUBLICAÇÕES"),
    (r"\bpublica[\ufffdc]?[\ufffdo]?es\b", r"publicações"),
    (r"\bRELA[\ufffdC]?[\ufffdA]?O\b", r"RELAÇÃO"),
    (r"\brela[\ufffdc]?[\ufffda]?o\b", r"relação"),
    (r"\bCERTID[\ufffdA]?O\b", r"CERTIDÃO"),
    (r"\bcertid[\ufffda]?o\b", r"certidão"),
    (r"\bCERTID[\ufffdO]?ES\b", r"CERTIDÕES"),
    (r"\bcertid[\ufffdo]?es\b", r"certidões"),
    (r"\bPETI[\ufffdC]?[\ufffdA]?O\b", r"PETIÇÃO"),
    (r"\bpeti[\ufffdc]?[\ufffda]?o\b", r"petição"),
    (r"\bPETI[\ufffdC]?[\ufffdO]?ES\b", r"PETIÇÕES"),
    (r"\bpeti[\ufffdc]?[\ufffdo]?es\b", r"petições"),
    (r"\bINDENIZA[\ufffdC]?[\ufffdA]?O\b", r"INDENIZAÇÃO"),
    (r"\bindeniza[\ufffdc]?[\ufffda]?o\b", r"indenização"),
    (r"\bINDENIZA[\ufffdC]?[\ufffdO]?ES\b", r"INDENIZAÇÕES"),
    (r"\bindeniza[\ufffdc]?[\ufffdo]?es\b", r"indenizações"),
    (r"\bPROCURA[\ufffdC]?[\ufffdA]?O\b", r"PROCURAÇÃO"),
    (r"\bprocura[\ufffdc]?[\ufffda]?o\b", r"procuração"),
    (r"\bDECLARA[\ufffdC]?[\ufffdA]?O\b", r"DECLARAÇÃO"),
    (r"\bdeclara[\ufffdc]?[\ufffda]?o\b", r"declaração"),
    (r"\bDECLARA[\ufffdC]?[\ufffdO]?ES\b", r"DECLARAÇÕES"),
    (r"\bdeclara[\ufffdc]?[\ufffdo]?es\b", r"declarações"),
    (r"\bINVESTIGA[\ufffdC]?[\ufffdA]?O\b", r"INVESTIGAÇÃO"),
    (r"\binvestiga[\ufffdc]?[\ufffda]?o\b", r"investigação"),
    (r"\bAUDI[\ufffdE]?NCIA(S?)\b", r"AUDIÊNCIA\1"),
    (r"\baudi[\ufffde]?ncia(s?)\b", r"audiência\1"),
    (r"\bPER[\ufffdI]?CIA(S?)\b", r"PERÍCIA\1"),
    (r"\bper[\ufffdi]?cia(s?)\b", r"perícia\1"),
    (r"\bPENS[\ufffdA]?O\b", r"PENSÃO"),
    (r"\bpens[\ufffda]?o\b", r"pensão"),
    (r"\bPENS[\ufffdO]?ES\b", r"PENSÕES"),
    (r"\bpens[\ufffdo]?es\b", r"pensões"),
    (r"\bALIMENT[\ufffdI]?CI([AO]S?)\b", r"ALIMENTÍCI\1"),
    (r"\baliment[\ufffdi]?ci([ao]s?)\b", r"alimentíci\1"),
    (r"\bOF[\ufffdI]?CIO(S?)\b", r"OFÍCIO\1"),
    (r"\bof[\ufffdi]?cio(s?)\b", r"ofício\1"),
    (r"\bHONOR[\ufffdA]?RIOS\b", r"HONORÁRIOS"),
    (r"\bhonor[\ufffda]?rios\b", r"honorários"),
    (r"\bLITIG[\ufffdA]?NCIA\b", r"LITIGÂNCIA"),
    (r"\blitig[\ufffda]?ncia\b", r"litigância"),
    (r"\bM[\ufffdA]?-F[\ufffdE]?\b", r"MÁ-FÉ"),
    (r"\bm[\ufffda]?-f[\ufffde]?\b", r"má-fé"),
    (r"\bBENEF[\ufffdI]?CIO(S?)\b", r"BENEFÍCIO\1"),
    (r"\bbenef[\ufffdi]?cio(s?)\b", r"benefício\1"),
    (r"\bC[\ufffdO]?NJUGE(S?)\b", r"CÔNJUGE\1"),
    (r"\bc[\ufffdo]?njuge(s?)\b", r"cônjuge\1"),
    (r"\bC[\ufffdO]?DIGO\b", r"CÓDIGO"),
    (r"\bc[\ufffdo]?digo\b", r"código"),
    (r"\bJURISPRUD[\ufffdE]?NCIA\b", r"JURISPRUDÊNCIA"),
    (r"\bjurisprud[\ufffde]?ncia\b", r"jurisprudência"),
    (r"\bM[\ufffdA]?XIMA V[\ufffdE]?NIA\b", r"MÁXIMA VÊNIA"),
    (r"\bm[\ufffda]?xima v[\ufffde]?nia\b", r"máxima vênia"),
    (r"\bATUA[\ufffdC]?[\ufffdA]?O\b", r"ATUAÇÃO"),
    (r"\batua[\ufffdc]?[\ufffda]?o\b", r"atuação"),
    (r"\bPRESEN[\ufffdC]?A\b", r"PRESENÇA"),
    (r"\bpresen[\ufffdc]?a\b", r"presença"),
    (r"\bDEMISS[\ufffdA]?O\b", r"DEMISSÃO"),
    (r"\bdemiss[\ufffda]?o\b", r"demissão"),
    (r"\bOMISS[\ufffdA]?O\b", r"OMISSÃO"),
    (r"\bomiss[\ufffda]?o\b", r"omissão"),
    (r"\bREALIZA[\ufffdC]?[\ufffdA]?O\b", r"REALIZAÇÃO"),
    (r"\brealiza[\ufffdc]?[\ufffda]?o\b", r"realização"),
    (r"\bFIXA[\ufffdC]?[\ufffdA]?O\b", r"FIXAÇÃO"),
    (r"\bfixa[\ufffdc]?[\ufffda]?o\b", r"fixação"),
    (r"\bEXECU[\ufffdC]?[\ufffdA]?O\b", r"EXECUÇÃO"),
    (r"\bexecu[\ufffdc]?[\ufffda]?o\b", r"execução"),
    (r"\bDISTRIBUI[\ufffdC]?[\ufffdA]?O\b", r"DISTRIBUIÇÃO"),
    (r"\bdistribui[\ufffdc]?[\ufffda]?o\b", r"distribuição"),
    (r"\bOBRIGA[\ufffdC]?[\ufffdA]?O\b", r"OBRIGAÇÃO"),
    (r"\bobriga[\ufffdc]?[\ufffda]?o\b", r"obrigação"),
    (r"\bSEPARA[\ufffdC]?[\ufffdA]?O\b", r"SEPARAÇÃO"),
    (r"\bsepara[\ufffdc]?[\ufffda]?o\b", r"separação"),
    (r"\bCONTRADI[\ufffdC]?[\ufffdA]?O\b", r"CONTRADIÇÃO"),
    (r"\bcontradi[\ufffdc]?[\ufffda]?o\b", r"contradição"),
    (r"\bIMPUGNA[\ufffdC]?[\ufffdA]?O\b", r"IMPUGNAÇÃO"),
    (r"\bimpugna[\ufffdc]?[\ufffda]?o\b", r"impugnação"),
    (r"\bCONTESTA[\ufffdC]?[\ufffdA]?O\b", r"CONTESTAÇÃO"),
    (r"\bcontesta[\ufffdc]?[\ufffda]?o\b", r"contestação"),
    (r"\bAPELA[\ufffdC]?[\ufffdA]?O\b", r"APELAÇÃO"),
    (r"\bapela[\ufffdc]?[\ufffda]?o\b", r"apelação"),
    (r"\bHOR[\ufffdA]?RIO\b", r"HORÁRIO"),
    (r"\bhor[\ufffda]?rio\b", r"horário"),
    (r"\bP[\ufffdU]?BLICO\b", r"PÚBLICO"),
    (r"\bp[\ufffdu]?blico\b", r"público"),
    (r"\bTR[\ufffdA]?NSITO\b", r"TRÂNSITO"),
    (r"\btr[\ufffda]?nsito\b", r"trânsito"),
    (r"\bIMPORT[\ufffdA]?NCIA\b", r"IMPORTÂNCIA"),
    (r"\bimport[\ufffda]?ncia\b", r"importância"),
    (r"\bR[\ufffdA]?PIDO\b", r"RÁPIDO"),
    (r"\br[\ufffda]?pido\b", r"rápido"),
    (r"\bD[\ufffdU]?VIDA(S?)\b", r"DÚVIDA\1"),
    (r"\bd[\ufffdu]?vida(s?)\b", r"dúvida\1"),
    (r"\bCOBRAN[\ufffdC]?A\b", r"COBRANÇA"),
    (r"\bcobran[\ufffdc]?a\b", r"cobrança"),
    (r"\bCRIAN[\ufffdC]?A(S?)\b", r"CRIANÇA\1"),
    (r"\bcrian[\ufffdc]?a(s?)\b", r"criança\1"),
    (r"\bENDERE[\ufffdC]?O(S?)\b", r"ENDEREÇO\1"),
    (r"\bendere[\ufffdc]?o(s?)\b", r"endereço\1"),
    (r"\bAVALIA[\ufffdC]?[\ufffdA]?O\b", r"AVALIAÇÃO"),
    (r"\bavalia[\ufffdc]?[\ufffda]?o\b", r"avaliação"),
    (r"\bDISPOSI[\ufffdC]?[\ufffdA]?O\b", r"DISPOSIÇÃO"),
    (r"\bdisposi[\ufffdc]?[\ufffda]?o\b", r"disposição"),
    (r"\bMANIFESTA[\ufffdC]?[\ufffdA]?O\b", r"MANIFESTAÇÃO"),
    (r"\bmanifesta[\ufffdc]?[\ufffda]?o\b", r"manifestação"),
    (r"\bA[\ufffdC][\ufffdA]?O\b", r"AÇÃO"),
    (r"\ba[\ufffdc][\ufffda]?o\b", r"ação"),
    (r"\bA[\ufffdC][\ufffdO]?ES\b", r"AÇÕES"),
    (r"\ba[\ufffdc][\ufffdo]?es\b", r"ações"),

    # Pronouns, adverbs, short common terms
    (r"\bJ[\ufffdA]?\b", r"JÁ"),
    (r"\bj[\ufffda]?\b", r"já"),
    (r"\bN[\ufffdA]?O\b", r"NÃO"),
    (r"\bn[\ufffda]?o\b", r"não"),
    (r"\bS[\ufffdO]?\b", r"SÓ"),
    (r"\bs[\ufffdo]?\b", r"só"),
    (r"\bAT[\ufffdE]?\b", r"ATÉ"),
    (r"\bat[\ufffde]?\b", r"até"),
    (r"\bM[\ufffdA]?E\b", r"MÃE"),
    (r"\bm[\ufffda]?e\b", r"mãe"),
    (r"\bTR[\ufffdE]?S\b", r"TRÊS"),
    (r"\btr[\ufffde]?s\b", r"três"),
    (r"\bAP[\ufffdO]?S\b", r"APÓS"),
    (r"\bap[\ufffdo]?s\b", r"após"),
    (r"\bEST[\ufffdA]?\b", r"ESTÁ"),
    (r"\best[\ufffda]?\b", r"está"),
    (r"\bEST[\ufffdA]?O\b", r"ESTÃO"),
    (r"\best[\ufffda]?o\b", r"estão"),
    (r"\bSER[\ufffdA]?\b", r"SERÁ"),
    (r"\bser[\ufffda]?\b", r"será"),
    (r"\bSER[\ufffdA]?O\b", r"SERÃO"),
    (r"\bser[\ufffda]?o\b", r"serão"),
    (r"\bHAVER[\ufffdA]?\b", r"HAVERÁ"),
    (r"\bhaver[\ufffda]?\b", r"haverá"),
    (r"\bPOR[\ufffdE]?M\b", r"PORÉM"),
    (r"\bpor[\ufffde]?m\b", r"porém"),
    (r"\bTAMB[\ufffdE]?M\b", r"TAMBÉM"),
    (r"\btamb[\ufffde]?m\b", r"também"),
    (r"\bAL[\ufffdE]?M\b", r"ALÉM"),
    (r"\bal[\ufffde]?m\b", r"além"),
    (r"\bPER[\ufffdI]?ODO\b", r"PERÍODO"),
    (r"\bper[\ufffdi]?odo\b", r"período"),
    (r"\bPADR[\ufffdA]?O\b", r"PADRÃO"),
    (r"\bpadr[\ufffda]?o\b", r"padrão"),
    (r"\bBANC[\ufffdA]?RI([AO]S?)\b", r"BANCÁRI\1"),
    (r"\bbanc[\ufffda]?ri([ao]s?)\b", r"bancári\1"),
    (r"\bPR[\ufffdO]?PRI([AO]S?)\b", r"PRÓPRI\1"),
    (r"\bpr[\ufffdo]?pri([ao]s?)\b", r"própri\1"),
    (r"\b[\ufffdI]?NDICO\b", r"ÍNDICO"),
    (r"\b[\ufffdi]?ndico\b", r"índico"),
    (r"\bSUPED[\ufffdA-Z]?NEO\b", r"SUPEDÂNEO"),
    (r"\bsuped[\ufffda-z]?neo\b", r"supedâneo"),
]


def _is_noise_token(tok: str) -> bool:
    """Check if token is explicit unmapped replacement or unprintable control noise.
    
    INVARIANTE LOSSLESS: Datas, CNJ, CPF, contas, códigos, protocolos e tokens alfanuméricos
    são conteúdo válido e NUNCA devem ser descartados por heurísticas de vogais ou comprimento.
    """
    if not tok:
        return False
    tok_clean = tok.strip(".,;:\"'()[]{}")
    if not tok_clean:
        return False
    if all(c == "\ufffd" or ord(c) < 32 for c in tok_clean):
        return True
    return False


def _is_corrupt_text(text: str) -> bool:
    """Detect if a text buffer is dominated by unmapped CMap glyphs or C0 control characters."""
    if not text:
        return False
    ctrl_count = sum(1 for c in text if ord(c) < 32 and c not in "\t\n\r")
    if ctrl_count >= 5 or (len(text) > 0 and (ctrl_count / len(text)) > 0.01):
        return True
    if text.count("\ufffd") >= 5 or (len(text) > 0 and (text.count("\ufffd") / len(text)) > 0.05):
        return True
    return False


def _is_corrupt_line(text: str) -> bool:
    """Check if line is predominantly noise from defective CMap."""
    if not text:
        return False
    clean = text.strip()
    if not clean:
        return False
    if any(ord(c) < 32 and c not in "\t\n\r" for c in clean):
        return True
    if "\ufffd" in clean:
        if clean.count("\ufffd") >= 2 or (clean.count("\ufffd") / max(1, len(clean))) > 0.10:
            return True
    words = clean.split()
    if words:
        noise_words = sum(1 for w in words if _is_noise_token(w))
        if noise_words > 0 and (noise_words / len(words)) >= 0.8:
            return True
    return False


def _clean_corrupt_cmap_tokens(text: str) -> str:
    """Filter out explicit unmapped glyph noise without altering valid alphanumeric tokens."""
    if not text:
        return ""
    # Strip C0 control chars except standard whitespace
    text = "".join(c for c in text if ord(c) >= 32 or c in "\t\n\r")
    text = re.sub(r"\ufffd+", "", text)
    return text


def sanitize_forensic_text(text: str) -> str:
    """Sanitize formatting and structural whitespace without modifying lexical characters or words.
    
    INVARIANTE LOSSLESS:
    O Markdown canônico dos Autos NUNCA pode corrigir, substituir, inventar ou eliminar
    conteúdo textual extraído do PDF. Preserva o texto PDFium exatamente quanto aos
    caracteres léxicos (sem REPAIR_PATTERNS como no->não, ser->será, 3ª->3º, etc.).
    """
    if not text:
        return ""
    s = text
    # Strip invalid C0 control chars except standard whitespace
    s = "".join(c for c in s if ord(c) >= 32 or c in "\t\n\r")
    # Clean up excessive horizontal spaces while preserving indentation and newlines
    normalized_lines = []
    for line in s.split("\n"):
        indent_match = re.match(r"^[ \t]*", line)
        indent = indent_match.group(0) if indent_match else ""
        normalized_lines.append(indent + re.sub(r"[ \t]{2,}", " ", line[len(indent):]))
    s = "\n".join(normalized_lines)
    return s


@dataclass
class StructuralBlock:
    block_id: int
    type_candidate: str  # document_title, section_title, subsection_title, blockquote, paragraph, list_item, metadata_field
    text: str
    bbox: tuple[float, float, float, float]
    font_size: float
    is_bold: bool
    is_italic: bool
    lines: list[LineInfo] = field(default_factory=list)


class _TableHTMLParser(HTMLParser):
    """Parse only table structure; document HTML is never emitted or executed."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.rows: list[dict[str, Any]] = []
        self._row: dict[str, Any] | None = None
        self._cell: dict[str, Any] | None = None
        self._cell_parts: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        tag = tag.lower()
        if tag == "tr":
            if self._row is not None:
                self.handle_endtag("tr")
            self._row = {"cells": []}
        elif tag in {"td", "th"} and self._row is not None:
            attributes = {key.lower(): value for key, value in attrs}
            self._cell = {
                "is_header": tag == "th",
                "colspan": _positive_int(attributes.get("colspan"), 1),
                "rowspan": _positive_int(attributes.get("rowspan"), 1),
            }
            self._cell_parts = []

    def handle_startendtag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        self.handle_starttag(tag, attrs)
        self.handle_endtag(tag)

    def handle_endtag(self, tag: str) -> None:
        tag = tag.lower()
        if tag in {"td", "th"} and self._cell is not None and self._row is not None:
            self._cell["text"] = " ".join("".join(self._cell_parts).split())
            self._row["cells"].append(self._cell)
            self._cell = None
            self._cell_parts = []
        elif tag == "tr" and self._row is not None:
            if self._cell is not None:
                self.handle_endtag("td")
            self.rows.append(self._row)
            self._row = None

    def handle_data(self, data: str) -> None:
        if self._cell is not None:
            self._cell_parts.append(data)


def _positive_int(value: str | None, default: int = 1) -> int:
    try:
        parsed = int(value or default)
    except (TypeError, ValueError):
        return default
    return max(1, parsed)


def _table_grid(model: dict[str, Any]) -> list[list[str]]:
    """Expand spans into a deterministic rectangular grid without duplicating text."""
    occupied: set[tuple[int, int]] = set()
    anchors: dict[tuple[int, int], str] = {}
    max_col = 0
    max_row = -1
    for row in model.get("rows", []):
        row_index = int(row.get("row_index", 0))
        column = 0
        for cell in row.get("cells", []):
            while (row_index, column) in occupied:
                column += 1
            colspan = _positive_int(str(cell.get("colspan", 1)))
            rowspan = _positive_int(str(cell.get("rowspan", 1)))
            anchors[(row_index, column)] = str(cell.get("text", ""))
            for rr in range(row_index, row_index + rowspan):
                for cc in range(column, column + colspan):
                    occupied.add((rr, cc))
                    max_row = max(max_row, rr)
            column += colspan
            max_col = max(max_col, column)
    row_count = max(max_row, max((int(row.get("row_index", 0)) for row in model.get("rows", [])), default=-1)) + 1
    return [[anchors.get((row_index, column), "") for column in range(max_col)] for row_index in range(row_count)]


def serialize_table_gfm(model: dict[str, Any]) -> str:
    """Serialize a structural table as safe GFM; no artificial column headers generated."""
    grid = _table_grid(model)
    if not grid or not any("".join(row).strip() for row in grid):
        return ""
    grid = [row for row in grid if any(cell.strip() for cell in row)]
    if not grid:
        return ""
    columns = max(len(row) for row in grid)
    grid = [row + [""] * (columns - len(row)) for row in grid]
    has_header = any(cell.get("is_header") for row in model.get("rows", []) for cell in row.get("cells", []))
    if has_header:
        header, data = grid[0], grid[1:]
    else:
        if len(grid) >= 2:
            header, data = grid[0], grid[1:]
        else:
            header, data = grid[0], []

    def safe(value: str) -> str:
        return value.replace("\\", "\\\\").replace("|", "\\|").replace("\r", " ").replace("\n", " ").strip()

    lines = ["| " + " | ".join(safe(value) for value in header) + " |", "| " + " | ".join("---" for _ in header) + " |"]
    if data:
        lines.extend("| " + " | ".join(safe(value) for value in row) + " |" for row in data)
    return "\n".join(lines)


def _canonical_table_for_lines(canonical_tables: list[dict[str, Any]], lines: list[LineInfo]) -> dict[str, Any] | None:
    """Return the one Canonical V1 instance owning a physical source block.

    The instance is emitted at its first physical source line and subsequent
    source lines are suppressed from *Markdown only*.  ``logical_text`` keeps
    its established raw-block path, so table presentation cannot retroact on
    Boundary or the retrieval identity.
    """
    line_ids = {line.raw_line_id for line in lines}
    if not line_ids:
        return None
    matches = [
        table for table in canonical_tables
        if line_ids.intersection(table.get("source_line_ids", []))
    ]
    return matches[0] if len(matches) == 1 else None


def parse_html_tables(text: str, page: int | None = None, source: str = "unknown") -> tuple[str, list[dict[str, Any]]]:
    """Replace complete HTML-like tables while retaining raw input in an audit model."""
    pattern = re.compile(r"<table\b[^>]*>.*?</table\s*>", re.IGNORECASE | re.DOTALL)
    tables: list[dict[str, Any]] = []

    def replace(match: re.Match[str]) -> str:
        raw_html = match.group(0)
        parser = _TableHTMLParser()
        try:
            parser.feed(raw_html)
            parser.close()
        except (AssertionError, ValueError):
            return raw_html
        if not parser.rows:
            return raw_html
        rows = []
        flat_cells = []
        occupied: set[tuple[int, int]] = set()
        for row_index, parsed_row in enumerate(parser.rows):
            cells = []
            column_index = 0
            for parsed_cell in parsed_row["cells"]:
                while (row_index, column_index) in occupied:
                    column_index += 1
                cell = {
                    "text": parsed_cell.get("text", ""),
                    "row_index": row_index,
                    "column_index": column_index,
                    "colspan": parsed_cell.get("colspan", 1),
                    "rowspan": parsed_cell.get("rowspan", 1),
                    "page": page,
                    "source": source,
                    "bbox": None,
                    "is_header": bool(parsed_cell.get("is_header")),
                }
                cells.append(cell)
                flat_cells.append(cell)
                for row_offset in range(cell["rowspan"]):
                    for column_offset in range(cell["colspan"]):
                        occupied.add((row_index + row_offset, column_index + column_offset))
                column_index += cell["colspan"]
            rows.append({"row_index": row_index, "cells": cells, "page": page, "source": source})
        model = {
            "type": "table",
            "page": page,
            "source": source,
            "bbox": None,
            "rows": rows,
            "cells": flat_cells,
            "raw_html": raw_html,
            "source_ref": {"page": page, "source": source, "kind": "table", "bbox": None},
        }
        model["column_count"] = len(_table_grid(model)[0]) if _table_grid(model) else 0
        model["markdown"] = serialize_table_gfm(model)
        tables.append(model)
        return model["markdown"]

    return pattern.sub(replace, text), tables


def normalize_tabular_markdown(text: str, page: int | None = None, source: str = "unknown") -> tuple[str, list[dict[str, Any]]]:
    return parse_html_tables(text, page=page, source=source)


def mark_cross_page_table_continuity(pages: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Annotate adjacent compatible tables without removing the visual page boundary."""
    for previous, current in zip(pages, pages[1:]):
        previous_tables = previous.get("tables", [])
        current_tables = current.get("tables", [])
        if not previous_tables or not current_tables:
            continue
        left, right = previous_tables[-1], current_tables[0]
        left_grid, right_grid = _table_grid(left), _table_grid(right)
        if not left_grid or not right_grid or len(left_grid[0]) != len(right_grid[0]):
            continue
        left_header = [" ".join(value.split()).lower() for value in left_grid[0]]
        right_header = [" ".join(value.split()).lower() for value in right_grid[0]]
        if any(left_header) and any(right_header) and left_header != right_header:
            continue
        identity = f"table-{previous.get('page')}-to-{current.get('page')}"
        for table in (left, right):
            table["logical_table_id"] = identity
            table["continuity_confidence"] = "strong"
        left["continues_to_page"] = current.get("page")
        right["continues_from_page"] = previous.get("page")
    return pages


def _is_separator_line(text: str) -> bool:
    clean = text.strip()
    return bool(re.fullmatch(r"[-_=*~]{3,}", clean))


def split_tabular_line(text: str) -> list[str]:
    """Split a line with tabular/columnar structure into discrete cells."""
    text = text.strip()
    if not text:
        return []
    # Check lawyer / notification method (Advogado / Forma / DJEN)
    m_djen = re.match(r"^(.*?\(OAB\s+[^\)]+\))\s+(DJEN|DJE|DO|Edital|Publica[cç][aã]o)$", text, re.IGNORECASE)
    if m_djen:
        return [m_djen.group(1).strip(), m_djen.group(2).strip()]
    if re.match(r"^(Advogado|Procurador)\s+(Forma|Meio)$", text, re.IGNORECASE):
        return re.split(r"\s+", text, maxsplit=1)

    # Check key-value or entity-document pairings (e.g. Banco / CNPJ or Nome / CPF)
    m_doc = re.match(r"^(.*?\b[A-Za-zÀ-ÿ\s\.\(\)]+)\s+(\d{2,3}\.\d{3}\.\d{3}(?:/\d{4})?-\d{2})$", text)
    if m_doc:
        return [m_doc.group(1).strip(), m_doc.group(2).strip()]
    if re.match(r"^(CNPJ|CPF)IFP\s+(Raz[aã]o\s+Social|Nome\s+Completo)$", text, re.IGNORECASE):
        m = re.match(r"^(CNPJ|CPF)IFP\s+(Raz[aã]o\s+Social|Nome\s+Completo)$", text, re.IGNORECASE)
        return [f"{m.group(1)}/IFP", m.group(2)]

    # Paystub summary header: Total de Vencimentos Total de Descontos
    if re.match(r"^Total\s+de\s+Vencimentos\s+Total\s+de\s+Descontos$", text, re.IGNORECASE):
        return ["Total de Vencimentos", "Total de Descontos"]

    # Paystub item table header: Código Descrição Referência Vencimentos Descontos
    if re.match(r"^C[óo]digo\s+(?:D\s*e\s*s\s*c\s*r\s*i\s*[çc]\s*[ãa]\s*o|Descri[cç][aã]o)\s+Refer[êe]ncia\s+Vencimentos\s+Descontos", text, re.IGNORECASE):
        return ["Código", "Descrição", "Referência", "Vencimentos", "Descontos"]

    # Paystub tax/base header: Sal. Base Sal. Contr. INSS Base de Cálc FGTS F.G.T.S. do Mês Base do I.R.R.F. Dep. IRRF
    if "Sal. Base" in text and "INSS" in text and "FGTS" in text:
        parts = ["Sal. Base", "Sal. Contr. INSS", "Base de Cálc FGTS", "F.G.T.S. do Mês", "Base do I.R.R.F.", "Dep. IRRF"]
        if "Dep. IRRF" not in text:
            parts = parts[:-1]
        return parts

    # Bank statement header: Data Descrição Docto Situação Crédito Débito Saldo
    if re.match(r"^Data\s+Descri[cç][aã]o\s+Docto\s+Situa[cç][aã]o", text, re.IGNORECASE):
        return ["Data", "Descrição", "Docto", "Situação", "Crédito (R$)", "Débito (R$)", "Saldo (R$)"]

    # Bank statement transaction line: Date + Description + Doc + [Credit/Debit] + Balance
    m_bank = re.match(r"^(\d{2}/\d{2}/\d{4})\s+(.+?)\s+(\d{6})\s+([+-]?\d[\d.,]*)\s+([+-]?\d[\d.,]*)$", text)
    if m_bank:
        return [m_bank.group(1), m_bank.group(2).strip(), m_bank.group(3), "", "", m_bank.group(4), m_bank.group(5)]

    # Bank statement line with Date + Description + Doc + amount + amount
    m_bank2 = re.match(r"^(\d{2}/\d{2}/\d{4})\s+(.+?)\s+([+-]?\d[\d.,]*)\s+([+-]?\d[\d.,]*)$", text)
    if m_bank2:
        return [m_bank2.group(1), m_bank2.group(2).strip(), "", "", "", m_bank2.group(3), m_bank2.group(4)]

    # Paystub entry row: Code (1-5 digits) + Description + [Ref/Qty] + [Vencimento] + [Desconto]
    m_paystub = re.match(
        r"^(\d{1,5})\s+([A-Za-zÀ-ÿ0-9\s\.\-/]+?)\s+(?:(\d{1,3}(?:[.,]\d{2})?)\s+)?(\d{1,3}(?:\.\d{3})*,\d{2})(?:\s+(\d{1,3}(?:\.\d{3})*,\d{2}))?$",
        text
    )
    if m_paystub:
        code = m_paystub.group(1)
        desc = m_paystub.group(2).strip()
        ref = m_paystub.group(3) or ""
        val1 = m_paystub.group(4)
        val2 = m_paystub.group(5)
        is_discount = any(k in desc.upper() for k in ["INSS", "IRRF", "DESCONTO", "ADIANTAMENTO", "VALE", "FALTA", "ATRASO", "CONSIGNADO", "PENSÃO"])
        if val2:
            return [code, desc, ref, val1, val2]
        elif is_discount:
            return [code, desc, ref, "", val1]
        else:
            return [code, desc, ref, val1, ""]

    # Sequence of 2 or more monetary amounts where amounts make up >= 70% of line
    m_amounts = re.findall(r"\b\d{1,3}(?:\.\d{3})*,\d{2}\b", text)
    if len(m_amounts) >= 2 and len(" ".join(m_amounts)) >= len(text) * 0.70:
        return m_amounts

    return [text]


def parse_ocorrencias_records(lines: list[LineInfo]) -> list[dict[str, Any]]:
    """Parse police occurrences records into 5-column table model.
    Columns: Delegacia, Número-Ano, Natureza, Data, Envolvimento
    """
    records = []
    i = 0
    m_header1 = re.compile(r"(?:\d+[\.\-]\s*)?Delegacia\s+N[úu\ufffd]mero/Ano\s+Natureza", re.IGNORECASE)
    m_header2 = re.compile(r"Data\s+do\s+fato\s+Envolvimento", re.IGNORECASE)
    m_num_ano = re.compile(r"\b([A-Z0-9\-]+/\d{4})\b")
    m_data_env = re.compile(r"^(\d{2}/\d{2}/\d{4})\s+(.+)$")

    while i < len(lines):
        txt = lines[i].text.strip()
        if m_header1.search(txt) and i + 3 < len(lines):
            val1_line = lines[i+1].text.strip()
            hdr2_line = lines[i+2].text.strip()
            val2_line = lines[i+3].text.strip()
            
            if m_header2.search(hdr2_line):
                # Line 1: Delegacia, Número-Ano, Natureza
                m1 = m_num_ano.search(val1_line)
                if m1:
                    delegacia = val1_line[:m1.start()].strip()
                    num_ano = m1.group(1).strip()
                    natureza = val1_line[m1.end():].strip()
                else:
                    delegacia, num_ano, natureza = val1_line, "", ""
                
                # Line 2: Data, Envolvimento
                m2 = m_data_env.match(val2_line)
                if m2:
                    data = m2.group(1).strip()
                    envolvimento = m2.group(2).strip()
                else:
                    data, envolvimento = val2_line, ""
                
                records.append({
                    "delegacia": delegacia,
                    "num_ano": num_ano,
                    "natureza": natureza,
                    "data": data,
                    "envolvimento": envolvimento,
                    "lines": [lines[i], lines[i+1], lines[i+2], lines[i+3]]
                })
                i += 4
                continue
        i += 1
    return records


def _detect_tabular_grid(lines: list[LineInfo]) -> tuple[list[str], list[list[str]]] | None:
    """Detect if a sequence of lines forms a multi-column table and return its prefix titles and normalized rectangular grid."""
    if not lines:
        return None

    # 1. Police occurrences records
    occ_recs = parse_ocorrencias_records(lines)
    if occ_recs and len(occ_recs) * 4 >= len(lines) * 0.70:
        header = ["Delegacia", "Número-Ano", "Natureza", "Data", "Envolvimento"]
        grid = [header]
        for r in occ_recs:
            grid.append([r["delegacia"], r["num_ano"], r["natureza"], r["data"], r["envolvimento"]])
        return [], grid

    raw_rows = []
    for line in lines:
        if "\ufffd" in line.text or _is_corrupt_line(line.text):
            return None
        cells = split_tabular_line(line.text)
        if cells:
            if any("\ufffd" in c or _is_noise_token(c) for c in cells):
                return None
            raw_rows.append(cells)
    if not raw_rows:
        return None
    prefix_titles: list[str] = []
    while raw_rows and len(raw_rows[0]) == 1 and any(len(r) >= 2 for r in raw_rows[1:]):
        prefix_titles.append(raw_rows[0][0])
        raw_rows = raw_rows[1:]

    if not raw_rows:
        return None

    col_counts = [len(r) for r in raw_rows]
    max_cols = max(col_counts)
    multi_cell_rows = sum(1 for count in col_counts if count >= 2)

    # Require repeated column structure with high occupancy (>= 70% of rows)
    if max_cols < 2 or multi_cell_rows < 2 or (multi_cell_rows / len(raw_rows) < 0.70):
        return None

    # Reject continuous prose: wrapped endings and judicial prose keywords
    wrapped_endings = re.compile(r"\b(de|do|da|dos|das|em|no|na|nos|nas|com|por|para|a|ao|aos|à|às|e|ou|que|se|o|os|as|um|uma)\s*$", re.IGNORECASE)
    prose_keywords = re.compile(r"\b(CONDENO|Vistos|Ante o exposto|Pelo exposto|alienação parental|cumprimento de sentença)\b", re.IGNORECASE)

    for line in lines:
        t = line.text.strip()
        if wrapped_endings.search(t) or prose_keywords.search(t):
            return None

    grid = [r + [""] * (max_cols - len(r)) for r in raw_rows]
    return prefix_titles, grid


def _is_marginal_furniture(text: str, bbox: tuple[float, float, float, float], page_width: float, page_height: float) -> bool:
    """Detect deterministic court marginal stamps, e-SAJ signatures and browser URLs.
    
    INVARIANTE LOSSLESS:
    Referência 'fl./fls.' em texto do corpo NUNCA basta para descartar linha.
    Carimbo e-SAJ só é reconhecido pela combinação forte de assinatura conhecida + geometria marginal.
    """
    lx0, ly0, lx1, ly1 = bbox
    normalized = " ".join(text.split()).lower()
    line_w = max(0.0, lx1 - lx0)
    line_h = max(0.0, ly1 - ly0)

    is_lateral_margin = (lx0 >= page_width * 0.85) or (lx1 <= page_width * 0.15)
    is_narrow_strip = line_w <= page_width * 0.18
    is_extreme_vertical = (ly1 <= page_height * 0.08) or (ly0 >= page_height * 0.92)

    # 1. Unambiguous e-SAJ digital signature stamp phrases in margin strip
    has_esaj_stamp = bool(re.search(r"(este documento é cópia do original|para conferir o original|assinado digitalmente por|https?://.*esaj)", normalized))
    if has_esaj_stamp:
        if is_lateral_margin or is_extreme_vertical or is_narrow_strip:
            return True

    # 2. Standalone page/folio markers strictly in extreme margin zones and short
    if line_w <= page_width * 0.30 and (is_extreme_vertical or is_lateral_margin):
        if re.fullmatch(r"(?:fls?\.?|folhas?|pág\.?|p\.)\s*\d+(?:\s*[-–—/]\s*\d+)?", normalized):
            return True

    # 3. Web browser print headers / footers at extreme vertical edge
    if is_extreme_vertical and re.search(r"(https?://|\.gov\.br|\.jus\.br|\b\d{2}/\d{2}/\d{4}\b|\b\d{1,3}\s*/\s*\d{1,3}\b)", normalized):
        if not re.search(r"\b(del\.pol|delegacia|d\.p\.|vara|ju[íi]zo|comarca|foro|tribunal|termo|artigo)\b", normalized):
            if line_w <= page_width * 0.60:
                return True

    # 4. Lawyer / law firm contact and address footers at extreme vertical edge
    if is_extreme_vertical and re.search(r"(?:tel\.?:|email:|e-mail:|\badv\b|advogad[ao]|oab|rua|avenida|alameda|travessa|jardim|bairro|sala\s+\d+|cep\s*\d+|@|www\.)", normalized):
        return True

    return False


CNJ_PROCESS_PATTERN = re.compile(r"\b\d{7}-\d{2}\.\d{4}\.\d\.\d{2}\.\d{4}\b")


def _region_kind(text: str, bbox: tuple[float, float, float, float], width: float, height: float, *, furniture: bool = False) -> str:
    """Classify a region without deciding whether it belongs in Markdown."""
    normalized = " ".join(text.split()).lower()
    x0, y0, x1, y1 = bbox
    if not furniture:
        return "body"
    if re.search(r"assinado eletronicamente|assinatura digital|documento é cópia do original", normalized):
        return "signature"
    if re.search(r"\bfls?\.\s*\d+\b|protocolado em|liberado nos autos|código\s+", normalized):
        return "stamp"
    region_width = max(0.0, x1 - x0)
    is_narrow = region_width <= width * 0.20
    if is_narrow and x0 <= width * 0.10:
        return "margin_left"
    if is_narrow and x1 >= width * 0.90:
        return "margin_right"
    if y1 >= height * 0.86:
        return "header"
    if y0 <= height * 0.14:
        return "footer"
    return "unknown" if furniture else "body"


def _process_references(text: str) -> list[dict[str, str]]:
    """Mentions are references only; this extractor never assigns document ownership."""
    return [
        {"process_id": process_id, "relation": "REFERENCE", "confidence": "UNRESOLVED"}
        for process_id in sorted(set(CNJ_PROCESS_PATTERN.findall(text)))
    ]


def _region(region_id: str, kind: str, text: str, raw_text: str, bbox: list[float], source_line_ids: list[int], *, included_in_markdown: bool, exclusion_reason: str | None = None, source: str) -> dict[str, Any]:
    return {
        "region_id": region_id,
        "kind": kind,
        "text": text,
        "raw_text": raw_text,
        "bbox": bbox,
        "source_line_ids": source_line_ids,
        "included_in_markdown": included_in_markdown,
        "exclusion_reason": exclusion_reason,
        "source": source,
        "process_references": _process_references(raw_text),
    }


def _bboxes_overlap(left: list[float], right: list[float]) -> bool:
    return max(left[0], right[0]) < min(left[2], right[2]) and max(left[1], right[1]) < min(left[3], right[3])


def _matrix_multiply(left: list[float], right: list[float]) -> list[float]:
    a, b, c, d, e, f = left
    g, h, i, j, k, l = right
    return [a * g + c * h, b * g + d * h, a * i + c * j, b * i + d * j, a * k + c * l + e, b * k + d * l + f]


def _matrix_bbox(matrix: list[float]) -> list[float]:
    a, b, c, d, e, f = matrix
    points = [(e, f), (a + e, b + f), (c + e, d + f), (a + c + e, b + d + f)]
    return [min(point[0] for point in points), min(point[1] for point in points), max(point[0] for point in points), max(point[1] for point in points)]


def _same_bbox(left: list[float] | None, right: list[float] | None, tolerance: float = 0.75) -> bool:
    return left is not None and right is not None and all(abs(a - b) <= tolerance for a, b in zip(left, right))


def _pdfium_raw_image_bytes(obj: Any) -> bytes:
    size = pdfium_raw.FPDFImageObj_GetImageDataRaw(obj, None, 0)
    buffer = ctypes.create_string_buffer(size)
    written = pdfium_raw.FPDFImageObj_GetImageDataRaw(obj, buffer, size)
    return buffer.raw[:written]


def _pdfium_image_assets(raw_page: Any, page_num: int, source_resolver: "VisualAssetSourceResolver | None" = None) -> list[dict[str, Any]]:
    """Inventory image objects without extracting or transforming their binary payload."""
    assets: list[dict[str, Any]] = []
    for object_index in range(pdfium_raw.FPDFPage_CountObjects(raw_page)):
        obj = pdfium_raw.FPDFPage_GetObject(raw_page, object_index)
        if pdfium_raw.FPDFPageObj_GetType(obj) != pdfium_raw.FPDF_PAGEOBJ_IMAGE:
            continue
        left, bottom, right, top = (ctypes.c_float() for _ in range(4))
        bounds_ok = bool(pdfium_raw.FPDFPageObj_GetBounds(
            obj, ctypes.byref(left), ctypes.byref(bottom), ctypes.byref(right), ctypes.byref(top),
        ))
        pixel_width, pixel_height = ctypes.c_uint(), ctypes.c_uint()
        pdfium_raw.FPDFImageObj_GetImagePixelSize(obj, ctypes.byref(pixel_width), ctypes.byref(pixel_height))
        filters: list[str] = []
        for filter_index in range(pdfium_raw.FPDFImageObj_GetImageFilterCount(obj)):
            size = pdfium_raw.FPDFImageObj_GetImageFilter(obj, filter_index, None, 0)
            if size <= 0:
                continue
            value = ctypes.create_string_buffer(size)
            pdfium_raw.FPDFImageObj_GetImageFilter(obj, filter_index, value, size)
            filters.append(value.value.decode("utf-8", errors="replace"))
        asset = {
            "visual_asset_id": f"p{page_num}-i{object_index:04d}",
            "page": page_num,
            "pdf_object_index": object_index,
            "z_order": object_index,
            "kind": "unknown",
            "bbox": [left.value, bottom.value, right.value, top.value] if bounds_ok else None,
            "geometry_status": "EXACT" if bounds_ok else "UNAVAILABLE",
            "pixel_size": {"width": pixel_width.value, "height": pixel_height.value},
            "filters": filters,
            "source": "pdfium_page_object",
            "overlapping_region_ids": [],
        }
        if source_resolver is not None:
            asset["_raw_image_bytes"] = _pdfium_raw_image_bytes(obj)
        assets.append(asset)
    if source_resolver is not None:
        source_resolver.associate(page_num, assets)
        for asset in assets:
            asset.pop("_raw_image_bytes", None)
    return assets


def _relate_visual_assets(assets: list[dict[str, Any]], regions: list[dict[str, Any]]) -> list[dict[str, Any]]:
    for asset in assets:
        bbox = asset.get("bbox")
        if bbox is not None:
            asset["overlapping_region_ids"] = [
                region["region_id"] for region in regions
                if _bboxes_overlap(bbox, region["bbox"])
            ]
    return assets


def _pdfium_object_bbox(obj: Any) -> tuple[list[float] | None, str]:
    left, bottom, right, top = (ctypes.c_float() for _ in range(4))
    bounds_ok = bool(pdfium_raw.FPDFPageObj_GetBounds(
        obj, ctypes.byref(left), ctypes.byref(bottom), ctypes.byref(right), ctypes.byref(top),
    ))
    if not bounds_ok:
        return None, "UNAVAILABLE"
    return [left.value, bottom.value, right.value, top.value], "EXACT"


def _paint_instance_ref(page_num: int, object_index: int, kind: str) -> dict[str, Any]:
    """Stable locator within the original PDFium page-object paint sequence.

    It intentionally points to the source document rather than duplicating a
    path's segments.  A future structural-PDF resolver may enrich this same
    record with a content-stream operation reference without changing callers.
    """
    return {
        "version": "v1",
        "page": page_num,
        "content_path": [f"PAGE/{page_num}", "PDFIUM_PAGE_OBJECTS"],
        "operation_index": object_index,
        "paint_order": object_index,
        "kind": kind,
        "source": "pdfium_page_object",
    }


def _path_visual_summary(obj: Any) -> dict[str, Any]:
    segment_count = int(pdfium_raw.FPDFPath_CountSegments(obj))
    bezier_type = getattr(pdfium_raw, "FPDF_SEGMENT_BEZIERTO", 1)
    has_curves = any(
        pdfium_raw.FPDFPathSegment_GetType(pdfium_raw.FPDFPath_GetPathSegment(obj, index)) == bezier_type
        for index in range(segment_count)
    )
    fill_mode, stroke = ctypes.c_long(), ctypes.c_long()
    pdfium_raw.FPDFPath_GetDrawMode(obj, ctypes.byref(fill_mode), ctypes.byref(stroke))
    stroke_width = ctypes.c_float()
    has_stroke_width = bool(pdfium_raw.FPDFPageObj_GetStrokeWidth(obj, ctypes.byref(stroke_width)))
    return {
        "segment_count": segment_count,
        "has_curves": has_curves,
        "draw_mode": {"fill_mode": fill_mode.value, "has_stroke": bool(stroke.value)},
        "stroke_width": stroke_width.value if has_stroke_width else None,
        "has_transparency": bool(pdfium_raw.FPDFPageObj_HasTransparency(obj)),
    }


def _form_visual_summary(obj: Any) -> dict[str, Any] | None:
    """Return a summary only when a Form has a non-text visual descendant."""
    count = int(pdfium_raw.FPDFFormObj_CountObjects(obj))
    kinds = {
        getattr(pdfium_raw, "FPDF_PAGEOBJ_TEXT", 1): "text",
        getattr(pdfium_raw, "FPDF_PAGEOBJ_PATH", 2): "path",
        getattr(pdfium_raw, "FPDF_PAGEOBJ_IMAGE", 3): "image",
        getattr(pdfium_raw, "FPDF_PAGEOBJ_SHADING", 4): "shading",
        getattr(pdfium_raw, "FPDF_PAGEOBJ_FORM", 5): "form",
    }
    child_counts: Counter[str] = Counter()
    for index in range(count):
        child_counts[kinds.get(pdfium_raw.FPDFPageObj_GetType(pdfium_raw.FPDFFormObj_GetObject(obj, index)), "unknown")] += 1
    visual_child_count = sum(value for kind, value in child_counts.items() if kind != "text")
    if not visual_child_count:
        return None
    return {
        "child_count": count,
        "child_types": dict(sorted(child_counts.items())),
        "visual_child_count": visual_child_count,
        "has_transparency": bool(pdfium_raw.FPDFPageObj_HasTransparency(obj)),
    }


def _pdfium_visual_items(raw_page: Any, page_num: int) -> list[dict[str, Any]]:
    """Compact factual index of non-raster painted page objects.

    PDFium owns the original graphic detail.  This index records only the
    instance locator, geometry, order and a query-oriented summary.
    """
    items: list[dict[str, Any]] = []
    types = {
        getattr(pdfium_raw, "FPDF_PAGEOBJ_PATH", 2): "path",
        getattr(pdfium_raw, "FPDF_PAGEOBJ_FORM", 5): "form",
        getattr(pdfium_raw, "FPDF_PAGEOBJ_SHADING", 4): "shading",
    }
    for object_index in range(pdfium_raw.FPDFPage_CountObjects(raw_page)):
        obj = pdfium_raw.FPDFPage_GetObject(raw_page, object_index)
        kind = types.get(pdfium_raw.FPDFPageObj_GetType(obj))
        if kind is None:
            continue
        summary: dict[str, Any]
        if kind == "path":
            summary = _path_visual_summary(obj)
        elif kind == "form":
            form_summary = _form_visual_summary(obj)
            if form_summary is None:
                continue
            summary = form_summary
        else:
            summary = {"has_transparency": bool(pdfium_raw.FPDFPageObj_HasTransparency(obj))}
        bbox, geometry_status = _pdfium_object_bbox(obj)
        items.append({
            "visual_item_id": f"p{page_num}-v{object_index:04d}",
            "page": page_num,
            "pdf_object_index": object_index,
            "z_order": object_index,
            "kind": kind,
            "bbox": bbox,
            "geometry_status": geometry_status,
            "paint_instance_ref": _paint_instance_ref(page_num, object_index, kind.upper()),
            "source": "pdfium_page_object",
            "summary": summary,
            "overlapping_region_ids": [],
            "overlapping_visual_asset_ids": [],
        })
    return items


def _classify_graphic_primitives(items: list[dict[str, Any]], lines: list[LineInfo]) -> list[dict[str, Any]]:
    """Classify horizontal path primitives without treating decoration as a table.

    PDF paths are provenance, not text cells.  A table ruling needs repeated
    horizontal *and* vertical grid members; an isolated path under a text span
    is an underline when measured against that span's local line height.
    """
    line_height = _local_paragraph_metrics(lines, 12.0).line_height if lines else 12.0
    horizontal: list[dict[str, Any]] = []
    vertical: list[dict[str, Any]] = []
    for item in items:
        bbox = item.get("bbox")
        if item.get("kind") != "path" or not bbox:
            continue
        width = max(0.0, bbox[2] - bbox[0])
        height = max(0.0, bbox[3] - bbox[1])
        if width >= max(line_height, height * 8.0):
            horizontal.append(item)
        elif height >= max(line_height, width * 8.0):
            vertical.append(item)

    # Rulings require a minimal rectangular/grid relationship, never just one
    # horizontal rule.  This metadata is deliberately independent of prose
    # table recognition, which still requires repeated textual cells.
    coherent_grid = len(horizontal) >= 2 and len(vertical) >= 2
    for item in items:
        item["graphic_classification"] = "OTHER_GRAPHIC"
        bbox = item.get("bbox")
        if item.get("kind") != "path" or not bbox:
            continue
        width = max(0.0, bbox[2] - bbox[0])
        height = max(0.0, bbox[3] - bbox[1])
        if width < max(line_height, height * 8.0):
            continue
        text_span = next((
            line for line in lines
            if (line.x_left <= bbox[0] + width * 0.15 and line.x_right >= bbox[2] - width * 0.15)
            and abs(line.y_bottom - bbox[3]) <= line_height * 0.45
            and width <= (line.x_right - line.x_left) * 1.15
        ), None)
        if text_span is not None and not coherent_grid:
            item["graphic_classification"] = "TEXT_UNDERLINE"
        elif coherent_grid:
            item["graphic_classification"] = "TABLE_RULING"
        else:
            item["graphic_classification"] = "HORIZONTAL_SEPARATOR"
    return items


def _relate_visual_items(items: list[dict[str, Any]], regions: list[dict[str, Any]], assets: list[dict[str, Any]]) -> list[dict[str, Any]]:
    for item in items:
        bbox = item.get("bbox")
        if bbox is None:
            continue
        item["overlapping_region_ids"] = [
            region["region_id"] for region in regions if _bboxes_overlap(bbox, region["bbox"])
        ]
        item["overlapping_visual_asset_ids"] = [
            asset["visual_asset_id"] for asset in assets
            if asset.get("bbox") is not None and _bboxes_overlap(bbox, asset["bbox"])
        ]
    return items


_IMAGE_DICTIONARY_KEYS = ("/Width", "/Height", "/BitsPerComponent", "/ColorSpace", "/Filter", "/DecodeParms", "/Decode", "/Interpolate", "/ImageMask", "/Mask", "/SMask")


def _sha256(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _pdf_reference(value: Any) -> dict[str, int] | None:
    if hasattr(value, "idnum") and hasattr(value, "generation"):
        return {"object_number": int(value.idnum), "generation": int(value.generation)}
    return None


def _pdf_value(value: Any, depth: int = 0) -> Any:
    """JSON-safe structural representation; stream payloads remain separate blobs."""
    reference = _pdf_reference(value)
    if reference is not None:
        resolved = value.get_object()
        return {"indirect_ref": reference, "value": _pdf_value(resolved, depth + 1)}
    if depth > 4:
        return str(value)
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    if isinstance(value, (list, tuple)):
        return [_pdf_value(item, depth + 1) for item in value]
    if hasattr(value, "keys"):
        return {str(key): _pdf_value(value[key], depth + 1) for key in sorted(value.keys(), key=str) if str(key) != "/Length"}
    return str(value)


def _stream_raw_bytes(stream: Any) -> bytes:
    data = getattr(stream, "_data", None)
    if data is None:
        raise ValueError("pypdf não expôs o stream bruto do objeto de imagem")
    return bytes(data)


def _stream_component(stream_value: Any, role: str) -> dict[str, Any] | None:
    if stream_value is None:
        return None
    reference = _pdf_reference(stream_value)
    stream = stream_value.get_object() if reference is not None else stream_value
    if not hasattr(stream, "keys") or not hasattr(stream, "_data"):
        return None
    raw_bytes = _stream_raw_bytes(stream)
    dictionary = {str(key): _pdf_value(stream[key]) for key in sorted(stream.keys(), key=str) if str(key) != "/Length"}
    return {
        "role": role,
        "blob_sha256": _sha256(raw_bytes),
        "raw_bytes_base64": base64.b64encode(raw_bytes).decode("ascii"),
        "byte_length": len(raw_bytes),
        "indirect_ref": reference,
        "dictionary": dictionary,
    }


def _icc_component(color_space: Any) -> dict[str, Any] | None:
    value = color_space.get_object() if _pdf_reference(color_space) is not None else color_space
    if not isinstance(value, (list, tuple)) or not value or str(value[0]) != "/ICCBased" or len(value) < 2:
        return None
    return _stream_component(value[1], "icc_profile")


class VisualAssetSourceResolver:
    """Read-only pypdf companion for source-only image metadata and dependencies."""

    def __init__(self, pdf_path: Path, page_numbers: set[int] | None = None) -> None:
        self._candidates: dict[int, dict[str, list[dict[str, Any]]]] = {}
        self._paint_candidates: dict[int, dict[str, list[dict[str, Any]]]] = {}
        try:
            from pypdf import PdfReader
            from pypdf.generic import ContentStream
            self.reader = PdfReader(str(pdf_path))
        except Exception:
            self.reader = None
            return

        for page_number, page in enumerate(self.reader.pages, start=1):

            if page_numbers is not None and page_number not in page_numbers:
                continue
            seen_forms: set[tuple[int, int]] = set()

            def visit(resources: Any, prefix: str = "") -> None:
                xobjects = resources.get("/XObject", {}) if hasattr(resources, "get") else {}
                for resource_name, stream_value in xobjects.items():
                    stream = stream_value.get_object()
                    name = f"{prefix}/{resource_name}" if prefix else str(resource_name)
                    subtype = str(stream.get("/Subtype"))
                    if subtype == "/Image":
                        raw_bytes = _stream_raw_bytes(stream)
                        self._candidates.setdefault(page_number, {}).setdefault(_sha256(raw_bytes), []).append({
                            "resource_name": name, "stream_value": stream_value,
                        })
                    elif subtype == "/Form":
                        reference = _pdf_reference(stream_value)
                        key = (reference or {}).get("object_number", id(stream)), (reference or {}).get("generation", 0)
                        if key not in seen_forms:
                            seen_forms.add(key)
                            visit(stream.get("/Resources", {}), name)

            visit(page.get("/Resources", {}))
            content = ContentStream(page.get_contents(), self.reader)
            inline_aliases = {"/W": "/Width", "/H": "/Height", "/BPC": "/BitsPerComponent", "/CS": "/ColorSpace", "/F": "/Filter", "/DP": "/DecodeParms", "/D": "/Decode", "/IM": "/ImageMask", "/I": "/Interpolate"}
            inline_index = 0
            for operands, operator in content.operations:
                if operator != b"INLINE IMAGE":
                    continue
                settings = operands["settings"]
                dictionary = {
                    inline_aliases.get(str(key), str(key)): _pdf_value(value)
                    for key, value in settings.items()
                }
                raw_bytes = bytes(operands["data"]).rstrip(b"\r\n")
                self._candidates.setdefault(page_number, {}).setdefault(_sha256(raw_bytes), []).append({
                    "resource_name": f"/INLINE/{inline_index:04d}",
                    "stream_value": None,
                    "inline_dictionary": dictionary,
                })
                inline_index += 1
            self._collect_paint_candidates(page_number, page, ContentStream)
        for candidates_by_blob in self._candidates.values():
            for candidates in candidates_by_blob.values():
                candidates.sort(key=lambda item: item["resource_name"])

    def _collect_paint_candidates(self, page_number: int, page: Any, content_stream_type: Any) -> None:
        """Enumerate actual paint operations, including nested Form XObjects."""
        paint_order = 0
        seen_forms: set[tuple[int, int, tuple[str, ...]]] = set()

        def add(raw_bytes: bytes, candidate: dict[str, Any]) -> None:
            self._paint_candidates.setdefault(page_number, {}).setdefault(_sha256(raw_bytes), []).append(candidate)

        def walk(contents: Any, resources: Any, matrix: list[float], path: tuple[str, ...]) -> None:
            nonlocal paint_order
            stream = content_stream_type(contents, self.reader)
            stack: list[list[float]] = []
            current = list(matrix)
            inline_index = 0
            for operation_index, (operands, operator) in enumerate(stream.operations):
                if operator == b"q":
                    stack.append(list(current))
                elif operator == b"Q":
                    if stack:
                        current = stack.pop()
                elif operator == b"cm" and len(operands) == 6:
                    current = _matrix_multiply(current, [float(value) for value in operands])
                elif operator == b"INLINE IMAGE":
                    settings = operands["settings"]
                    aliases = {"/W": "/Width", "/H": "/Height", "/BPC": "/BitsPerComponent", "/CS": "/ColorSpace", "/F": "/Filter", "/DP": "/DecodeParms", "/D": "/Decode", "/IM": "/ImageMask", "/I": "/Interpolate"}
                    raw_bytes = bytes(operands["data"]).rstrip(b"\r\n")
                    add(raw_bytes, {"resource_name": "/".join((*path, f"INLINE/{inline_index:04d}")), "stream_value": None, "inline_dictionary": {aliases.get(str(key), str(key)): _pdf_value(value) for key, value in settings.items()}, "paint_instance_ref": {"page": page_number, "content_path": list(path), "operation_index": operation_index, "paint_order": paint_order, "kind": "INLINE_IMAGE"}, "paint_bbox": _matrix_bbox(current), "paint_matrix": list(current)})
                    paint_order += 1
                    inline_index += 1
                elif operator == b"Do" and operands:
                    name = str(operands[0])
                    xobjects = resources.get("/XObject", {}) if hasattr(resources, "get") else {}
                    value = xobjects.get(name)
                    if value is None:
                        continue
                    obj = value.get_object()
                    subtype = str(obj.get("/Subtype"))
                    child_path = (*path, name)
                    if subtype == "/Image":
                        raw_bytes = _stream_raw_bytes(obj)
                        add(raw_bytes, {"resource_name": "/".join(child_path), "stream_value": value, "paint_instance_ref": {"page": page_number, "content_path": list(path), "operation_index": operation_index, "paint_order": paint_order, "kind": "XOBJECT_IMAGE"}, "paint_bbox": _matrix_bbox(current), "paint_matrix": list(current)})
                        paint_order += 1
                    elif subtype == "/Form":
                        reference = _pdf_reference(value)
                        key = ((reference or {}).get("object_number", id(obj)), (reference or {}).get("generation", 0), child_path)
                        if key not in seen_forms:
                            seen_forms.add(key)
                            form_matrix = [float(value) for value in obj.get("/Matrix", [1, 0, 0, 1, 0, 0])]
                            walk(obj, obj.get("/Resources", resources), _matrix_multiply(current, form_matrix), child_path)

        walk(page.get_contents(), page.get("/Resources", {}), [1, 0, 0, 1, 0, 0], (f"PAGE/{page_number}",))

    def _source_record(self, raw_bytes: bytes, candidate: dict[str, Any], match_status: str) -> dict[str, Any]:
        blob_sha256 = _sha256(raw_bytes)
        stream_value = candidate["stream_value"]
        if "inline_dictionary" in candidate:
            dictionary, components = candidate["inline_dictionary"], []
        else:
            stream = stream_value.get_object()
            dictionary = {str(key): _pdf_value(stream[key]) for key in _IMAGE_DICTIONARY_KEYS if key in stream}
            components = [component for component in (
                _stream_component(stream.get("/SMask"), "soft_mask"),
                _stream_component(stream.get("/Mask"), "explicit_mask"),
                _icc_component(stream.get("/ColorSpace")),
            ) if component is not None]
        identity = {
            "blob_sha256": blob_sha256,
            "dictionary": dictionary,
            "components": [{key: component.get(key) for key in ("role", "blob_sha256", "indirect_ref", "dictionary")} for component in components],
        }
        paint_instance_ref = candidate.get("paint_instance_ref")
        source_object_ref = _pdf_reference(stream_value) if stream_value is not None else {
            "kind": "INLINE_IMAGE",
            "content_path": (paint_instance_ref or {}).get("content_path", []),
            "operation_index": (paint_instance_ref or {}).get("operation_index"),
        }
        return {
            "match_status": match_status,
            "resource_name": candidate["resource_name"],
            "source_object_ref": source_object_ref,
            "paint_instance_ref": paint_instance_ref,
            "paint_matrix": candidate.get("paint_matrix"),
            "blob_sha256": blob_sha256,
            "raw_bytes_base64": base64.b64encode(raw_bytes).decode("ascii"),
            "byte_length": len(raw_bytes),
            "dictionary": dictionary,
            "components": components,
            "source_identity_sha256": _sha256(json.dumps(identity, ensure_ascii=True, sort_keys=True, separators=(",", ":")).encode("utf-8")),
        }

    def source_for(self, page_number: int, raw_bytes: bytes) -> dict[str, Any]:
        """Legacy source lookup: only safe for a single structural candidate."""
        blob_sha256 = _sha256(raw_bytes)
        candidates = self._candidates.get(page_number, {}).get(blob_sha256, [])
        if len(candidates) != 1:
            status = "UNRESOLVED" if not candidates else "AMBIGUOUS_INSTANCE_MATCH"
            return {"match_status": status, "blob_sha256": blob_sha256, "raw_bytes_base64": base64.b64encode(raw_bytes).decode("ascii"), "byte_length": len(raw_bytes)}
        return self._source_record(raw_bytes, candidates[0], "MATCHED_BY_RAW_BLOB")

    def associate(self, page_number: int, assets: list[dict[str, Any]]) -> None:
        """Attach a source only when a paint operation identifies the PDFium instance."""
        candidates_by_blob = self._paint_candidates.get(page_number, {})
        for asset in assets:
            raw_bytes = asset["_raw_image_bytes"]
            blob_sha256 = _sha256(raw_bytes)
            candidates = [candidate for candidate in candidates_by_blob.get(blob_sha256, []) if _same_bbox(asset.get("bbox"), candidate.get("paint_bbox"))]
            asset["visual_asset_source_version"] = "v1"
            if len(candidates) == 1:
                asset["visual_asset_source"] = self._source_record(raw_bytes, candidates[0], "MATCHED_BY_BLOB_GEOMETRY")
            else:
                status = "UNRESOLVED_INSTANCE_MATCH" if not candidates else "AMBIGUOUS_INSTANCE_MATCH"
                asset["visual_asset_source"] = {"match_status": status, "blob_sha256": blob_sha256, "raw_bytes_base64": base64.b64encode(raw_bytes).decode("ascii"), "byte_length": len(raw_bytes), "candidate_count": len(candidates)}


def _build_regions(page_num: int, width: float, height: float, raw_lines: list[dict[str, Any]], blocks: list[dict[str, Any]], furniture: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Create a complete, additive region inventory from pre-filter PDFium lines."""
    regions: list[dict[str, Any]] = []
    covered_line_ids: set[int] = set()
    furniture_by_line = {line_id: item for item in furniture for line_id in item.get("source_line_ids", [])}
    for block in blocks:
        ids = list(block.get("source_line_ids", []))
        covered_line_ids.update(ids)
        raw_text = "\n".join(str(item.get("raw_text", item.get("text", ""))) for item in raw_lines if item["raw_line_id"] in ids)
        kind = _region_kind(block["text"], tuple(block["bbox"]), width, height)
        regions.append(_region(
            f"p{page_num}-r{len(regions) + 1:04d}", kind, block["text"], raw_text or block["text"], list(block["bbox"]), ids,
            included_in_markdown=True, source="pdfium_block",
        ))
    for raw_line in raw_lines:
        line_id = raw_line["raw_line_id"]
        if line_id in covered_line_ids:
            continue
        item = furniture_by_line.get(line_id)
        is_furniture = item is not None
        kind = _region_kind(raw_line["text"], tuple(raw_line["bbox"]), width, height, furniture=True) if is_furniture else "unknown"
        regions.append(_region(
            f"p{page_num}-r{len(regions) + 1:04d}", kind, raw_line["text"], raw_line.get("raw_text", raw_line["text"]), list(raw_line["bbox"]), [line_id],
            included_in_markdown=False, exclusion_reason=(item or {}).get("reason", "filtered_before_markdown"), source="pdfium_raw_line",
        ))
    return regions


def _is_font_bold(fname: str, weight: int, flags: int) -> bool:
    """Check if font is genuinely bold based on font name and weight."""
    fn = fname.lower()
    if any(b in fn for b in ["-bold", "_bold", "bolditalic", "boldoblique", "black", "heavy"]):
        return True
    if weight >= 700 and not fn.endswith("psmt") and not fn == "centurygothic":
        return True
    return False


BULLET_CHARS = ("•", "●", "▪", "◦", "\u2022", "\u25cf", "\u25aa", "\u25e6")
BULLET_REGEX = re.compile(r"(?:^|\n|\s+)[•●▪◦\u2022\u25cf\u25aa\u25e6]\s*")
FOLIO_SUFFIX = re.compile(r"\s*\((?P<reference>(?:fls?\.?|folhas?)\s*[^)]*)\)\s*$", re.IGNORECASE)
QUOTE_INTRO = re.compile(
    r"(?:afirm(?:ou|a)|declar(?:ou|a)|relat(?:ou|a)|esclarec(?:eu|e)|"
    r"consign(?:ou|a)|diss(?:e|eram?)|consta\s+que|afirmando\s+que)\s*:\s*$",
    re.IGNORECASE,
)
QUOTE_START = re.compile(r"^[\"“«]")
NON_TERMINAL_ABBREVIATION = re.compile(
    r"(?:fls?\.?|arts?\.?|pp?\.?|pág\.?|nº|incs?\.?|dr\.?|dra\.?|des\.?|min\.?|rel\.?)$",
    re.IGNORECASE,
)
FUNCTIONAL_ENDING = re.compile(
    r"(?:de|da|do|das|dos|em|no|na|nos|nas|por|para|com|sem|ao|aos|à|às|e|ou|que|como|conforme|entre|sobre|até|após|desde|contra|mediante|cujo|cuja|cujos|cujas)$",
    re.IGNORECASE,
)
LIST_MARKER = re.compile(
    r"^(?P<marker>\(?(?P<value>(?:[a-z]|[ivxlcdm]+|\d+))\s*[.)\-–—]\)?)(?:\s+|(?<=[-–—]))(?P<body>.+)$",
    re.IGNORECASE,
)


def _is_title_body(body: str) -> bool:
    """Determine whether text form is a structural title/heading without lexical dependencies."""
    clean = body.strip()
    if not clean or len(clean) > 120:
        return False
    # Sentence-ending punctuation or clause punctuation indicates prose/sentence, not a heading
    if clean.endswith((".", ";", ",", "!", "?")) or "," in clean:
        return False
    # Key-value or contact field pattern (e.g. label followed by colon and data)
    if re.match(r"^[^:]{1,30}:\s*\S+", clean):
        return False
    words = [w for w in re.split(r"[\s/\-]+", clean) if w]
    if not words:
        return False
    # 1. All-caps title (e.g. any domain uppercase heading: "DOS FATOS", "METODOLOGIA", etc.)
    if clean.isupper() and len(clean) >= 3:
        return True
    # 2. Title Case: first word capitalized, all major words (len > 3) capitalized/digits
    if words[0][0].isupper() and all(w[0].isupper() or w.isdigit() for w in words if len(w) > 3):
        return True
    return False


def extract_list_items(block_text: str) -> list[str]:
    """Split block text into individual clean list items if bullet markers are present."""
    if any(c in block_text for c in BULLET_CHARS):
        parts = [p.strip() for p in BULLET_REGEX.split(block_text) if p.strip()]
        items = []
        for p in parts:
            reflowed = " ".join(p.split())
            if reflowed:
                items.append(reflowed)
        return items

    lines = [l.strip() for l in block_text.splitlines() if l.strip()]
    if not lines:
        return []

    marker_indices = [i for i, l in enumerate(lines) if _list_marker(l)]
    if marker_indices:
        items = []
        for idx, start_i in enumerate(marker_indices):
            end_i = marker_indices[idx + 1] if idx + 1 < len(marker_indices) else len(lines)
            first = re.sub(
                r"^(?:[-*•●▪◦]|\(?(?:[a-z]|[ivxlcdm]+|\d+)\s*[.)\-–—]\)?)\s*",
                "",
                lines[start_i],
                flags=re.IGNORECASE,
            ).strip()
            item_text = " ".join([first, *lines[start_i + 1:end_i]]).strip()
            if item_text:
                items.append(item_text)
        return items

    return [" ".join(block_text.split())]


def _is_quote_intro(text: str) -> bool:
    return bool(QUOTE_INTRO.search(" ".join(text.split())))


def _is_direct_quote(text: str, lines: list[LineInfo], previous_text: str = "", previous_type: str = "") -> bool:
    clean_text = " ".join(text.split()).strip()
    if not QUOTE_START.match(clean_text):
        if previous_type != "blockquote" or _is_quote_intro(clean_text):
            return False
        if re.match(r"^(?:[-*•●▪◦]|\d+[.)])\s+", clean_text) or _looks_like_list_item(clean_text, lines, previous_text):
            return False
        if clean_text.upper() in TOP_LEVEL_LEGAL_DOC_TITLES:
            return False
        marker_match = LIST_MARKER.match(clean_text)
        if marker_match and _is_title_body(marker_match.group("body")):
            return False
        previous_clean = " ".join(previous_text.split()).strip()
        previous_closed_quote = _quote_is_closed(previous_clean)
        return not previous_closed_quote
    if _is_quote_intro(previous_text):
        return True
    if FOLIO_SUFFIX.search(clean_text):
        return True
    # A block that starts with discourse markers and closes its quotation is
    # stronger evidence of transcription than bold/size/centering signals.
    return len(lines) > 1 or _quote_is_closed(clean_text)


TOP_LEVEL_LEGAL_DOC_TITLES = {
    "ACÓRDÃO", "VOTO", "RELATÓRIO", "EMENTA", "SENTENÇA", "DECISÃO", "DESPACHO",
    "TERMO DE AUDIÊNCIA", "PETIÇÃO INICIAL", "MANIFESTAÇÃO", "CONTESTAÇÃO",
    "RÉPLICA", "CERTIDÃO DE REMESSA DE RELAÇÃO", "CERTIDÃO DE PUBLICAÇÃO",
    "RECURSO DE APELAÇÃO", "AGRAVO DE INSTRUMENTO", "EMBARGOS DE DECLARAÇÃO"
}


def _classify_block(
    block_text: str,
    lines: list[LineInfo],
    b_size: float,
    b_bold: bool,
    b_italic: bool,
    body_font_size: float,
    previous_text: str = "",
    previous_type: str = "",
    next_text: str = "",
    *,
    page_num: int = 1,
    block_index: int = 0,
    total_blocks: int = 1,
) -> str:
    """Classify block role based on local typographic contrast and geometry."""
    clean_text = " ".join(block_text.split()).strip()
    is_upper = clean_text.isupper() and len(clean_text) >= 4

    # Documentary meaning takes precedence over visual heading signals.
    if _is_direct_quote(clean_text, lines, previous_text, previous_type):
        return "blockquote"

    # Tabular structure detection (conservative geometry and occupancy)
    grid = _detect_tabular_grid(lines)
    if grid is not None:
        return "table"

    # 1. Opening judicial addressing / piece header on first page of a document
    is_doc_opening = (page_num == 1 and block_index <= 1 and (not previous_text or previous_type in {"", "document_title", "section_title"}))
    has_judicial_vocative = bool(re.match(r"^(?:EXCELENT[ÍI]SSIM|AO\s+JU[ÍI]ZO|AO\s+DOUTO\s+JU[ÍI]ZO|ILUSTR[ÍI]SSIM|AO\s+MINIST[ÉE]RIO\s+P[ÚU]BLICO|FORO\s+DE|COMARCA\s+DE|TRIBUNAL\s+DE\s+JUSTI[ÇC]A|VARA\s+DE\s+FAM[ÍI]LIA|VARA\s+C[ÍI]VEL|JU[ÍI]ZO\s+DE\s+DIREITO)", clean_text, re.IGNORECASE))
    if is_doc_opening and has_judicial_vocative:
        if b_bold or b_size >= body_font_size * 0.95 or is_upper:
            return "document_title" if (b_size >= body_font_size * 1.1 or is_upper) else "section_title"

    # Addressing lines appearing mid-document or without opening context remain paragraphs
    if has_judicial_vocative and not is_doc_opening:
        return "paragraph"

    # 2. Signatures, lawyer registrations, and OAB lines are paragraphs
    if re.search(r"\bOAB(?:/[A-Z]{2})?\s*[\d\.\-]+", clean_text, re.IGNORECASE) or re.match(r"^(?:OAB\s*[\d\.\-/\\A-Z]+|ADVOGAD[OA]|PROMOTOR(?:A)?\s+DE\s+JUSTI[ÇC]A|PROCURADOR(?:A)?|JUIZ(?:A)?\s+DE\s+DIREITO|DIRETOR(?:A)?\s+DE\s+SERVI[ÇC]O)\s*$", clean_text, re.IGNORECASE):
        return "paragraph"

    sig_line_regex = re.compile(r"^(?:OAB\s*[\d\.\-/\\A-Z]+|ADVOGAD[OA]|PROMOTOR(?:A)?(?:\s+DE\s+JUSTI[ÇC]A)?|PROCURADOR(?:A)?|JUIZ(?:A)?(?:\s+DE\s+DIREITO)?|DIRETOR(?:A)?|TEL:|E-MAIL:|ENDERE[ÇC]O:|[A-Za-zÀ-ÿ\s]+,\s*\d{1,2}\s+de\s+[a-zç]+\s+de\s+\d{4})", re.IGNORECASE)
    is_adjacent_sig = bool(sig_line_regex.match(next_text.strip())) or bool(sig_line_regex.match(previous_text.strip()))
    if is_adjacent_sig:
        words = clean_text.split()
        if 2 <= len(words) <= 5 and not any(w.lower() in ["ação", "autos", "processo", "vara", "comarca", "tribunal", "artigo", "lei", "pedido", "fatos", "direito", "preliminar", "preliminarmente", "justiça", "gratuita"] for w in words):
            return "paragraph"

    # 3. Document Titles (#)
    if clean_text.upper() in TOP_LEVEL_LEGAL_DOC_TITLES and (b_size >= body_font_size * 1.15 or clean_text.upper() in {"SENTENÇA", "DECISÃO", "ACÓRDÃO", "DESPACHO"} or (b_bold and is_doc_opening)):
        return "document_title"

    # 4. Lists
    if _looks_like_list_item(clean_text, lines, previous_text, next_text):
        return "list_item"

    # 5. Section and Subsection titles
    if b_bold and len(lines) <= 4 and len(clean_text) < 220:
        # Subordinate numbered headings (e.g. IV.1, 1.1, 2.1, (a))
        if re.match(r"^(?:[IVXLCDM]+\.\d+|\d+\.\d+|\([a-z]\)|[a-z]\))\s+", clean_text, re.IGNORECASE):
            return "subsection_title"

        # Numbered/prefixed or standard section titles by structural title form
        match_marker = LIST_MARKER.match(clean_text)
        if match_marker and _is_title_body(match_marker.group("body")):
            return "section_title"

        # Short topical titles not containing address/party boilerplate
        if (is_upper or _is_title_body(clean_text) or b_size > body_font_size or len(clean_text) < 60) and not re.search(r"\b(RUA|AVENIDA|ALAMEDA|CEP|TEL|SÃO PAULO|PIRACAIA|SANTO ANDRÉ|CPF|RG|AUTOR|RÉU|REQUERENTE|REQUERIDO)\b", clean_text, re.IGNORECASE):
            if len(clean_text) < 90 and not clean_text.endswith((".", ";", ",")):
                return "section_title" if (is_upper or b_size >= body_font_size * 1.1) else "subsection_title"

        return "paragraph"

    # 6. Tabular structure detection
    grid = _detect_tabular_grid(lines)
    if grid is not None:
        return "table"

    return "paragraph"


def reflow_paragraph_elements(text: str) -> list[str]:
    """Reflow paragraph text, ensuring list items with bullet markers are rendered as Markdown list items."""
    if not any(c in text for c in BULLET_CHARS):
        reflowed = " ".join(text.split())
        return [reflowed] if reflowed else []

    match = re.search(r"[•●▪◦\u2022\u25cf\u25aa\u25e6]", text)
    if not match:
        reflowed = " ".join(text.split())
        return [reflowed] if reflowed else []

    intro = text[:match.start()].strip()
    bullet_part = text[match.start():]
    items = [p.strip() for p in BULLET_REGEX.split(bullet_part) if p.strip()]

    elements: list[str] = []
    if intro:
        elements.append(" ".join(intro.split()))
    for it in items:
        reflowed_it = " ".join(it.split())
        if reflowed_it:
            elements.append(f"- {reflowed_it}")
    if not elements:
        reflowed = " ".join(text.split())
        return [reflowed] if reflowed else []
    return elements


def block_markdown(block_type: str, block_text: str) -> str:
    """Render one structural block without losing documentary semantics."""
    if block_type in ["paragraph", ""] and any(c in block_text for c in BULLET_CHARS):
        return "\n\n".join(reflow_paragraph_elements(block_text))
    reflowed = " ".join(block_text.split())
    if block_type == "blockquote":
        match = FOLIO_SUFFIX.search(reflowed)
        quote_text = reflowed[:match.start()].rstrip() if match else reflowed
        lines = [f"> *{quote_text}*"]
        if match:
            lines.extend([">", f"> *{match.group('reference').strip()}*"])
        return "\n".join(lines)
    if block_type == "document_title":
        return f"# {reflowed}"
    if block_type == "section_title":
        return f"## {reflowed}"
    if block_type == "subsection_title":
        return f"### {reflowed}"
    return reflowed


def _block_text(lines: list[LineInfo], *, preserve_paragraphs: bool = False) -> str:
    """Join a block, retaining structural paragraph restarts when requested."""
    pieces: list[str] = []
    for line in lines:
        if preserve_paragraphs and line.paragraph_start and pieces:
            pieces.append("\n\n")
        elif pieces:
            if pieces[-1].endswith("-"):
                pass
            else:
                pieces.append(" ")
        pieces.append(line.text)
    return "".join(pieces).strip()


def _starts_list(text: str) -> bool:
    clean = text.strip()
    return bool(re.match(r"^[-*•●▪◦]\s+", clean) or LIST_MARKER.match(clean))


def _list_marker(text: str) -> tuple[str, str, int] | None:
    clean = text.strip()
    if re.match(r"^[-*•●▪◦]\s+", clean):
        return clean[0], "bullet", 0
    match = LIST_MARKER.match(clean)
    if not match:
        return None
    value = match.group("value").lower()
    if value.isdigit():
        return match.group("marker"), "numeric", int(value)
    if all(char in "ivxlcdm" for char in value):
        roman = {"i": 1, "v": 5, "x": 10, "l": 50, "c": 100, "d": 500, "m": 1000}
        total, previous = 0, 0
        for char in reversed(value):
            number = roman[char]
            total += -number if number < previous else number
            previous = max(previous, number)
        return match.group("marker"), "roman", total
    return match.group("marker"), "alpha", ord(value) - ord("a") + 1


def _list_paragraph_restart(
    previous: list[LineInfo],
    current: list[LineInfo],
    body_font_size: float,
    metrics: LineFlowMetrics,
) -> tuple[bool, dict[str, Any]]:
    """Decide an internal list paragraph from positive local-flow evidence.

    A list marker's x-position is not a paragraph signal: many PDFs align the
    marker and every wrapped line at the same left edge.  A restart therefore
    needs an already-observed continuation/body flow and a meaningful return
    to a distinct first-line indentation, or a separately evidenced paragraph
    gap.  The returned evidence is intentionally data-only so callers can
    record every emitted internal boundary.
    """
    if not previous or not current or not _list_marker(_block_text(previous)) or _list_marker(_block_text(current)):
        return False, {"reason": "NOT_LIST_CONTINUATION"}

    marker_line = next((line for line in previous if _list_marker(line.text)), None)
    if marker_line is None:
        return False, {"reason": "MISSING_LIST_MARKER"}
    previous_line, current_line = previous[-1], current[0]
    continuation_lines = [line for line in previous if line is not marker_line]
    # No body-flow sample yet means the first unmarked line is a wrap by
    # default; equality with the marker edge is never enough to restart.
    if not continuation_lines:
        return False, {"reason": "NO_BODY_FLOW_SAMPLE"}

    body_left = float(median(line.x_left for line in continuation_lines))
    body_spread = float(median(abs(line.x_left - body_left) for line in continuation_lines))
    # The page-wide left cluster can be bimodal (first-line + body) and is
    # therefore deliberately not used here.  This tolerance belongs to the
    # observed body-flow cluster only.
    indent_tolerance = max(body_spread * 3.0, metrics.column_width * 0.035)
    first_line_left = marker_line.x_left
    baseline_delta = previous_line.y_bottom - current_line.y_bottom
    leading_tolerance = max(metrics.baseline_mad * 3.0, metrics.line_height * 0.20)
    normal_leading = baseline_delta <= metrics.baseline + leading_tolerance
    same_region = _column_compatible([previous_line], [current_line], body_font_size)
    same_typography = _typography_compatible([previous_line], [current_line])
    current_at_body = abs(current_line.x_left - body_left) <= indent_tolerance
    current_at_first = abs(current_line.x_left - first_line_left) <= indent_tolerance
    first_indent_delta = abs(first_line_left - body_left)
    current_indent_delta = abs(current_line.x_left - body_left)
    significant_first_indent = first_indent_delta > indent_tolerance and current_indent_delta > indent_tolerance
    enlarged_gap = baseline_delta > metrics.baseline + max(metrics.baseline_mad * 2.0, metrics.line_height * 0.15)
    previous_fill = (previous_line.x_right - previous_line.x_left) / metrics.column_width
    terminal = bool(re.search(r"[.!?…][\"”»')\]]*\s*$", previous_line.text.rstrip()))
    first_alpha = next((char for char in current_line.text.lstrip() if char.isalpha()), "")
    strong_continuation = (
        normal_leading
        and same_region
        and same_typography
        and current_at_body
        and _wrap_flow(previous_line, current_line, metrics, body_font_size)
    ) or (
        normal_leading
        and same_region
        and same_typography
        and not terminal
        and bool(first_alpha and first_alpha.islower())
    )
    # A distinct body flow followed by a return to the first-line indentation
    # is positive restart evidence.  A larger local paragraph gap is an
    # independent second route, but ordinary leading always remains a wrap.
    restart_by_indent = significant_first_indent and current_at_first and not strong_continuation
    restart_by_gap = enlarged_gap and current_indent_delta > indent_tolerance and not strong_continuation
    if restart_by_indent:
        reason = "DISTINCT_FIRST_LINE_INDENT"
    elif restart_by_gap:
        reason = "PARAGRAPH_GAP_AND_INDENT"
    else:
        reason = "NORMAL_BODY_FLOW"
    return restart_by_indent or restart_by_gap, {
        "reason": reason,
        "dominant_body_left": body_left,
        "first_line_text_left": first_line_left,
        "x_left_previous": previous_line.x_left,
        "x_left_current": current_line.x_left,
        "gap_over_local_leading": baseline_delta / max(metrics.baseline, 1.0),
        "previous_fill_ratio": previous_fill,
        "terminal_punctuation": terminal,
        "next_first_alphabetic": first_alpha,
        "same_region": same_region,
        "same_typography": same_typography,
        "normal_leading": normal_leading,
        "current_at_body_left": current_at_body,
        "current_at_first_line_left": current_at_first,
    }


def _list_item_markdown_from_paragraphs(paragraphs: list[list[str]]) -> str:
    """Serialize the already-identified paragraphs of one semantic item."""
    rendered = [" ".join(paragraph).strip() for paragraph in paragraphs if paragraph]
    if not rendered:
        return ""
    first = re.sub(
        r"^(?:[-*•●▪◦]|\(?(?:[a-z]|[ivxlcdm]+|\d+)\s*[.)\-–—]\)?)\s*",
        "",
        rendered[0],
        flags=re.IGNORECASE,
    ).strip()
    # Native Markdown continuation paragraphs are indented under the same
    # list item; they are not separate list entries.
    return "- " + first + "".join(f"\n\n  {paragraph}" for paragraph in rendered[1:])


def _list_item_markdown(lines: list[LineInfo]) -> str:
    """Serialize one list item, retaining paragraph boundaries inside it."""
    paragraphs: list[list[str]] = [[]]
    for line in lines:
        if line.paragraph_start and paragraphs[-1]:
            paragraphs.append([])
        paragraphs[-1].append(line.text)
    return _list_item_markdown_from_paragraphs(paragraphs)


def _stored_list_item_markdown(block_text: str) -> str:
    """Re-serialize a persisted list block without flattening blank paragraphs."""
    paragraphs = [paragraph.splitlines() for paragraph in re.split(r"\n\s*\n", block_text) if paragraph.strip()]
    return _list_item_markdown_from_paragraphs(paragraphs)


def _list_sequence(previous_text: str, current_text: str) -> bool:
    previous = _list_marker(previous_text)
    current = _list_marker(current_text)
    return bool(previous and current and previous[1] == current[1] and current[2] == previous[2] + 1)


def _looks_like_list_item(text: str, lines: list[LineInfo], previous_text: str = "", next_text: str = "") -> bool:
    clean = text.strip()
    if not clean or not lines:
        return False

    # A CNJ is an identifier, not a numeric list marker. Treating its hyphen as
    # enumeration punctuation drops the leading process number in list Markdown.
    if CNJ_PROCESS_PATTERN.fullmatch(clean):
        return False

    # Party initials followed by a parenthesized qualification (for example,
    # "R. (MENOR REPRESENTADA)") are identifiers, not alphabetic enumerations.
    alpha_marker = LIST_MARKER.match(clean)
    if (
        alpha_marker
        and len(alpha_marker.group("value")) == 1
        and alpha_marker.group("value").isalpha()
        and alpha_marker.group("marker").rstrip(")").endswith(".")
        and alpha_marker.group("body").lstrip().startswith("(")
    ):
        return False

    if re.match(r"^[-*•●▪◦]\s+", clean):
        return True

    marker = _list_marker(clean)
    if not marker:
        return False

    match = LIST_MARKER.match(clean)
    if match:
        body = match.group("body").strip()
        is_bold_heading_candidate = all(l.is_bold for l in lines) and len(lines) <= 2
        if is_bold_heading_candidate and _is_title_body(body):
            if not _list_sequence(previous_text, clean) and not _list_sequence(clean, next_text):
                return False

    return True


def _starts_quote(text: str) -> bool:
    return bool(QUOTE_START.match(text.strip()))


def _quote_is_closed(text: str) -> bool:
    """Recognize straight/curly closing quotes in standalone or continued quote blocks."""
    clean = text.strip()
    if not clean:
        return True
    search_target = clean[1:] if QUOTE_START.match(clean) else clean
    return bool(re.search(r'["”»]', search_target))


def _split_inline_quote(text: str, is_continuation: bool = False) -> tuple[str, str] | None:
    """Split a block where an active quotation closes inline and is followed by substantial prose.

    Handles nested quotes, paired straight quotes, and depth-tracked curly quotes/guillemets.

    Returns:
        (quote_text, prose_text) if the block contains an inline quotation closure
        followed by non-citation prose; otherwise None.
    """
    clean = text.strip()
    if not clean:
        return None

    quote_start_match = QUOTE_START.match(clean)
    if not quote_start_match and not is_continuation:
        return None

    start_char = clean[0] if quote_start_match else ""

    # 1. Asymmetric curly double quotes
    if start_char == "“" or (is_continuation and "”" in clean and clean.count("”") >= clean.count('"')):
        depth = 1
        end_pos = None
        start_idx = 1 if start_char == "“" else 0
        for i in range(start_idx, len(clean)):
            ch = clean[i]
            if ch == "“":
                depth += 1
            elif ch == "”":
                depth -= 1
                if depth == 0:
                    punc_match = re.match(r"^[.,;:!?]*", clean[i + 1:])
                    end_pos = i + 1 + (punc_match.end() if punc_match else 0)
                    break
        if end_pos is None:
            return None

    # 2. Asymmetric guillemets
    elif start_char == "«" or (is_continuation and "»" in clean and '"' not in clean):
        depth = 1
        end_pos = None
        start_idx = 1 if start_char == "«" else 0
        for i in range(start_idx, len(clean)):
            ch = clean[i]
            if ch == "«":
                depth += 1
            elif ch == "»":
                depth -= 1
                if depth == 0:
                    punc_match = re.match(r"^[.,;:!?]*", clean[i + 1:])
                    end_pos = i + 1 + (punc_match.end() if punc_match else 0)
                    break
        if end_pos is None:
            return None

    # 3. Straight double quotes (or continuation with straight quotes)
    else:
        quote_indices = [i for i, ch in enumerate(clean) if ch == '"']
        if not quote_indices:
            match = re.search(r'["”»][.,;:!?]*', clean)
            if not match:
                return None
            end_pos = match.end()
        else:
            if quote_start_match:
                if len(quote_indices) < 2 or len(quote_indices) % 2 != 0:
                    return None
                last_idx = quote_indices[-1]
            else:
                if len(quote_indices) % 2 != 1:
                    return None
                last_idx = quote_indices[-1]

            punc_match = re.match(r"^[.,;:!?]*", clean[last_idx + 1:])
            end_pos = last_idx + 1 + (punc_match.end() if punc_match else 0)

    quote_part = clean[:end_pos].strip()
    prose_part = clean[end_pos:].strip()

    if not prose_part:
        return None

    # If the remainder is purely a parenthetical reference / citation suffix:
    # e.g. "(fls. 12)", "(DIAS, Maria Berenice...)", "(STJ, REsp...)"
    if re.match(r"^\([^)]+\)\.?$", prose_part):
        return None

    return quote_part, prose_part


def _looks_institutional_furniture(text: str) -> bool:
    normalized = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii").lower()
    signals = (
        "tribunal",
        "comarca",
        "foro",
        "vara",
        "cep",
        "poder judiciario",
        "horario de atendimento",
        "praca",
    )
    return sum(signal in normalized for signal in signals) >= 2


def _is_known_heading_title(text: str) -> bool:
    clean = text.strip()
    if not clean:
        return False
    if re.match(r"^(?:EXCELENT[ÍI]SSIM|MM\.?\s*JU[ÍI]Z|AO\s+JU[ÍI]ZO|ILUSTR[ÍI]SSIM|OAB\b|ADVOGAD|PROMOTOR)", clean, re.IGNORECASE):
        return False
    match = LIST_MARKER.match(clean)
    if match:
        return _is_title_body(match.group("body"))
    return _is_title_body(clean)


def _looks_visual_heading(lines: list[LineInfo], body_font_size: float) -> bool:
    text = _block_text(lines)
    clean = text.strip()
    if len(lines) > 4 or len(clean) >= 220 or not all(line.is_bold for line in lines):
        return False
    if re.search(r"\bOAB(?:/[A-Z]{2})?\s*[\d\.\-]+", clean, re.IGNORECASE) or re.match(r"^(?:EXCELENT[ÍI]SSIM|MM\.?\s*JU[ÍI]Z|AO\s+JU[ÍI]ZO|ILUSTR[ÍI]SSIM|OAB\b|ADVOGAD|PROMOTOR|FORO\s+DE|COMARCA\s+DE|TRIBUNAL\s+DE\s+JUSTI[ÇC]A)", clean, re.IGNORECASE):
        return False
    if clean.isupper() and len(clean) >= 4 and not re.search(r"\b(RUA|AVENIDA|ALAMEDA|CEP|TEL|SÃO PAULO|PIRACAIA|SANTO ANDRÉ|CPF|RG)\b", clean, re.IGNORECASE):
        if not clean.endswith((".", ";", ",")) or len(clean) < 90:
            return True
    if _is_known_heading_title(clean):
        return True
    return False


def _looks_field_line(line: LineInfo, body_font_size: float) -> bool:
    """Recognize a compact label/value field without promoting ordinary prose.

    This deliberately requires a short label ending in a colon.  It is not a
    document-specific vocabulary and it keeps cover/form fields out of prose
    flow; long legal sentences containing a colon remain PROSE.
    """
    text = line.text.strip()
    label = re.match(r"^(?P<label>[^:]{1,48}):\s*\S+", text)
    if not label or len(text) > 180:
        return False
    return line.is_bold or len(label.group("label").split()) <= 5


def _physical_flow_kind(line: LineInfo, body_font_size: float) -> FlowKind:
    """Conservative pre-continuity classification of a physical text line."""
    text = line.text.strip()
    if not text:
        return FlowKind.UNKNOWN
    if _is_separator_line(text):
        return FlowKind.FURNITURE
    if _looks_institutional_furniture(text):
        return FlowKind.FURNITURE
    if _list_marker(text):
        return FlowKind.LIST_ITEM
    if _starts_quote(text):
        return FlowKind.QUOTE
    if _looks_field_line(line, body_font_size):
        return FlowKind.FIELD
    if _looks_visual_heading([line], body_font_size):
        return FlowKind.HEADING
    return FlowKind.PROSE


def continues_heading(previous: LineInfo, current: LineInfo, metrics: LineFlowMetrics, body_font_size: float) -> bool:
    """A multiline heading is allowed only within the same heading flow."""
    baseline_delta = previous.y_bottom - current.y_bottom
    leading_tolerance = max(metrics.baseline_mad * 3.0, metrics.line_height * 0.35)
    return (
        _column_compatible([previous], [current], body_font_size)
        and _typography_compatible([previous], [current])
        and baseline_delta <= metrics.baseline + leading_tolerance
    )


def continues_quote(previous: LineInfo, current: LineInfo, metrics: LineFlowMetrics, body_font_size: float) -> bool:
    """Quote flow is isolated from prose and ends only on a real close."""
    if bool(re.search(r"[\"”»]\s*[,.;:!?]*$", previous.text.strip())):
        return False
    return _column_compatible([previous], [current], body_font_size) and _font_metrics_compatible([previous], [current])


def continues_field(previous: LineInfo, current: LineInfo, metrics: LineFlowMetrics, body_font_size: float) -> bool:
    """Cover/form fields are intentionally atomic, even when visually close."""
    return False


def continues_prose(previous: LineInfo, current: LineInfo, metrics: LineFlowMetrics, body_font_size: float) -> bool:
    """Normal wrapped prose is the default; boundaries require positive evidence."""
    baseline_delta = previous.y_bottom - current.y_bottom
    leading_tolerance = max(metrics.baseline_mad * 3.0, metrics.line_height * 0.20)
    same_region = _column_compatible([previous], [current], body_font_size)
    same_typography = _typography_compatible([previous], [current])
    normal_leading = baseline_delta <= metrics.baseline + leading_tolerance
    previous_fill = (previous.x_right - previous.x_left) / max(metrics.column_width, 1.0)
    current_at_body_left = abs(current.x_left - metrics.left_edge) <= metrics.left_tolerance
    terminal = bool(re.search(r"[.!?…][\"”»')\]]*\s*$", previous.text.rstrip()))
    return same_region and same_typography and normal_leading and previous_fill >= 0.85 and current_at_body_left and not terminal


def continues_list_item(previous: LineInfo, current: LineInfo, metrics: LineFlowMetrics, body_font_size: float) -> bool:
    """A non-marker physical line can continue the active list item."""
    return not bool(_list_marker(current.text)) and _column_compatible([previous], [current], body_font_size)


def _typed_flow_nodes(blocks: list[list[LineInfo]], block_types: list[str]) -> list[TypedFlowNode]:
    """Materialize the explicit structural AST before Markdown serialization."""
    kind_by_type = {
        "paragraph": FlowKind.PROSE,
        "": FlowKind.PROSE,
        "list_item": FlowKind.LIST_ITEM,
        "document_title": FlowKind.HEADING,
        "section_title": FlowKind.HEADING,
        "subsection_title": FlowKind.HEADING,
        "blockquote": FlowKind.QUOTE,
        "metadata_field": FlowKind.FIELD,
        "table": FlowKind.TABLE,
    }
    nodes: list[TypedFlowNode] = []
    for lines, block_type in zip(blocks, block_types):
        kind = kind_by_type.get(block_type, FlowKind.UNKNOWN)
        # Preserve pre-continuity identity where the later presentation
        # classifier intentionally has no separate Markdown token (FIELD and
        # FURNITURE).  A uniform non-prose physical flow must not be silently
        # relabelled as generic paragraph during emission.
        physical_kinds = {_physical_flow_kind(line, Counter([line.font_size]).most_common(1)[0][0]) for line in lines}
        if kind not in {FlowKind.QUOTE, FlowKind.LIST_ITEM} and len(physical_kinds) == 1:
            physical_kind = next(iter(physical_kinds))
            if physical_kind in {FlowKind.FIELD, FlowKind.FURNITURE}:
                kind = physical_kind
        if kind is FlowKind.LIST_ITEM:
            paragraphs: list[list[LineInfo]] = [[]]
            for line in lines:
                if line.paragraph_start and paragraphs[-1]:
                    paragraphs.append([])
                paragraphs[-1].append(line)
            children = [TypedFlowNode(FlowKind.PROSE, paragraph, reason="list_internal_paragraph") for paragraph in paragraphs if paragraph]
            nodes.append(TypedFlowNode(kind, lines, children=children, reason="classified_list_item"))
        else:
            nodes.append(TypedFlowNode(kind, lines, reason=f"classified_{block_type or 'paragraph'}"))
    return nodes


def _serialize_typed_flow_node(node: TypedFlowNode, block_type: str) -> list[str] | None:
    """Serialize an already-decided AST node; never infer a new boundary.

    ``None`` is reserved for TABLE because its cell model is emitted by the
    existing grid serializer.  All non-table text boundaries, notably nested
    list paragraphs, come exclusively from the AST children.
    """
    if node.kind is FlowKind.TABLE:
        return None
    if node.kind is FlowKind.LIST_ITEM:
        paragraphs = [[line.text for line in child.lines] for child in node.children]
        rendered = _list_item_markdown_from_paragraphs(paragraphs)
        return [rendered] if rendered else []
    text = _block_text(node.lines, preserve_paragraphs=False)
    if _is_separator_line(text):
        return ["---"]
    if node.kind is FlowKind.HEADING or node.kind is FlowKind.QUOTE:
        return [block_markdown(block_type, text)]
    return reflow_paragraph_elements(text)


def _column_compatible(previous: list[LineInfo], current: list[LineInfo], body_font_size: float) -> bool:
    left_delta = abs(previous[-1].x_left - current[0].x_left)
    tolerance = max(12.0, body_font_size * 1.5)
    if left_delta <= tolerance:
        return True
    left = max(previous[-1].x_left, current[0].x_left)
    right = min(previous[-1].x_right, current[0].x_right)
    overlap = max(0.0, right - left)
    shorter = max(1.0, min(previous[-1].x_right - previous[-1].x_left, current[0].x_right - current[0].x_left))
    # A justified first/last line can be substantially shorter while staying
    # in the same text band; distinct columns still have little or no overlap.
    return overlap / shorter >= 0.25


def _typography_compatible(previous: list[LineInfo], current: list[LineInfo]) -> bool:
    previous_size = Counter(line.font_size for line in previous).most_common(1)[0][0]
    current_size = Counter(line.font_size for line in current).most_common(1)[0][0]
    previous_bold = Counter(line.is_bold for line in previous).most_common(1)[0][0]
    current_bold = Counter(line.is_bold for line in current).most_common(1)[0][0]
    previous_italic = Counter(line.is_italic for line in previous).most_common(1)[0][0]
    current_italic = Counter(line.is_italic for line in current).most_common(1)[0][0]
    return abs(previous_size - current_size) <= 1.0 and previous_bold == current_bold and previous_italic == current_italic


def _font_metrics_compatible(previous: list[LineInfo], current: list[LineInfo]) -> bool:
    """Return the non-emphatic part of the typography comparison.

    Bold/italic flags are useful paragraph evidence, but PDF text extraction can
    assign them to a single line in an otherwise uniform prose flow.  A strong
    textual continuation may therefore override that *soft* visual difference;
    a material font-size change remains structural evidence.
    """
    previous_size = Counter(line.font_size for line in previous).most_common(1)[0][0]
    current_size = Counter(line.font_size for line in current).most_common(1)[0][0]
    return abs(previous_size - current_size) <= 1.0


def _logical_continuation(previous_text: str, current_text: str) -> bool:
    previous = previous_text.rstrip()
    current = current_text.lstrip()
    if not current or not previous:
        return False
    if current[0].islower():
        return True
    if previous.endswith((",", ";", ":", "-", "–", "—", "(", "[", "{", "/")):
        return True
    if NON_TERMINAL_ABBREVIATION.search(previous):
        return bool(re.match(r"^(?:\d|[A-Z]?\d)", current))

    opening = sum(previous.count(char) for char in "([{\"“«")
    closing = sum(previous.count(char) for char in ")]}") + sum(previous.count(char) for char in "\"”»")
    if opening > closing:
        return True

    previous_word = re.search(r"([\wÀ-ÿº]+)[\s.,;:!?\-–—/]*$", previous)
    if previous_word and FUNCTIONAL_ENDING.fullmatch(previous_word.group(1)):
        return True
    if re.search(r"R\$\s*$", previous, re.IGNORECASE):
        return bool(re.match(r"^\d", current))

    if re.match(r"^(?:\d|[A-Z]?\d)", current) and not re.search(r"[.!?]\s*$", previous):
        return True

    # A capitalized continuation is common in split names/titles
    # (e.g. "Câmara de Direito" + "Privado.").  The second clause also
    # covers a full name split after its first token without relying on any
    # legal vocabulary.
    if current[0].isupper() and len(current.split()) <= 3 and re.search(r"\w$", previous):
        return True
    previous_tail = re.search(r"(?:^|\s)([A-ZÀ-Ý][a-zà-ÿ]+)\s*$", previous)
    current_head = re.match(r"([A-ZÀ-Ý][a-zà-ÿ]+)(?:\s+(?:[A-ZÀ-Ý][a-zà-ÿ]+|da|das|de|do|dos|e))", current)
    if previous_tail and current_head and not re.search(r"[.!?]\s*$", previous):
        return True
    return False


def _local_paragraph_metrics(lines: list[LineInfo], body_font_size: float) -> LineFlowMetrics:
    """Infer local line-flow geometry without global pixel thresholds."""
    heights = [max(1.0, line.y_top - line.y_bottom) for line in lines]
    baselines = [
        previous.y_bottom - current.y_bottom
        for previous, current in zip(lines, lines[1:])
        if 0 < previous.y_bottom - current.y_bottom < max(120.0, body_font_size * 12.0)
        and _column_compatible([previous], [current], body_font_size)
    ]
    line_height = float(median(heights)) if heights else max(1.0, body_font_size)
    baseline = float(median(baselines)) if baselines else max(line_height * 1.25, body_font_size * 1.25)
    baseline = max(baseline, line_height)
    baseline_mad = float(median([abs(value - baseline) for value in baselines])) if baselines else line_height * 0.1
    lefts = [line.x_left for line in lines]
    rights = [line.x_right for line in lines]
    left_edge = float(median(lefts)) if lefts else 0.0
    right_edge = float(median(rights)) if rights else left_edge + line_height
    column_width = max(line_height, right_edge - left_edge)
    left_mad = float(median([abs(value - left_edge) for value in lefts])) if lefts else 0.0
    right_mad = float(median([abs(value - right_edge) for value in rights])) if rights else 0.0
    # Tolerances scale with the observed column, while robust dispersion keeps
    # a justified text band from being distorted by short final lines.
    return LineFlowMetrics(
        line_height=line_height,
        baseline=baseline,
        baseline_mad=baseline_mad,
        left_edge=left_edge,
        right_edge=right_edge,
        column_width=column_width,
        left_tolerance=max(left_mad * 3.0, column_width * 0.035),
        right_tolerance=max(right_mad * 3.0, column_width * 0.06),
    )


def _wrap_flow(previous: LineInfo, current: LineInfo, metrics: LineFlowMetrics, body_font_size: float) -> bool:
    """Whether geometry strongly describes an ordinary wrapped text line."""
    baseline_delta = previous.y_bottom - current.y_bottom
    leading_tolerance = max(metrics.baseline_mad * 3.0, metrics.line_height * 0.20)
    previous_fills_right = abs(previous.x_right - metrics.right_edge) <= metrics.right_tolerance
    current_at_left = abs(current.x_left - metrics.left_edge) <= metrics.left_tolerance
    return (
        _column_compatible([previous], [current], body_font_size)
        and _font_metrics_compatible([previous], [current])
        and baseline_delta <= metrics.baseline + leading_tolerance
        and previous_fills_right
        and current_at_left
    )


def _paragraph_end_flow(previous: LineInfo, current: LineInfo, metrics: LineFlowMetrics, body_font_size: float) -> bool:
    """Strong local evidence that two adjacent lines are different paragraphs."""
    baseline_delta = previous.y_bottom - current.y_bottom
    previous_short = (metrics.right_edge - previous.x_right) > metrics.right_tolerance
    current_at_left = abs(current.x_left - metrics.left_edge) <= metrics.left_tolerance
    enlarged_gap = baseline_delta > metrics.baseline + max(metrics.baseline_mad * 2.0, metrics.line_height * 0.15)
    return _column_compatible([previous], [current], body_font_size) and previous_short and (enlarged_gap or current_at_left)


def _strong_text_flow_continuation(previous_text: str, current_text: str, same_flow: bool) -> bool:
    """Generic linguistic tie-breaker; never overrides structural boundaries."""
    if not same_flow or re.search(r"[.!?…][\"”»')\]]*\s*$", previous_text.rstrip()):
        return False
    first_alpha = next((char for char in current_text.lstrip() if char.isalpha()), "")
    return bool(first_alpha and first_alpha.islower())


def segment_logical_paragraphs(
    physical_lines: list[LineInfo],
    body_font_size: float = 12.0,
    boundary_trace: list[dict[str, Any]] | None = None,
    page_geometry: tuple[float, float] = (595.0, 842.0),
    page_num: int = 1,
) -> list[list[LineInfo]]:
    """Build logical paragraph nodes from ordered physical PDF lines using Themis-Doc Boundary v2 (Candidate A)."""
    if not physical_lines:
        return []
    from core.paragraph_boundary_engine import ParagraphBoundaryEngine
    engine = ParagraphBoundaryEngine()
    return engine.segment_paragraphs(
        physical_lines,
        body_font_size=body_font_size,
        boundary_trace=boundary_trace,
        page_geometry=page_geometry,
        page_num=page_num,
    )



def paragraph_segmentation_suspicions(
    physical_lines: list[LineInfo], paragraphs: list[list[LineInfo]], body_font_size: float,
) -> dict[str, list[dict[str, Any]]]:
    """Report high-confidence geometry contradictions after segmentation.

    This is intentionally diagnostic: it neither rewrites source text nor
    suppresses structural boundaries.  Consumers can rank the emitted line-id
    pairs across a corpus and inspect only genuine geometry disagreements.
    """
    if not physical_lines:
        return {"suspicious_breaks": [], "suspicious_merges": []}
    metrics = _local_paragraph_metrics(physical_lines, body_font_size)
    breaks: list[dict[str, Any]] = []
    merges: list[dict[str, Any]] = []
    for previous, current in zip(paragraphs, paragraphs[1:]):
        left, right = previous[-1], current[0]
        previous_text = _block_text(previous)
        current_text = _block_text(current)
        structural_boundary = (
            _looks_visual_heading(previous, body_font_size)
            or _looks_visual_heading(current, body_font_size)
            or bool(_list_marker(current_text))
            or (previous_text.isupper() and current_text.isupper())
            or _looks_institutional_furniture(previous_text)
            or _looks_institutional_furniture(current_text)
            or bool(re.search(r"[.!?][\"”»')\]]*\s*$", previous_text))
        )
        if not structural_boundary and _wrap_flow(left, right, metrics, body_font_size) and _typography_compatible(previous, current):
            breaks.append({
                "confidence": "HIGH",
                "previous_source_line_id": left.raw_line_id,
                "current_source_line_id": right.raw_line_id,
                "reason": "WRAP_FLOW_ACROSS_PARAGRAPH_BOUNDARY",
            })
    for paragraph in paragraphs:
        for previous, current in zip(paragraph, paragraph[1:]):
            is_list_internal = bool(_list_marker(_block_text([paragraph[0]])))
            if not is_list_internal and _paragraph_end_flow(previous, current, metrics, body_font_size):
                merges.append({
                    "confidence": "HIGH",
                    "previous_source_line_id": previous.raw_line_id,
                    "current_source_line_id": current.raw_line_id,
                    "reason": "PARAGRAPH_END_FLOW_WITHOUT_BOUNDARY",
                })
    return {"suspicious_breaks": breaks, "suspicious_merges": merges}


def merge_logical_blocks(raw_blocks: list[list[LineInfo]], body_font_size: float) -> list[list[LineInfo]]:
    """Compatibility wrapper: segment the supplied physical lines into paragraph nodes."""
    all_lines = [line for block in raw_blocks for line in block]
    if not all_lines:
        return []
    max_y = max(line.y_top for line in all_lines)
    ph = 842.0 if max_y > 150.0 else max(max_y + 30.0, 100.0)
    return segment_logical_paragraphs(
        all_lines,
        body_font_size,
        page_geometry=(595.0, ph),
    )


def _render_page_as_png_base64(raw_page: Any) -> tuple[str, int, int] | None:
    """Render page bitmap using PDFium and return base64 encoded PNG and dimensions."""
    try:
        import io
        from PIL import Image
        width = int(round(pdfium_raw.FPDF_GetPageWidthF(raw_page) * 2.0))
        height = int(round(pdfium_raw.FPDF_GetPageHeightF(raw_page) * 2.0))
        if width <= 0 or height <= 0:
            return None
        bitmap = pdfium_raw.FPDFBitmap_Create(width, height, 1)
        pdfium_raw.FPDFBitmap_FillRect(bitmap, 0, 0, width, height, 0xFFFFFFFF)
        pdfium_raw.FPDF_RenderPageBitmap(bitmap, raw_page, 0, 0, width, height, 0, 0x01)
        buf_ptr = pdfium_raw.FPDFBitmap_GetBuffer(bitmap)
        stride = pdfium_raw.FPDFBitmap_GetStride(bitmap)
        raw_bytes = ctypes.string_at(buf_ptr, stride * height)
        img = Image.frombuffer('RGBA', (width, height), raw_bytes, 'raw', 'BGRA', stride, 1)
        pdfium_raw.FPDFBitmap_Destroy(bitmap)

        buf = io.BytesIO()
        img.save(buf, format="PNG")
        png_bytes = buf.getvalue()
        b64 = base64.b64encode(png_bytes).decode("ascii")
        return b64, width, height
    except Exception:
        return None


def _glyph_runs_from_char_boxes(
    raw_line_id: int,
    raw_text: str,
    char_boxes: list[tuple[int, float, float, float, float]],
) -> list[GlyphRun]:
    """Group one PDFium raw line into horizontal runs using only geometry.

    PDFium may flatten physically separated columns into a single text line.
    A gap larger than the local glyph height is therefore retained as an
    intraline boundary.  Whitespace and glyph values are not interpreted.
    """
    if not char_boxes:
        return []

    heights = [top - bottom for _, left, right, bottom, top in char_boxes if right > left and top > bottom]
    widths = [right - left for _, left, right, bottom, top in char_boxes if right > left]
    local_height = median(heights) if heights else 1.0
    local_width = median(widths) if widths else 1.0
    # A normal inter-word advance stays in the run; a layout-scale blank does
    # not.  Both terms make the threshold scale-free across font sizes.
    gap_threshold = max(2.0, local_height * 0.75, local_width * 1.5)

    runs: list[GlyphRun] = []
    run_start = 0
    run_left = char_boxes[0][1]
    run_right = char_boxes[0][2]
    run_bottom = char_boxes[0][3]
    run_top = char_boxes[0][4]
    prior_right = char_boxes[0][2]
    gap_before: float | None = None

    def finish(end: int, before: float | None) -> None:
        text = raw_text[run_start:end].strip()
        if text:
            runs.append(GlyphRun(
                raw_line_id=raw_line_id,
                text=text,
                bbox=(run_left, run_bottom, run_right, run_top),
                gap_before=before,
                gap_before_normalized=(before / local_height) if before is not None and local_height > 0 else None,
            ))

    for offset, left, right, bottom, top in char_boxes[1:]:
        gap = left - prior_right
        if gap > gap_threshold:
            finish(offset, gap_before)
            run_start = offset
            run_left, run_right, run_bottom, run_top = left, right, bottom, top
            gap_before = gap
        else:
            run_right = max(run_right, right)
            run_left = min(run_left, left)
            run_bottom = min(run_bottom, bottom)
            run_top = max(run_top, top)
        prior_right = right
    finish(len(raw_text), gap_before)
    return runs


def _extract_page_raw_data(
    raw_page: Any,
    raw_textpage: Any,
    page_num: int,
    source_resolver: VisualAssetSourceResolver | None = None,
    include_glyph_runs: bool = False,
) -> dict[str, Any]:
    """Extract character runs, geometry, visual assets and separate local marginal furniture."""
    width = pdfium_raw.FPDF_GetPageWidthF(raw_page)
    height = pdfium_raw.FPDF_GetPageHeightF(raw_page)
    n_chars = pdfium_raw.FPDFText_CountChars(raw_textpage)

    visual_assets = _pdfium_image_assets(raw_page, page_num, source_resolver)
    visual_items = _pdfium_visual_items(raw_page, page_num)
    has_images = bool(visual_assets)

    has_visual_objects = False
    try:
        n_page_objs = pdfium_raw.FPDFPage_CountObjects(raw_page)
        if n_page_objs > 0:
            for obj_idx in range(n_page_objs):
                obj_ptr = pdfium_raw.FPDFPage_GetObject(raw_page, obj_idx)
                obj_t = pdfium_raw.FPDFPageObj_GetType(obj_ptr)
                if obj_t in (pdfium_raw.FPDF_PAGEOBJ_IMAGE, pdfium_raw.FPDF_PAGEOBJ_PATH, pdfium_raw.FPDF_PAGEOBJ_SHADING, pdfium_raw.FPDF_PAGEOBJ_FORM):
                    has_visual_objects = True
                    break
    except Exception:
        has_visual_objects = False

    is_visually_filled = bool(has_images or has_visual_objects or len(visual_items) > 0)

    if n_chars == 0:
        return {
            "page": page_num,
            "width": width,
            "height": height,
            "n_chars": 0,
            "full_text": "",
            "line_structs": [],
            "raw_line_records": [],
            "glyph_runs_by_raw_line": {},
            "clean_lines": [],
            "furniture_records": [],
            "visual_assets": visual_assets,
            "visual_items": visual_items,
            "has_images": is_visually_filled,
            "is_visually_filled": is_visually_filled,
            "quality": "SCANNED" if is_visually_filled else "EMPTY",
            "fallback_status": "NEED_OCR" if is_visually_filled else None,
        }

    full_text = ""
    buf_len = (n_chars + 1) * 2
    raw_buf = ctypes.create_string_buffer(buf_len)
    chars_written = pdfium_raw.FPDFText_GetText(raw_textpage, 0, n_chars, ctypes.cast(raw_buf, ctypes.POINTER(ctypes.c_ushort)))
    if chars_written > 0:
        full_text = raw_buf.raw[: (chars_written - 1) * 2].decode("utf-16le", errors="replace")

    if _is_corrupt_text(full_text):
        return {
            "page": page_num,
            "width": width,
            "height": height,
            "n_chars": n_chars,
            "full_text": full_text,
            "line_structs": [],
            "raw_line_records": [],
            "glyph_runs_by_raw_line": {},
            "clean_lines": [],
            "furniture_records": [],
            "visual_assets": visual_assets,
            "visual_items": visual_items,
            "has_images": is_visually_filled,
            "is_visually_filled": is_visually_filled,
            "quality": "BAD",
            "fallback_status": "NEED_OCR",
        }

    lines_raw = full_text.split("\n")
    line_structs: list[LineInfo] = []
    raw_line_records: list[dict[str, Any]] = []
    # Never handed to _build_page_structure or serialized.  This is an
    # explicitly requested offline-diagnostic projection of PDFium geometry.
    glyph_runs_by_raw_line: dict[int, list[GlyphRun]] = {}
    char_cursor = 0

    font_name_buf = ctypes.create_string_buffer(512)
    flags_val = ctypes.c_int(0)

    for raw_line_id, l_text in enumerate(lines_raw, start=1):
        l_stripped = l_text.strip()
        l_len = len(l_text)
        if not l_stripped:
            char_cursor += l_len + 1
            continue

        start_c = char_cursor
        end_c = min(char_cursor + len(l_text), n_chars)
        char_cursor += l_len + 1

        xs: list[float] = []
        ys_b: list[float] = []
        ys_t: list[float] = []
        sizes: list[float] = []
        bolds: list[bool] = []
        italics: list[bool] = []
        char_boxes: list[tuple[int, float, float, float, float]] = []

        for ci in range(start_c, end_c):
            l = ctypes.c_double(0)
            r = ctypes.c_double(0)
            b = ctypes.c_double(0)
            t = ctypes.c_double(0)
            pdfium_raw.FPDFText_GetCharBox(raw_textpage, ci, ctypes.byref(l), ctypes.byref(r), ctypes.byref(b), ctypes.byref(t))
            if r.value > l.value:
                xs.extend([l.value, r.value])
                ys_b.append(b.value)
                ys_t.append(t.value)
                if include_glyph_runs:
                    char_boxes.append((ci - start_c, l.value, r.value, b.value, t.value))

            sz = pdfium_raw.FPDFText_GetFontSize(raw_textpage, ci)
            wt = pdfium_raw.FPDFText_GetFontWeight(raw_textpage, ci)

            buflen = pdfium_raw.FPDFText_GetFontInfo(raw_textpage, ci, font_name_buf, 512, ctypes.byref(flags_val))
            fname = font_name_buf.value.decode("utf-8", errors="replace") if buflen > 0 else ""
            flags = flags_val.value
            is_b = _is_font_bold(fname, wt, flags)
            is_it = ("italic" in fname.lower()) or ("oblique" in fname.lower()) or bool(flags & 0x40)

            sizes.append(sz)
            bolds.append(is_b)
            italics.append(is_it)

        if xs:
            bx0, bx1 = min(xs), max(xs)
            by0, by1 = min(ys_b), max(ys_t)
            dom_sz = Counter(sizes).most_common(1)[0][0] if sizes else 12.0
            dom_bold = Counter(bolds).most_common(1)[0][0] if bolds else False
            dom_italic = Counter(italics).most_common(1)[0][0] if italics else False

            raw_line_records.append({
                "raw_line_id": raw_line_id,
                "text": l_stripped,
                "raw_text": l_text,
                "bbox": [bx0, by0, bx1, by1],
                "font_size": dom_sz,
                "is_bold": dom_bold,
                "is_italic": dom_italic,
            })
            if include_glyph_runs:
                glyph_runs_by_raw_line[raw_line_id] = _glyph_runs_from_char_boxes(raw_line_id, l_text, char_boxes)

            sanitized_l_stripped = sanitize_forensic_text(l_stripped)
            final_line_text = sanitized_l_stripped if sanitized_l_stripped else l_stripped
            if not _is_corrupt_line(final_line_text) and len(final_line_text.strip()) > 0:
                line_structs.append(LineInfo(
                    text=final_line_text,
                    bbox=(bx0, by0, bx1, by1),
                    font_size=dom_sz,
                    is_bold=dom_bold,
                    is_italic=dom_italic,
                    y_top=by1,
                    y_bottom=by0,
                    x_left=bx0,
                    x_right=bx1,
                    raw_line_id=raw_line_id,
                ))

    clean_lines: list[LineInfo] = []
    furniture_records: list[dict[str, Any]] = []

    for line in line_structs:
        if _is_marginal_furniture(line.text, line.bbox, width, height):
            furniture_records.append({
                "page": page_num,
                "bbox": list(line.bbox),
                "text": line.text,
                "raw_text": next((item["raw_text"] for item in raw_line_records if item["raw_line_id"] == line.raw_line_id), line.text),
                "classification": "furniture",
                "reason": "marginal_furniture_geometry",
                "source_line_ids": [line.raw_line_id],
            })
        else:
            clean_lines.append(line)

    return {
        "page": page_num,
        "width": width,
        "height": height,
        "n_chars": n_chars,
        "full_text": full_text,
        "line_structs": line_structs,
        "raw_line_records": raw_line_records,
        "glyph_runs_by_raw_line": glyph_runs_by_raw_line,
        "clean_lines": clean_lines,
        "furniture_records": furniture_records,
        "visual_assets": visual_assets,
        "visual_items": visual_items,
        "has_images": is_visually_filled,
        "is_visually_filled": is_visually_filled,
        "quality": "GOOD",
        "fallback_status": None,
    }


def filter_document_recurring_lines(pages_raw: dict[int, dict[str, Any]]) -> dict[int, dict[str, Any]]:
    """Scan clean lines across multi-page document context and isolate recurring headers/footers."""
    if len(pages_raw) < 2:
        return pages_raw

    # Create immutable snapshots of clean_lines across all pages for global recurrence detection
    snapshots: dict[int, list[LineInfo]] = {
        p_num: list(pdata["clean_lines"])
        for p_num, pdata in pages_raw.items()
    }

    # Identify lines to remove per page based on global multi-page recurrence
    suppressed_line_ids_by_page: dict[int, set[str]] = defaultdict(set)
    furniture_to_add_by_page: dict[int, list[dict[str, Any]]] = defaultdict(list)

    for p_num, pdata in pages_raw.items():
        h = pdata["height"]
        for l in snapshots[p_num]:
            is_top = l.y_top >= h * 0.78
            is_bot = l.y_bottom <= h * 0.18
            if not (is_top or is_bot):
                continue

            norm = _normalize_furniture_text(l.text)
            if len(norm) < 4:
                continue

            region = "header" if is_top else "footer"
            match_count = 1
            for other_pno, other_lines in snapshots.items():
                if other_pno == p_num:
                    continue
                other_h = pages_raw[other_pno]["height"]
                for other_l in other_lines:
                    other_is_top = other_l.y_top >= other_h * 0.78
                    other_is_bot = other_l.y_bottom <= other_h * 0.18
                    other_region = "header" if other_is_top else "footer"
                    if other_region != region:
                        continue
                    other_norm = _normalize_furniture_text(other_l.text)
                    if norm == other_norm or _furniture_similarity(norm, other_norm) >= 0.85:
                        if abs(l.y_bottom - other_l.y_bottom) <= 30.0 and abs(l.x_left - other_l.x_left) <= 60.0:
                            match_count += 1
                            break

            if match_count >= 2:
                suppressed_line_ids_by_page[p_num].add(l.raw_line_id)
                furniture_to_add_by_page[p_num].append({
                    "page": p_num,
                    "bbox": list(l.bbox),
                    "text": l.text,
                    "raw_text": next((item["raw_text"] for item in pdata["raw_line_records"] if item["raw_line_id"] == l.raw_line_id), l.text),
                    "classification": "furniture",
                    "reason": f"recurring_{region}",
                    "source_line_ids": [l.raw_line_id],
                })

    # Apply filter modifications to each page after global analysis is complete
    for p_num, pdata in pages_raw.items():
        suppressed_ids = suppressed_line_ids_by_page.get(p_num, set())
        if suppressed_ids:
            pdata["clean_lines"] = [
                l for l in pdata["clean_lines"]
                if l.raw_line_id not in suppressed_ids
            ]
            pdata["furniture_records"].extend(furniture_to_add_by_page.get(p_num, []))

    return pages_raw


def _build_page_structure(
    raw_page: Any,
    pdata: dict[str, Any],
    page_num: int,
    total_pages: int = 1,
    initial_previous_text: str = "",
    initial_previous_type: str = "",
    canonical_tables: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Consolidate paragraphs, classify blocks, extract tables and format Markdown for a single page."""
    width = pdata["width"]
    height = pdata["height"]
    line_structs = pdata["line_structs"]
    raw_line_records = pdata["raw_line_records"]
    raw_record_by_id = {int(row["raw_line_id"]): row for row in raw_line_records}

    def line_source(lines: list[LineInfo]) -> tuple[str, str, list[str]]:
        engines = sorted({
            str(raw_record_by_id.get(line.raw_line_id, {}).get("ocr_engine"))
            for line in lines
            if raw_record_by_id.get(line.raw_line_id, {}).get("provenance") == "ocr"
            and raw_record_by_id.get(line.raw_line_id, {}).get("ocr_engine")
        })
        if not engines:
            return "pdfium_block", "pdfium", []
        has_native = any(
            raw_record_by_id.get(line.raw_line_id, {}).get("provenance") != "ocr"
            for line in lines
        )
        return (
            ("pdfium_block+" if has_native else "") + "+".join(engines),
            "mixed" if has_native else "ocr",
            engines,
        )
    clean_lines = pdata["clean_lines"]
    furniture_records = pdata["furniture_records"]
    visual_assets = pdata["visual_assets"]
    visual_items = pdata["visual_items"]
    full_text = pdata["full_text"]
    is_visually_filled = pdata["is_visually_filled"]
    n_chars = pdata["n_chars"]

    if n_chars == 0 or not line_structs or _is_corrupt_text(full_text):
        rendered_info = _render_page_as_png_base64(raw_page) if (raw_page and is_visually_filled) else None
        placeholder = "*[Página digitalizada / Anexo visual]*" if is_visually_filled else ""
        if rendered_info:
            b64_data, img_w, img_h = rendered_info
            visual_assets.append({
                "visual_asset_id": f"p{page_num}-raster-page",
                "page": page_num,
                "kind": "rendered_page_image",
                "bbox": [0.0, 0.0, width, height],
                "pixel_size": {"width": img_w, "height": img_h},
                "mime_type": "image/png",
                "source": "pdfium_page_render",
            })
        raw_text_region = [] if not full_text else [_region(
            f"p{page_num}-r0001", "unknown", full_text, full_text,
            [0.0, 0.0, width, height], [], included_in_markdown=False,
            exclusion_reason="pdfium_text_geometry_unavailable", source="pdfium_raw_text",
        )]
        residual_regions = _build_regions(page_num, width, height, raw_line_records, [], furniture_records) if line_structs else raw_text_region
        qual = "BAD" if _is_corrupt_text(full_text) else ("SCANNED" if is_visually_filled else "EMPTY")
        empty_fallback = "NEED_OCR" if (is_visually_filled or qual == "BAD") else None
        if pdata.get("page_category") == "TEXTUAL_VISUAL":
            empty_fallback = "TEXTUAL_VISUAL_OCR_APPLIED" if pdata.get("ocr_provenance") else "TEXTUAL_VISUAL_OCR_EMPTY"
        return {
            "page": page_num,
            "text": placeholder,
            "logical_text": "[Página digitalizada / Anexo visual]" if is_visually_filled else "",
            "raw_pdfium_text": pdata.get("native_full_text", full_text),
            "raw_lines": raw_line_records,
            "lines": [
                {
                    "line_id": index,
                    "text": line.text,
                    "bbox": list(line.bbox),
                    "font_size": line.font_size,
                    "is_bold": line.is_bold,
                    "is_italic": line.is_italic,
                    "raw_line_id": line.raw_line_id,
                    "source": raw_record_by_id.get(line.raw_line_id, {}).get("source", "pdfium"),
                    "provenance": raw_record_by_id.get(line.raw_line_id, {}).get("provenance", "pdfium"),
                }
                for index, line in enumerate(line_structs, start=1)
            ],
            "blocks": [],
            "furniture": furniture_records,
            "regions_version": "v1",
            "regions": residual_regions,
            "visual_assets_version": "v1",
            "visual_assets": _relate_visual_assets(visual_assets, residual_regions),
            "visual_items_version": "v1",
            "visual_items": _relate_visual_items(visual_items, residual_regions, visual_assets),
            "source_refs": [],
            "tables": [],
            "has_images": is_visually_filled,
            "quality": qual,
            "fallback_status": empty_fallback,
            "page_geometry": {"width": width, "height": height},
            "page_category": pdata.get("page_category", "NATIVE_VALID"),
            "ocr_engine": pdata.get("ocr_engine"),
            "ocr_provenance": pdata.get("ocr_provenance", []),
            "triage_metrics": pdata.get("triage_metrics", {}),
        }

    # Sort clean lines in top-to-bottom reading order (y_top descending)
    clean_lines.sort(key=lambda l: (-round(l.y_top / 4.0) * 4.0, l.x_left))
    visual_items = _classify_graphic_primitives(visual_items, clean_lines)

    # Determine body font size
    body_sizes = [l.font_size for l in clean_lines if not l.is_bold]
    body_font_size = Counter(body_sizes).most_common(1)[0][0] if body_sizes else 12.0

    # Cluster lines into blocks
    occ_recs = parse_ocorrencias_records(clean_lines)
    occ_lines = [line for r in occ_recs for line in r["lines"]] if occ_recs else []
    occ_line_ids = {id(line) for line in occ_lines}

    raw_blocks: list[list[LineInfo]] = []
    paragraph_boundary_trace: list[dict[str, Any]] = []

    if occ_lines:
        occ_indices = [idx for idx, l in enumerate(clean_lines) if id(l) in occ_line_ids]
        first_occ_idx = min(occ_indices)
        last_occ_idx = max(occ_indices)
        before_lines = clean_lines[:first_occ_idx]
        after_lines = clean_lines[last_occ_idx + 1:]
        if before_lines:
            raw_blocks.extend(segment_logical_paragraphs(
                before_lines, body_font_size, paragraph_boundary_trace, page_geometry=(width, height), page_num=page_num
            ))
        raw_blocks.append(occ_lines)
        if after_lines:
            raw_blocks.extend(segment_logical_paragraphs(
                after_lines, body_font_size, paragraph_boundary_trace, page_geometry=(width, height), page_num=page_num
            ))
    else:
        raw_blocks = segment_logical_paragraphs(
            clean_lines, body_font_size, paragraph_boundary_trace, page_geometry=(width, height), page_num=page_num
        )
    flow_metrics = _local_paragraph_metrics(clean_lines, body_font_size)
    paragraph_diagnostics = paragraph_segmentation_suspicions(clean_lines, raw_blocks, body_font_size)

    source_refs: list[dict[str, Any]] = []
    block_records: list[dict[str, Any]] = []
    md_elements: list[str] = []
    logical_elements: list[str] = []
    tables: list[dict[str, Any]] = []
    canonical_tables = canonical_tables or []
    emitted_canonical_table_ids: set[str] = set()

    block_id = 1
    previous_text = initial_previous_text
    previous_type = initial_previous_type
    for block_index, b_lines in enumerate(raw_blocks):
        b_raw_text = _block_text(b_lines, preserve_paragraphs=True)
        if not b_raw_text:
            continue

        bx0 = min(l.bbox[0] for l in b_lines)
        by0 = min(l.bbox[1] for l in b_lines)
        bx1 = max(l.bbox[2] for l in b_lines)
        by1 = max(l.bbox[3] for l in b_lines)
        b_size = Counter(l.font_size for l in b_lines).most_common(1)[0][0]
        b_bold = Counter(l.is_bold for l in b_lines).most_common(1)[0][0]
        b_italic = Counter(l.is_italic for l in b_lines).most_common(1)[0][0]
        bbox = (bx0, by0, bx1, by1)
        canonical_table = _canonical_table_for_lines(canonical_tables, b_lines)

        cand_type = _classify_block(
            b_raw_text,
            b_lines,
            b_size,
            b_bold,
            b_italic,
            body_font_size,
            previous_text,
            previous_type,
            _block_text(raw_blocks[block_index + 1]) if block_index + 1 < len(raw_blocks) else "",
            page_num=page_num,
            block_index=block_index,
            total_blocks=len(raw_blocks),
        )

        if cand_type == "blockquote":
            is_quote_cont = (previous_type == "blockquote" and not _starts_quote(b_raw_text))
            inline_split = _split_inline_quote(b_raw_text, is_continuation=is_quote_cont)
            if inline_split:
                quote_text, prose_text = inline_split
                accum = ""
                split_line_idx = len(b_lines)
                for idx, line in enumerate(b_lines):
                    accum += (" " if accum else "") + line.text
                    if any(delim in line.text for delim in ['"', '”', '»']) and len(accum.strip()) >= len(quote_text) * 0.8:
                        split_line_idx = idx + 1
                        break
                quote_lines = b_lines[:split_line_idx] if split_line_idx > 0 else b_lines[:1]
                prose_lines = b_lines[split_line_idx:] if split_line_idx < len(b_lines) else b_lines[-1:]

                q_bx0 = min(l.bbox[0] for l in quote_lines)
                q_by0 = min(l.bbox[1] for l in quote_lines)
                q_bx1 = max(l.bbox[2] for l in quote_lines)
                q_by1 = max(l.bbox[3] for l in quote_lines)

                p_bx0 = min(l.bbox[0] for l in prose_lines)
                p_by0 = min(l.bbox[1] for l in prose_lines)
                p_bx1 = max(l.bbox[2] for l in prose_lines)
                p_by1 = max(l.bbox[3] for l in prose_lines)

                md_elements.append(block_markdown("blockquote", quote_text))
                md_elements.extend(reflow_paragraph_elements(prose_text))
                logical_elements.append(" ".join(b_raw_text.split()))

                quote_source, quote_provenance, _ = line_source(quote_lines)
                source_refs.append({
                    "page": page_num,
                    "source": quote_source,
                    "provenance": quote_provenance,
                    "bbox": [q_bx0, q_by0, q_bx1, q_by1],
                    "source_line_ids": [line.raw_line_id for line in quote_lines],
                    "font_size": b_size,
                    "is_bold": b_bold,
                    "is_italic": b_italic
                })
                prose_source, prose_provenance, _ = line_source(prose_lines)
                source_refs.append({
                    "page": page_num,
                    "source": prose_source,
                    "provenance": prose_provenance,
                    "bbox": [p_bx0, p_by0, p_bx1, p_by1],
                    "source_line_ids": [line.raw_line_id for line in prose_lines],
                    "font_size": b_size,
                    "is_bold": b_bold,
                    "is_italic": b_italic
                })

                block_records.append({
                    "block_id": block_id,
                    "type_candidate": "blockquote",
                    "text": quote_text,
                    "bbox": [q_bx0, q_by0, q_bx1, q_by1],
                    "font_size": b_size,
                    "is_bold": b_bold,
                    "is_italic": b_italic,
                    "source": "typography+geometry",
                    "source_line_ids": [line.raw_line_id for line in quote_lines],
                    "flow_kind": FlowKind.QUOTE.value,
                    "ast": {
                        "kind": FlowKind.QUOTE.value,
                        "source_line_ids": [line.raw_line_id for line in quote_lines],
                        "bbox": [q_bx0, q_by0, q_bx1, q_by1],
                        "children": [],
                    },
                })
                block_id += 1

                block_records.append({
                    "block_id": block_id,
                    "type_candidate": "paragraph",
                    "text": prose_text,
                    "bbox": [p_bx0, p_by0, p_bx1, p_by1],
                    "font_size": b_size,
                    "is_bold": b_bold,
                    "is_italic": b_italic,
                    "source": "typography+geometry",
                    "source_line_ids": [line.raw_line_id for line in prose_lines],
                    "flow_kind": FlowKind.PROSE.value,
                    "ast": {
                        "kind": FlowKind.PROSE.value,
                        "source_line_ids": [line.raw_line_id for line in prose_lines],
                        "bbox": [p_bx0, p_by0, p_bx1, p_by1],
                        "children": [],
                    },
                })
                block_id += 1

                previous_text = prose_text
                previous_type = "paragraph"
                continue

        typed_node = _typed_flow_nodes([b_lines], [cand_type])[0]
        typed_rendered = _serialize_typed_flow_node(typed_node, cand_type)

        if canonical_table is not None:
            from core.table_canonical_projection import canonical_table_markdown
            canonical_id = str(canonical_table.get("instance_id", ""))
            if canonical_id not in emitted_canonical_table_ids:
                canonical_markdown = canonical_table_markdown(canonical_table, serialize_table_gfm)
                if canonical_markdown:
                    md_elements.append(canonical_markdown)
                    tables.append(canonical_table)
                    emitted_canonical_table_ids.add(canonical_id)
                else:
                    # Invalid/empty projection is not allowed to erase the block.
                    canonical_table = None

        if canonical_table is None and typed_rendered is not None:
            md_elements.extend(typed_rendered)
        elif canonical_table is None and cand_type == "table":
            res = _detect_tabular_grid(b_lines)
            if res:
                prefix_titles, grid = res
                for title in prefix_titles:
                    for el in reflow_paragraph_elements(title):
                        md_elements.append(el)
                        logical_elements.append(el)
                has_hdr = any(
                    re.search(r"\b(Delegacia|Advogado|Forma|CNPJ|CPF|Raz[aã]o|Nome|IFP|Especifica[cç][aã]o|Saldos?|Rendimentos?|Valor|Data|Item|Descri[cç][aã]o)\b", c, re.IGNORECASE)
                    for c in grid[0]
                )
                t_model = {
                    "type": "table",
                    "page": page_num,
                    "source": "pdfium_geometry",
                    "bbox": [bx0, by0, bx1, by1],
                    "rows": [
                        {
                            "row_index": r_idx,
                            "cells": [
                                {
                                    "text": cell_txt,
                                    "row_index": r_idx,
                                    "column_index": c_idx,
                                    "colspan": 1,
                                    "rowspan": 1,
                                    "is_header": bool(r_idx == 0 and has_hdr)
                                }
                                for c_idx, cell_txt in enumerate(r_cells)
                            ]
                        }
                        for r_idx, r_cells in enumerate(grid)
                    ],
                    "column_count": len(grid[0])
                }
                t_md = serialize_table_gfm(t_model)
                t_model["markdown"] = t_md
                tables.append(t_model)
                md_elements.append(t_md)
                logical_elements.append(" | ".join(" ".join(c.split()) for row in grid for c in row if c.strip()))
            else:
                for el in reflow_paragraph_elements(b_raw_text):
                    md_elements.append(el)
                    logical_elements.append(" ".join(b_raw_text.split()))
        if cand_type == "list_item":
            logical_elements.extend(extract_list_items(b_raw_text))
        elif cand_type != "table":
            if any(c in b_raw_text for c in BULLET_CHARS):
                for el in reflow_paragraph_elements(b_raw_text):
                    cleaned_el = re.sub(r"^[-*•●▪◦]\s*", "", el).strip()
                    if cleaned_el:
                        logical_elements.append(cleaned_el)
            else:
                logical_elements.append(" ".join(b_raw_text.split()))
        elif canonical_table is not None:
            # Keep the legacy logical-text contribution byte-for-byte stable.
            # Canonical V1 owns only the presentation projection and the
            # persisted table structure; it must not replace the established
            # logical identity with either b_raw_text or canonical cell text.
            legacy_table = _detect_tabular_grid(b_lines)
            if legacy_table:
                prefix_titles, grid = legacy_table
                for title in prefix_titles:
                    logical_elements.extend(reflow_paragraph_elements(title))
                logical_elements.append(
                    " | ".join(
                        " ".join(cell.split())
                        for row in grid
                        for cell in row
                        if cell.strip()
                    )
                )
            else:
                logical_elements.append(" ".join(b_raw_text.split()))

        ref_source, ref_provenance, ref_engines = line_source(b_lines)
        source_refs.append({
            "page": page_num,
            "source": ref_source,
            "provenance": ref_provenance,
            "bbox": [bx0, by0, bx1, by1],
            "source_line_ids": [line.raw_line_id for line in b_lines],
            "font_size": b_size,
            "is_bold": b_bold,
            "is_italic": b_italic
        })

        block_records.append({
            "block_id": block_id,
            "type_candidate": cand_type,
            "text": b_raw_text,
            "bbox": [bx0, by0, bx1, by1],
            "font_size": b_size,
            "is_bold": b_bold,
            "is_italic": b_italic,
            "source": ref_source if ref_engines else "typography+geometry",
            "provenance": ref_provenance,
            "ocr_engines": ref_engines,
            "source_line_ids": [line.raw_line_id for line in b_lines],
            "flow_kind": typed_node.kind.value,
            "ast": {
                "kind": typed_node.kind.value,
                "source_line_ids": typed_node.source_line_ids,
                "bbox": list(typed_node.bbox),
                "children": [
                    {"kind": child.kind.value, "source_line_ids": child.source_line_ids, "bbox": list(child.bbox)}
                    for child in typed_node.children
                ],
            },
        })
        previous_text = b_raw_text
        previous_type = cand_type
        block_id += 1

    page_markdown = "\n\n".join(md_elements).strip()
    page_markdown, html_tables = normalize_tabular_markdown(
        page_markdown, page=page_num, source="pdfium_structuralizer"
    )
    tables.extend(html_tables)

    page_markdown = sanitize_forensic_text(page_markdown)

    is_residual = len(page_markdown.strip()) < 25 or len(clean_lines) == 0 or _is_corrupt_text(page_markdown)
    if is_residual and (is_visually_filled or _is_corrupt_text(page_markdown)):
        rendered_info = _render_page_as_png_base64(raw_page) if (raw_page and is_visually_filled) else None
        if rendered_info:
            b64_data, img_w, img_h = rendered_info
            # Raster bytes belong to the original-PDF endpoint, not to the
            # textual page contract. The placeholder keeps this page eligible
            # for the existing lazy ``visual_ref`` projection.
            page_markdown = "*[Página digitalizada / Anexo visual]*"
            visual_assets.append({
                "visual_asset_id": f"p{page_num}-raster-page",
                "page": page_num,
                "kind": "rendered_page_image",
                "bbox": [0.0, 0.0, width, height],
                "pixel_size": {"width": img_w, "height": img_h},
                "mime_type": "image/png",
                "source": "pdfium_page_render",
            })
        else:
            page_markdown = "*[Página digitalizada / Anexo visual]*"
        logical_elements = ["[Página digitalizada / Anexo visual]"]

    quality = "BAD" if (_is_corrupt_text(full_text) or _is_corrupt_text(page_markdown)) else ("SCANNED" if (is_visually_filled and is_residual) else ("GOOD" if not is_residual else "EMPTY"))
    fallback_status = "NEED_OCR" if (is_visually_filled and is_residual) or quality == "BAD" else None
    if pdata.get("page_category") == "TEXTUAL_VISUAL":
        fallback_status = "TEXTUAL_VISUAL_OCR_APPLIED" if pdata.get("ocr_provenance") else "TEXTUAL_VISUAL_OCR_EMPTY"

    regions = _build_regions(page_num, width, height, raw_line_records, block_records, furniture_records)
    for region in regions:
        engines = sorted({
            str(raw_record_by_id.get(int(line_id), {}).get("ocr_engine"))
            for line_id in region.get("source_line_ids", [])
            if raw_record_by_id.get(int(line_id), {}).get("provenance") == "ocr"
            and raw_record_by_id.get(int(line_id), {}).get("ocr_engine")
        })
        if engines:
            has_native = any(
                raw_record_by_id.get(int(line_id), {}).get("provenance") != "ocr"
                for line_id in region.get("source_line_ids", [])
            )
            region["source"] = ("pdfium_raw_line+" if has_native else "") + "+".join(engines)
            region["provenance"] = "mixed" if has_native else "ocr"
    visual_assets = _relate_visual_assets(visual_assets, regions)
    visual_items = _relate_visual_items(visual_items, regions, visual_assets)
    return {
        "page": page_num,
        "text": page_markdown,
        "logical_text": sanitize_forensic_text("\n\n".join(logical_elements).strip()),
        "lines": [
            {
                "line_id": index,
                "text": line.text,
                "bbox": list(line.bbox),
                "font_size": line.font_size,
                "is_bold": line.is_bold,
                "is_italic": line.is_italic,
                "raw_line_id": line.raw_line_id,
                "source": raw_record_by_id.get(line.raw_line_id, {}).get("source", "pdfium"),
                "provenance": raw_record_by_id.get(line.raw_line_id, {}).get("provenance", "pdfium"),
            }
            for index, line in enumerate(line_structs, start=1)
        ],
        "blocks": block_records,
        "furniture": furniture_records,
        "regions_version": "v1",
        "regions": regions,
        "visual_assets_version": "v1",
        "visual_assets": visual_assets,
        "visual_items_version": "v1",
        "visual_items": visual_items,
        "raw_pdfium_text": pdata.get("native_full_text", full_text),
        "raw_lines": raw_line_records,
        "source_refs": source_refs,
        "tables": tables,
        "has_images": is_visually_filled,
        "quality": quality,
        "fallback_status": fallback_status,
        "page_geometry": {"width": width, "height": height},
        "page_category": pdata.get("page_category", "NATIVE_VALID"),
        "ocr_engine": pdata.get("ocr_engine"),
        "ocr_provenance": pdata.get("ocr_provenance", []),
        "triage_metrics": pdata.get("triage_metrics", {}),
        "paragraph_flow": {
            "line_height": flow_metrics.line_height,
            "baseline": flow_metrics.baseline,
            "baseline_mad": flow_metrics.baseline_mad,
            "left_edge": flow_metrics.left_edge,
            "right_edge": flow_metrics.right_edge,
            "column_width": flow_metrics.column_width,
            "left_tolerance": flow_metrics.left_tolerance,
            "right_tolerance": flow_metrics.right_tolerance,
        },
        "paragraph_diagnostics": paragraph_diagnostics,
        "paragraph_boundary_trace": paragraph_boundary_trace,
    }


def extract_page_structure(
    raw_page: Any,
    raw_textpage: Any,
    page_num: int,
    source_resolver: VisualAssetSourceResolver | None = None,
    canonical_tables: list[dict[str, Any]] | None = None,
    document_id: str | None = None,
) -> dict[str, Any]:
    """Extract character runs, lines, blocks and structured text using pure PDFium."""
    raw_data = _extract_page_raw_data(
        raw_page, raw_textpage, page_num, source_resolver,
        include_glyph_runs=bool(document_id),
    )
    if document_id and canonical_tables is None:
        try:
            from core.table_canonical_runtime import reconstruct_canonical_tables
            canonical_tables = reconstruct_canonical_tables(
                raw_data, document_id=document_id, page_number=page_num,
            )
        except Exception:
            # Table reconstruction is an optional presentation layer.  Its
            # failure must retain the established structuralizer fallback.
            canonical_tables = None
    return _build_page_structure(raw_page, raw_data, page_num, total_pages=1, canonical_tables=canonical_tables)


def extract_page_glyph_runs(raw_page: Any, raw_textpage: Any, page_num: int) -> dict[int, list[GlyphRun]]:
    """Return transient intraline geometry for an offline diagnostic consumer.

    The result is deliberately not included in :func:`extract_page_structure`
    and callers must keep it in memory only.
    """
    return _extract_page_raw_data(
        raw_page,
        raw_textpage,
        page_num,
        include_glyph_runs=True,
    )["glyph_runs_by_raw_line"]


def _textual_visual_region_jobs(
    page: Any,
    page_num: int,
    width: float,
    height: float,
    regions: list[dict[str, float]],
    *,
    scale: float = 2.4,
) -> list[dict[str, Any]]:
    """Render only the detector's candidate rectangles for the OCR adapter."""
    if not regions:
        return []
    bitmap = page.render(scale=scale)
    image = bitmap.to_pil().convert("RGB")
    jobs: list[dict[str, Any]] = []
    for index, region in enumerate(regions, start=1):
        x0 = max(0, int(round(region["x0"] * scale)))
        x1 = min(image.width, int(round(region["x1"] * scale)))
        y0 = max(0, int(round((height - region["y1"]) * scale)))
        y1 = min(image.height, int(round((height - region["y0"]) * scale)))
        if x1 - x0 < 16 or y1 - y0 < 8:
            continue
        crop = image.crop((x0, y0, x1, y1))
        encoded = io.BytesIO()
        crop.save(encoded, format="PNG")
        jobs.append({
            "region_id": f"p{page_num}-tv-{index:02d}",
            "page": page_num,
            "image_bytes": encoded.getvalue(),
            "origin_px": [x0, y0],
            "scale": scale,
            "page_height": height,
        })
    return jobs


def _append_textual_visual_ocr(
    pdata: dict[str, Any],
    jobs: list[dict[str, Any]],
    recognized: dict[str, Any],
    page_num: int,
) -> None:
    """Append non-overlapping OCR line geometry before paragraph reconstruction."""
    if not jobs:
        return
    records = pdata["raw_line_records"]
    existing = list(pdata["line_structs"])
    existing_ids = [line.raw_line_id for line in existing]
    next_id = max(existing_ids, default=0) + 1
    engines = recognized.get("engine_by_region", {})
    results = recognized.get("regions", {})
    added_text: list[str] = []
    provenance: list[dict[str, Any]] = []
    for job in jobs:
        engine = engines.get(job["region_id"])
        if not engine:
            continue
        origin_x, origin_y = job["origin_px"]
        scale = float(job["scale"])
        for item in results.get(job["region_id"], []):
            text = str(item.get("text", "")).strip()
            local = item.get("bbox_px", [0, 0, 0, 0])
            if len(local) != 4 or not text:
                continue
            px0, py0, px1, py1 = (float(value) for value in local)
            if (
                len(text) <= 4
                and (py1 - py0) < 10.0
                and re.fullmatch(r"[A-Z]{2,4}[,.:]?", text.upper())
            ):
                # Suppress tiny OCR readings from logos/emblems, not document text.
                continue
            bbox = (
                max(0.0, (origin_x + px0) / scale),
                max(0.0, job["page_height"] - (origin_y + py1) / scale),
                min(pdata["width"], (origin_x + px1) / scale),
                min(pdata["height"], job["page_height"] - (origin_y + py0) / scale),
            )
            if bbox[2] <= bbox[0] or bbox[3] <= bbox[1]:
                continue
            # Native text wins at overlapping physical coordinates. OCR is additive
            # only where PDFium has no corresponding line, preventing double content.
            duplicate = False
            for line in existing:
                ix0, iy0 = max(bbox[0], line.bbox[0]), max(bbox[1], line.bbox[1])
                ix1, iy1 = min(bbox[2], line.bbox[2]), min(bbox[3], line.bbox[3])
                intersection = max(0.0, ix1 - ix0) * max(0.0, iy1 - iy0)
                ocr_area = max(1.0, (bbox[2] - bbox[0]) * (bbox[3] - bbox[1]))
                if intersection / ocr_area >= 0.35:
                    duplicate = True
                    break
            if duplicate:
                continue
            line = LineInfo(
                text=text,
                bbox=bbox,
                font_size=11.0,
                is_bold=False,
                is_italic=False,
                y_top=bbox[3],
                y_bottom=bbox[1],
                x_left=bbox[0],
                x_right=bbox[2],
                raw_line_id=next_id,
            )
            next_id += 1
            confidence = item.get("confidence")
            record = {
                "raw_line_id": line.raw_line_id,
                "text": text,
                "raw_text": text,
                "bbox": list(bbox),
                "font_size": line.font_size,
                "is_bold": False,
                "is_italic": False,
                "source": engine,
                "provenance": "ocr",
                "ocr_engine": engine,
                "confidence": confidence,
                "page": page_num,
                "page_region_id": job["region_id"],
            }
            records.append(record)
            existing.append(line)
            added_text.append(text)
            provenance.append({
                "page": page_num,
                "source": engine,
                "provenance": "ocr",
                "bbox": list(bbox),
                "raw_line_id": line.raw_line_id,
                "region_id": job["region_id"],
                "confidence": confidence,
            })
            if _is_marginal_furniture(text, bbox, pdata["width"], pdata["height"]):
                pdata["furniture_records"].append({
                    "page": page_num,
                    "bbox": list(bbox),
                    "text": text,
                    "raw_text": text,
                    "classification": "furniture",
                    "reason": "ocr_marginal_furniture_geometry",
                    "source_line_ids": [line.raw_line_id],
                })
            else:
                pdata["clean_lines"].append(line)
    if not added_text:
        return
    pdata["line_structs"] = existing
    pdata["n_chars"] += sum(len(text) for text in added_text)
    pdata["native_full_text"] = pdata.get("native_full_text", pdata["full_text"])
    pdata["full_text"] = "\n".join([pdata["native_full_text"], *added_text]).strip()
    pdata["page_category"] = "TEXTUAL_VISUAL"
    pdata["ocr_engine"] = sorted({str(item["source"]) for item in provenance})
    pdata["ocr_provenance"] = provenance
    pdata["fallback_status"] = "TEXTUAL_VISUAL_OCR_APPLIED"


def extract_document_pages(
    doc: Any,
    page_numbers: set[int] | list[int],
    source_resolver: VisualAssetSourceResolver | None = None,
    enable_heron_fallback: bool | None = None,
    canonical_tables_by_page: dict[int, list[dict[str, Any]]] | None = None,
    document_id: str | None = None,
) -> dict[int, dict[str, Any]]:
    """Extract, filter recurring furniture across document context, structure paragraphs and mark continuity."""
    sorted_pnums = sorted(page_numbers)
    raw_pages_map: dict[int, dict[str, Any]] = {}
    pdf_pages_map: dict[int, Any] = {}
    textual_visual_jobs_by_page: dict[int, list[dict[str, Any]]] = {}
    all_textual_visual_jobs: list[dict[str, Any]] = []

    for p_num in sorted_pnums:
        page_idx = p_num - 1
        page = doc.get_page(page_idx)
        pdf_pages_map[p_num] = page
        raw_page = page.raw
        textpage = page.get_textpage()
        raw_textpage = textpage.raw
        raw_data = _extract_page_raw_data(
            raw_page, raw_textpage, p_num, source_resolver,
            include_glyph_runs=bool(document_id and canonical_tables_by_page is None),
        )
        from core.page_triage import PageCategory, triage_page
        triage = triage_page(page, p_num, raw_textpage)
        raw_data["page_category"] = triage.category.value
        raw_data["triage_metrics"] = triage.metrics
        if triage.category == PageCategory.TEXTUAL_VISUAL:
            jobs = _textual_visual_region_jobs(
                page, p_num, raw_data["width"], raw_data["height"],
                triage.metrics.get("candidate_regions_pdf", []),
            )
            textual_visual_jobs_by_page[p_num] = jobs
            all_textual_visual_jobs.extend(jobs)
        raw_pages_map[p_num] = raw_data

    if all_textual_visual_jobs:
        from core.ocr.textual_visual_adapter import recognize_textual_visual_regions
        try:
            recognized = recognize_textual_visual_regions(all_textual_visual_jobs)
        except Exception:
            # Keep the page's visual evidence and native text if both OCR paths fail.
            recognized = {"engine_by_region": {}, "regions": {}}
        for p_num, jobs in textual_visual_jobs_by_page.items():
            _append_textual_visual_ocr(raw_pages_map[p_num], jobs, recognized, p_num)

    # Multi-page line-level recurring furniture filter across document context
    if len(raw_pages_map) >= 2:
        filter_document_recurring_lines(raw_pages_map)

    results: dict[int, dict[str, Any]] = {}
    prev_text = ""
    prev_type = ""
    for p_num in sorted_pnums:
        page = pdf_pages_map[p_num]
        pentry = raw_pages_map[p_num]
        canonical_tables = (canonical_tables_by_page or {}).get(p_num)
        if document_id and canonical_tables_by_page is None:
            try:
                from core.table_canonical_runtime import reconstruct_canonical_tables
                canonical_tables = reconstruct_canonical_tables(
                    pentry, document_id=document_id, page_number=p_num,
                )
            except Exception:
                # A genuine canonical-chain failure intentionally reaches the
                # legacy detector below; raw text/boundary results stay intact.
                canonical_tables = None
        results[p_num] = _build_page_structure(
            page.raw,
            pentry,
            p_num,
            total_pages=len(sorted_pnums),
            initial_previous_text=prev_text,
            initial_previous_type=prev_type,
            canonical_tables=canonical_tables,
        )
        blocks = results[p_num].get("blocks", [])
        if (
            blocks
            and blocks[-1].get("type_candidate") == "blockquote"
            and not _quote_is_closed(blocks[-1].get("text", ""))
        ):
            prev_text = blocks[-1].get("text", "")
            prev_type = "blockquote"
        else:
            prev_text = ""
            prev_type = ""

    return mark_cross_page_continuity(results)


def _normalize_furniture_text(text: str) -> str:
    normalized = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii").lower()
    normalized = re.sub(r"\b(?:pagina|pag|fls?|folhas?)\s*\d+\b", " ", normalized)
    normalized = re.sub(r"\d+", "#", normalized)
    normalized = re.sub(r"[^a-z#]+", " ", normalized)
    return " ".join(normalized.split())


def _furniture_similarity(left: str, right: str) -> float:
    if left == right:
        return 1.0
    return SequenceMatcher(None, left, right, autojunk=False).ratio()


def deduplicate_recurring_furniture(pages_data: dict[int, dict[str, Any]], page_heights: dict[int, float]) -> dict[int, dict[str, Any]]:
    """
    Identify recurring headers and footers across consecutive pages.
    Keeps the FIRST occurrence in the Readable Markdown, suppresses subsequent occurrences,
    and preserves all suppressed occurrences in page['furniture'] and source_refs with
    reason 'recurring_header' or 'recurring_footer'.
    """
    sorted_pnums = sorted(pages_data.keys())

    candidates_by_region_norm: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)

    for p_num in sorted_pnums:
        p_data = pages_data[p_num]
        height = page_heights.get(p_num, 842.0)

        for idx, blk in enumerate(p_data["blocks"]):
            bx0, by0, bx1, by1 = blk["bbox"]
            is_top = by1 >= height * 0.78
            is_bottom = by0 <= height * 0.18

            if not (is_top or is_bottom):
                continue

            norm = _normalize_furniture_text(blk["text"])
            if len(norm) < 4:
                continue

            region = "header" if is_top else "footer"
            key = (region, norm)
            candidates_by_region_norm[key].append({
                "page": p_num,
                "block_idx": idx,
                "region": region,
                "norm": norm,
                "block": blk
            })

    suppressed_by_page: dict[int, set[int]] = defaultdict(set)
    recurring_furniture_by_page: dict[int, list[dict[str, Any]]] = defaultdict(list)

    all_candidates = [item for occurrences in candidates_by_region_norm.values() for item in occurrences]
    furniture_groups: list[list[dict[str, Any]]] = []
    for candidate in all_candidates:
        matching = next(
            (
                group for group in furniture_groups
                if group[0]["region"] == candidate["region"]
                and _furniture_similarity(group[0]["norm"], candidate["norm"]) >= 0.85
            ),
            None,
        )
        if matching is None:
            furniture_groups.append([candidate])
        else:
            matching.append(candidate)

    for run_candidates in furniture_groups:
        if len(run_candidates) < 2:
            continue
        occurrences = sorted(run_candidates, key=lambda item: item["page"])
        runs: list[list[dict[str, Any]]] = []
        current_run = [occurrences[0]]
        for occ in occurrences[1:]:
            prev_occ = current_run[-1]
            if occ["page"] - prev_occ["page"] <= 2:
                current_run.append(occ)
            else:
                if len(current_run) >= 2:
                    runs.append(current_run)
                current_run = [occ]
        if len(current_run) >= 2:
            runs.append(current_run)

        for run in runs:
            # Every occurrence is furniture: preserve it only in provenance,
            # never in the readable Markdown projection.
            for occ in run:
                p_num = occ["page"]
                b_idx = occ["block_idx"]
                suppressed_by_page[p_num].add(b_idx)
                recurring_furniture_by_page[p_num].append({
                    "page": p_num,
                    "bbox": list(occ["block"]["bbox"]),
                    "text": occ["block"]["text"],
                    "classification": "furniture",
                    "reason": f"recurring_{occ['region']}",
                    "confidence": "high",
                    "source_line_ids": list(occ["block"].get("source_line_ids", [])),
                })

    result: dict[int, dict[str, Any]] = {}
    for p_num in sorted_pnums:
        p_data = pages_data[p_num]
        suppressed_indices = suppressed_by_page.get(p_num, set())
        new_furniture = list(p_data["furniture"]) + recurring_furniture_by_page.get(p_num, [])

        if not suppressed_indices:
            result[p_num] = {
                **p_data,
                "furniture": new_furniture
            }
            continue

        kept_blocks = [blk for idx, blk in enumerate(p_data["blocks"]) if idx not in suppressed_indices]
        suppressed_line_ids = {
            line_id
            for idx, block in enumerate(p_data["blocks"])
            if idx in suppressed_indices
            for line_id in block.get("source_line_ids", [])
        }
        regions = []
        for region in p_data.get("regions", []):
            updated = dict(region)
            if suppressed_line_ids.intersection(updated.get("source_line_ids", [])):
                updated["included_in_markdown"] = False
                updated["exclusion_reason"] = "recurring_header_or_footer"
                updated["kind"] = _region_kind(
                    updated.get("text", ""), tuple(updated["bbox"]),
                    p_data["page_geometry"]["width"], p_data["page_geometry"]["height"], furniture=True,
                )
            regions.append(updated)

        md_elements = []
        for blk in kept_blocks:
            cand_type = blk["type_candidate"]
            b_text = blk["text"]
            if cand_type in ["document_title", "section_title", "subsection_title", "blockquote"]:
                md_elements.append(block_markdown(cand_type, b_text))
            elif cand_type == "list_item":
                item_markdown = _stored_list_item_markdown(b_text)
                if item_markdown:
                    md_elements.append(item_markdown)
            elif cand_type == "table":
                lines_info = [
                    LineInfo(
                        text=l,
                        bbox=tuple(blk["bbox"]),
                        font_size=blk.get("font_size", 12.0),
                        is_bold=blk.get("is_bold", False),
                        is_italic=blk.get("is_italic", False),
                        y_top=blk["bbox"][3],
                        y_bottom=blk["bbox"][1],
                        x_left=blk["bbox"][0],
                        x_right=blk["bbox"][2],
                    )
                    for l in b_text.splitlines()
                    if l.strip()
                ]
                grid = _detect_tabular_grid(lines_info)
                if grid:
                    has_hdr = any(
                        re.search(r"\b(Advogado|Forma|CNPJ|CPF|Raz[aã]o|Nome|IFP|Especifica[cç][aã]o|Saldos?|Rendimentos?|Valor|Data|Item|Descri[cç][aã]o)\b", c, re.IGNORECASE)
                        for c in grid[0]
                    )
                    t_model = {
                        "type": "table",
                        "page": p_num,
                        "rows": [
                            {"row_index": r_idx, "cells": [{"text": cell_txt, "is_header": bool(r_idx == 0 and has_hdr), "colspan": 1, "rowspan": 1} for cell_txt in r_cells]}
                            for r_idx, r_cells in enumerate(grid)
                        ],
                    }
                    md_elements.append(serialize_table_gfm(t_model))
                else:
                    for el in reflow_paragraph_elements(b_text):
                        md_elements.append(el)
            else:
                for el in reflow_paragraph_elements(b_text):
                    md_elements.append(el)

        normalized_text, tables = normalize_tabular_markdown(
            "\n\n".join(md_elements).strip(), page=p_num, source="pdfium_structuralizer"
        )
        result[p_num] = {
            **p_data,
            "text": normalized_text,
            "furniture": new_furniture,
            "regions": regions,
            "tables": tables
        }

    return result


def mark_cross_page_continuity(pages_data: dict[int, dict[str, Any]]) -> dict[int, dict[str, Any]]:
    """Annotate strong paragraph continuation across cleaned page boundaries using Themis-Doc Boundary v2."""
    from core.paragraph_boundary_engine import ParagraphBoundaryEngine
    engine = ParagraphBoundaryEngine()

    result = {page: dict(data) for page, data in pages_data.items()}
    sorted_pages = sorted(result)
    for previous_page, current_page in zip(sorted_pages, sorted_pages[1:]):
        prev_data = result[previous_page]
        curr_data = result[current_page]

        blocks_prev = prev_data.get("blocks", [])
        blocks_curr = curr_data.get("blocks", [])
        lines_prev = prev_data.get("lines", [])
        lines_curr = curr_data.get("lines", [])

        block_lids_prev = {lid for b in blocks_prev for lid in b.get("source_line_ids", [])}
        clean_lines_prev = [l for l in lines_prev if l.get("raw_line_id") in block_lids_prev and l.get("text", "").strip()]

        block_lids_curr = {lid for b in blocks_curr for lid in b.get("source_line_ids", [])}
        clean_lines_curr = [l for l in lines_curr if l.get("raw_line_id") in block_lids_curr and l.get("text", "").strip()]

        if clean_lines_prev and clean_lines_curr:
            l_a = clean_lines_prev[-1]
            l_b = clean_lines_curr[0]
            prev_t = clean_lines_prev[-2].get("text", "") if len(clean_lines_prev) >= 2 else ""
            next_t = clean_lines_curr[1].get("text", "") if len(clean_lines_curr) >= 2 else ""
            pw = prev_data.get("page_geometry", {}).get("width", 595.0)
            ph = prev_data.get("page_geometry", {}).get("height", 842.0)

            decision = engine.evaluate_cross_page(
                l_a,
                l_b,
                prev_line=prev_t,
                next_line=next_t,
                page_geometry=(pw, ph),
                page_prev=previous_page,
                page_next=current_page,
            )

            if decision.decision == "CONTINUA":
                identity = f"page-{previous_page}-tail-to-page-{current_page}-head"
                result[previous_page] = {
                    **result[previous_page],
                    "continues_to_page": current_page,
                    "logical_paragraph_id": identity,
                    "continuity_confidence": "strong",
                    "cross_page_provenance": decision.evidences,
                }
                result[current_page] = {
                    **result[current_page],
                    "continues_from_page": previous_page,
                    "logical_paragraph_id": identity,
                    "continuity_confidence": "strong",
                    "cross_page_provenance": decision.evidences,
                }
        else:
            # Fallback for synthetic/mock pages without physical line structures
            previous_text = prev_data.get("text", "").strip()
            current_text = curr_data.get("text", "").strip()
            if not previous_text or not current_text:
                continue

            previous_tail = previous_text.split("\n\n")[-1].strip()
            current_head = current_text.split("\n\n")[0].strip()
            if not previous_tail or not current_head:
                continue
            if current_head.startswith(("#", ">", "- ", "* ")) or _starts_list(current_head):
                continue
            if previous_tail.startswith(("#", ">", "- ", "* ")) or _starts_list(previous_tail):
                continue
            if not _logical_continuation(previous_tail, current_head):
                continue

            identity = f"page-{previous_page}-tail-to-page-{current_page}-head"
            result[previous_page] = {
                **result[previous_page],
                "continues_to_page": current_page,
                "logical_paragraph_id": identity,
                "continuity_confidence": "strong",
            }
            result[current_page] = {
                **result[current_page],
                "continues_from_page": previous_page,
                "logical_paragraph_id": identity,
                "continuity_confidence": "strong",
            }

    return result
