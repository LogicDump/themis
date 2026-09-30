from __future__ import annotations

import argparse
import json
import re
import sys
import time
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.documentos.deadline_specialist_contract_v1 import ContextRequest, DeadlineSpecialistOutput, score_specialist_output

ALLOWED_ACT_TYPES = [
    "PROVIDE_DOCUMENTS", "PROVIDE_INFORMATION", "RESPOND_TO_OPPOSING_SUBMISSION",
    "SPECIFY_EVIDENCE", "MANIFEST_AFTER_MEASURE", "FILE_MEMORIALS", "FILE_DEFENSE",
]


JSON_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "required": ["operative_instruction", "context_sufficiency", "procedural_act_type", "action_text", "recipient_text", "recipient_role", "recipient_participant_ids", "explicit_term_value", "explicit_term_unit", "explicit_term_date", "trigger_text", "antecedent_source_event_id", "candidate_antecedent_event_ids", "candidate_rule_ids", "model_preferred_rule_id", "context_requests", "source_spans", "confidence"],
    "properties": {
        "operative_instruction": {"type": "boolean"},
        "context_sufficiency": {"type": "string", "enum": ["SUFFICIENT", "NEEDS_CONTEXT", "AMBIGUOUS_REVIEW"]},
        "procedural_act_type": {"anyOf": [{"type": "string", "enum": ALLOWED_ACT_TYPES}, {"type": "null"}]},
        "action_text": {"type": ["string", "null"]},
        "recipient_text": {"type": ["string", "null"]},
        "recipient_role": {"type": "string", "enum": ["PLAINTIFF", "DEFENDANT", "BOTH_PARTIES", "THIRD_PARTY", "PROSECUTOR", "EXPERT", "WITNESS", "COURT_AUXILIARY", "OTHER", "UNRESOLVED"]},
        "recipient_participant_ids": {"type": "array", "items": {"type": "string"}},
        "explicit_term_value": {"type": ["integer", "null"], "minimum": 1},
        "explicit_term_unit": {"type": "string", "enum": ["DAYS", "BUSINESS_DAYS", "HOURS", "MONTHS", "DATE_CERTAIN", "UNSPECIFIED"]},
        "explicit_term_date": {"type": ["string", "null"]},
        "trigger_text": {"type": ["string", "null"]},
        "antecedent_source_event_id": {"type": ["string", "null"]},
        "candidate_antecedent_event_ids": {"type": "array", "items": {"type": "string"}},
        "candidate_rule_ids": {"type": "array", "items": {"type": "string"}},
        "model_preferred_rule_id": {"type": ["string", "null"]},
        "context_requests": {"type": "array", "items": {"type": "object", "additionalProperties": False, "required": ["kind", "reason", "purpose", "query_hint", "candidate_event_ids"], "properties": {
            "kind": {"type": "string", "enum": ["ANTECEDENT_PLEADING", "COMMUNICATION_EVENT", "PROCESS_PARTICIPANTS", "LEGAL_CONTEXT", "PROCEDURAL_ACT_CONTEXT", "SOURCE_DOCUMENT"]},
            "reason": {"type": "string"}, "purpose": {"type": "string", "enum": ["SEMANTIC_RESOLUTION", "TRIGGER_RESOLUTION", "RULE_RESOLUTION"]},
            "query_hint": {"type": ["string", "null"]}, "candidate_event_ids": {"type": "array", "items": {"type": "string"}}
        }}},
        "source_spans": {"type": "array", "items": {"type": "object"}},
        "confidence": {"type": "object", "additionalProperties": {"type": "number", "minimum": 0, "maximum": 1}}
    }
}
SYSTEM = '''Você é um extrator jurídico especializado. Sua função é extrair fatos semânticos do trecho e decidir se o contexto fornecido é suficiente. Você NÃO calcula data de vencimento, NÃO inventa termo inicial, NÃO escolhe regra legal sem base e NÃO presume quem é "parte contrária" sem resolver o antecedente relevante.

Estados obrigatórios para SUFICIÊNCIA SEMÂNTICA do ato:
- SUFFICIENT: o trecho/contexto basta para entender semanticamente a instrução e preencher os campos do ato. Ainda pode haver context_requests com purpose TRIGGER_RESOLUTION ou RULE_RESOLUTION para etapas posteriores.
- NEEDS_CONTEXT: falta material para resolver semanticamente o próprio ato. Inclua ao menos um context_request com purpose SEMANTIC_RESOLUTION.
- AMBIGUOUS_REVIEW: há múltiplas interpretações semânticas plausíveis mesmo com o contexto disponível; preserve candidatos quando existirem.

Cada context_request também declara purpose:
- SEMANTIC_RESOLUTION: contexto necessário para entender o ato, destinatário ou antecedente.
- TRIGGER_RESOLUTION: contexto necessário para localizar o fato/comunicação que inicia a contagem; isso NÃO torna a semântica do ato insuficiente.
- RULE_RESOLUTION: contexto necessário para escolher a regra jurídica aplicável; isso NÃO torna a semântica do ato insuficiente.

NÃO peça contexto apenas para obter detalhes que não são necessários aos campos deste contrato. Exemplos: para "apresentar os documentos solicitados", não é necessário conhecer a lista dos documentos para classificar PROVIDE_DOCUMENTS; para "parte requerida", o papel DEFENDANT basta e recipient_participant_ids pode permanecer []; a identidade canônica do participante só é necessária quando o próprio texto depende de referência externa, como "a terceira interessada mencionada na capa".

Use cada tipo de contexto somente assim:
- ANTECEDENT_PLEADING: para resolver referência relacional como "parte contrária" ou ato antecedente relevante.
- COMMUNICATION_EVENT: para localizar ciência/intimação/publicação/recebimento que aciona o prazo.
- PROCESS_PARTICIPANTS: para resolver identidade canônica de participante mencionada indiretamente.
- LEGAL_CONTEXT: para escolher regime/classe/regra material aplicável.
- PROCEDURAL_ACT_CONTEXT: somente quando o próprio tipo/significado do ato não pode ser classificado pelo trecho atual.
- SOURCE_DOCUMENT: somente quando o trecho está truncado/incompleto e o documento-fonte é indispensável.

Recipient roles permitidos: PLAINTIFF, DEFENDANT, BOTH_PARTIES, THIRD_PARTY, PROSECUTOR, EXPERT, WITNESS, COURT_AUXILIARY, OTHER, UNRESOLVED.
Term units permitidos: DAYS, BUSINESS_DAYS, HOURS, MONTHS, DATE_CERTAIN, UNSPECIFIED.
Procedural act types:
- PROVIDE_DOCUMENTS: apresentar/juntar documentos.
- PROVIDE_INFORMATION: prestar/informar dados ou esclarecimentos.
- RESPOND_TO_OPPOSING_SUBMISSION: manifestar-se sobre petição/ato da parte adversa.
- SPECIFY_EVIDENCE: indicar/especificar provas.
- MANIFEST_AFTER_MEASURE: manifestar-se após cumprimento/efetivação de medida.
- FILE_MEMORIALS: apresentar memoriais.
- FILE_DEFENSE: apresentar contestação/defesa.
Se não houver instrução operativa dirigida a parte/terceiro, use procedural_act_type=null. Pedido formulado por uma parte NÃO é ordem judicial.

Responda SOMENTE com um objeto JSON válido, sem markdown, sem explicação externa, contendo exatamente estas chaves:
operative_instruction, context_sufficiency, procedural_act_type, action_text, recipient_text, recipient_role, recipient_participant_ids, explicit_term_value, explicit_term_unit, explicit_term_date, trigger_text, antecedent_source_event_id, candidate_antecedent_event_ids, candidate_rule_ids, model_preferred_rule_id, context_requests, source_spans, confidence.

context_requests é uma lista de objetos {kind, reason, purpose, query_hint, candidate_event_ids}. Use [] quando não precisar de contexto. Não inclua due_date nem faça aritmética de prazo.'''


def _request_json(url: str, payload: dict, timeout: int = 180) -> dict:
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(url, data=body, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8"))


def call_ollama(model: str, prompt: str) -> tuple[str, dict]:
    payload = {
        "model": model,
        "system": SYSTEM,
        "prompt": prompt,
        "stream": False,
        "think": False,
        "format": JSON_SCHEMA,
        "options": {"temperature": 0, "seed": 42, "num_predict": 900},
    }
    started = time.perf_counter()
    data = _request_json("http://127.0.0.1:11434/api/generate", payload)
    elapsed = time.perf_counter() - started
    return str(data.get("response", "")), {
        "elapsed_s": elapsed,
        "prompt_eval_count": data.get("prompt_eval_count"),
        "eval_count": data.get("eval_count"),
        "load_duration_ns": data.get("load_duration"),
        "prompt_eval_duration_ns": data.get("prompt_eval_duration"),
        "eval_duration_ns": data.get("eval_duration"),
    }


def call_openai(base_url: str, model: str, prompt: str) -> tuple[str, dict]:
    payload = {
        "model": model,
        "messages": [{"role": "system", "content": SYSTEM}, {"role": "user", "content": prompt}],
        "temperature": 0,
        "max_tokens": 1800,
        "stream": False,
        "response_format": {"type": "json_schema", "json_schema": {"name": "deadline_specialist", "schema": JSON_SCHEMA, "strict": True}},
    }
    started = time.perf_counter()
    data = _request_json(base_url.rstrip("/") + "/v1/chat/completions", payload)
    elapsed = time.perf_counter() - started
    text = data["choices"][0]["message"].get("content") or ""
    usage = data.get("usage") or {}
    return text, {"elapsed_s": elapsed, "prompt_eval_count": usage.get("prompt_tokens"), "eval_count": usage.get("completion_tokens")}


def extract_json(text: str) -> dict:
    text = text.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text)
        text = re.sub(r"\s*```$", "", text)
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        start, end = text.find("{"), text.rfind("}")
        if start >= 0 and end > start:
            return json.loads(text[start:end + 1])
        raise


def to_output(data: dict) -> tuple[DeadlineSpecialistOutput, list[str]]:
    schema_warnings: list[str] = []
    confidence_raw = data.get("confidence") or {}
    if not isinstance(confidence_raw, dict):
        schema_warnings.append("confidence_not_object")
        confidence_raw = {}
    requests_raw = data.get("context_requests") or ()
    if not isinstance(requests_raw, (list, tuple)):
        schema_warnings.append("context_requests_not_array")
        requests_raw = ()
    operative_raw = data.get("operative_instruction")
    if not isinstance(operative_raw, bool):
        schema_warnings.append("operative_instruction_not_boolean")
    if isinstance(operative_raw, str):
        operative_value = operative_raw.strip().casefold() not in {"", "false", "não", "nao", "no"}
    else:
        operative_value = bool(operative_raw)
    term_value = data.get("explicit_term_value")
    if isinstance(term_value, str) and term_value.strip().isdigit():
        schema_warnings.append("explicit_term_value_string_coerced")
        term_value = int(term_value.strip())
    context_sufficiency = str(data.get("context_sufficiency") or "").upper()
    recipient_role = str(data.get("recipient_role") or "UNRESOLVED").upper()
    explicit_term_unit = str(data.get("explicit_term_unit") or "UNSPECIFIED").upper()
    antecedent_source_event_id = data.get("antecedent_source_event_id")
    candidate_antecedents = tuple(str(x) for x in data.get("candidate_antecedent_event_ids") or ())
    if antecedent_source_event_id and str(antecedent_source_event_id) in candidate_antecedents:
        schema_warnings.append("resolved_antecedent_repeated_as_candidate")
        candidate_antecedents = tuple(x for x in candidate_antecedents if x != str(antecedent_source_event_id))
    normalized_requests = []
    for item in requests_raw:
        if not isinstance(item, dict) or not item.get("kind"):
            continue
        kind = str(item.get("kind"))
        purpose = str(item.get("purpose") or "SEMANTIC_RESOLUTION")
        if kind in {"SEMANTIC_RESOLUTION", "TRIGGER_RESOLUTION", "RULE_RESOLUTION"} and purpose in {"ANTECEDENT_PLEADING", "COMMUNICATION_EVENT", "PROCESS_PARTICIPANTS", "LEGAL_CONTEXT", "PROCEDURAL_ACT_CONTEXT", "SOURCE_DOCUMENT"}:
            schema_warnings.append("context_kind_purpose_swapped")
            kind, purpose = purpose, kind
        normalized_requests.append(ContextRequest(
            kind=kind,
            reason=str(item.get("reason") or "contexto adicional necessário"),
            purpose=purpose,
            query_hint=item.get("query_hint"),
            candidate_event_ids=tuple(str(x) for x in item.get("candidate_event_ids") or ()),
        ))
    requests = tuple(normalized_requests)
    output = DeadlineSpecialistOutput(
        operative_instruction=operative_value,
        context_sufficiency=context_sufficiency,
        procedural_act_type=data.get("procedural_act_type"),
        action_text=data.get("action_text"),
        recipient_text=data.get("recipient_text"),
        recipient_role=recipient_role,
        recipient_participant_ids=tuple(str(x) for x in data.get("recipient_participant_ids") or ()),
        explicit_term_value=term_value,
        explicit_term_unit=explicit_term_unit,
        explicit_term_date=data.get("explicit_term_date"),
        trigger_text=data.get("trigger_text"),
        antecedent_source_event_id=antecedent_source_event_id,
        candidate_antecedent_event_ids=candidate_antecedents,
        candidate_rule_ids=tuple(str(x) for x in data.get("candidate_rule_ids") or ()),
        model_preferred_rule_id=data.get("model_preferred_rule_id"),
        context_requests=requests,
        source_spans=tuple(data.get("source_spans") or ()),
        confidence={str(k): float(v) for k, v in confidence_raw.items() if isinstance(v, (int, float)) and not isinstance(v, bool)},
    )
    return output, schema_warnings


def expected_output(data: dict) -> DeadlineSpecialistOutput:
    requests = tuple(ContextRequest(kind=x["kind"], reason=x["reason"], purpose=x.get("purpose", "SEMANTIC_RESOLUTION"), query_hint=x.get("query_hint"), candidate_event_ids=tuple(x.get("candidate_event_ids") or ())) for x in data.get("context_requests") or ())
    return DeadlineSpecialistOutput(
        operative_instruction=data["operative_instruction"], context_sufficiency=data["context_sufficiency"],
        procedural_act_type=data.get("procedural_act_type"), recipient_role=data.get("recipient_role", "UNRESOLVED"),
        recipient_participant_ids=tuple(data.get("recipient_participant_ids") or ()),
        explicit_term_value=data.get("explicit_term_value"), explicit_term_unit=data.get("explicit_term_unit", "UNSPECIFIED"),
        explicit_term_date=data.get("explicit_term_date"), antecedent_source_event_id=data.get("antecedent_source_event_id"),
        candidate_antecedent_event_ids=tuple(data.get("candidate_antecedent_event_ids") or ()),
        model_preferred_rule_id=data.get("model_preferred_rule_id"), context_requests=requests,
    )


def make_prompt(case: dict) -> str:
    return "TRECHO:\n" + case["excerpt"] + "\n\nCONTEXTO FORNECIDO:\n" + json.dumps(case.get("context") or [], ensure_ascii=False, indent=2)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--backend", choices=("ollama", "openai"), required=True)
    ap.add_argument("--model", required=True)
    ap.add_argument("--base-url", default="http://127.0.0.1:18081")
    ap.add_argument("--cases", default=str(Path(__file__).with_name("cases.jsonl")))
    ap.add_argument("--output", required=True)
    args = ap.parse_args()
    cases = [json.loads(line) for line in Path(args.cases).read_text(encoding="utf-8-sig").splitlines() if line.strip()]
    results = []
    for index, case in enumerate(cases, 1):
        prompt = make_prompt(case)
        raw = ""
        try:
            raw, perf = call_ollama(args.model, prompt) if args.backend == "ollama" else call_openai(args.base_url, args.model, prompt)
            actual, schema_warnings = to_output(extract_json(raw))
            expected = expected_output(case["expected"])
            score = score_specialist_output(expected, actual)
            parse_error = None
        except Exception as exc:
            perf = {}
            score = {"field_accuracy": 0.0, "context_need_recall": 0.0, "context_need_precision": 0.0, "dangerous_false_resolution": False, "safe_abstention": False, "field_results": {}}
            parse_error = f"{type(exc).__name__}: {exc}"
            actual = None
            schema_warnings = []
        row = {"id": case["id"], "score": score, "performance": perf, "parse_error": parse_error, "schema_warnings": schema_warnings, "raw": raw, "actual": actual.as_dict() if actual else None}
        results.append(row)
        print(f"[{index:02d}/{len(cases)}] {case['id']}: acc={score['field_accuracy']:.3f} dangerous={score['dangerous_false_resolution']} error={parse_error}", flush=True)
    valid = [r for r in results if not r["parse_error"]]
    summary = {
        "backend": args.backend, "model": args.model, "cases": len(results), "parsed": len(valid),
        "mean_field_accuracy": sum(r["score"]["field_accuracy"] for r in results) / len(results),
        "mean_context_need_recall": sum(r["score"]["context_need_recall"] for r in results) / len(results),
        "mean_context_need_precision": sum(r["score"]["context_need_precision"] for r in results) / len(results),
        "dangerous_false_resolutions": sum(bool(r["score"]["dangerous_false_resolution"]) for r in results),
        "safe_abstentions": sum(bool(r["score"]["safe_abstention"]) for r in results),
        "mean_elapsed_s": sum(float(r["performance"].get("elapsed_s") or 0) for r in results) / len(results),
    }
    Path(args.output).write_text(json.dumps({"summary": summary, "results": results}, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
