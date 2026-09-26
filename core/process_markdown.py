"""Portable, rebuildable Markdown projections for a Process Package."""
from __future__ import annotations

import hashlib
import json
import sqlite3
from pathlib import Path
from typing import Any


SCHEMA = "themis.process-markdown/v1"


def _frontmatter(metadata: dict[str, Any]) -> str:
    # JSON is a strict YAML 1.2 subset and avoids a runtime dependency.
    return "---\n" + json.dumps(metadata, ensure_ascii=False, indent=2) + "\n---\n\n"


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def generate_process_markdown(
    db: sqlite3.Connection,
    package: Path,
    process_id: str,
) -> list[dict[str, Any]]:
    """Materialize process, document and movement views from canonical rows."""
    output = package / "markdown"
    documents_dir = output / "documents"
    movements_dir = output / "movements"
    documents_dir.mkdir(parents=True, exist_ok=True)
    movements_dir.mkdir(parents=True, exist_ok=True)

    process = db.execute(
        "SELECT process_id,status FROM processes WHERE process_id=?", (process_id,)
    ).fetchone()
    if not process:
        raise ValueError(f"Processo ausente no process.db: {process_id}")
    metadata_row = db.execute(
        "SELECT classe,assunto,tribunal,comarca,unidade,grau,status,summary "
        "FROM process_metadata WHERE process_id=?",
        (process_id,),
    ).fetchone()
    metadata = dict(metadata_row) if metadata_row else {}
    tables = {row[0] for row in db.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    parties = []
    if {"party_relations", "legal_entities"}.issubset(tables):
        parties = [
            {"name": row[0], "role": row[1] or row[2]}
            for row in db.execute(
                "SELECT le.display_name,pr.role,pr.role_raw "
                "FROM party_relations pr JOIN legal_entities le USING(entity_id) "
                "WHERE pr.owner_type='PROCESS' AND pr.owner_id=? "
                "ORDER BY pr.role,le.display_name",
                (process_id,),
            )
        ]
    base = {
        "schema": SCHEMA,
        "cnj": process_id,
        "tribunal": metadata.get("tribunal"),
        "class": metadata.get("classe"),
        "subject": metadata.get("assunto"),
        "venue": metadata.get("comarca"),
        "unit": metadata.get("unidade"),
        "degree": metadata.get("grau"),
        "process_status": metadata.get("status") or process[1],
        "parties": parties,
    }

    docs = list(db.execute(
        "SELECT d.document_id,d.document_type,d.status,d.page_count,f.sha256 "
        "FROM documents d JOIN files f USING(file_id) "
        "WHERE d.process_id=? ORDER BY d.created_at,d.document_id",
        (process_id,),
    ))
    movements = list(db.execute(
        "SELECT movement_id,sequence,movement_type,title,actor,occurred_at,page_start,page_end "
        "FROM movements WHERE process_id=? ORDER BY sequence,movement_id",
        (process_id,),
    ))

    generated: list[Path] = []
    index = output / "index.md"
    index_text = _frontmatter({**base, "kind": "process-index"}) + f"# Processo {process_id}\n\n"
    if metadata.get("summary"):
        index_text += str(metadata["summary"]).strip() + "\n\n"
    index_text += "## Documentos\n\n"
    index_text += "\n".join(
        f"- [{doc['document_type'] or 'Documento'}](documents/{doc['document_id']}.md) — "
        f"`{doc['document_id']}` ({doc['page_count']} páginas)"
        for doc in docs
    )
    index_text += "\n\n## Movimentos\n\n"
    index_text += "\n".join(
        f"- [{movement['sequence']}. {movement['title'] or movement['movement_type'] or 'Movimento'}]"
        f"(movements/{movement['movement_id']}.md) — {movement['occurred_at'] or 'data não informada'}"
        for movement in movements
    ) + "\n"
    index.write_text(index_text, encoding="utf-8")
    generated.append(index)

    for doc in docs:
        document_id = doc["document_id"]
        source = {
            "document_id": document_id,
            "sha256": doc["sha256"],
            "path": f"fontes/objetos/{document_id}.pdf",
        }
        target = documents_dir / f"{document_id}.md"
        text = _frontmatter({
            **base,
            "kind": "document",
            "document_id": document_id,
            "document_type": doc["document_type"],
            "document_status": doc["status"],
            "page_count": doc["page_count"],
            "source": source,
        })
        text += f"# {doc['document_type'] or 'Documento'}\n\nDocumento `{document_id}`. Fonte SHA-256 `{doc['sha256']}`.\n\n"
        for page in db.execute(
            "SELECT page_number,content FROM pages WHERE document_id=? ORDER BY page_number",
            (document_id,),
        ):
            text += f"<a id=\"page-{page['page_number']}\"></a>\n\n### Página {page['page_number']}\n\n{page['content']}\n\n"
        target.write_text(text, encoding="utf-8")
        generated.append(target)

    for movement in movements:
        movement_id = movement["movement_id"]
        pieces = list(db.execute(
            "SELECT mp.document_id,mp.piece_order,mp.page_start,mp.page_end,d.document_type "
            "FROM movement_pieces mp LEFT JOIN documents d USING(document_id) "
            "WHERE mp.movement_id=? ORDER BY mp.piece_order",
            (movement_id,),
        ))
        summary = db.execute(
            "SELECT summary_text FROM movement_summaries WHERE movement_id=? "
            "ORDER BY summary_version DESC LIMIT 1",
            (movement_id,),
        ).fetchone()
        source_refs = [
            {"movement_id": movement_id, "document_id": piece["document_id"],
             "page_start": piece["page_start"], "page_end": piece["page_end"]}
            for piece in pieces
        ]
        target = movements_dir / f"{movement_id}.md"
        frontmatter = {
            **base,
            "kind": "movement",
            "movement_id": movement_id,
            "sequence": movement["sequence"],
            "movement_type": movement["movement_type"],
            "actor": movement["actor"],
            "occurred_at": movement["occurred_at"],
            "page_range": {"start": movement["page_start"], "end": movement["page_end"]},
            "source_refs": source_refs,
        }
        text = _frontmatter(frontmatter) + f"# {movement['title'] or movement['movement_type'] or 'Movimento'}\n\n"
        if summary:
            text += f"## Resumo\n\n{summary['summary_text']}\n\n"
        text += "## Peças\n\n" + "\n".join(
            f"- [{piece['document_type'] or 'Documento'}](../documents/{piece['document_id']}.md#page-{piece['page_start'] or 1}) "
            f"— `{piece['document_id']}`, páginas {piece['page_start'] or '?'}–{piece['page_end'] or '?'}"
            for piece in pieces
        ) + "\n"
        target.write_text(text, encoding="utf-8")
        generated.append(target)

    generated_set = set(generated)
    for stale in output.rglob("*.md"):
        if stale not in generated_set:
            stale.unlink()
    return [
        {
            "path": path.relative_to(package).as_posix(),
            "sha256": _sha256(path),
            "size_bytes": path.stat().st_size,
        }
        for path in generated
    ]
