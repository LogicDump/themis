"""Projeção unificada de leitura (Read Model) de LegalEvent.

Este módulo implementa a projeção somente-leitura dos eventos jurídicos a partir
das tabelas de domínio canônicas existentes (deadlines, hearings, pending_items),
sem criar ou duplicar persistência no SQLite.

Conforme auditoria do Core:
- DEADLINE -> projetado a partir de 'deadlines'
- HEARING  -> projetado a partir de 'hearings' (+ 'hearing_participants')
- PENDING  -> projetado a partir de 'pending_items'
- PUBLICATION -> projetado de publications; usa published_on quando conhecido e,
                 caso contrário, available_on como data operacional explicitamente identificada.

O Core retorna estritamente dados de domínio limpos, sem propriedades visuais
(como tone, codicon, dot_class ou formatações de interface).
"""
from __future__ import annotations

import json
import re
import sqlite3
import unicodedata
from datetime import datetime
from pathlib import Path
from typing import Any

from core.runtime_paths import index_db_path
from core.documentos.legal_deadline_rules_v1 import get_catalog

SUPPORTED_KINDS = {"DEADLINE", "HEARING", "PENDING", "PUBLICATION"}

KIND_ALIASES = {
    "DEADLINE": "DEADLINE",
    "DEADLINES": "DEADLINE",
    "PRAZO": "DEADLINE",
    "PRAZOS": "DEADLINE",
    "HEARING": "HEARING",
    "HEARINGS": "HEARING",
    "AUDIENCIA": "HEARING",
    "AUDIENCIAS": "HEARING",
    "PENDING": "PENDING",
    "PENDING_ITEMS": "PENDING",
    "PENDENCIA": "PENDING",
    "PENDENCIAS": "PENDING",
    "PUBLICATION": "PUBLICATION",
    "PUBLICATIONS": "PUBLICATION",
    "PUBLICACAO": "PUBLICATION",
    "PUBLICACOES": "PUBLICATION",
}


def _json_or_default(raw: Any, default: Any) -> Any:
    if raw is None or raw == "":
        return default
    if isinstance(raw, (dict, list)):
        return raw
    try:
        return json.loads(str(raw))
    except Exception:
        return default




def _pt_date(value: Any) -> str | None:
    text = str(value or "")[:10]
    if len(text) == 10 and text[4] == "-" and text[7] == "-":
        return f"{text[8:10]}/{text[5:7]}/{text[0:4]}"
    return None



def _canonical_party_role_label(raw_role: Any, base_role: str | None = None) -> str:
    value = _norm_match_text(raw_role).upper().replace(" ", "")
    mapping = {
        "EXEQTE": "Exequente",
        "EXEQUENTE": "Exequente",
        "EXECTDO": "Executado",
        "EXECUTADO": "Executado",
        "EXECUTADA": "Executada",
        "REQTE": "Requerente",
        "REQUERENTE": "Requerente",
        "REQDO": "Requerido",
        "REQUERIDO": "Requerido",
        "REQDA": "Requerida",
        "REQUERIDA": "Requerida",
        "AUTOR": "Autor",
        "AUTORA": "Autora",
        "REU": "Réu",
        "RE": "Ré",
    }
    if value in mapping:
        return mapping[value]
    return {
        "CLAIMANT": "Requerente",
        "RESPONDENT": "Requerido",
        "PUBLIC_PROSECUTOR": "Ministério Público",
    }.get(str(base_role or "").upper(), str(raw_role or "").strip() or "Parte")


def _deadline_recipient_label(
    db: sqlite3.Connection,
    *,
    process_id: str,
    recipient_role: str | None,
    participant_ids_json: Any = None,
) -> str | None:
    if recipient_role == "BOTH_PARTIES":
        return "Partes"
    ids = _json_or_default(participant_ids_json, [])
    participant_columns = (
        {str(row[1]) for row in db.execute("PRAGMA table_info(process_participants)").fetchall()}
        if _has_table(db, "process_participants")
        else set()
    )
    required_participant_columns = {"participant_id", "process_id", "display_name", "base_role"}
    entity_expr = "entity_id" if "entity_id" in participant_columns else "NULL AS entity_id"
    rows: list[sqlite3.Row] = []
    if required_participant_columns <= participant_columns:
        if isinstance(ids, list) and ids:
            placeholders = ",".join("?" for _ in ids)
            rows = db.execute(
                f"SELECT participant_id,{entity_expr},display_name,base_role FROM process_participants "
                f"WHERE process_id=? AND participant_id IN ({placeholders}) ORDER BY display_name",
                [process_id, *ids],
            ).fetchall()
        if not rows:
            base_role = {
                "PLAINTIFF": "CLAIMANT",
                "DEFENDANT": "RESPONDENT",
                "PUBLIC_PROSECUTOR": "PUBLIC_PROSECUTOR",
            }.get(str(recipient_role or "").upper())
            if base_role:
                rows = db.execute(
                    f"SELECT participant_id,{entity_expr},display_name,base_role FROM process_participants "
                    "WHERE process_id=? AND base_role=? ORDER BY display_name",
                    (process_id, base_role),
                ).fetchall()

    labels: list[str] = []
    for row in rows:
        raw_role = None
        if row["entity_id"] and _has_table(db, "party_relations"):
            rel = db.execute(
                """SELECT role_raw,role FROM party_relations
                   WHERE owner_type='PROCESS' AND owner_id=? AND entity_id=?
                     AND upper(role) NOT LIKE 'ADVOG%'
                   ORDER BY party_relation_id LIMIT 1""",
                (process_id, row["entity_id"]),
            ).fetchone()
            if rel:
                raw_role = rel["role_raw"] or rel["role"]
        role_label = _canonical_party_role_label(raw_role, row["base_role"])
        labels.append(f"{row['display_name']} — {role_label}")
    if labels:
        return "; ".join(labels)

    # Compatibility fallback for stale participant projections. Structured
    # provider cover facts are enough to identify a canonical claimant or
    # respondent even when process_participants has not yet been rematerialized.
    # Do not use this path for UNRESOLVED/"parte contrária": ambiguity must stay
    # explicit until the obligation resolver identifies the actual recipient.
    wanted = str(recipient_role or "").upper()
    role_values = {
        "PLAINTIFF": {"REQTE", "REQUERENTE", "AUTOR", "AUTORA", "EXEQTE", "EXEQUENTE", "CLAIMANT"},
        "DEFENDANT": {"REQDO", "REQDA", "REQUERIDO", "REQUERIDA", "REU", "RE", "EXECTDO", "EXECUTADO", "EXECUTADA", "RESPONDENT"},
    }.get(wanted)
    if role_values and _has_table(db, "party_relations") and _has_table(db, "legal_entities"):
        fallback_rows = db.execute(
            """SELECT le.display_name,pr.role_raw,pr.role
               FROM party_relations pr
               JOIN legal_entities le USING(entity_id)
               WHERE pr.owner_type='PROCESS' AND pr.owner_id=?
                 AND upper(pr.role) NOT LIKE 'ADVOG%'
               ORDER BY le.display_name,pr.party_relation_id""",
            (process_id,),
        ).fetchall()
        fallback_labels: list[str] = []
        seen_names: set[str] = set()
        for relation in fallback_rows:
            normalized_role = _norm_match_text(relation["role_raw"] or relation["role"]).upper().replace(" ", "")
            if normalized_role not in role_values:
                continue
            name = str(relation["display_name"] or "").strip()
            if not name or name.casefold() in seen_names:
                continue
            seen_names.add(name.casefold())
            fallback_labels.append(
                f"{name} — {_canonical_party_role_label(relation['role_raw'] or relation['role'])}"
            )
        if fallback_labels:
            return "; ".join(fallback_labels)
    return None


def _deadline_display_details(db: sqlite3.Connection, row: sqlite3.Row, provenance: dict[str, Any]) -> dict[str, Any]:
    calc = provenance.get("calculation_provenance") or {}
    epistemics = calc.get("communication_date_epistemics") or {}
    obligation_prov = provenance.get("obligation_provenance") or {}
    pipeline = obligation_prov.get("deadline_resolution_pipeline") or {}
    specialist = pipeline.get("specialist") or {}
    resolution = pipeline.get("rule_resolution") or {}

    recipient_label = None
    calculation_marker = provenance.get("deadline_calculation") or {}
    obligation_id = calculation_marker.get("obligation_id")
    if obligation_id and _has_table(db, "deadline_obligations"):
        obligation_row = db.execute(
            "SELECT process_id,recipient_role,recipient_participant_ids_json FROM deadline_obligations WHERE obligation_id=?",
            (obligation_id,),
        ).fetchone()
        if obligation_row:
            recipient_label = _deadline_recipient_label(
                db,
                process_id=str(obligation_row["process_id"]),
                recipient_role=obligation_row["recipient_role"],
                participant_ids_json=obligation_row["recipient_participant_ids_json"],
            )

    available_on = ((epistemics.get("available_on") or {}).get("value"))
    published_on = ((epistemics.get("published_on") or {}).get("value"))
    counting_start = ((epistemics.get("counting_start") or {}).get("value"))
    origin_event_id = calc.get("communication_event_id") or row["triggering_event"]

    origin_date = None
    source_event_id = obligation_prov.get("source_event_id")
    if source_event_id and _has_table(db, "process_events"):
        event_row = db.execute(
            "SELECT event_date FROM process_events WHERE event_id=?",
            (source_event_id,),
        ).fetchone()
        if event_row:
            origin_date = event_row["event_date"]

    origin_autos_target = None
    origin_folio = None
    origin_refs = ((obligation_prov.get("source_refs") or {}).get("origin") or {})
    origin_pages = origin_refs.get("pages") or []
    if origin_pages:
        first_page = origin_pages[0] or {}
        if first_page.get("document_id"):
            origin_autos_target = {
                "process_id": row["owner_id"] if row["owner_type"] == "PROCESS" else None,
                "document_id": first_page.get("document_id"),
                "pdf_page": first_page.get("page_number"),
            }
            if _has_table(db, "pages"):
                page_row = db.execute(
                    "SELECT process_folio FROM pages WHERE document_id=? AND page_number=? LIMIT 1",
                    (first_page.get("document_id"), first_page.get("page_number")),
                ).fetchone()
                if page_row and page_row["process_folio"]:
                    origin_folio = str(page_row["process_folio"])
                    origin_autos_target["process_folio"] = origin_folio

    communication_refs = calc.get("communication_source_refs") or []
    origin_publication_id = None
    for ref in communication_refs:
        if str(ref.get("source_entity") or "").upper() == "PUBLICATION" and ref.get("source_id"):
            origin_publication_id = f"publication:{ref['source_id']}"
            break

    term_data = _json_or_default(row["term"], {})
    value = term_data.get("value")
    unit = str(term_data.get("unit") or "")
    counting_policy = str(term_data.get("counting_policy_id") or "")
    if isinstance(value, int):
        if unit == "DAYS" and counting_policy == "CPC_BUSINESS_DAYS":
            term_label = f"{value} dias úteis"
        elif unit == "DAYS":
            term_label = f"{value} dias"
        elif unit == "HOURS":
            term_label = f"{value} horas"
        elif unit == "MONTHS":
            term_label = f"{value} meses"
        else:
            term_label = str(value)
    else:
        term_label = None

    deadline_type_labels = {
        "JUDICIAL_ORDER": "Prazo judicial",
        "STATUTORY": "Prazo legal",
    }
    deadline_type_label = deadline_type_labels.get(str(row["deadline_type"] or ""), "Prazo processual")

    legal_parts: list[str] = []
    rule_basis = resolution.get("legal_basis") or {}
    article = rule_basis.get("article")
    statute = rule_basis.get("statute")
    if article and statute:
        statute_label = "CPC" if "13.105/2015" in str(statute) else str(statute)
        legal_parts.append(f"Prazo fixado pelo juízo com fundamento no art. {article} do {statute_label}.")
    if counting_policy == "CPC_BUSINESS_DAYS":
        legal_parts.append("Contagem em dias úteis, conforme arts. 219 e 224 do CPC.")
    if available_on:
        legal_parts.append("Publicação e início da contagem pelo regime do DJEN (Lei 11.419/2006, art. 4º, §§ 3º e 4º).")

    origin_label = None
    if available_on:
        origin_label = f"Intimação DJEN — disponibilizada em {_pt_date(available_on)}"
    elif origin_date:
        origin_label = f"Ato judicial de {_pt_date(origin_date)}"

    counted_days: list[str] = []
    excluded_days: list[str] = []
    calculation_ref = provenance.get("deadline_calculation") or {}
    calculation_id = calculation_ref.get("calculation_id")
    if calculation_id and _has_table(db, "deadline_calculations"):
        calc_row = db.execute(
            "SELECT calculation_json FROM deadline_calculations WHERE calculation_id=?",
            (calculation_id,),
        ).fetchone()
        calc_json = _json_or_default(calc_row["calculation_json"], {}) if calc_row else {}
        for step in calc_json.get("calculation_trace") or []:
            if step.get("action") == "COUNTED" and step.get("date"):
                ordinal = step.get("ordinal")
                label = _pt_date(step.get("date")) or str(step.get("date"))
                counted_days.append(f"{label} ({ordinal}º)" if ordinal else label)
            elif step.get("action") == "EXCLUDED" and step.get("date"):
                label = _pt_date(step.get("date")) or str(step.get("date"))
                reason = str(step.get("reason") or "")
                reason_labels = {
                    "HOLIDAY": "não útil",
                    "SUSPENDED": "suspensão",
                    "RECESS": "recesso",
                    "COMMUNICATION_START_RULE": "regra de início",
                }
                reason_label = reason_labels.get(reason, reason.lower().replace("_", " ") if reason else "")
                excluded_days.append(f"{label} ({reason_label})" if reason_label else label)

    return {
        "deadline_type_label": deadline_type_label,
        "term_label": term_label,
        "origin_label": origin_label,
        "origin_event_id": origin_event_id,
        "origin_act_date": origin_date,
        "origin_act_date_label": _pt_date(origin_date),
        "origin_folio": origin_folio,
        "origin_autos_target": origin_autos_target,
        "origin_publication_id": origin_publication_id,
        "determination": specialist.get("action_text") or row["description"],
        "available_on": available_on,
        "available_on_label": _pt_date(available_on),
        "published_on": published_on,
        "published_on_label": _pt_date(published_on),
        "counting_start": counting_start,
        "counting_start_label": _pt_date(counting_start),
        "due_date_label": _pt_date(row["due_at"]),
        "counted_days_label": ", ".join(counted_days) or None,
        "excluded_days_label": ", ".join(excluded_days) or None,
        "legal_basis_label": " ".join(legal_parts) or None,
        "recipient_label": recipient_label,
    }


def _legal_deadline_title(value: Any) -> str:
    title = str(value or "").strip()
    title = re.sub(r"\s+(?:\W+\s*)?polo\s+(?:ativo|passivo)\s*$", "", title, flags=re.IGNORECASE)
    return title or "Vencimento processual"


def _deadline_term_label(value: Any, unit: Any, rule: dict[str, Any] | None = None) -> str | None:
    effective_value = value
    effective_unit = str(unit or "")
    if effective_value is None and rule:
        effective_value = rule.get("term_value", rule.get("default_term_value"))
        effective_unit = str(rule.get("term_unit") or effective_unit)
    if not isinstance(effective_value, int) or effective_value <= 0:
        return None
    counting_policy = str((rule or {}).get("counting_policy_id") or "")
    if effective_unit == "BUSINESS_DAYS" or counting_policy.endswith("BUSINESS_DAYS"):
        return f"{effective_value} dias úteis"
    if effective_unit in {"DAYS", "CONTINUOUS_DAYS"}:
        return f"{effective_value} dias"
    if effective_unit == "HOURS":
        return f"{effective_value} horas"
    if effective_unit == "MONTHS":
        return f"{effective_value} meses"
    return str(effective_value)


def _pending_deadline_title(obligation: dict[str, Any], rule: dict[str, Any]) -> str:
    rule_id = str(obligation.get("resolved_rule_id") or "")
    if rule_id == "CPC_ART_1023_P2_EMBARGOS_RESPONSE":
        return "Manifestação sobre embargos de declaração"
    labels = {
        "CONTESTATION": "Contestação",
        "REPLY_PRELIMINARY": "Réplica à contestação",
        "REPLY_NEW_FACT": "Manifestação sobre fatos novos",
        "DOCUMENT_RESPONSE": "Manifestação sobre documentos",
    }
    procedural = [
        item for item in rule.get("procedural_act_types", rule.get("applicable_act_types", []))
        if item != "*"
    ]
    if procedural and procedural[0] in labels:
        return labels[procedural[0]]
    source_label = str(
        obligation.get("origin_event_title")
        or obligation.get("origin_event_subtype")
        or ""
    ).strip()
    source_label = re.sub(r"\s*\(pag(?:s)?\.?[^)]*\)\.pdf\s*$", "", source_label, flags=re.IGNORECASE)
    source_label = re.sub(r"\.pdf\s*$", "", source_label, flags=re.IGNORECASE)
    return source_label or "Pendência"


def _pending_deadline_status(reason_code: str | None, review_required: Any) -> str:
    labels = {
        "MEASURE_EFFECTIVENESS_TRIGGER_NOT_CONFIRMED": "Aguardando efetivação da medida",
        "HEARING_TRIGGER_NOT_CONFIRMED": "Aguardando audiência",
        "CALENDAR_COVERAGE_MISSING": "Calendário pendente de validação",
        "COMMUNICATION_TRIGGER_MISSING": "Aguardando publicação/intimação",
        "RESOLVED_RULE_MISSING": "Regra jurídica pendente de resolução",
    }
    if reason_code in labels:
        return labels[reason_code]
    if bool(review_required):
        return "Revisão jurídica necessária"
    return "Aguardando publicação/intimação"


def _norm_match_text(value: Any) -> str:
    text = unicodedata.normalize("NFKD", str(value or ""))
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    return re.sub(r"\s+", " ", text).strip().casefold()


def _document_piece_type_map(db: sqlite3.Connection) -> dict[str, str]:
    result: dict[str, str] = {}
    if not _has_table(db, "movements"):
        return result
    for row in db.execute("SELECT payload_json FROM movements").fetchall():
        try:
            payload = json.loads(row["payload_json"] or "{}")
        except (TypeError, ValueError):
            continue
        for component in payload.get("components") or ():
            if not isinstance(component, dict) or not component.get("document_id"):
                continue
            label = component.get("piece_type") or component.get("artifact_type")
            if label:
                result[str(component["document_id"])] = str(label)
    return result


def _piece_priority(label: str | None) -> int:
    normalized = _norm_match_text(label)
    if "certidao de publicacao" in normalized:
        return 0
    if "certidao" in normalized:
        return 1
    if "ato ordinatorio" in normalized or "comunicacao" in normalized:
        return 2
    if "despacho" in normalized or "decisao" in normalized or "sentenca" in normalized:
        return 3
    return 9


def _originating_act_priority(label: str | None) -> int:
    normalized = _norm_match_text(label)
    if "ato ordinatorio" in normalized:
        return 0
    if "despacho" in normalized or "decisao" in normalized or "sentenca" in normalized:
        return 1
    if "comunicacao" in normalized:
        return 2
    if "certidao" in normalized:
        return 5
    return 9


def _hearing_autos_target(
    scheduled_at: str | None,
    hearing_type: str | None,
    page_rows: list[sqlite3.Row],
    document_types: dict[str, str],
    *,
    process_id: str,
) -> dict[str, Any] | None:
    if not scheduled_at:
        return None
    iso = str(scheduled_at)[:10]
    if len(iso) != 10:
        return None
    human = f"{iso[8:10]}/{iso[5:7]}/{iso[0:4]}"
    hearing_token = _norm_match_text(hearing_type or "audiencia")
    candidates: list[tuple[int, int, sqlite3.Row]] = []
    for page in page_rows:
        text = _norm_match_text(page["content"])
        if human not in text:
            continue
        if hearing_token and hearing_token not in text and "audiencia" not in text and "concilia" not in text:
            continue
        label = _norm_match_text(document_types.get(str(page["document_id"])))
        if "certidao de publicacao" in label:
            priority = 2
        elif "certidao" in label:
            priority = 0
        elif "ato ordinatorio" in label or "comunicacao" in label:
            priority = 1
        else:
            priority = 3
        candidates.append((priority, int(page["process_folio"] or 10**9), page))
    if not candidates:
        return None
    candidates.sort(key=lambda item: (item[0], item[1], item[2]["page_number"]))
    page = candidates[0][2]
    return {
        "process_id": process_id,
        "document_id": page["document_id"],
        "pdf_page": page["page_number"],
        "process_folio": str(page["process_folio"]) if page["process_folio"] is not None else None,
    }


def _parse_document_date(value: Any) -> datetime | None:
    text = str(value or "").strip()
    if not text:
        return None
    for fmt in (
        "%d/%m/%Y %H:%M",
        "%d/%m/%Y",
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%d",
    ):
        try:
            return datetime.strptime(text[:19] if "%S" in fmt else text, fmt)
        except ValueError:
            continue
    try:
        return datetime.fromisoformat(text.replace("Z", "+00:00")).replace(tzinfo=None)
    except ValueError:
        return None


def _publication_temporal_rank(
    publication_date: str | None,
    occurred_at: str | None,
) -> tuple[int, int]:
    published = _parse_document_date(publication_date)
    occurred = _parse_document_date(occurred_at)
    if published is None or occurred is None:
        return (2, 10**9)
    delta = (published.date() - occurred.date()).days
    if delta >= 0:
        return (0, delta)
    return (1, abs(delta))


def _publication_autos_target(
    publication_text: str | None,
    page_rows: list[sqlite3.Row],
    document_types: dict[str, str],
    *,
    process_id: str,
    communication_number: str | None = None,
    publication_date: str | None = None,
    document_dates: dict[str, str] | None = None,
    anchor_text: str | None = None,
    prefer_originating_act: bool = False,
) -> dict[str, Any] | None:
    document_dates = document_dates or {}

    def candidate_key(page: sqlite3.Row) -> tuple[int, int, int, int, int]:
        temporal_bucket, temporal_distance = _publication_temporal_rank(
            publication_date,
            document_dates.get(str(page["document_id"])),
        )
        piece_label = document_types.get(str(page["document_id"]))
        piece_priority = (
            _originating_act_priority(piece_label)
            if prefer_originating_act
            else _piece_priority(piece_label)
        )
        return (
            temporal_bucket,
            temporal_distance,
            piece_priority,
            int(page["process_folio"] or 10**9),
            page["page_number"],
        )

    normalized_anchor = _norm_match_text(anchor_text)
    if len(normalized_anchor) >= 20:
        anchored = [
            page for page in page_rows
            if normalized_anchor in _norm_match_text(page["content"])
        ]
        if anchored:
            near = [
                page for page in anchored
                if _publication_temporal_rank(
                    publication_date,
                    document_dates.get(str(page["document_id"])),
                )[0] == 0
                and _publication_temporal_rank(
                    publication_date,
                    document_dates.get(str(page["document_id"])),
                )[1] <= 30
            ]
            anchored = near or anchored
            anchored.sort(key=candidate_key)
            page = anchored[0]
            return {
                "process_id": process_id,
                "document_id": page["document_id"],
                "pdf_page": page["page_number"],
                "process_folio": str(page["process_folio"]) if page["process_folio"] is not None else None,
            }

    if communication_number:
        exact = [page for page in page_rows if str(communication_number) in str(page["content"] or "")]
        if exact:
            exact.sort(key=candidate_key)
            page = exact[0]
            return {
                "process_id": process_id,
                "document_id": page["document_id"],
                "pdf_page": page["page_number"],
                "process_folio": str(page["process_folio"]) if page["process_folio"] is not None else None,
            }

    normalized = _norm_match_text(publication_text)
    if len(normalized) < 40:
        return None
    chunks = [
        chunk.strip()
        for chunk in re.split(r"[.;]", normalized)
        if len(chunk.strip()) >= 35
    ]
    # Do not keep only the longest chunks: DJEN headers and process metadata
    # are often longer than the operative sentence itself. Keeping all
    # meaningful chunks lets the actual order/intimation match the originating
    # act, after which temporal gating removes stale historical repetitions.
    probes = chunks or [normalized[:160]]

    scored: list[tuple[int, sqlite3.Row]] = []
    for page in page_rows:
        page_text = _norm_match_text(page["content"])
        if not page_text:
            continue
        score = 0
        for probe in probes:
            if probe[:140] and probe[:140] in page_text:
                score += 3
            elif len(probe) >= 80 and probe[:80] in page_text:
                score += 2
            elif len(probe) >= 55 and probe[:55] in page_text:
                score += 1
        if score:
            scored.append((score, page))

    if not scored:
        return None

    # If at least one textual match belongs to an act shortly before the
    # publication, ignore undated/remote historical matches. This prevents
    # repeated boilerplate from jumping to an old folio merely because that
    # page has more overlapping publication text.
    temporally_near: list[tuple[int, sqlite3.Row]] = []
    for item in scored:
        bucket, distance = _publication_temporal_rank(
            publication_date,
            document_dates.get(str(item[1]["document_id"])),
        )
        if bucket == 0 and distance <= 30:
            temporally_near.append(item)
    candidates = temporally_near or scored

    candidates.sort(
        key=lambda item: (
            -item[0],
            (
                _originating_act_priority(document_types.get(str(item[1]["document_id"])))
                if prefer_originating_act
                else _piece_priority(document_types.get(str(item[1]["document_id"])))
            ),
            *_publication_temporal_rank(
                publication_date,
                document_dates.get(str(item[1]["document_id"])),
            ),
            int(item[1]["process_folio"] or 10**9),
            item[1]["page_number"],
        )
    )
    best_score = candidates[0][0]
    if best_score < 3:
        return None
    page = candidates[0][1]
    return {
        "process_id": process_id,
        "document_id": page["document_id"],
        "pdf_page": page["page_number"],
        "process_folio": str(page["process_folio"]) if page["process_folio"] is not None else None,
    }

def _has_table(db: sqlite3.Connection, table_name: str) -> bool:
    row = db.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?",
        (table_name,),
    ).fetchone()
    return row is not None


class LegalEventProjection:
    """Projeção de leitura que agrega eventos de múltiplas entidades canônicas."""

    @classmethod
    def _ensure_row_factory(cls, db: sqlite3.Connection) -> None:
        if db.row_factory is None:
            db.row_factory = sqlite3.Row

    @classmethod
    def project_deadlines(
        cls,
        db: sqlite3.Connection,
        *,
        process_id: str | None = None,
    ) -> list[dict[str, Any]]:
        cls._ensure_row_factory(db)
        if not _has_table(db, "deadlines"):
            return []

        query = """
            SELECT
                deadline_id,
                owner_type,
                owner_id,
                title,
                description,
                deadline_type,
                term,
                due_at,
                date_precision,
                timezone,
                status,
                priority,
                responsible,
                triggering_event,
                legal_basis,
                confidence,
                confirmation_status,
                source_refs_json,
                provenance_json,
                created_at,
                updated_at
            FROM deadlines
        """
        params: list[Any] = []
        if process_id:
            query += " WHERE owner_id=? OR (owner_type='PROCESS' AND owner_id=?)"
            params.extend([process_id, process_id])
        query += " ORDER BY due_at ASC, deadline_id ASC"

        rows = db.execute(query, params).fetchall()
        events: list[dict[str, Any]] = []
        document_types = _document_piece_type_map(db)
        document_dates: dict[str, str] = {}
        if _has_table(db, "movement_pieces") and _has_table(db, "movements"):
            for movement in db.execute(
                """SELECT mp.document_id,m.occurred_at
                   FROM movement_pieces mp
                   JOIN movements m ON m.movement_id=mp.movement_id
                   WHERE mp.document_id IS NOT NULL AND m.occurred_at IS NOT NULL"""
            ).fetchall():
                document_id = str(movement["document_id"])
                occurred_at = str(movement["occurred_at"])
                previous = document_dates.get(document_id)
                if previous is None:
                    document_dates[document_id] = occurred_at
                else:
                    previous_date = _parse_document_date(previous)
                    current_date = _parse_document_date(occurred_at)
                    if current_date and (previous_date is None or current_date > previous_date):
                        document_dates[document_id] = occurred_at

        page_rows_by_process: dict[str, list[sqlite3.Row]] = {}
        if _has_table(db, "pages"):
            page_query = "SELECT p.document_id,p.page_number,p.process_folio,p.content,d.process_id FROM pages p JOIN documents d ON d.document_id=p.document_id"
            for page in db.execute(page_query).fetchall():
                page_rows_by_process.setdefault(str(page["process_id"]), []).append(page)

        for r in rows:
            due_at = r["due_at"]
            date_str = str(due_at)[:10] if due_at else None
            provenance = _json_or_default(r["provenance_json"], {})
            display_details = _deadline_display_details(db, r, provenance)
            if not display_details.get("origin_autos_target") and display_details.get("origin_publication_id"):
                publication_id = str(display_details["origin_publication_id"]).split("publication:", 1)[-1]
                pub_row = db.execute(
                    "SELECT full_text,provenance_json,process_id,available_on,published_on FROM publications WHERE publication_id=?",
                    (publication_id,),
                ).fetchone()
                if pub_row:
                    pub_provenance = _json_or_default(pub_row["provenance_json"], {})
                    raw_item = pub_provenance.get("raw_item") or {}
                    communication_number = raw_item.get("numeroComunicacao") or raw_item.get("numero_comunicacao")
                    display_details["origin_autos_target"] = _publication_autos_target(
                        pub_row["full_text"],
                        page_rows_by_process.get(str(pub_row["process_id"]), []),
                        document_types,
                        process_id=str(pub_row["process_id"]),
                        communication_number=str(communication_number) if communication_number else None,
                        publication_date=pub_row["available_on"] or pub_row["published_on"],
                        document_dates=document_dates,
                        anchor_text=r["description"],
                        prefer_originating_act=True,
                    )
                    target = display_details.get("origin_autos_target") or {}
                    if target.get("process_folio"):
                        display_details["origin_folio"] = target["process_folio"]
            events.append({
                "id": f"deadline:{r['deadline_id']}",
                "kind": "DEADLINE",
                "source_entity": "deadlines",
                "source_id": r["deadline_id"],
                "owner_type": r["owner_type"],
                "owner_id": r["owner_id"],
                "process_id": r["owner_id"] if r["owner_type"] == "PROCESS" else None,
                "title": _legal_deadline_title(r["title"]),
                "description": r["description"],
                "term": r["term"],
                "deadline_type": r["deadline_type"],
                "due_at": due_at,
                "relevant_at": due_at,
                "date": date_str,
                "date_precision": r["date_precision"],
                "timezone": r["timezone"],
                "status": r["status"],
                "priority": r["priority"],
                "responsible": r["responsible"],
                "triggering_event": r["triggering_event"],
                "legal_basis": r["legal_basis"],
                "confidence": r["confidence"],
                "confirmation_status": r["confirmation_status"],
                "source_refs": _json_or_default(r["source_refs_json"], []),
                "provenance": provenance,
                **display_details,
                "created_at": r["created_at"],
                "updated_at": r["updated_at"],
            })

        return events

    @classmethod
    def project_hearings(
        cls,
        db: sqlite3.Connection,
        *,
        process_id: str | None = None,
    ) -> list[dict[str, Any]]:
        cls._ensure_row_factory(db)
        if not _has_table(db, "hearings"):
            return []

        query = """
            SELECT
                hearing_id,
                process_id,
                hearing_type,
                scheduled_at,
                date_precision,
                location,
                meeting_info,
                status,
                outcome_notes,
                source_refs_json,
                provenance_json,
                created_at,
                updated_at
            FROM hearings
        """
        params: list[Any] = []
        if process_id:
            query += " WHERE process_id=?"
            params.append(process_id)
        query += " ORDER BY scheduled_at ASC, hearing_id ASC"

        rows = db.execute(query, params).fetchall()
        has_participants = _has_table(db, "hearing_participants")
        events: list[dict[str, Any]] = []
        document_types = _document_piece_type_map(db)
        page_rows_by_process: dict[str, list[sqlite3.Row]] = {}
        if _has_table(db, "pages"):
            page_query = "SELECT p.document_id,p.page_number,p.process_folio,p.content,d.process_id FROM pages p JOIN documents d ON d.document_id=p.document_id"
            for page in db.execute(page_query).fetchall():
                page_rows_by_process.setdefault(str(page["process_id"]), []).append(page)

        for r in rows:
            scheduled_at = r["scheduled_at"]
            date_str = str(scheduled_at)[:10] if scheduled_at else None
            h_type = r["hearing_type"] or "Audiência"
            h_id = r["hearing_id"]
            autos_target = _hearing_autos_target(
                scheduled_at,
                r["hearing_type"],
                page_rows_by_process.get(str(r["process_id"]), []),
                document_types,
                process_id=str(r["process_id"]),
            )

            participants = []
            if has_participants:
                p_rows = db.execute(
                    "SELECT participant, role FROM hearing_participants WHERE hearing_id=? ORDER BY participant",
                    (h_id,),
                ).fetchall()
                participants = [{"name": p["participant"], "role": p["role"]} for p in p_rows]

            events.append({
                "id": f"hearing:{h_id}",
                "kind": "HEARING",
                "source_entity": "hearings",
                "source_id": h_id,
                "owner_type": "PROCESS",
                "owner_id": r["process_id"],
                "process_id": r["process_id"],
                "title": f"Audiência ({h_type})" if r["hearing_type"] else "Audiência",
                "hearing_type": r["hearing_type"],
                "description": r["outcome_notes"],
                "scheduled_at": scheduled_at,
                "relevant_at": scheduled_at,
                "date": date_str,
                "date_precision": r["date_precision"],
                "location": r["location"],
                "meeting_info": r["meeting_info"],
                "status": r["status"],
                "outcome_notes": r["outcome_notes"],
                "participants": participants,
                "autos_target": autos_target,
                "source_refs": _json_or_default(r["source_refs_json"], []),
                "provenance": _json_or_default(r["provenance_json"], {}),
                "created_at": r["created_at"],
                "updated_at": r["updated_at"],
            })

        return events

    @classmethod
    def project_pending_deadline_obligations(
        cls,
        db: sqlite3.Connection,
        *,
        process_id: str | None = None,
    ) -> list[dict[str, Any]]:
        cls._ensure_row_factory(db)
        required = {
            "deadline_obligations",
            "deadline_instructions",
            "process_events",
            "deadline_calculations",
        }
        if not all(_has_table(db, table) for table in required):
            return []

        rules = {str(rule.get("rule_id") or ""): rule for rule in get_catalog()}
        query = """
            SELECT
                o.*,
                i.source_event_id,
                i.action_text AS instruction_action_text,
                i.recipient_text AS instruction_recipient_text,
                i.source_refs_json AS instruction_source_refs_json,
                e.event_date AS origin_event_date,
                e.event_time AS origin_event_time,
                e.date_precision AS origin_date_precision,
                e.title AS origin_event_title,
                e.event_subtype AS origin_event_subtype
            FROM deadline_obligations o
            JOIN deadline_instructions i
              ON i.instruction_id=o.originating_instruction_id
            LEFT JOIN process_events e
              ON e.event_id=i.source_event_id
            WHERE o.status='ACTIVE'
        """
        params: list[Any] = []
        if process_id:
            query += " AND o.process_id=?"
            params.append(process_id)
        query += " ORDER BY e.event_date,e.event_time,o.obligation_id"

        events: list[dict[str, Any]] = []
        for row in db.execute(query, params).fetchall():
            obligation = dict(row)
            latest = db.execute(
                """SELECT status,due_date,calculation_json,created_at
                   FROM deadline_calculations
                   WHERE process_id=? AND obligation_id=?
                   ORDER BY created_at DESC, calculation_id DESC
                   LIMIT 1""",
                (obligation["process_id"], obligation["obligation_id"]),
            ).fetchone()
            if latest and str(latest["status"] or "").upper() == "CALCULATED" and latest["due_date"]:
                continue

            calculation = _json_or_default(latest["calculation_json"], {}) if latest else {}
            reason = calculation.get("reason") or {}
            reason_code = reason.get("code") if isinstance(reason, dict) else None
            rule = rules.get(str(obligation.get("resolved_rule_id") or ""), {})
            term_label = _deadline_term_label(
                obligation.get("term_value"),
                obligation.get("term_unit"),
                rule,
            )
            status_label = _pending_deadline_status(reason_code, obligation.get("review_required"))

            source_refs = _json_or_default(obligation.get("source_refs_json"), {})
            if not source_refs:
                source_refs = _json_or_default(obligation.get("instruction_source_refs_json"), {})
            origin = source_refs.get("origin") if isinstance(source_refs, dict) else {}
            pages = (origin or {}).get("pages") or []
            autos_target = None
            if pages:
                first = pages[0] or {}
                document_id = first.get("document_id")
                pdf_page = first.get("page_number")
                if document_id:
                    autos_target = {
                        "process_id": obligation["process_id"],
                        "document_id": document_id,
                        "pdf_page": pdf_page,
                    }
                    if pdf_page and _has_table(db, "pages"):
                        page_row = db.execute(
                            """SELECT process_folio FROM pages
                               WHERE document_id=? AND page_number=? LIMIT 1""",
                            (document_id, pdf_page),
                        ).fetchone()
                        if page_row and page_row["process_folio"] is not None:
                            autos_target["process_folio"] = str(page_row["process_folio"])

            recipient_label = _deadline_recipient_label(
                db,
                process_id=str(obligation["process_id"]),
                recipient_role=obligation.get("recipient_role"),
                participant_ids_json=obligation.get("recipient_participant_ids_json"),
            )
            recipient_text = str(
                obligation.get("recipient_text")
                or obligation.get("instruction_recipient_text")
                or ""
            ).strip()
            if not recipient_label and recipient_text:
                recipient_label = (
                    f"{recipient_text} — destinatário a resolver"
                    if str(obligation.get("recipient_role") or "").upper() == "UNRESOLVED"
                    else recipient_text
                )

            event_date = obligation.get("origin_event_date")
            relevant_at = event_date
            legal_basis = rule.get("legal_basis") or {}
            article = legal_basis.get("article")
            paragraph = legal_basis.get("paragraph")
            legal_basis_label = None
            if article:
                try:
                    article_label = f"{int(str(article)):,}".replace(",", ".")
                except Exception:
                    article_label = str(article)
                legal_basis_label = f"CPC art. {article_label}"
                if paragraph:
                    legal_basis_label += f", {paragraph}"
                legal_basis_label += "."

            rule_id = str(obligation.get("resolved_rule_id") or "")
            description = str(obligation.get("instruction_action_text") or obligation.get("action_text") or "").strip()
            if rule_id == "CPC_ART_1023_P2_EMBARGOS_RESPONSE":
                description = "Manifeste-se a parte contrária sobre os embargos de declaração."

            events.append({
                "id": f"pending-obligation:{obligation['obligation_id']}",
                "kind": "PENDING",
                "pending_type": "DEADLINE_OBLIGATION",
                "source_entity": "deadline_obligations",
                "source_id": obligation["obligation_id"],
                "owner_type": "PROCESS",
                "owner_id": obligation["process_id"],
                "process_id": obligation["process_id"],
                "title": _pending_deadline_title(obligation, rule),
                "description": description,
                "due_at": None,
                "relevant_at": relevant_at,
                "date": event_date,
                "date_precision": obligation.get("origin_date_precision"),
                "status": status_label,
                "priority": "NORMAL",
                "responsible": None,
                "source_origin": obligation.get("origin_event_subtype"),
                "resolved_at": None,
                "source_refs": source_refs,
                "provenance": _json_or_default(obligation.get("provenance_json"), {}),
                "autos_target": autos_target,
                "origin_autos_target": autos_target,
                "origin_folio": autos_target.get("process_folio") if autos_target else None,
                "origin_event_id": obligation.get("source_event_id"),
                "origin_act_date": event_date,
                "origin_act_date_label": _pt_date(event_date),
                "term_label": term_label,
                "recipient_label": recipient_label,
                "legal_basis_label": legal_basis_label,
                "calculation_reason_code": reason_code,
                "review_required": bool(obligation.get("review_required")),
                "created_at": obligation.get("created_at"),
                "updated_at": obligation.get("updated_at"),
            })

        return events

    @classmethod
    def project_pending_items(
        cls,
        db: sqlite3.Connection,
        *,
        process_id: str | None = None,
    ) -> list[dict[str, Any]]:
        cls._ensure_row_factory(db)
        if not _has_table(db, "pending_items"):
            return []

        query = """
            SELECT
                pending_id,
                owner_type,
                owner_id,
                title,
                description,
                status,
                priority,
                responsible,
                due_at,
                source_origin,
                source_refs_json,
                provenance_json,
                resolved_at,
                created_at,
                updated_at
            FROM pending_items
        """
        params: list[Any] = []
        if process_id:
            query += " WHERE owner_id=? OR (owner_type='PROCESS' AND owner_id=?)"
            params.extend([process_id, process_id])
        query += " ORDER BY due_at ASC, pending_id ASC"

        rows = db.execute(query, params).fetchall()
        events: list[dict[str, Any]] = []

        for r in rows:
            due_at = r["due_at"]
            date_str = str(due_at)[:10] if due_at else None
            events.append({
                "id": f"pending:{r['pending_id']}",
                "kind": "PENDING",
                "source_entity": "pending_items",
                "source_id": r["pending_id"],
                "owner_type": r["owner_type"],
                "owner_id": r["owner_id"],
                "process_id": r["owner_id"] if r["owner_type"] == "PROCESS" else None,
                "title": r["title"],
                "description": r["description"],
                "due_at": due_at,
                "relevant_at": due_at,
                "date": date_str,
                "status": r["status"],
                "priority": r["priority"],
                "responsible": r["responsible"],
                "source_origin": r["source_origin"],
                "resolved_at": r["resolved_at"],
                "source_refs": _json_or_default(r["source_refs_json"], []),
                "provenance": _json_or_default(r["provenance_json"], {}),
                "created_at": r["created_at"],
                "updated_at": r["updated_at"],
            })

        return events

    @classmethod
    def project_publications(cls, db: sqlite3.Connection, *, process_id: str | None = None) -> list[dict[str, Any]]:
        cls._ensure_row_factory(db)
        if not _has_table(db, "publications"):
            return []
        query = "SELECT * FROM publications WHERE coalesce(published_on, available_on) IS NOT NULL"
        params: list[Any] = []
        if process_id:
            query += " AND process_id=?"
            params.append(process_id)
        query += " ORDER BY coalesce(published_on, available_on), publication_id"

        events: list[dict[str, Any]] = []
        document_types = _document_piece_type_map(db)
        page_rows_by_process: dict[str, list[sqlite3.Row]] = {}
        if _has_table(db, "pages"):
            page_query = "SELECT p.document_id,p.page_number,p.process_folio,p.content,d.process_id FROM pages p JOIN documents d ON d.document_id=p.document_id"
            for page in db.execute(page_query).fetchall():
                page_rows_by_process.setdefault(str(page["process_id"]), []).append(page)

        for r in db.execute(query, params).fetchall():
            published_on = r["published_on"]
            available_on = r["available_on"]
            relevant_at = published_on or available_on
            publication_type = str(r["publication_type"] or "").strip()
            publication_title = {
                "INTIMATION": "Intimação",
                "CITATION": "Citação",
                "NOTICE": "Notificação",
            }.get(publication_type.upper(), publication_type or "Publicação")
            provenance = _json_or_default(r["provenance_json"], {})
            raw_item = provenance.get("raw_item") or {}
            communication_number = raw_item.get("numeroComunicacao") or raw_item.get("numero_comunicacao")
            autos_target = _publication_autos_target(
                r["full_text"],
                page_rows_by_process.get(str(r["process_id"]), []),
                document_types,
                process_id=str(r["process_id"]),
                communication_number=str(communication_number) if communication_number else None,
            )
            events.append({
                "id": f"publication:{r['publication_id']}",
                "kind": "PUBLICATION",
                "source_entity": "publications",
                "source_id": r["publication_id"],
                "owner_type": "PROCESS",
                "owner_id": r["process_id"],
                "process_id": r["process_id"],
                "title": publication_title,
                "publication_type": publication_type or None,
                "description": r["full_text"],
                "published_at": published_on,
                "available_at": available_on,
                "date_basis": "PUBLISHED" if published_on else "AVAILABLE",
                "relevant_at": relevant_at,
                "date": relevant_at,
                "tribunal": r["tribunal"],
                "organ": r["organ"],
                "medium": r["medium"],
                "status": r["publication_status"],
                "active": None if r["active"] is None else bool(r["active"]),
                "canceled_on": r["canceled_on"],
                "cancellation_reason": r["cancellation_reason"],
                "recipients": _json_or_default(r["recipients_json"], []),
                "recipient_lawyers": _json_or_default(r["recipient_lawyers_json"], []),
                "source_url": r["source_url"],
                "autos_target": autos_target,
                "provenance": _json_or_default(r["provenance_json"], {}),
                "created_at": r["created_at"],
                "updated_at": r["updated_at"],
            })
        return events

    @classmethod
    def list_events(
        cls,
        db: sqlite3.Connection,
        *,
        process_id: str | None = None,
        kind: str | None = None,
        query: str | None = None,
    ) -> list[dict[str, Any]]:
        normalized_kind = None
        if kind:
            k_upper = str(kind).strip().upper()
            if k_upper and k_upper not in {"ALL", "TODOS"}:
                normalized_kind = KIND_ALIASES.get(k_upper)
                if not normalized_kind:
                    return []

        all_events: list[dict[str, Any]] = []

        if normalized_kind is None or normalized_kind == "DEADLINE":
            all_events.extend(cls.project_deadlines(db, process_id=process_id))

        if normalized_kind is None or normalized_kind == "HEARING":
            all_events.extend(cls.project_hearings(db, process_id=process_id))

        if normalized_kind is None or normalized_kind == "PENDING":
            all_events.extend(cls.project_pending_items(db, process_id=process_id))
            all_events.extend(cls.project_pending_deadline_obligations(db, process_id=process_id))

        if normalized_kind is None or normalized_kind == "PUBLICATION":
            all_events.extend(cls.project_publications(db, process_id=process_id))

        if query:
            q_lower = query.strip().lower()
            filtered: list[dict[str, Any]] = []
            for evt in all_events:
                title = str(evt.get("title") or "").lower()
                desc = str(evt.get("description") or "").lower()
                owner = str(evt.get("owner_id") or "").lower()
                extra = str(evt.get("legal_basis") or evt.get("location") or "").lower()
                if q_lower in title or q_lower in desc or q_lower in owner or q_lower in extra:
                    filtered.append(evt)
            all_events = filtered

        # Ordenação cronológica estável por relevant_at canônico (com chaves nulas ao final) e ID
        def _sort_key(item: dict[str, Any]) -> tuple[int, str, str]:
            t = item.get("relevant_at") or item.get("date") or ""
            return (0 if t else 1, t, item.get("id", ""))

        all_events.sort(key=_sort_key)
        return all_events

    @classmethod
    def get_event(
        cls,
        db: sqlite3.Connection,
        event_id: str,
    ) -> dict[str, Any] | None:
        if not event_id:
            return None

        clean_id = str(event_id).strip()

        if clean_id.startswith("deadline:"):
            raw_id = clean_id.split(":", 1)[1]
            for evt in cls.project_deadlines(db):
                if evt["source_id"] == raw_id or evt["id"] == clean_id:
                    return evt
            return None

        if clean_id.startswith("hearing:"):
            raw_id = clean_id.split(":", 1)[1]
            for evt in cls.project_hearings(db):
                if evt["source_id"] == raw_id or evt["id"] == clean_id:
                    return evt
            return None

        if clean_id.startswith("pending-obligation:"):
            raw_id = clean_id.split(":", 1)[1]
            for evt in cls.project_pending_deadline_obligations(db):
                if evt["source_id"] == raw_id or evt["id"] == clean_id:
                    return evt
            return None

        if clean_id.startswith("pending:"):
            raw_id = clean_id.split(":", 1)[1]
            for evt in cls.project_pending_items(db):
                if evt["source_id"] == raw_id or evt["id"] == clean_id:
                    return evt
            return None

        if clean_id.startswith("publication:"):
            raw_id = clean_id.split(":", 1)[1]
            return next((evt for evt in cls.project_publications(db) if evt["source_id"] == raw_id), None)

        # Busca irrestrita sem prefixo
        for evt in cls.list_events(db):
            if evt["id"] == clean_id or evt["source_id"] == clean_id:
                return evt

        return None


def list_events(
    *,
    process_id: str | None = None,
    kind: str | None = None,
    query: str | None = None,
    db_path: Path | str | None = None,
    db: sqlite3.Connection | None = None,
) -> list[dict[str, Any]]:
    """Função pública de conveniência para listar LegalEvents."""
    if db is not None:
        return LegalEventProjection.list_events(db, process_id=process_id, kind=kind, query=query)

    target = Path(db_path or index_db_path()).resolve()
    if not target.is_file():
        return []

    conn = sqlite3.connect(target.as_uri() + "?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    try:
        return LegalEventProjection.list_events(conn, process_id=process_id, kind=kind, query=query)
    finally:
        conn.close()


def get_event(
    event_id: str,
    *,
    db_path: Path | str | None = None,
    db: sqlite3.Connection | None = None,
) -> dict[str, Any] | None:
    """Função pública de conveniência para buscar um único LegalEvent pelo ID."""
    if db is not None:
        return LegalEventProjection.get_event(db, event_id)

    target = Path(db_path or index_db_path()).resolve()
    if not target.is_file():
        return None

    conn = sqlite3.connect(target.as_uri() + "?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    try:
        return LegalEventProjection.get_event(conn, event_id)
    finally:
        conn.close()
