"""V1 offline 2D merger for V0 table-region diagnostics.

The V0 model evidence is deliberately reused.  This layer only joins its
candidate fragments in physical page space; it neither reads textual content
for decisions nor writes to the canonical store.
"""
from __future__ import annotations

import argparse
import json
import sqlite3
import sys
from collections import Counter
from pathlib import Path

try:
    from core.runtime_paths import index_db_path
except ModuleNotFoundError:
    from runtime_paths import index_db_path
from typing import Any

import onnxruntime as ort

THEMIS_ROOT = Path(__file__).resolve().parents[1]
if str(THEMIS_ROOT) not in sys.path:
    sys.path.insert(0, str(THEMIS_ROOT))

from core import table_region_assembler_v0 as v0


VERTICAL_MERGE_PAGE_RATIO = 0.18
HORIZONTAL_GAP_PAGE_RATIO = 0.20


def _bbox_gap(a: list[float], b: list[float]) -> tuple[float, float, float]:
    """Return horizontal gap, vertical gap, and horizontal overlap in points."""
    h_gap = max(0.0, max(a[0], b[0]) - min(a[2], b[2]))
    v_gap = max(0.0, max(a[1], b[1]) - min(a[3], b[3]))
    h_overlap = max(0.0, min(a[2], b[2]) - max(a[0], b[0]))
    return h_gap, v_gap, h_overlap


def _union_bbox(regions: list[dict[str, Any]]) -> list[float]:
    boxes = [region["bbox"] for region in regions]
    return [
        round(min(box[0] for box in boxes), 2), round(min(box[1] for box in boxes), 2),
        round(max(box[2] for box in boxes), 2), round(max(box[3] for box in boxes), 2),
    ]


class _UnionFind:
    def __init__(self, size: int) -> None:
        self.parent = list(range(size))

    def find(self, value: int) -> int:
        while self.parent[value] != value:
            self.parent[value] = self.parent[self.parent[value]]
            value = self.parent[value]
        return value

    def union(self, left: int, right: int) -> None:
        left, right = self.find(left), self.find(right)
        if left != right:
            self.parent[right] = left


def _connection(
    a: dict[str, Any], b: dict[str, Any], page_width: float, page_height: float,
    vertical_merge_page_ratio: float = VERTICAL_MERGE_PAGE_RATIO,
) -> tuple[bool, dict[str, Any]]:
    h_gap, v_gap, h_overlap = _bbox_gap(a["bbox"], b["bbox"])
    a_width = max(1.0, a["bbox"][2] - a["bbox"][0])
    b_width = max(1.0, b["bbox"][2] - b["bbox"][0])
    overlap_ratio = h_overlap / min(a_width, b_width)
    same_row_band = v_gap <= max(8.0, page_height * 0.015)
    stacked_compatible = v_gap <= page_height * vertical_merge_page_ratio and overlap_ratio >= 0.20
    side_by_side_compatible = same_row_band and h_gap <= page_width * HORIZONTAL_GAP_PAGE_RATIO
    return (stacked_compatible or side_by_side_compatible), {
        "horizontal_gap": round(h_gap, 2),
        "vertical_gap": round(v_gap, 2),
        "horizontal_overlap_ratio": round(overlap_ratio, 3),
        "same_row_band": same_row_band,
        "reason": "stacked_shared_x" if stacked_compatible else ("same_row_horizontal_proximity" if side_by_side_compatible else "not_compatible"),
    }


def merge_page(page: dict[str, Any], *, vertical_merge_page_ratio: float = VERTICAL_MERGE_PAGE_RATIO) -> dict[str, Any]:
    fragments = page["candidate_regions"]
    page_width = float(page["page_geometry"]["width"])
    page_height = float(page["page_geometry"]["height"])
    union_find = _UnionFind(len(fragments))
    merge_events: list[dict[str, Any]] = []
    prevented_merges: list[dict[str, Any]] = []
    for left in range(len(fragments)):
        for right in range(left + 1, len(fragments)):
            connected, evidence = _connection(
                fragments[left], fragments[right], page_width, page_height,
                vertical_merge_page_ratio,
            )
            if connected:
                union_find.union(left, right)
                merge_events.append({"fragments": [left, right], **evidence})
            elif evidence["vertical_gap"] > page_height * vertical_merge_page_ratio and evidence["horizontal_overlap_ratio"] >= 0.20:
                # Explicitly retain the physical separation: this is what prevents
                # two independent pay stubs on one page from becoming one region.
                prevented_merges.append({"fragments": [left, right], "reason": "vertical_separation", **evidence})
    components: dict[int, list[dict[str, Any]]] = {}
    for index, fragment in enumerate(fragments):
        components.setdefault(union_find.find(index), []).append(fragment)

    regions: list[dict[str, Any]] = []
    rejected = list(page["rejected_activations"])
    for component in components.values():
        line_ids = sorted({line_id for fragment in component for line_id in fragment["line_ids"]})
        strong_parts = sum(fragment["confidence"] == "strong" for fragment in component)
        mean_probability = sum(fragment["geometry_evidence"]["mean_p_table"] for fragment in component) / len(component)
        if len(component) == 1 and component[0]["confidence"] != "strong":
            rejected.append({
                "line_ids": line_ids,
                "reason": "isolated_spatial_component",
                "evidence": {"mean_p_table": round(mean_probability, 5), "fragment_count": 1},
            })
            continue
        regions.append({
            "bbox": _union_bbox(component),
            "line_ids": line_ids,
            "confidence": "strong" if strong_parts or (len(component) >= 3 and mean_probability >= v0.STRONG_THRESHOLD) else "ambiguous",
            "fragment_count_v0": len(component),
            "mean_p_table": round(mean_probability, 5),
            "geometry_evidence": {
                "merge_basis": "2d_row_bands_x_alignment_local_gaps",
                "source_fragment_bboxes": [fragment["bbox"] for fragment in component],
                "source_row_bands": sum(fragment["geometry_evidence"]["row_band_count"] for fragment in component),
                "source_columnar_lines": sum(fragment["geometry_evidence"]["columnar_line_count"] for fragment in component),
            },
        })
    result = dict(page)
    result["v0_candidate_region_count"] = len(fragments)
    result["candidate_regions"] = sorted(regions, key=lambda item: (item["bbox"][1], item["bbox"][0]))
    result["rejected_activations"] = rejected
    result["spatial_merge_events"] = merge_events
    result["prevented_merges"] = prevented_merges
    return result


def analyze_process(db: sqlite3.Connection, process_id: str, session: ort.InferenceSession) -> dict[str, Any]:
    base = v0.analyze_process(db, process_id, session)
    pages = [merge_page(page) for page in base["pages"]]
    regions = [region for page in pages for region in page["candidate_regions"]]
    rejected = [item for page in pages for item in page["rejected_activations"]]
    merge_events = [event for page in pages for event in page["spatial_merge_events"]]
    prevented = [event for page in pages for event in page["prevented_merges"]]
    return {
        "process_id": process_id,
        "page_count": len(pages),
        "v0_candidate_region_count": base["candidate_region_count"],
        "candidate_region_count": len(regions),
        "pages_affected": sum(bool(page["candidate_regions"]) for page in pages),
        "region_confidence_counts": dict(Counter(region["confidence"] for region in regions)),
        "rejected_activation_count": len(rejected),
        "spatial_merge_count": len(merge_events),
        "prevented_merge_count": len(prevented),
        "samples": {
            "strong": [region for region in regions if region["confidence"] == "strong"][:3],
            "ambiguous": [region for region in regions if region["confidence"] == "ambiguous"][:3],
            "rejected": rejected[:3],
            "merges": merge_events[:3],
            "prevented_merges": prevented[:3],
        },
        "pages": pages,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--db", type=Path, default=index_db_path())
    parser.add_argument("--process", action="append", dest="processes", default=["1029994-43.2023.8.26.0554", "1000045-87.2026.8.26.0450"])
    parser.add_argument("--output", type=Path, default=Path("scratch/table_region_assembler_v1.json"))
    args = parser.parse_args()
    db = sqlite3.connect(args.db.resolve().as_uri() + "?mode=ro&immutable=1", uri=True)
    db.row_factory = sqlite3.Row
    session = ort.InferenceSession(str(v0.MODEL_PATH_DEFAULT), providers=["CPUExecutionProvider"])
    try:
        processes = [analyze_process(db, process_id, session) for process_id in args.processes]
    finally:
        db.close()
    output = {
        "prototype": "THEMIS-TABLE-REGION-ASSEMBLER-V1",
        "mode": "offline-read-only",
        "model": v0.MODEL_PATH_DEFAULT.name,
        "comparison_base": "THEMIS-TABLE-REGION-ASSEMBLER-V0",
        "spatial_thresholds": {"vertical_merge_page_ratio": VERTICAL_MERGE_PAGE_RATIO, "horizontal_gap_page_ratio": HORIZONTAL_GAP_PAGE_RATIO},
        "processes": processes,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")
    for process in processes:
        print(f"{process['process_id']}: V0 {process['v0_candidate_region_count']} -> V1 {process['candidate_region_count']} regiões em {process['pages_affected']} páginas")
    print(f"JSON: {args.output.resolve()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
