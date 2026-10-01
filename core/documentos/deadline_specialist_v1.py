"""Local semantic specialist for deadline obligations.

The specialist classifies semantic facts only. It never computes due dates,
counts days, reads calendars, or treats model output as legal authority.
"""
from __future__ import annotations

import json
import re
import sqlite3
import unicodedata
from pathlib import Path
from typing import Any, Iterable, Mapping

import numpy as np

from core.documentos.deadline_specialist_contract_v1 import (
    ContextRequest,
    DeadlineSpecialistOutput,
)
from core.documentos.deadline_rule_resolver_v1 import resolve_deadline_rule
from core.documentos.legal_context_v1 import LegalContext
from core.documentos.legal_deadline_rules_v1 import get_catalog
from core.retrieval.onnx_embed import generate_embedding_onnx

MODEL_VERSION = "deadline-specialist-encoder-heads-v1"
HEADS_PATH = Path(__file__).resolve().parents[1] / "models" / "deadline_specialist_heads_v1.npz"

TASK_LABELS = {
    "operative_instruction": (False, True),
    "context_sufficiency": ("SUFFICIENT", "NEEDS_CONTEXT", "AMBIGUOUS_REVIEW"),
    "recipient_role": ("PLAINTIFF", "DEFENDANT", "BOTH_PARTIES", "THIRD_PARTY", "UNRESOLVED"),
    "procedural_act_type": (
        "PROVIDE_DOCUMENTS", "PROVIDE_INFORMATION", "RESPOND_TO_OPPOSING_SUBMISSION",
        "SPECIFY_EVIDENCE", "MANIFEST_AFTER_MEASURE", "FILE_MEMORIALS", "FILE_DEFENSE", "NONE",
    ),
}
_OPPOSING = re.compile(r"\b(parte\s+(?:contr[aá]ria|adversa)|polo\s+oposto|ex\s+advers[oa])\b", re.I)
_PARTY_REQUEST = re.compile(r"\b(?:a\s+parte\s+)?(?:autor[ae]?|r[eé]u|r[eé]|requerente|requerid[oa]|exequente|executad[oa])\s+(?:requer|pede|postula|pleiteia)\b", re.I)
_JUDICIAL_VERB = re.compile(r"\b(?:intim(?:e-se|em-se|ar)|cite-se|oficie-se|determino|determina-se|faculto|concedo|d[eê]-se\s+vista|vista\s+[aà]|apresentem|manifeste-se|manifeste-se)\b", re.I)
_CLERICAL_ONLY = re.compile(r"^\s*(?:junte-se|anote-se|certifique-se|ap[oó]s,?\s*conclusos|voltem\s+conclusos|arquive-se)[\s.;,-]*(?:(?:junte-se|anote-se|certifique-se|ap[oó]s,?\s*conclusos|voltem\s+conclusos|arquive-se)[\s.;,-]*)*$", re.I)
_TERM = re.compile(
    r"\b(?:prazo(?:\s+comum)?\s+de|prazo\s+para\s+[^.;]{1,120}?\s+ser[a\u00e1\uFFFD]\s+de|em|dentro\s+de)"
    r"\s*(\d{1,3})(?:\s*\([^)]*\))?\s*(dias\s+(?:úteis|uteis|\uFFFDteis)|dias\s+corridos|dias|horas|meses)\b",
    re.I,
)
_DATE = re.compile(r"\bat[eé]\s+(\d{1,2})/(\d{1,2})/(\d{4})\b", re.I)
_EXPLICIT_TRIGGER = re.compile(
    r"\b(?:a\s+contar\s+de|contad[oa]s?\s+a\s+partir\s+d[aeo]|"
    r"ap[oó]s\s+(?:a|o)|da\s+intima[cç][aã]o|da\s+ci[eê]ncia|da\s+publica[cç][aã]o)"
    r"[^.;]{0,180}",
    re.I,
)
_PARTY_ACTION = re.compile(
    r"\b(?:manifeste-se|manifestem-se|manifeste[m]?|conteste[m]?|apresente[m]?\s+(?:a\s+)?(?:contesta[cç][aã]o|defesa|manifesta[cç][aã]o|documentos?)|"
    r"(?:para|sobre)\s+manifesta[cç][aã]o|contesta.{0,2}o|"
    r"responda[m]?|especifique[m]?|indique[m]?\s+(?:as?\s+)?provas?|digam\s+(?:as\s+)?provas?|"
    r"comprove[m]?|informe[m]?|junte[m]?|compare[cç]a[m]?)\b", re.I
)
_DIRECT_ROLES = (
    (re.compile(r"\b(?:ambas\s+as\s+partes|(?:as|[àa]s)\s+partes|autor\s+e\s+r[eé]u|requerente\s+e\s+requerid[oa])\b", re.I), "BOTH_PARTIES"),
    (re.compile(r"\b(?:autor[ae]?|requerente|exequente)\b", re.I), "PLAINTIFF"),
    (re.compile(r"\b(?:r[eé]u|r[eé]|requerid[oa]|executad[oa])\b", re.I), "DEFENDANT"),
    (re.compile(r"\b(?:minist[eé]rio\s+p[uú]blico|promotor(?:a)?(?:\s+de\s+justi[cç]a)?)\b", re.I), "PROSECUTOR"),
    (re.compile(r"\b(?:perit[oa]|expert)\b", re.I), "EXPERT"),
    (re.compile(r"\b(?:empresa|institui[cç][aã]o|terceir[oa]|oficiad[oa]|empregador[ae]?)\b", re.I), "THIRD_PARTY"),
)
_INDIRECT_PARTICIPANT = re.compile(r"\b(?:mencionad[oa]\s+na\s+capa|cadastrad[oa]\s+no\s+polo|indicad[oa]\s+na\s+capa|constante\s+da\s+capa)\b", re.I)
_ACT_PATTERNS = (
    (re.compile(r"\b(?:contesta.{0,2}o|ofere[c\u00e7\uFFFD]a\s+defesa|apresente\s+defesa|responda\s+[aà]\s+demanda)\b", re.I), "FILE_DEFENSE"),
    (re.compile(r"\b(?:memoriais|alega[cç][oõ]es\s+finais)\b", re.I), "FILE_MEMORIALS"),
    (re.compile(r"\b(?:especifi(?:que|quem)|indiquem?|digam)\b.{0,80}\bprovas?\b", re.I | re.S), "SPECIFY_EVIDENCE"),
    (re.compile(r"\b(?:ap[oó]s|depois\s+de).{0,90}\b(?:medida|dilig[eê]ncia|cumprimento|efetiva[cç][aã]o)\b", re.I | re.S), "MANIFEST_AFTER_MEASURE"),
    (re.compile(r"\b(?:junte|juntem|apresente|apresentem|traga|tragam|encaminhe|encaminhem)\b.{0,100}\b(?:documentos?|comprovantes?|declara[cç][aã]o)\b", re.I | re.S), "PROVIDE_DOCUMENTS"),
    (re.compile(r"\b(?:informe|informem|esclare[cç]a|esclare[cç]am|preste|prestem|comunique|comuniquem)\b.{0,100}\b(?:dados?|informa[cç][oõ]es?|pagamentos?|v[ií]nculo)\b", re.I | re.S), "PROVIDE_INFORMATION"),
)

def _norm(value: Any) -> str:
    text = unicodedata.normalize("NFKD", str(value or ""))
    return " ".join("".join(ch for ch in text if not unicodedata.combining(ch)).split()).casefold()

def _model_predictions(text: str) -> tuple[dict[str, Any], dict[str, float]]:
    if not HEADS_PATH.is_file():
        return {}, {}
    vector = generate_embedding_onnx(text)
    if not vector:
        return {}, {}
    x = np.asarray(vector, dtype=np.float32)
    data = np.load(HEADS_PATH, allow_pickle=False)
    predictions: dict[str, Any] = {}
    confidence: dict[str, float] = {}
    for task, labels in TASK_LABELS.items():
        w = data[f"{task}_weight"]
        b = data[f"{task}_bias"]
        logits = w @ x + b
        shifted = logits - np.max(logits)
        probs = np.exp(shifted) / np.sum(np.exp(shifted))
        index = int(np.argmax(probs))
        predictions[task] = labels[index]
        confidence[task] = float(probs[index])
    return predictions, confidence
def _explicit_term(text: str) -> tuple[int | None, str, str | None]:
    match = _TERM.search(text)
    if match:
        value = int(match.group(1))
        raw = _norm(match.group(2))
        if "util" in raw or "uteis" in raw or "úteis" in raw or "\ufffdteis" in raw:
            unit = "BUSINESS_DAYS"
        elif "dia" in raw:
            unit = "DAYS"
        elif "hora" in raw:
            unit = "HOURS"
        else:
            unit = "MONTHS"
        return (value if value > 0 else None), unit if value > 0 else "UNSPECIFIED", match.group(0)
    match = _DATE.search(text)
    if match:
        day, month, year = match.groups()
        return None, "DATE_CERTAIN", f"{year}-{int(month):02d}-{int(day):02d}"
    return None, "UNSPECIFIED", None

def _direct_role(text: str) -> str | None:
    for pattern, role in _DIRECT_ROLES:
        if pattern.search(text):
            return role
    return None

def _act_type(text: str, model_value: str | None) -> str | None:
    normalized = _norm(text)
    if _OPPOSING.search(text) and "embargos de declaracao" in normalized:
        return "DECLARATORY_EMBARGOS_RESPONSE"
    if _OPPOSING.search(text):
        return "RESPOND_TO_OPPOSING_SUBMISSION"
    for pattern, value in _ACT_PATTERNS:
        if pattern.search(text):
            return value
    return None if model_value in (None, "NONE") else model_value

def _inverse_role(actor_role: str | None) -> str | None:
    value = str(actor_role or "").upper()
    if value in {"PLAINTIFF", "CLAIMANT"}:
        return "DEFENDANT"
    if value in {"DEFENDANT", "RESPONDENT"}:
        return "PLAINTIFF"
    return None

def _semantic_antecedents(context: Iterable[Mapping[str, Any]]) -> list[Mapping[str, Any]]:
    return [
        item for item in context
        if str(item.get("type") or "").upper() in {"ANTECEDENT_PLEADING", "ANTECEDENT_CANDIDATE"}
        or item.get("actor_role")
    ]

def _resolve_opposing(context: Iterable[Mapping[str, Any]]) -> tuple[str, str | None, tuple[str, ...], str]:
    candidates = _semantic_antecedents(context)
    resolved = [(item, _inverse_role(item.get("actor_role"))) for item in candidates]
    resolved = [(item, role) for item, role in resolved if role]
    if not resolved:
        return "UNRESOLVED", None, (), "NEEDS_CONTEXT"
    roles = {role for _, role in resolved}
    ids = tuple(str(item.get("event_id")) for item, _ in resolved if item.get("event_id"))
    if len(roles) != 1:
        return "UNRESOLVED", None, ids, "AMBIGUOUS_REVIEW"
    # Candidate ordering is supplied by the retriever: first is the strongest.
    winner = resolved[0][0]
    return next(iter(roles)), str(winner.get("event_id")) if winner.get("event_id") else None, (), "SUFFICIENT"

def _participant_ids(db: sqlite3.Connection | None, process_id: str | None, role: str) -> tuple[str, ...]:
    if db is None or not process_id:
        return ()
    role_map = {
        "PLAINTIFF": ("CLAIMANT",), "DEFENDANT": ("RESPONDENT",),
        "BOTH_PARTIES": ("CLAIMANT", "RESPONDENT"), "THIRD_PARTY": ("THIRD_PARTY",),
        "PROSECUTOR": ("PUBLIC_PROSECUTOR",), "EXPERT": ("EXPERT",),
    }
    bases = role_map.get(role, ())
    if not bases:
        return ()
    placeholders = ",".join("?" for _ in bases)
    rows = db.execute(
        f"SELECT participant_id FROM process_participants WHERE process_id=? AND base_role IN ({placeholders}) ORDER BY participant_id",
        (process_id, *bases),
    ).fetchall()
    return tuple(str(row[0]) for row in rows)
def analyze_deadline_text(
    text: str,
    *,
    context: Iterable[Mapping[str, Any]] = (),
    db: sqlite3.Connection | None = None,
    process_id: str | None = None,
) -> DeadlineSpecialistOutput:
    excerpt = " ".join(str(text or "").split())
    predictions, confidence = _model_predictions(excerpt)
    operative = bool(predictions.get("operative_instruction", False))
    if _PARTY_REQUEST.search(excerpt) or _CLERICAL_ONLY.fullmatch(excerpt):
        operative = False
    elif _JUDICIAL_VERB.search(excerpt) or (_PARTY_ACTION.search(excerpt) and _TERM.search(excerpt)):
        operative = True

    if not operative:
        return DeadlineSpecialistOutput(
            operative_instruction=False, context_sufficiency="SUFFICIENT",
            recipient_role="UNRESOLVED", explicit_term_unit="UNSPECIFIED",
            confidence=confidence,
        )

    term_value, term_unit, term_marker = _explicit_term(excerpt)
    act_type = _act_type(excerpt, predictions.get("procedural_act_type"))
    recipient_role = _direct_role(excerpt) or str(predictions.get("recipient_role") or "UNRESOLVED")
    # Filing a defense/contestation is structurally an act of the defendant.
    # Prefer this procedural fact over an uncertain model-head role.
    if act_type == "FILE_DEFENSE" and _direct_role(excerpt) is None:
        recipient_role = "DEFENDANT"
    sufficiency = str(predictions.get("context_sufficiency") or "SUFFICIENT")
    antecedent_id: str | None = None
    candidate_antecedents: tuple[str, ...] = ()
    requests: list[ContextRequest] = []
    resolution_method = "MODEL_HEAD"

    if _OPPOSING.search(excerpt):
        recipient_role, antecedent_id, candidate_antecedents, sufficiency = _resolve_opposing(context)
        resolution_method = "ANTECEDENT_RELATION"
        if sufficiency == "NEEDS_CONTEXT":
            requests.append(ContextRequest(
                kind="ANTECEDENT_PLEADING", purpose="SEMANTIC_RESOLUTION",
                reason="A expressão relacional depende do ato antecedente relevante que provocou a ordem.",
                query_hint="localizar a petição ou manifestação substantiva relacionada ao comando",
            ))
    elif _INDIRECT_PARTICIPANT.search(excerpt):
        sufficiency = "NEEDS_CONTEXT"
        requests.append(ContextRequest(
            kind="PROCESS_PARTICIPANTS", purpose="SEMANTIC_RESOLUTION",
            reason="A referência indireta depende do cadastro processual para identificar canonicamente o destinatário.",
        ))
    elif recipient_role != "UNRESOLVED":
        sufficiency = "SUFFICIENT"
        resolution_method = "EXPLICIT_ROLE"

    if candidate_antecedents:
        sufficiency = "AMBIGUOUS_REVIEW"

    if recipient_role == "THIRD_PARTY":
        has_communication = any(str(x.get("type") or "").upper() == "COMMUNICATION_EVENT" for x in context)
        if not has_communication:
            requests.append(ContextRequest(
                kind="COMMUNICATION_EVENT", purpose="TRIGGER_RESOLUTION",
                reason="É necessário comprovar o recebimento ou ciência da ordem pelo terceiro para resolver o marco temporal.",
            ))
    if act_type == "MANIFEST_AFTER_MEASURE":
        requests.append(ContextRequest(
            kind="COMMUNICATION_EVENT", purpose="TRIGGER_RESOLUTION",
            reason="É necessário verificar a efetivação da medida e a comunicação que aciona o prazo.",
        ))
    if act_type == "FILE_DEFENSE" and term_value is None and term_unit == "UNSPECIFIED":
        requests.append(ContextRequest(
            kind="LEGAL_CONTEXT", purpose="RULE_RESOLUTION",
            reason="Regime e classe processual são necessários para selecionar a regra material de prazo.",
        ))

    participant_ids = _participant_ids(db, process_id, recipient_role)
    trigger_match = _EXPLICIT_TRIGGER.search(excerpt)
    trigger_text = trigger_match.group(0).strip() if trigger_match else None
    return DeadlineSpecialistOutput(
        operative_instruction=True,
        context_sufficiency=sufficiency,
        procedural_act_type=act_type,
        action_text=excerpt,
        recipient_text=_OPPOSING.search(excerpt).group(0) if _OPPOSING.search(excerpt) else None,
        recipient_role=recipient_role,
        recipient_participant_ids=participant_ids,
        explicit_term_value=term_value,
        explicit_term_unit=term_unit,
        explicit_term_date=term_marker if term_unit == "DATE_CERTAIN" else None,
        trigger_text=trigger_text,
        antecedent_source_event_id=antecedent_id,
        candidate_antecedent_event_ids=candidate_antecedents,
        context_requests=tuple(requests),
        confidence=confidence,
    )

def derive_legal_context(db: sqlite3.Connection, process_id: str) -> tuple[LegalContext | None, dict[str, Any]]:
    if not db.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='process_metadata'").fetchone():
        return None, {"reason": "PROCESS_METADATA_MISSING"}
    row = db.execute(
        "SELECT classe,assunto,tribunal,comarca,unidade,fase,provenance_json FROM process_metadata WHERE process_id=?",
        (process_id,),
    ).fetchone()
    if not row:
        return None, {"reason": "PROCESS_METADATA_MISSING"}
    value = _norm(" ".join(str(row[key] or "") for key in ("classe", "assunto")))
    tribunal = str(row["tribunal"] or "").upper().strip()
    if "juizado especial" in value:
        domain, regime = "SPECIAL_COURTS", "LAW_9099"
    elif any(x in value for x in ("criminal", "acao penal", "inquerito", "crime")):
        domain, regime = "CRIMINAL", "CPP"
    elif any(x in value for x in ("trabalh", "reclamacao trabalhista")) or tribunal.startswith("TRT"):
        domain, regime = "LABOR", "CLT"
    elif any(x in value for x in ("civel", "civil", "familia", "alimentos", "paternidade", "execucao")) or tribunal.startswith(("TJ", "TRF")):
        domain, regime = "CIVIL", "CPC"
    else:
        return None, {"reason": "LEGAL_REGIME_UNRESOLVED", "classe": row["classe"], "assunto": row["assunto"], "tribunal": tribunal}
    jurisdiction = tribunal[2:4] if re.fullmatch(r"TJ[A-Z]{2}", tribunal) else tribunal or "BR"
    ctx = LegalContext(
        legal_domain=domain, base_regime=regime, procedure_class=row["classe"],
        applicable_regimes=(regime,), jurisdiction=jurisdiction,
        procedural_phase=row["fase"],
    )
    provenance = {
        "source": "process_metadata", "classe": row["classe"], "assunto": row["assunto"],
        "tribunal": tribunal, "comarca": row["comarca"], "unidade": row["unidade"],
        "fase": row["fase"],
    }
    return ctx, provenance
def _catalog_act(output: DeadlineSpecialistOutput, context: Iterable[Mapping[str, Any]]) -> tuple[str | None, tuple[str, ...]]:
    act = output.procedural_act_type
    if act == "FILE_DEFENSE":
        return "CONTESTATION", ("CPC_ART_335_CONTESTATION",)
    if act == "DECLARATORY_EMBARGOS_RESPONSE":
        return "DECLARATORY_EMBARGOS_RESPONSE", ("CPC_ART_1023_P2_EMBARGOS_RESPONSE",)
    if act == "RESPOND_TO_OPPOSING_SUBMISSION":
        antecedent = " ".join(str(x.get("text") or "") for x in context)
        normalized = _norm(antecedent)
        features = [x.get("rule_features") for x in context if isinstance(x.get("rule_features"), Mapping)]
        if any(bool(f.get("is_contestation")) for f in features):
            if any(bool(f.get("mentions_preliminary")) for f in features):
                return "REPLY_PRELIMINARY", ("CPC_ART_351_REPLY_PRELIMINARY",)
            if any(bool(f.get("mentions_new_fact")) for f in features):
                return "REPLY_NEW_FACT", ("CPC_ART_350_REPLY_NEW_FACT",)
            # A contestation must never be downgraded to a document response
            # merely because its summary mentions documents. Without a more
            # specific art. 350/351 feature, abstain into residual/review path.
            return "RESIDUAL_PARTY_ACT", ("CPC_ART_218_P3_RESIDUAL",)
        if any(bool(f.get("document_submission")) for f in features):
            return "DOCUMENT_RESPONSE", ("CPC_ART_437_P1_DOCUMENT_RESPONSE",)
        if "preliminar" in normalized or "art. 337" in normalized or "artigo 337" in normalized:
            return "REPLY_PRELIMINARY", ("CPC_ART_351_REPLY_PRELIMINARY",)
        if any(x in normalized for x in ("impeditivo", "modificativo", "extintivo")):
            return "REPLY_NEW_FACT", ("CPC_ART_350_REPLY_NEW_FACT",)
        if "documento" in normalized:
            return "DOCUMENT_RESPONSE", ("CPC_ART_437_P1_DOCUMENT_RESPONSE",)
        return "RESIDUAL_PARTY_ACT", ("CPC_ART_218_P3_RESIDUAL",)
    return act, ()

def resolve_specialist_rule(
    output: DeadlineSpecialistOutput,
    legal_context: LegalContext | None,
    *,
    context: Iterable[Mapping[str, Any]] = (),
    relevant_date: str | None = None,
) -> dict[str, Any]:
    if not output.operative_instruction:
        return {"resolved_rule_id": None, "review_required": False, "resolution_method": "NOT_OPERATIVE"}
    if output.explicit_term_unit == "DATE_CERTAIN":
        return {"resolved_rule_id": None, "review_required": False, "resolution_method": "DATE_CERTAIN_OBSERVED"}
    if legal_context is None:
        return {"resolved_rule_id": None, "review_required": True, "resolution_method": "LEGAL_CONTEXT_MISSING"}
    catalog_act, candidates = _catalog_act(output, context)
    # Restrict candidates to the resolved legal regime before invoking the legal resolver.
    catalog = get_catalog()
    compatible_ids = []
    compatible_rules = []
    for rule_id in candidates:
        rule = next((r for r in catalog if r["rule_id"] == rule_id), None)
        if rule and str(rule.get("base_regime") or "").upper() in legal_context.applicable_regimes:
            compatible_ids.append(rule_id)
            compatible_rules.append(rule)

    # A number stated in the order may merely restate a statutory deadline.
    # When the classified act has a specific compatible rule with the same
    # duration, keep the observed term on the instruction/obligation but let
    # the deterministic resolver retain the statutory rule identity.
    explicit_value = output.explicit_term_value
    explicit_unit = output.explicit_term_unit
    statutory_confirmation = (
        explicit_value is not None
        and bool(compatible_rules)
        and any(
            int(rule.get("term_value") or rule.get("default_term_value") or -1) == explicit_value
            and rule.get("category") != "JUDICIAL_ORDER"
            for rule in compatible_rules
        )
    )
    return resolve_deadline_rule(
        legal_context=legal_context,
        procedural_act_type=catalog_act or "RESIDUAL_PARTY_ACT",
        explicit_term_value=None if statutory_confirmation else explicit_value,
        explicit_term_unit=None if statutory_confirmation else explicit_unit,
        candidate_rule_ids=compatible_ids,
        recipient_role=output.recipient_role,
        relevant_date=relevant_date,
        catalog=catalog,
    )

def deadline_candidate_windows(text: str) -> tuple[str, ...]:
    """Split operative text at sentence and numbered-item boundaries."""
    source = " ".join(str(text or "").split())
    if not source:
        return ()
    # Numbered rulings commonly contain several independent determinations in
    # one sentence. Split before each item marker, then preserve each item as
    # its own semantic unit.
    item_starts = [m.start() for m in re.finditer(r"(?:^|\s)(?:\(?\d{1,2}[.)]|[IVXLCDM]{1,6}[.)])\s+", source, re.I)]
    boundaries = {0, len(source)}
    for match in re.finditer(r"[.;!?](?=\s|$)", source):
        if match.group(0) == ".":
            prefix = source[max(0, match.start() - 16):match.start()].casefold()
            if re.search(r"\b(?:art|fls?|n|nº|dr|dra|etc)$", prefix):
                continue
        boundaries.add(match.end())
    boundaries.update(item_starts)
    ordered = sorted(boundaries)
    segments: list[str] = []
    for left, right in zip(ordered, ordered[1:]):
        segment = source[left:right].strip(" .;-")
        segment = re.sub(r"^(?:\(?\d{1,2}[.)]|[IVXLCDM]{1,6}[.)])\s+", "", segment, flags=re.I)
        if segment:
            segments.append(segment)

    # Attach a detached term/date sentence to the immediately preceding
    # instruction, never across another numbered item or operative command.
    merged: list[str] = []
    for segment in segments:
        if merged and not _JUDICIAL_VERB.search(segment) and (_TERM.search(segment) or _DATE.search(segment)):
            merged[-1] = f"{merged[-1]}. {segment}"
        else:
            merged.append(segment)

    windows: list[str] = []
    for segment in merged:
        verbs = list(_JUDICIAL_VERB.finditer(segment))
        if not verbs:
            # A court can state a deadline declaratively, e.g. "O prazo para
            # oferta de contestação será de 15 dias úteis".
            if (_TERM.search(segment) or _DATE.search(segment)) and segment not in windows:
                windows.append(segment)
            continue
        # Multiple determinations within a segment start independent windows.
        starts = [0] + [m.start() for m in verbs[1:]]
        ends = starts[1:] + [len(segment)]
        for start, end in zip(starts, ends):
            window = segment[start:end].strip(" .;-")
            if window and window not in windows:
                windows.append(window)
    return tuple(windows)


def is_party_deadline_candidate(text: str) -> bool:
    """Whether a window contains a party act or an explicit temporal term."""
    value = str(text or "")
    return bool(_PARTY_ACTION.search(value) or _TERM.search(value) or _DATE.search(value))
