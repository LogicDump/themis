"""Leitura dos Autos diretamente do snapshot process-centric v2."""
from __future__ import annotations
import sqlite3
from typing import Any

def get_autos_ondemand(db: sqlite3.Connection, process_id: str, offset: int = 0, limit: int | None = None) -> dict[str, Any] | None:
    snapshot = db.execute("SELECT snapshot_id FROM docket_snapshots WHERE process_id=? ORDER BY created_at DESC LIMIT 1", (process_id,)).fetchone()
    if not snapshot:
        return None
    rows = db.execute(
        """SELECT p.page_number,p.content,p.quality,d.document_id
        FROM docket_documents dd JOIN documents d ON d.document_id=dd.document_id
        JOIN pages p ON p.document_id=d.document_id
        WHERE dd.snapshot_id=? ORDER BY dd.ordinal,p.page_number""",
        (snapshot["snapshot_id"],),
    ).fetchall()
    rows = rows[offset: offset + limit if limit is not None else None]
    pages = [{"page": row["page_number"], "text": row["content"], "content": row["content"], "quality": row["quality"], "document_id": row["document_id"]} for row in rows]
    return {"process_id": process_id, "snapshot_id": snapshot["snapshot_id"], "pages": pages, "markdown": "\n\n".join(page["content"] for page in pages), "status": "ready"}
