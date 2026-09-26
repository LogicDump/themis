"""Deterministic FolioResolver for resolving process_folio from physical PDF page evidence.
Extracts anchors, rejects foreign citations, discovers monotonic offset segments,
and propagates folios with high confidence without hallucinating synthetic pages.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class FolioResolution(str, Enum):
    EXPLICIT = "EXPLICIT"
    INFERRED_HIGH = "INFERRED_HIGH"
    AMBIGUOUS = "AMBIGUOUS"
    UNKNOWN = "UNKNOWN"


@dataclass
class FolioCandidate:
    folio: int
    source: str = "unknown"
    is_stamp: bool = False
    process_id_match: bool = False
    raw_context: str = ""
    confidence: float = 1.0


@dataclass
class PageFolioInput:
    pdf_page: int
    text: str = ""
    candidates: list[FolioCandidate] = field(default_factory=list)
    process_id: str | None = None


@dataclass
class PageFolioResult:
    pdf_page: int
    process_folio: int | None
    resolution: FolioResolution
    evidence: dict[str, Any] = field(default_factory=dict)


@dataclass
class FolioGap:
    after_folio: int
    before_folio: int
    first_absent_folio: int
    last_absent_folio: int
    reason: str = "UNKNOWN"


@dataclass
class FolioSegment:
    start_pdf_page: int
    end_pdf_page: int
    start_folio: int
    end_folio: int
    offset: int  # folio - pdf_page
    anchors: list[int] = field(default_factory=list)


@dataclass
class FolioResolutionResult:
    pages: list[PageFolioResult]
    folio_gaps: list[FolioGap]
    segments: list[FolioSegment]
    total_pages: int
    explicit_count: int
    inferred_high_count: int
    ambiguous_count: int
    unknown_count: int


class FolioResolver:
    """Deterministic resolver that establishes process_folio from physical page evidence."""

    def __init__(self, target_process_id: str | None = None) -> None:
        self.target_process_id = target_process_id

    def extract_candidates_from_text(self, text: str, pdf_page: int, process_id: str | None = None) -> list[FolioCandidate]:
        """Extract candidate folio numbers and classify whether they are authentic stamps or body citations."""
        candidates: list[FolioCandidate] = []
        if not text or not text.strip():
            return candidates

        pid = process_id or self.target_process_id
        pid_clean = pid.replace("-", "").replace(".", "") if pid else None

        # 1. Authentic court stamps in footer/margins
        # Matches: "protocolado em ... e código ... fls. 11", "liberado nos autos em ... fls. 11", "processo 1000045-... fls. 11"
        stamp_pattern = re.compile(
            r"(?:protocolado\s+em|liberado\s+nos\s+autos\s+em|processo\s+\d{7}-\d{2}\.\d{4}\.\d\.\d{2}\.\d{4}|código\s+[A-Za-z0-9]+).*?fls\.\s*(\d+)",
            re.IGNORECASE | re.DOTALL,
        )

        # Check for explicit process CNJ in the stamp
        proc_explicit_pattern = re.compile(
            r"(?:protocolado\s+em|liberado\s+nos\s+autos\s+em|informe\s+o\s+processo).*?(?:" + re.escape(pid_clean or "") + r").*?fls\.\s*(\d+)" if pid_clean else r"$^",
            re.IGNORECASE | re.DOTALL,
        )

        for match in stamp_pattern.finditer(text):
            folio_val = int(match.group(1))
            ctx = match.group(0)
            
            # Check if stamp contains a different CNJ process number
            cnj_mentions = re.findall(r"\d{7}-\d{2}\.\d{4}\.\d\.\d{2}\.\d{4}", ctx)
            is_different_proc = False
            if pid_clean and cnj_mentions:
                is_different_proc = any(c.replace("-", "").replace(".", "") != pid_clean for c in cnj_mentions)

            is_proc_explicit = bool(proc_explicit_pattern.search(text)) if pid_clean else True
            candidates.append(FolioCandidate(
                folio=folio_val,
                source="court_stamp",
                is_stamp=True,
                process_id_match=not is_different_proc,
                raw_context=ctx[-100:],
                confidence=1.0 if is_proc_explicit else 0.8,
            ))

        # 2. Check trailing line / footer "fls. N"
        tail = text[-350:] if len(text) > 350 else text
        tail_matches = re.findall(r"fls\.\s*(\d+)", tail, re.IGNORECASE)
        if tail_matches:
            tail_val = int(tail_matches[-1])
            if not any(c.folio == tail_val for c in candidates):
                candidates.append(FolioCandidate(
                    folio=tail_val,
                    source="page_tail",
                    is_stamp=True,
                    process_id_match=True,
                    raw_context=tail[-100:],
                    confidence=0.9,
                ))

        # 3. Body text mentions (e.g. "conforme fls. 332", "decisão de fls. 205")
        body_pattern = re.compile(r"(?:fls?\.?|folhas?)\s*(\d+)", re.IGNORECASE)
        for match in body_pattern.finditer(text):
            folio_val = int(match.group(1))
            if not any(c.folio == folio_val for c in candidates):
                start = max(0, match.start() - 40)
                end = min(len(text), match.end() + 40)
                candidates.append(FolioCandidate(
                    folio=folio_val,
                    source="body_citation",
                    is_stamp=False,
                    process_id_match=False,
                    raw_context=text[start:end].strip(),
                    confidence=0.2,
                ))

        return candidates

    def resolve(self, pages_input: list[PageFolioInput]) -> FolioResolutionResult:
        """Resolve process_folio across a sequence of physical pages."""
        if not pages_input:
            return FolioResolutionResult(
                pages=[],
                folio_gaps=[],
                segments=[],
                total_pages=0,
                explicit_count=0,
                inferred_high_count=0,
                ambiguous_count=0,
                unknown_count=0,
            )

        sorted_inputs = sorted(pages_input, key=lambda p: p.pdf_page)

        page_anchors: dict[int, int] = {}
        explicit_pages: set[int] = set()
        page_candidates_map: dict[int, list[FolioCandidate]] = {}

        for p_in in sorted_inputs:
            candidates = p_in.candidates if p_in.candidates else self.extract_candidates_from_text(p_in.text, p_in.pdf_page, p_in.process_id)
            page_candidates_map[p_in.pdf_page] = candidates

            # Identify strong authentic stamps
            strong_stamps = [c for c in candidates if c.is_stamp and c.process_id_match]
            if strong_stamps:
                unique_folios = {c.folio for c in strong_stamps}
                if len(unique_folios) == 1:
                    folio_val = strong_stamps[0].folio
                    page_anchors[p_in.pdf_page] = folio_val
                    # Mark explicit if strong high confidence
                    if any(c.confidence >= 0.95 for c in strong_stamps):
                        explicit_pages.add(p_in.pdf_page)

        # Segment discovery based on monotonic anchor offset constancy
        anchor_pages = sorted(page_anchors.keys())
        segments: list[FolioSegment] = []

        if anchor_pages:
            current_anchors = [anchor_pages[0]]
            current_offset = page_anchors[anchor_pages[0]] - anchor_pages[0]

            for next_page in anchor_pages[1:]:
                next_folio = page_anchors[next_page]
                next_offset = next_folio - next_page

                # Check if anchor continues the monotonic sequence
                if next_offset == current_offset and next_folio > page_anchors[current_anchors[-1]]:
                    current_anchors.append(next_page)
                else:
                    # Breakpoint detected
                    start_p = current_anchors[0]
                    end_p = current_anchors[-1]
                    segments.append(FolioSegment(
                        start_pdf_page=start_p,
                        end_pdf_page=end_p,
                        start_folio=page_anchors[start_p],
                        end_folio=page_anchors[end_p],
                        offset=current_offset,
                        anchors=list(current_anchors),
                    ))
                    current_anchors = [next_page]
                    current_offset = next_offset

            # Close final segment
            start_p = current_anchors[0]
            end_p = current_anchors[-1]
            segments.append(FolioSegment(
                start_pdf_page=start_p,
                end_pdf_page=end_p,
                start_folio=page_anchors[start_p],
                end_folio=page_anchors[end_p],
                offset=current_offset,
                anchors=list(current_anchors),
            ))

        # Boundary expansion
        expanded_segments: list[FolioSegment] = []
        if segments:
            for idx, seg in enumerate(segments):
                seg_start = 1 if idx == 0 else segments[idx - 1].end_pdf_page + 1
                seg_end = sorted_inputs[-1].pdf_page if idx == len(segments) - 1 else seg.end_pdf_page

                start_folio = seg_start + seg.offset
                end_folio = seg_end + seg.offset

                expanded_segments.append(FolioSegment(
                    start_pdf_page=seg_start,
                    end_pdf_page=seg_end,
                    start_folio=start_folio,
                    end_folio=end_folio,
                    offset=seg.offset,
                    anchors=seg.anchors,
                ))

        # Detect gaps
        gaps: list[FolioGap] = []
        for idx in range(len(expanded_segments) - 1):
            curr_seg = expanded_segments[idx]
            next_seg = expanded_segments[idx + 1]

            if next_seg.start_folio > curr_seg.end_folio + 1:
                first_absent = curr_seg.end_folio + 1
                last_absent = next_seg.start_folio - 1
                gaps.append(FolioGap(
                    after_folio=curr_seg.end_folio,
                    before_folio=next_seg.start_folio,
                    first_absent_folio=first_absent,
                    last_absent_folio=last_absent,
                    reason="UNKNOWN",
                ))

        results: list[PageFolioResult] = []
        explicit_count = 0
        inferred_high_count = 0
        ambiguous_count = 0
        unknown_count = 0

        for p_in in sorted_inputs:
            p_num = p_in.pdf_page
            candidates = page_candidates_map.get(p_num, [])

            matching_seg = next(
                (s for s in expanded_segments if s.start_pdf_page <= p_num <= s.end_pdf_page),
                None,
            )

            if matching_seg:
                computed_folio = p_num + matching_seg.offset

                if p_num in explicit_pages or (p_num in page_anchors and not p_in.text):
                    res = FolioResolution.EXPLICIT
                    explicit_count += 1
                    evidence = {
                        "anchor_folio": page_anchors.get(p_num, computed_folio),
                        "segment_offset": matching_seg.offset,
                        "source": "authentic_stamp",
                    }
                elif p_num in page_anchors:
                    res = FolioResolution.EXPLICIT
                    explicit_count += 1
                    evidence = {
                        "anchor_folio": page_anchors[p_num],
                        "segment_offset": matching_seg.offset,
                        "source": "authentic_stamp",
                    }
                else:
                    res = FolioResolution.INFERRED_HIGH
                    inferred_high_count += 1
                    evidence = {
                        "inferred_from_segment": (matching_seg.start_pdf_page, matching_seg.end_pdf_page),
                        "segment_offset": matching_seg.offset,
                        "anchors_in_segment": len(matching_seg.anchors),
                    }

                rejected_citations = [c.folio for c in candidates if c.folio != computed_folio]
                if rejected_citations:
                    evidence["rejected_foreign_citations"] = rejected_citations

                results.append(PageFolioResult(
                    pdf_page=p_num,
                    process_folio=computed_folio,
                    resolution=res,
                    evidence=evidence,
                ))
            else:
                stamps = [c for c in candidates if c.is_stamp]
                if len(stamps) > 1:
                    ambiguous_count += 1
                    results.append(PageFolioResult(
                        pdf_page=p_num,
                        process_folio=None,
                        resolution=FolioResolution.AMBIGUOUS,
                        evidence={"conflicting_candidates": [c.folio for c in candidates]},
                    ))
                else:
                    unknown_count += 1
                    results.append(PageFolioResult(
                        pdf_page=p_num,
                        process_folio=None,
                        resolution=FolioResolution.UNKNOWN,
                        evidence={"reason": "no_supporting_anchors"},
                    ))

        return FolioResolutionResult(
            pages=results,
            folio_gaps=gaps,
            segments=expanded_segments,
            total_pages=len(results),
            explicit_count=explicit_count,
            inferred_high_count=inferred_high_count,
            ambiguous_count=ambiguous_count,
            unknown_count=unknown_count,
        )
