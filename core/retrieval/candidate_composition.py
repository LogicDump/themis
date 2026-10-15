"""Compose documentary evidence without comparing incompatible retrieval scores."""
from __future__ import annotations

import re
from collections.abc import Sequence
from typing import Any

_DATE = re.compile(r"\b\d{1,2}[/.-]\d{1,2}[/.-]\d{4}\b")


def compose_candidates(
    hierarchical: list[dict[str, Any]], direct: list[dict[str, Any]], top_k: int,
    *, owners: dict[str, dict[str, Any]] | None = None,
    query: str = "", routed_pages: Sequence[dict[str, Any]] = (),
    summaries: Sequence[dict[str, Any]] = (), process_id: str = "",
) -> list[dict[str, Any]]:
    """Fuse equal rank votes, then diversify by documentary movement.

    Original scores belong to different spaces and are retained, never compared.
    A dated Markdown heading can disappear from passage selection. For temporal
    queries, recover that already-routed page only when a CURRENT summary routes
    to the same literal date. Summaries never supply the returned evidence.
    """
    if top_k <= 0:
        return []
    owners = owners or {}
    hierarchy = list(hierarchical)
    if re.search(r"\b(data|quando|dia|hora|horário|horario)\b", query.casefold()):
        summary_dates = {
            row["movement_id"]: set(_DATE.findall(row.get("summary_text") or ""))
            for row in summaries
        }
        recovered = []
        represented = {row["page_id"] for row in hierarchy}
        for page in routed_pages:
            if page["page_id"] in represented:
                continue
            text = page.get("content") or ""
            heading_dates = set(_DATE.findall("\n".join(
                line for line in text.splitlines() if re.match(r"^\s{0,3}#{1,6}\s", line)
            )))
            if not heading_dates & summary_dates.get(page["movement_id"], set()):
                continue
            sref = {"process_id": process_id, "document_id": page["document_id"],
                    "pdf_page": page["page_number"], "process_folio": page["process_folio"]}
            recovered.append({
                "page_id": page["page_id"], "source_ref": sref, "excerpt": text,
                "movement_id": page["movement_id"], "movement_sequence": page["sequence"],
                "movement_title": page["title"], "evidence": [],
                "autos_navigation": {"process_id": process_id, "document_id": page["document_id"],
                    "page": page["page_number"], "folio": page["process_folio"],
                    "target_text": text[:200], "autos_path": f"/processes/{process_id}/autos"},
            })
            represented.add(page["page_id"])
        # Explicit values confirmed in both route and document precede passages
        # that may contain only a related event. Both retrieval strategies still
        # receive the same fusion weight below.
        hierarchy = recovered + hierarchy

    candidates: dict[str, dict[str, Any]] = {}
    votes: dict[str, float] = {}
    for stream in (hierarchy, direct):
        seen: set[str] = set()
        for hit in stream:
            key = hit["page_id"]
            if key in seen or not (hit.get("excerpt") or "").strip():
                continue
            seen.add(key)
            votes[key] = votes.get(key, 0.0) + 1.0 / (60 + len(seen))
            # A complete hierarchical passage replaces a truncated page prefix.
            # This chooses the representation, not the retrieval strategy rank.
            if key not in candidates:
                candidates[key] = dict(hit)
            owner = owners.get(key)
            if owner and not candidates[key].get("movement_id"):
                candidates[key].update(owner)

    selected: list[dict[str, Any]] = []
    groups: dict[str, int] = {}
    while candidates and len(selected) < top_k:
        def group(key: str) -> str:
            row = candidates[key]
            return str(row.get("movement_id") or row.get("source_ref", {}).get("document_id") or key)

        key = min(candidates, key=lambda key: (
            -votes[key] / (1 + groups.get(group(key), 0)), key,
        ))
        selected_group = group(key)
        item = candidates.pop(key)
        item.update(source_id=len(selected) + 1, composition_score=round(votes[key], 8))
        item.setdefault("score", item["composition_score"])
        selected.append(item)
        groups[selected_group] = groups.get(selected_group, 0) + 1
    return selected
