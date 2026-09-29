"""Canonical persistence and operational projection for deadline calculations."""
from __future__ import annotations

import hashlib
import json
import re
import sqlite3
import uuid
from dataclasses import asdict, is_dataclass
from datetime import date, datetime, timezone
from typing import Any, Iterable, Mapping

from core.documentos.deadline_engine_v1 import (
    CommunicationFact,
    DeadlineCalculationInput,
    calculate_deadline,
)
from core.documentos.deadline_policies_v1 import (
    COMMUNICATION_POLICIES,
    COUNTING_POLICIES,
    REGIME_COUNTING_POLICY_IDS,
    SUSPENSION_POLICIES,
    CourtCalendar,
)
from core.documentos.legal_deadline_rules_v1 import get_catalog
from core.documentos.legal_context_v1 import LegalContext

MIGRATION_VERSION = "deadline-calculation-store-v1"
ID_NAMESPACE = uuid.UUID("da2c0972-82bc-4dab-94a0-c7d591244021")

SCHEMA = """
CREATE TABLE IF NOT EXISTS deadline_calculations(
  calculation_id TEXT PRIMARY KEY,
  process_id TEXT NOT NULL,
  obligation_id TEXT NOT NULL,
  communication_event_id TEXT,
  resolved_rule_id TEXT,
  rule_version TEXT,
  status TEXT NOT NULL CHECK(status IN ('CALCULATED','UNRESOLVED','REVIEW_REQUIRED')),
  due_date TEXT,
  trigger_date TEXT,
  counting_start_date TEXT,
  counting_policy_id TEXT,
  counting_policy_version TEXT,
  communication_policy_id TEXT,
  term_value INTEGER,
  term_unit TEXT,
  calculation_json TEXT NOT NULL,
  legal_basis_json TEXT NOT NULL DEFAULT '{}',
  provenance_json TEXT NOT NULL DEFAULT '{}',
  calendar_version TEXT,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL,
  UNIQUE(process_id, calculation_id),
  FOREIGN KEY(process_id, obligation_id)
    REFERENCES deadline_obligations(process_id, obligation_id) ON DELETE CASCADE,
  FOREIGN KEY(communication_event_id) REFERENCES process_events(event_id) ON DELETE SET NULL
);
CREATE INDEX IF NOT EXISTS idx_deadline_calculations_obligation
  ON deadline_calculations(process_id, obligation_id, updated_at);
CREATE INDEX IF NOT EXISTS idx_deadline_calculations_status_due
  ON deadline_calculations(process_id, status, due_date);
"""

_DAY = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def _now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), default=str)


def _value(value: Any) -> dict[str, Any]:
    if is_dataclass(value):
        return asdict(value)
    return dict(value or {})


def _digest(value: Mapping[str, Any]) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def calculation_identity(
    *, process_id: str, obligation_id: str, result: Mapping[str, Any]
) -> tuple[str, str]:
    """Return stable identity and canonical identity material for this input set."""
    provenance = result.get("provenance") or {}
    communication = provenance.get("communication") or {}
    policies = provenance.get("policies") or {}
    counting = policies.get("counting") or {}
    material = {
        "process_id": process_id,
        "obligation_id": obligation_id,
        "legal_domain": result.get("legal_domain"),
        "base_regime": result.get("base_regime"),
        "resolved_rule_id": result.get("resolved_rule_id"),
        "rule_version": result.get("rule_version"),
        "counting_policy_id": result.get("counting_policy_id"),
        "counting_policy_version": result.get("counting_policy_version"),
        "communication_policy_id": result.get("communication_policy_id"),
        "communication_policy_version": communication.get("version"),
        "communication_event_id": result.get("communication_event_id"),
        "term_value": result.get("term_value"),
        "term_unit": result.get("term_unit"),
        "trigger_date": result.get("trigger_date"),
        "counting_start_date": result.get("counting_start_date"),
        "calendar_version": result.get("calendar_version"),
        "suspension_policies": policies.get("suspensions", []),
        "policy_catalog_versions": provenance.get("policy_catalog_versions", {}),
    }
    return "dc_" + uuid.uuid5(ID_NAMESPACE, _digest(material)).hex, _digest(material)


def migrate_connection(db: sqlite3.Connection) -> dict[str, Any]:
    db.execute("PRAGMA foreign_keys=ON")
    db.execute("CREATE TABLE IF NOT EXISTS schema_migrations(version TEXT PRIMARY KEY, applied_at TEXT NOT NULL)")
    applied = db.execute("SELECT 1 FROM schema_migrations WHERE version=?", (MIGRATION_VERSION,)).fetchone()
    db.executescript(SCHEMA)
    db.execute("INSERT OR IGNORE INTO schema_migrations(version, applied_at) VALUES(?,?)", (MIGRATION_VERSION, _now()))
    db.commit()
    return {"migration_version": MIGRATION_VERSION, "already_applied": bool(applied)}


def persist_calculation(
    db: sqlite3.Connection,
    *,
    process_id: str,
    obligation_id: str,
    result: Any,
    commit: bool = True,
) -> str:
    """Upsert the full immutable-shaped result under its deterministic identity."""
    value = _value(result)
    status = value.get("status")
    due_date = value.get("due_date")
    if status not in {"CALCULATED", "UNRESOLVED", "REVIEW_REQUIRED"}:
        raise ValueError("status de DeadlineCalculation inválido")
    if status == "CALCULATED":
        if not isinstance(due_date, str) or not _DAY.fullmatch(due_date):
            raise ValueError("CALCULATED exige due_date YYYY-MM-DD")
        date.fromisoformat(due_date)
    elif status in {"UNRESOLVED", "REVIEW_REQUIRED"} and due_date is not None:
        raise ValueError("resultado não calculado não pode conter due_date")
    obligation = db.execute(
        "SELECT process_id FROM deadline_obligations WHERE obligation_id=?", (obligation_id,)
    ).fetchone()
    if not obligation or str(obligation["process_id"]) != process_id:
        raise ValueError("obligation_id não pertence ao processo informado")
    communication_event_id = value.get("communication_event_id")
    if communication_event_id:
        event = db.execute(
            "SELECT process_id FROM process_events WHERE event_id=?", (communication_event_id,)
        ).fetchone()
        if not event or str(event["process_id"]) != process_id:
            raise ValueError("communication_event_id não pertence ao processo informado")
    calculation_id, _ = calculation_identity(process_id=process_id, obligation_id=obligation_id, result=value)
    now = _now()
    db.execute(
        """INSERT INTO deadline_calculations(
          calculation_id,process_id,obligation_id,communication_event_id,resolved_rule_id,rule_version,status,
          due_date,trigger_date,counting_start_date,counting_policy_id,counting_policy_version,
          communication_policy_id,term_value,term_unit,calculation_json,legal_basis_json,provenance_json,
          calendar_version,created_at,updated_at
        ) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
        ON CONFLICT(calculation_id) DO UPDATE SET
          communication_event_id=excluded.communication_event_id,resolved_rule_id=excluded.resolved_rule_id,
          rule_version=excluded.rule_version,status=excluded.status,due_date=excluded.due_date,
          trigger_date=excluded.trigger_date,counting_start_date=excluded.counting_start_date,
          counting_policy_id=excluded.counting_policy_id,counting_policy_version=excluded.counting_policy_version,
          communication_policy_id=excluded.communication_policy_id,term_value=excluded.term_value,
          term_unit=excluded.term_unit,calculation_json=excluded.calculation_json,
          legal_basis_json=excluded.legal_basis_json,provenance_json=excluded.provenance_json,
          calendar_version=excluded.calendar_version,updated_at=excluded.updated_at""",
        (calculation_id, process_id, obligation_id, communication_event_id, value.get("resolved_rule_id"),
         value.get("rule_version"), value["status"], value.get("due_date"), value.get("trigger_date"),
         value.get("counting_start_date"), value.get("counting_policy_id"), value.get("counting_policy_version"),
         value.get("communication_policy_id"), value.get("term_value"), value.get("term_unit"), _json(value),
         _json(value.get("legal_basis") or {}), _json(value.get("provenance") or {}), value.get("calendar_version"),
         now, now),
    )
    if commit:
        db.commit()
    return calculation_id


def list_calculations(db: sqlite3.Connection, process_id: str, obligation_id: str | None = None) -> list[dict[str, Any]]:
    if not db.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='deadline_calculations'").fetchone():
        return []
    query = "SELECT * FROM deadline_calculations WHERE process_id=?"
    params: list[Any] = [process_id]
    if obligation_id is not None:
        query += " AND obligation_id=?"
        params.append(obligation_id)
    query += " ORDER BY created_at, calculation_id"
    rows = []
    for row in db.execute(query, params).fetchall():
        item = dict(row)
        item["calculation"] = json.loads(item["calculation_json"])
        item["legal_basis"] = json.loads(item.pop("legal_basis_json") or "{}")
        item["provenance"] = json.loads(item.pop("provenance_json") or "{}")
        rows.append(item)
    return rows


def _unresolved_result(
    *, obligation: Mapping[str, Any], code: str, process_id: str,
    communication_event_id: str | None = None, context: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    catalog_rule = next((r for r in get_catalog() if r.get("rule_id") == obligation.get("resolved_rule_id")), {})
    explicit_rule = obligation.get("resolved_rule_id") == "JUDICIAL_EXPLICIT_TERM"
    rule = ({"rule_id": "JUDICIAL_EXPLICIT_TERM", "rule_version": catalog_rule.get("rule_version"),
             "legal_basis": {"kind": "OBSERVED_JUDICIAL_TERM"}} if explicit_rule else catalog_rule)
    counting_id = rule.get("counting_policy_id")
    if explicit_rule and context:
        counting_id = dict(REGIME_COUNTING_POLICY_IDS).get(str(context.get("base_regime") or "").upper())
    counting_policy = next((p for p in COUNTING_POLICIES if p.policy_id == counting_id), None)
    communication_id = rule.get("communication_policy_id")
    communication_policy = next((p for p in COMMUNICATION_POLICIES if p.policy_id == communication_id), None)
    provenance = {"obligation_id": obligation["obligation_id"],
                  "obligation_provenance": json.loads(obligation.get("provenance_json") or "{}"),
                  "legal_context": dict(context) if context else None,
                  "rule": {"authority": rule.get("authority"), "official_source": rule.get("official_source"),
                           "verified_at": rule.get("verified_at")},
                  "policy_catalog_versions": {
                      "counting": ({"policy_id": counting_policy.policy_id, "version": counting_policy.policy_version}
                                   if counting_policy else None),
                      "communication": ({"policy_id": communication_policy.policy_id, "version": communication_policy.policy_version}
                                        if communication_policy else None),
                      "suspensions": [],
                  }}
    return {
        "status": "UNRESOLVED", "resolved_rule_id": obligation.get("resolved_rule_id"),
        "rule_version": rule.get("rule_version"), "legal_domain": (context or {}).get("legal_domain"),
        "base_regime": (context or {}).get("base_regime"), "term_value": obligation.get("term_value"),
        "term_unit": obligation.get("term_unit"), "counting_policy_id": counting_id,
        "counting_policy_version": counting_policy.policy_version if counting_policy else None,
        "communication_policy_id": communication_id,
        "communication_event_id": communication_event_id, "trigger_date": None,
        "trigger_resolution_method": None, "counting_start_date": None, "due_date": None,
        "counted_days": [], "excluded_days": [], "applied_suspensions": [],
        "calendar_version": None, "calendar_provenance": [], "calculation_trace": [],
        "legal_basis": {"rule": rule.get("legal_basis")} if rule else {},
        "provenance": provenance, "reason": {"code": code},
    }


def _publication_communication(
    db: sqlite3.Connection,
    *,
    process_id: str,
    obligation: Mapping[str, Any],
    communication_event_id: str | None,
) -> tuple[CommunicationFact | None, str | None]:
    instruction_ids = [str(obligation["originating_instruction_id"])]
    instruction_ids.extend(json.loads(obligation.get("supporting_instruction_ids_json") or "[]"))
    placeholders = ",".join("?" for _ in instruction_ids)
    rows = db.execute(
        f"SELECT instruction_id,source_event_id,source_entity,source_id FROM deadline_instructions "
        f"WHERE process_id=? AND instruction_id IN ({placeholders}) ORDER BY instruction_id",
        (process_id, *instruction_ids),
    ).fetchall()
    events = []
    for row in rows:
        if communication_event_id and row["source_event_id"] != communication_event_id:
            continue
        if row["source_entity"] == "PUBLICATION":
            events.append(str(row["source_event_id"]))
    if communication_event_id:
        if communication_event_id not in events:
            return None, "COMMUNICATION_EVENT_NOT_LINKED_TO_OBLIGATION"
        events = [communication_event_id]
    if len(set(events)) != 1:
        return None, "COMMUNICATION_EVENT_AMBIGUOUS" if events else "COMMUNICATION_TRIGGER_MISSING"
    event_id = events[0]
    event = db.execute(
        "SELECT * FROM process_events WHERE process_id=? AND event_id=? AND event_type='PUBLICATION'",
        (process_id, event_id),
    ).fetchone()
    if not event:
        return None, "COMMUNICATION_EVENT_MISSING"
    publication = db.execute(
        "SELECT * FROM publications WHERE process_id=? AND publication_id=?",
        (process_id, event["source_id"]),
    ).fetchone()
    if not publication:
        return None, "PUBLICATION_SOURCE_MISSING"
    if publication["active"] == 0 or str(publication["publication_status"] or "").upper() in {"CANCELED", "CANCELLED"}:
        return None, "COMMUNICATION_CANCELED"
    if str(publication["provider"] or "").upper() != "DJEN_COMUNICA" or str(publication["medium"] or "").upper() != "D":
        return None, "COMMUNICATION_METHOD_UNSUPPORTED"
    provenance = {
        "source_entity": "PUBLICATION", "source_id": publication["publication_id"],
        "source": "DJEN_API", "source_event_id": event_id,
        "process_event": {"event_id": event_id, "event_type": event["event_type"],
                          "event_date": event["event_date"], "date_precision": event["date_precision"],
                          "source_refs": json.loads(event["source_refs_json"] or "[]"),
                          "provenance": json.loads(event["provenance_json"] or "{}")},
        "available_on": {"value": publication["available_on"], "epistemic_status": "OBSERVED", "source": "DJEN_API"},
        "published_on": ({"value": publication["published_on"], "epistemic_status": "OBSERVED", "source": "DJEN_API"}
                          if publication["published_on"] else None),
    }
    source_refs = [{"source_entity": "PUBLICATION", "source_id": publication["publication_id"],
                    "source_event_id": event_id, "source_url": publication["source_url"],
                    "communication_id": publication["communication_id"]}]
    fact = CommunicationFact(
        source_event_id=event_id, event_type="PUBLICATION", communication_method="DJEN_PUBLICATION",
        source_refs=tuple(source_refs), provenance=provenance,
        available_on=publication["available_on"], published_on=publication["published_on"],
    )
    return fact, None


def _remove_obligation_projections(db: sqlite3.Connection, *, process_id: str, obligation_id: str) -> None:
    if not db.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='deadlines'").fetchone():
        return
    for row in db.execute(
        "SELECT deadline_id,provenance_json FROM deadlines WHERE owner_type='PROCESS' AND owner_id=?",
        (process_id,),
    ).fetchall():
        try:
            marker = json.loads(row["provenance_json"] or "{}").get("deadline_calculation", {})
        except (TypeError, ValueError):
            continue
        if marker.get("obligation_id") == obligation_id:
            db.execute("DELETE FROM deadlines WHERE deadline_id=?", (row["deadline_id"],))


def _project_deadline(
    db: sqlite3.Connection,
    *,
    process_id: str,
    obligation: Mapping[str, Any],
    result: Mapping[str, Any],
    calculation_id: str,
    rule: Mapping[str, Any],
    commit: bool,
) -> str:
    due_date = result.get("due_date")
    if result.get("status") != "CALCULATED" or not due_date or not _DAY.fullmatch(str(due_date)):
        raise ValueError("somente resultado CALCULATED com due_date DAY pode ser projetado")
    date.fromisoformat(str(due_date))
    from core.documentos.domain_objects_v1 import submit_deadline_candidates

    provenance = json.loads(obligation.get("provenance_json") or "{}")
    marker = {"obligation_id": obligation["obligation_id"], "calculation_id": calculation_id}
    projection_provenance = {
        "deadline_calculation": marker,
        "obligation_provenance": provenance,
        "calculation_provenance": result.get("provenance") or {},
        "calculation_legal_basis": result.get("legal_basis") or {},
        "source_refs": [{"entity": "deadline_obligation", "id": obligation["obligation_id"]},
                        {"entity": "deadline_calculation", "id": calculation_id},
                        {"entity": "deadline_instruction", "id": obligation.get("originating_instruction_id")},
                        {"entity": "process_event", "id": result.get("communication_event_id")},
                        {"entity": "process_event", "id": obligation.get("antecedent_source_event_id")},
                        {"entity": "origin_source_refs", "refs": json.loads(obligation.get("source_refs_json") or "{}") }],
    }
    procedure_types = [x for x in rule.get("procedural_act_types", rule.get("applicable_act_types", [])) if x != "*"]
    deadline_type = procedure_types[0] if procedure_types else rule.get("category") or result.get("resolved_rule_id")
    title = obligation.get("action_text") or rule.get("name") or result.get("resolved_rule_id") or "Prazo processual"
    term = _json({"value": result.get("term_value"), "unit": result.get("term_unit"),
                  "counting_policy_id": result.get("counting_policy_id"),
                  "counting_policy_version": result.get("counting_policy_version")})
    legal_basis = _json(result.get("legal_basis") or {})
    fingerprint = "deadline-calculation:" + hashlib.sha256(str(obligation["obligation_id"]).encode("utf-8")).hexdigest()
    ids = submit_deadline_candidates(db, "PROCESS", process_id, [{
        "title": str(title), "description": obligation.get("action_text"), "deadline_type": deadline_type,
        "term": term, "due_at": str(due_date), "date_precision": "DAY", "status": "CANDIDATE",
        "triggering_event": result.get("communication_event_id"), "legal_basis": legal_basis,
        "confirmation_status": "PENDING", "source_refs": projection_provenance["source_refs"],
        "provenance": projection_provenance, "fingerprint": fingerprint,
    }], commit=False)
    if commit:
        db.commit()
    return ids[0]


def calculate_and_materialize(
    db: sqlite3.Connection,
    *,
    process_id: str,
    obligation_id: str,
    calendar_entries: Iterable[CourtCalendar | Mapping[str, Any]],
    communication_event_id: str | None = None,
    communication_policy_id: str | None = None,
    requires_personal_notice: bool = False,
    applicable_suspension_exceptions: Mapping[str, str] | None = None,
    commit: bool = True,
) -> dict[str, Any]:
    """Calculate, audit, and reconcile the one operational deadline for an obligation."""
    if not db.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='deadline_calculations'").fetchone():
        migrate_connection(db)
    row = db.execute(
        "SELECT * FROM deadline_obligations WHERE obligation_id=? AND process_id=?",
        (obligation_id, process_id),
    ).fetchone()
    if not row:
        raise ValueError("obligation_id não pertence ao processo informado")
    obligation = dict(row)
    obligation_provenance = json.loads(obligation.get("provenance_json") or "{}")
    rule: dict[str, Any] = {}
    resolved_communication_policy_id = communication_policy_id
    context = obligation_provenance.get("legal_context")
    fact, communication_error = _publication_communication(
        db, process_id=process_id, obligation=obligation, communication_event_id=communication_event_id
    )
    event_id = fact.source_event_id if fact else None

    if (not context or not isinstance(context, dict)
            or not context.get("legal_domain") or not context.get("base_regime")
            or not context.get("jurisdiction")
            or not isinstance(context.get("applicable_regimes"), (list, tuple))
            or not context.get("applicable_regimes")):
        result = _unresolved_result(obligation=obligation, code="LEGAL_CONTEXT_MISSING", process_id=process_id,
                                   communication_event_id=event_id, context=context)
    elif communication_error:
        result = _unresolved_result(obligation=obligation, code=communication_error, process_id=process_id,
                                   communication_event_id=event_id, context=context)
    elif not obligation.get("resolved_rule_id"):
        result = _unresolved_result(obligation=obligation, code="RESOLVED_RULE_MISSING", process_id=process_id,
                                   communication_event_id=event_id, context=context)
    elif not isinstance(obligation.get("term_value"), int) or obligation["term_value"] <= 0 or obligation.get("term_unit") in (None, "", "UNSPECIFIED"):
        result = _unresolved_result(obligation=obligation, code="TERM_INPUT_MISSING", process_id=process_id,
                                   communication_event_id=event_id, context=context)
    else:
        try:
            legal_context = LegalContext.from_mapping(context)
        except (TypeError, ValueError):
            result = _unresolved_result(obligation=obligation, code="LEGAL_CONTEXT_MISSING", process_id=process_id,
                                       communication_event_id=event_id, context=context)
            rule = {}
        else:
            rule = None
        rules = get_catalog()
        matching_rules = [r for r in rules if r.get("rule_id") == obligation["resolved_rule_id"]]
        if rule == {}:
            pass
        elif obligation["resolved_rule_id"] != "JUDICIAL_EXPLICIT_TERM" and len(matching_rules) != 1:
            result = _unresolved_result(obligation=obligation, code="RESOLVED_RULE_NOT_FOUND", process_id=process_id,
                                       communication_event_id=event_id, context=context)
        else:
            if obligation["resolved_rule_id"] == "JUDICIAL_EXPLICIT_TERM":
                rule = {"rule_id": "JUDICIAL_EXPLICIT_TERM",
                        "rule_version": matching_rules[0].get("rule_version") if matching_rules else None,
                        "category": "JUDICIAL_ORDER", "procedural_act_types": [],
                        "communication_policy_id": None, "counting_policy_id": None}
            else:
                rule = matching_rules[0]
            if rule.get("recipient_roles") and obligation.get("recipient_role") not in rule["recipient_roles"]:
                result = _unresolved_result(obligation=obligation, code="RECIPIENT_ROLE_MISSING_OR_INCOMPATIBLE",
                                           process_id=process_id, communication_event_id=event_id, context=context)
            elif rule.get("procedure_classes") and legal_context.procedure_class not in rule["procedure_classes"]:
                result = _unresolved_result(obligation=obligation, code="PROCEDURE_CLASS_MISSING_OR_INCOMPATIBLE",
                                           process_id=process_id, communication_event_id=event_id, context=context)
            else:
                policy_id = communication_policy_id or rule.get("communication_policy_id")
                if not policy_id and fact:
                    policy_id = "DJEN_PUBLICATION"
                resolved_communication_policy_id = policy_id
                if not policy_id:
                    result = _unresolved_result(obligation=obligation, code="COMMUNICATION_POLICY_MISSING",
                                               process_id=process_id, communication_event_id=event_id, context=context)
                else:
                    observed_dates = [x for x in (fact.published_on, fact.available_on) if x] if fact else []
                    if not observed_dates:
                        result = _unresolved_result(obligation=obligation, code="COMMUNICATION_TRIGGER_MISSING",
                                                   process_id=process_id, communication_event_id=event_id, context=context)
                    else:
                        relevant_date = observed_dates[0]
                        calculation = DeadlineCalculationInput(
                            legal_context=context, resolved_rule_id=str(obligation["resolved_rule_id"]),
                            term_value=obligation["term_value"], term_unit=str(obligation["term_unit"]),
                            counting_policy_id=rule.get("counting_policy_id"), communication_policy_id=policy_id,
                            communication_fact=fact, calendar_entries=tuple(calendar_entries), relevant_date=relevant_date,
                            rule_version=rule.get("rule_version"),
                            explicit_counting_qualifier=obligation.get("counting_qualifier"),
                            requires_personal_notice=requires_personal_notice,
                            applicable_suspension_exceptions=applicable_suspension_exceptions or {},
                            resolved_rule_provenance={"source_event_id": obligation_provenance.get("source_event_id"),
                                                      "obligation_id": obligation_id,
                                                      "instruction_id": obligation.get("originating_instruction_id")},
                        )
                        computed = calculate_deadline(calculation)
                        result = asdict(computed)
                        result["communication_event_id"] = fact.source_event_id
                        result["provenance"] = dict(result.get("provenance") or {})
                        result["provenance"].update({
                            "obligation_id": obligation_id,
                            "obligation_provenance": obligation_provenance,
                            "legal_context": context,
                            "communication_event_id": fact.source_event_id,
                        })
                        policy_counting_id = (computed.counting_policy_id or rule.get("counting_policy_id")
                            or dict(REGIME_COUNTING_POLICY_IDS).get(context.get("base_regime")))
                        selected_counting = next((p for p in COUNTING_POLICIES if p.policy_id == policy_counting_id), None)
                        selected_communication = next((p for p in COMMUNICATION_POLICIES if p.policy_id == policy_id), None)
                        selected_suspensions = ([p for p in SUSPENSION_POLICIES
                            if selected_counting and p.policy_id in selected_counting.suspension_policy_ids])
                        result["provenance"]["policy_catalog_versions"] = {
                            "counting": ({"policy_id": selected_counting.policy_id, "version": selected_counting.policy_version}
                                         if selected_counting else None),
                            "communication": ({"policy_id": selected_communication.policy_id, "version": selected_communication.policy_version}
                                              if selected_communication else None),
                            "suspensions": [{"policy_id": p.policy_id, "version": p.policy_version} for p in selected_suspensions],
                        }

    if fact:
        result.setdefault("provenance", {})
        selected_communication = next((p for p in COMMUNICATION_POLICIES
                                       if p.policy_id == (resolved_communication_policy_id or rule.get("communication_policy_id") or "DJEN_PUBLICATION")), None)
        selected_counting = next((p for p in COUNTING_POLICIES
                                  if p.policy_id == result.get("counting_policy_id")), None)
        result["communication_policy_id"] = (selected_communication.policy_id
                                              if selected_communication else result.get("communication_policy_id"))
        versions = result["provenance"].setdefault("policy_catalog_versions", {})
        versions["communication"] = ({"policy_id": selected_communication.policy_id,
                                       "version": selected_communication.policy_version}
                                      if selected_communication else None)
        if selected_counting:
            versions["counting"] = {"policy_id": selected_counting.policy_id,
                                     "version": selected_counting.policy_version}
            versions["suspensions"] = [
                {"policy_id": p.policy_id, "version": p.policy_version}
                for p in SUSPENSION_POLICIES if p.policy_id in selected_counting.suspension_policy_ids
            ]
        result["provenance"]["communication_date_epistemics"] = {
            "available_on": {"value": fact.available_on,
                             "epistemic_status": "OBSERVED" if fact.available_on else "UNRESOLVED",
                             "source": "DJEN_API"},
            "published_on": ({"value": fact.published_on, "epistemic_status": "OBSERVED", "source": "DJEN_API"}
                             if fact.published_on else {"value": result.get("trigger_date"),
                                 "epistemic_status": "DERIVED" if result.get("trigger_date") else "UNRESOLVED",
                                 "policy": selected_communication.policy_id if selected_communication else (communication_policy_id or rule.get("communication_policy_id")),
                                 "derived_from": "available_on"}),
            "counting_start": {"value": result.get("counting_start_date"),
                               "epistemic_status": "DERIVED" if result.get("counting_start_date") else "UNRESOLVED",
                               "policy": selected_communication.policy_id if selected_communication else (communication_policy_id or rule.get("communication_policy_id"))},
        }
        result["provenance"].setdefault("communication_source", fact.provenance)

    calculation_id = persist_calculation(db, process_id=process_id, obligation_id=obligation_id, result=result, commit=False)
    _remove_obligation_projections(db, process_id=process_id, obligation_id=obligation_id)
    deadline_id = None
    if result.get("status") == "CALCULATED" and result.get("due_date"):
        deadline_id = _project_deadline(db, process_id=process_id, obligation=obligation, result=result,
                                        calculation_id=calculation_id, rule=rule, commit=False)
    if commit:
        db.commit()
    return {"process_id": process_id, "obligation_id": obligation_id, "calculation_id": calculation_id,
            "status": result["status"], "due_date": result.get("due_date"), "deadline_id": deadline_id,
            "reason": result.get("reason")}
