"""Themis-Doc Boundary v2 - Canonical Paragraph Boundary Engine.

Decides paragraph boundary continuity (CONTINUA vs QUEBRA) using Candidate A (TabMLP)
trained on PDFium geometry, typography, and lexical features.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from statistics import median
from typing import Any, Literal

import numpy as np
import onnxruntime as ort

MODEL_PATH_DEFAULT = Path(__file__).resolve().parent / "models" / "candidate_a_tabmlp.onnx"
PUNCT_CHARS = [".", ":", "?", "!", ";", ",", "-", ")"]


@dataclass(frozen=True)
class LineGeom:
    text: str
    bbox: tuple[float, float, float, float]  # (x0, y0, x1, y1)
    font_size: float
    is_bold: bool
    is_italic: bool
    page_num: int = 1
    raw_line_id: int = 0

    @property
    def x_left(self) -> float:
        return self.bbox[0]

    @property
    def y_bottom(self) -> float:
        return self.bbox[1]

    @property
    def x_right(self) -> float:
        return self.bbox[2]

    @property
    def y_top(self) -> float:
        return self.bbox[3]

    @property
    def width(self) -> float:
        return max(0.0, self.bbox[2] - self.bbox[0])

    @property
    def height(self) -> float:
        return max(0.0, self.bbox[3] - self.bbox[1])


@dataclass
class AdjacentLinePair:
    """Pair of adjacent lines with layout and context attributes."""

    text_a: str
    text_b: str
    bbox_a: tuple[float, float, float, float]
    bbox_b: tuple[float, float, float, float]
    vertical_gap: float
    margins_indentation: dict[str, float]
    width_a: float
    width_b: float
    font_a: dict[str, Any]
    font_b: dict[str, Any]
    same_column: bool
    cross_page: bool = False
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class BoundaryDecision:
    """Decision output for a single boundary between adjacent lines."""

    decision: Literal["CONTINUA", "QUEBRA"]
    prob_continua: float = 0.0
    prob_quebra: float = 0.0
    is_low_confidence: bool = False
    geometry_vote: Literal["CONTINUA", "QUEBRA"] = "QUEBRA"
    language_vote: Literal["CONTINUA", "QUEBRA"] = "QUEBRA"
    is_conflict: bool = False
    evidences: dict[str, Any] = field(default_factory=dict)
    rule_summary: str = ""


def extract_32_features(
    r: dict[str, Any] | AdjacentLinePair,
    prev_line: str = "",
    next_line: str = "",
    page_w: float = 595.0,
    page_h: float = 842.0,
) -> np.ndarray:
    """Extract exactly the 32 normalized geometric + lexical features required by Candidate A."""
    feats = np.zeros(32, dtype=np.float32)

    if isinstance(r, AdjacentLinePair):
        fs_a = max(1.0, float(r.font_a.get("size") or 12.0))
        fs_b = max(1.0, float(r.font_b.get("size") or 12.0))
        pw = max(100.0, float(page_w or 595.0))
        ph = max(100.0, float(page_h or 842.0))
        bbox_a = r.bbox_a or (0, 0, 0, 0)
        bbox_b = r.bbox_b or (0, 0, 0, 0)
        y_gap = float(r.vertical_gap or 0.0)
        x_indent = float(r.margins_indentation.get("delta_left") or 0.0)
        is_bold_a = bool(r.font_a.get("is_bold"))
        is_bold_b = bool(r.font_b.get("is_bold"))
        is_italic_a = bool(r.font_a.get("is_italic"))
        is_italic_b = bool(r.font_b.get("is_italic"))
        cross_page = bool(r.cross_page)
        text_a = (r.text_a or "").strip()
        text_b = (r.text_b or "").strip()
        prev_t = (prev_line or "").strip()
        next_t = (next_line or "").strip()
    else:
        fs_a = max(1.0, float(r.get("font_size_a") or 12.0))
        fs_b = max(1.0, float(r.get("font_size_b") or 12.0))
        pw = max(100.0, float(r.get("page_w") or page_w or 595.0))
        ph = max(100.0, float(r.get("page_h") or page_h or 842.0))
        bbox_a = r.get("bbox_a") or (0, 0, 0, 0)
        bbox_b = r.get("bbox_b") or (0, 0, 0, 0)
        y_gap = float(r.get("y_gap") or 0.0)
        x_indent = float(r.get("x_indent") or 0.0)
        is_bold_a = bool(r.get("is_bold_a"))
        is_bold_b = bool(r.get("is_bold_b"))
        is_italic_a = bool(r.get("is_italic_a"))
        is_italic_b = bool(r.get("is_italic_b"))
        cross_page = bool(r.get("cross_page"))
        text_a = (r.get("line_a") or "").strip()
        text_b = (r.get("line_b") or "").strip()
        prev_t = (r.get("prev_line") or prev_line or "").strip()
        next_t = (r.get("next_line") or next_line or "").strip()

    # 1. Geometric normalized features (0..15)
    feats[0] = np.clip(y_gap / fs_a, -2.0, 6.0)
    feats[1] = np.clip(x_indent / fs_a, -10.0, 20.0)
    feats[2] = np.clip((pw - bbox_a[2]) / pw, 0.0, 1.0)
    feats[3] = np.clip((bbox_a[2] - bbox_a[0]) / pw, 0.0, 1.0)
    feats[4] = np.clip((bbox_b[2] - bbox_b[0]) / pw, 0.0, 1.0)
    feats[5] = np.clip(fs_a / 12.0, 0.3, 3.0)
    feats[6] = np.clip(fs_b / 12.0, 0.3, 3.0)
    feats[7] = np.clip(fs_b / fs_a, 0.2, 5.0)
    feats[8] = 1.0 if is_bold_a else 0.0
    feats[9] = 1.0 if is_bold_b else 0.0
    feats[10] = 1.0 if is_bold_a != is_bold_b else 0.0
    feats[11] = 1.0 if is_italic_a else 0.0
    feats[12] = 1.0 if is_italic_b else 0.0
    feats[13] = 1.0 if cross_page else 0.0
    feats[14] = np.clip(bbox_a[1] / ph, 0.0, 1.0)
    feats[15] = np.clip(bbox_b[1] / ph, 0.0, 1.0)

    # 2. Lexical dense features (16..31)
    feats[16] = min(1.0, len(text_a) / 100.0)
    feats[17] = min(1.0, len(text_b) / 100.0)
    feats[18] = min(1.0, len(prev_t) / 100.0)
    feats[19] = min(1.0, len(next_t) / 100.0)

    last_char_a = text_a[-1] if text_a else ""
    for idx, pc in enumerate(PUNCT_CHARS):
        if last_char_a == pc:
            feats[20 + idx] = 1.0

    first_char_b = text_b[0] if text_b else ""
    if first_char_b.isupper():
        feats[28] = 1.0
    elif first_char_b.islower():
        feats[29] = 1.0
    elif first_char_b.isdigit():
        feats[30] = 1.0
    elif first_char_b in ("-", "•", "*", "_", "–"):
        feats[31] = 1.0

    return feats


class ParagraphBoundaryEngine:
    """Canonical decider for paragraph boundaries using Themis-Doc Boundary v2 (Candidate A)."""

    _cached_session: ort.InferenceSession | None = None

    def __init__(self, model_path: Path | str | None = None, threshold: float = 0.50):
        if model_path is None:
            self.model_path = MODEL_PATH_DEFAULT
        else:
            self.model_path = Path(model_path)
        self.threshold = threshold

    @classmethod
    def get_session(cls, model_path: Path) -> ort.InferenceSession:
        if cls._cached_session is None:
            cls._cached_session = ort.InferenceSession(str(model_path), providers=["CPUExecutionProvider"])
        return cls._cached_session

    def evaluate_pair(
        self,
        pair: AdjacentLinePair,
        prev_line: str = "",
        next_line: str = "",
        page_w: float = 595.0,
        page_h: float = 842.0,
    ) -> BoundaryDecision:
        """Evaluate a single boundary pair using Candidate A."""
        sess = self.get_session(self.model_path)
        feat = extract_32_features(pair, prev_line=prev_line, next_line=next_line, page_w=page_w, page_h=page_h)
        feats = np.array([feat], dtype=np.float32)
        probs = sess.run(["boundary_prob"], {"geom_features": feats})[0][0]
        p_cont = float(probs[0])
        p_queb = float(probs[1])
        decision = "CONTINUA" if p_cont >= self.threshold else "QUEBRA"
        is_low_conf = (0.35 <= p_cont <= 0.65)
        evidences = {
            "prob_cont": p_cont,
            "prob_continua": p_cont,
            "prob_quebra": p_queb,
            "is_low_confidence": is_low_conf,
            "model": "candidate_a_tabmlp.onnx",
            "threshold": self.threshold,
            "cross_page": pair.cross_page,
        }
        rule_summary = f"ThemisBoundaryV2|P(CONT)={p_cont:.4f}|{decision}"
        return BoundaryDecision(
            decision=decision,
            prob_continua=p_cont,
            prob_quebra=p_queb,
            is_low_confidence=is_low_conf,
            geometry_vote=decision,
            language_vote=decision,
            is_conflict=False,
            evidences=evidences,
            rule_summary=rule_summary,
        )

    def segment_paragraphs(
        self,
        lines: list[Any],
        body_font_size: float = 12.0,
        boundary_trace: list[dict[str, Any]] | None = None,
        page_geometry: tuple[float, float] = (595.0, 842.0),
        page_num: int = 1,
    ) -> list[list[Any]]:
        """Cluster ordered lines into paragraph blocks purely using Candidate A."""
        if not lines:
            return []
        if len(lines) == 1:
            return [[lines[0]]]

        pw, ph = page_geometry

        # Ensure LineGeom representation for pair construction
        geoms = []
        for idx, l in enumerate(lines):
            if isinstance(l, LineGeom):
                geoms.append(l)
            else:
                geoms.append(LineGeom(
                    text=l.text,
                    bbox=tuple(l.bbox),
                    font_size=l.font_size,
                    is_bold=l.is_bold,
                    is_italic=getattr(l, "is_italic", False),
                    page_num=page_num,
                    raw_line_id=getattr(l, "raw_line_id", idx),
                ))

        pairs = build_adjacent_pairs_from_lines(geoms, page_num=page_num)
        if not pairs:
            return [[l] for l in lines]

        # Extract features batch with local context
        feat_list = []
        for idx, pair in enumerate(pairs):
            prev_t = geoms[idx - 1].text if idx > 0 else ""
            next_t = geoms[idx + 2].text if idx + 2 < len(geoms) else ""
            feat_list.append(extract_32_features(pair, prev_line=prev_t, next_line=next_t, page_w=pw, page_h=ph))

        sess = self.get_session(self.model_path)
        feats = np.array(feat_list, dtype=np.float32)
        probs_all = sess.run(["boundary_prob"], {"geom_features": feats})[0]

        # Assemble paragraph blocks
        paragraphs: list[list[Any]] = [[lines[0]]]
        for idx, (curr_line, probs) in enumerate(zip(lines[1:], probs_all)):
            p_cont = float(probs[0])
            p_queb = float(probs[1])
            dec = "CONTINUA" if p_cont >= self.threshold else "QUEBRA"
            is_low_conf = (0.35 <= p_cont <= 0.65)

            if boundary_trace is not None:
                prev_line = lines[idx]
                prev_id = getattr(prev_line, "raw_line_id", idx)
                curr_id = getattr(curr_line, "raw_line_id", idx + 1)
                boundary_trace.append({
                    "boundary_id": f"p{prev_id}-{curr_id}",
                    "producer_stage": "themis_doc_boundary_v2",
                    "rule_id": "THEMIS_DOC_BOUNDARY_V2",
                    "previous_source_line_id": prev_id,
                    "next_source_line_id": curr_id,
                    "decision": "BREAK" if dec == "QUEBRA" else "CONTINUE",
                    "model_decision": dec,
                    "prob_continua": p_cont,
                    "prob_quebra": p_queb,
                    "is_low_confidence": is_low_conf,
                    "hard": False,
                    "metrics": {
                        "prob_cont": p_cont,
                        "prob_quebra": p_queb,
                        "is_low_confidence": is_low_conf,
                    },
                })

            if dec == "QUEBRA":
                paragraphs.append([curr_line])
            else:
                paragraphs[-1].append(curr_line)

        return paragraphs

    def evaluate_cross_page(
        self,
        last_line_prev: Any,
        first_line_next: Any,
        prev_line: str = "",
        next_line: str = "",
        page_geometry: tuple[float, float] = (595.0, 842.0),
        page_prev: int = 1,
        page_next: int = 2,
    ) -> BoundaryDecision:
        """Evaluate cross-page boundary using Candidate A."""
        pw, ph = page_geometry

        def _to_line_geom(l: Any, p_num: int) -> LineGeom:
            if isinstance(l, LineGeom):
                return l
            if isinstance(l, dict):
                return LineGeom(
                    text=l.get("text", ""),
                    bbox=tuple(l.get("bbox", (0, 0, 0, 0))),
                    font_size=float(l.get("font_size", 12.0)),
                    is_bold=bool(l.get("is_bold")),
                    is_italic=bool(l.get("is_italic")),
                    page_num=p_num,
                    raw_line_id=int(l.get("raw_line_id", 0)),
                )
            return LineGeom(
                text=getattr(l, "text", ""),
                bbox=tuple(getattr(l, "bbox", (0, 0, 0, 0))),
                font_size=float(getattr(l, "font_size", 12.0)),
                is_bold=bool(getattr(l, "is_bold", False)),
                is_italic=bool(getattr(l, "is_italic", False)),
                page_num=p_num,
                raw_line_id=int(getattr(l, "raw_line_id", 0)),
            )

        geom_a = _to_line_geom(last_line_prev, page_prev)
        geom_b = _to_line_geom(first_line_next, page_next)
        cp_pair = build_cross_page_pair(geom_a, geom_b, page_prev, page_next)
        return self.evaluate_pair(cp_pair, prev_line=prev_line, next_line=next_line, page_w=pw, page_h=ph)


def build_adjacent_pairs_from_lines(
    lines: list[LineGeom],
    page_num: int = 1,
) -> list[AdjacentLinePair]:
    """Construct AdjacentLinePair instances for every consecutive pair of lines on a page."""
    if len(lines) < 2:
        return []

    # Compute median line-to-line leading
    leadings: list[float] = []
    for prev, curr in zip(lines, lines[1:]):
        delta = prev.y_bottom - curr.y_bottom
        if 4.0 <= delta <= 40.0:
            leadings.append(delta)
    median_leading = float(median(leadings)) if leadings else 14.0

    # Column boundary estimate from page lines
    lefts = [l.x_left for l in lines]
    rights = [l.x_right for l in lines]
    column_left = float(median(lefts)) if lefts else 50.0
    column_right = float(median(rights)) if rights else column_left + 400.0
    column_width = max(10.0, column_right - column_left)

    pairs: list[AdjacentLinePair] = []

    for prev, curr in zip(lines, lines[1:]):
        v_gap = prev.y_bottom - curr.y_top
        width_a = prev.width
        width_b = curr.width

        # Column compatibility
        h_overlap = min(prev.x_right, curr.x_right) - max(prev.x_left, curr.x_left)
        same_col = (h_overlap > 0 and abs(prev.x_left - curr.x_left) < 180.0)

        margins_indent = {
            "median_leading": median_leading,
            "column_left": column_left,
            "column_right": column_right,
            "column_width": column_width,
            "left_a": prev.x_left,
            "left_b": curr.x_left,
            "delta_left": curr.x_left - prev.x_left,
            "indent_b": curr.x_left - column_left,
            "right_margin_a": column_right - prev.x_right,
            "fill_ratio_a": width_a / column_width,
            "fill_ratio_b": width_b / column_width,
        }

        font_a = {
            "size": prev.font_size,
            "is_bold": prev.is_bold,
            "is_italic": prev.is_italic,
        }
        font_b = {
            "size": curr.font_size,
            "is_bold": curr.is_bold,
            "is_italic": curr.is_italic,
        }

        pair = AdjacentLinePair(
            text_a=prev.text,
            text_b=curr.text,
            bbox_a=prev.bbox,
            bbox_b=curr.bbox,
            vertical_gap=v_gap,
            margins_indentation=margins_indent,
            width_a=width_a,
            width_b=width_b,
            font_a=font_a,
            font_b=font_b,
            same_column=same_col,
            cross_page=False,
            metadata={
                "page_a": page_num,
                "page_b": page_num,
                "line_id_a": prev.raw_line_id,
                "line_id_b": curr.raw_line_id,
            },
        )
        pairs.append(pair)

    return pairs


def build_cross_page_pair(
    last_line_prev: LineGeom,
    first_line_next: LineGeom,
    page_prev: int,
    page_next: int,
) -> AdjacentLinePair:
    """Construct AdjacentLinePair for lines on the boundary between two consecutive pages."""
    width_a = last_line_prev.width
    width_b = first_line_next.width

    ref_col_width = 450.0
    fill_ratio_a = min(1.0, width_a / ref_col_width)
    fill_ratio_b = min(1.0, width_b / ref_col_width)

    margins_indent = {
        "median_leading": 12.0,
        "column_left": 50.0,
        "column_right": 500.0,
        "column_width": ref_col_width,
        "left_a": last_line_prev.x_left,
        "left_b": first_line_next.x_left,
        "delta_left": first_line_next.x_left - last_line_prev.x_left,
        "indent_b": max(0.0, first_line_next.x_left - 50.0),
        "right_margin_a": max(0.0, 500.0 - last_line_prev.x_right),
        "fill_ratio_a": fill_ratio_a,
        "fill_ratio_b": fill_ratio_b,
    }

    font_a = {
        "size": last_line_prev.font_size,
        "is_bold": last_line_prev.is_bold,
        "is_italic": last_line_prev.is_italic,
    }
    font_b = {
        "size": first_line_next.font_size,
        "is_bold": first_line_next.is_bold,
        "is_italic": first_line_next.is_italic,
    }

    return AdjacentLinePair(
        text_a=last_line_prev.text,
        text_b=first_line_next.text,
        bbox_a=last_line_prev.bbox,
        bbox_b=first_line_next.bbox,
        vertical_gap=0.0,
        margins_indentation=margins_indent,
        width_a=width_a,
        width_b=width_b,
        font_a=font_a,
        font_b=font_b,
        same_column=True,
        cross_page=True,
        metadata={
            "page_a": page_prev,
            "page_b": page_next,
            "line_id_a": last_line_prev.raw_line_id,
            "line_id_b": first_line_next.raw_line_id,
        },
    )


def assemble_experimental_paragraphs(
    lines: list[LineGeom],
    decisions: list[BoundaryDecision],
) -> list[list[LineGeom]]:
    """Assemble logical paragraphs purely from sequence of BoundaryDecision decisions."""
    if not lines:
        return []
    if len(lines) == 1:
        return [[lines[0]]]

    paragraphs: list[list[LineGeom]] = [[lines[0]]]

    for curr_line, dec in zip(lines[1:], decisions):
        if dec.decision == "QUEBRA":
            paragraphs.append([curr_line])
        else:
            paragraphs[-1].append(curr_line)

    return paragraphs
