from __future__ import annotations

import argparse
import json
import sys
import time
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.legal_skills.actor_role_v1 import (
    ACTOR_ROLE_JSON_SCHEMA,
    build_actor_role_input,
    build_actor_role_instructions,
    score_actor_role,
    validate_actor_role,
)
from core.legal_skills.fact_extractor_v1 import (
    FACT_EXTRACTOR_JSON_SCHEMA,
    build_fact_extractor_input,
    build_fact_extractor_instructions,
    score_fact_extraction,
    validate_fact_extraction,
)
from core.legal_skills.claim_request_v1 import (
    CLAIM_REQUEST_JSON_SCHEMA,
    build_claim_request_input,
    build_claim_request_instructions,
    score_claim_request,
    validate_claim_request,
)
from core.legal_skills.evidence_mapper_v1 import (
    EVIDENCE_MAPPER_JSON_SCHEMA,
    build_evidence_mapper_input,
    build_evidence_mapper_instructions,
    score_evidence_mapping,
    validate_evidence_mapping,
)
from core.legal_skills.contradiction_detector_v1 import (
    CONTRADICTION_JSON_SCHEMA,
    build_contradiction_input,
    build_contradiction_instructions,
    build_contradiction_llm_input,
    score_contradictions,
    validate_contradictions,
)


def _request_json(url: str, payload: dict, timeout: int = 180) -> dict:
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(url, data=body, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8"))


def call_ollama(model: str, system: str, prompt: str, schema: dict) -> tuple[str, dict]:
    payload = {
        "model": model,
        "system": system,
        "prompt": prompt,
        "stream": False,
        "think": False,
        "format": schema,
        "options": {"temperature": 0, "seed": 42, "num_predict": 1400},
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


def source_from_case(case: dict) -> dict:
    return {
        "process_id": "bench_proc",
        "movement_id": case["id"],
        "title": "Benchmark",
        "actor": case.get("actor"),
        "occurred_at": None,
        "movement_type": "Benchmark",
        "pages": [{
            "document_id": "doc1",
            "pdf_page": 1,
            "content": case["text"],
        }],
    }


def frame_from_case(case: dict) -> dict:
    return {
        "process_id": "bench_proc",
        "participants": case.get("participants") or [],
        "representations": case.get("representations") or [],
    }


def actor_case_input(case: dict) -> dict:
    return build_actor_role_input(source_from_case(case), frame_from_case(case))


def fact_case_input(case: dict) -> dict:
    actor_input = actor_case_input(case)
    actor_output = validate_actor_role(case["actor_output"], actor_input)
    return build_fact_extractor_input(actor_input, actor_output)


def claim_case_input(case: dict) -> dict:
    actor_input = actor_case_input(case)
    actor_output = validate_actor_role(case["actor_output"], actor_input)
    return build_claim_request_input(actor_input, actor_output)


def evidence_case_input(case: dict) -> dict:
    actor_input = actor_case_input(case)
    actor_output = validate_actor_role(case["actor_output"], actor_input)
    fact_input = build_fact_extractor_input(actor_input, actor_output)
    fact_output = validate_fact_extraction(case["fact_output"], fact_input)
    return build_evidence_mapper_input(fact_input, fact_output, case["evidence_sources"])


def contradiction_case_input(case: dict) -> dict:
    return build_contradiction_input(
        "bench_proc",
        case["fact_outputs"],
        case.get("evidence_outputs") or [],
    )


def run_case(case: dict, model: str) -> dict:
    skill = case["skill"]
    if skill == "ACTOR_ROLE":
        skill_input = actor_case_input(case)
        system = build_actor_role_instructions()
        schema = ACTOR_ROLE_JSON_SCHEMA
        validator = lambda value: validate_actor_role(value, skill_input)
        scorer = score_actor_role
    elif skill == "FACT_EXTRACTOR":
        skill_input = fact_case_input(case)
        system = build_fact_extractor_instructions()
        schema = FACT_EXTRACTOR_JSON_SCHEMA
        validator = lambda value: validate_fact_extraction(value, skill_input)
        scorer = score_fact_extraction
    elif skill == "CLAIM_REQUEST":
        skill_input = claim_case_input(case)
        system = build_claim_request_instructions()
        schema = CLAIM_REQUEST_JSON_SCHEMA
        validator = lambda value: validate_claim_request(value, skill_input)
        scorer = score_claim_request
    elif skill == "EVIDENCE_MAPPER":
        skill_input = evidence_case_input(case)
        system = build_evidence_mapper_instructions()
        schema = EVIDENCE_MAPPER_JSON_SCHEMA
        validator = lambda value: validate_evidence_mapping(value, skill_input)
        scorer = score_evidence_mapping
    elif skill == "CONTRADICTION_DETECTOR":
        skill_input = contradiction_case_input(case)
        system = build_contradiction_instructions()
        schema = CONTRADICTION_JSON_SCHEMA
        validator = lambda value: validate_contradictions(value, skill_input)
        scorer = score_contradictions
    else:
        raise ValueError(f"skill desconhecida: {skill}")

    model_input = (
        build_contradiction_llm_input(skill_input)
        if skill == "CONTRADICTION_DETECTOR"
        else skill_input
    )
    raw, perf = call_ollama(
        model,
        system,
        json.dumps(model_input, ensure_ascii=False),
        schema,
    )
    try:
        parsed = json.loads(raw)
        actual = validator(parsed)
        score = scorer(case["expected"], actual)
        error = None
    except Exception as exc:
        actual = None
        score = {}
        error = f"{type(exc).__name__}: {exc}"
    return {
        "id": case["id"],
        "skill": skill,
        "expected": case["expected"],
        "actual": actual,
        "score": score,
        "error": error,
        "raw": raw,
        "perf": perf,
    }


def summarize(results: list[dict]) -> dict:
    summary: dict[str, dict] = {}
    for skill in sorted({item["skill"] for item in results}):
        rows = [item for item in results if item["skill"] == skill]
        valid = [item for item in rows if item["error"] is None]
        block = {
            "cases": len(rows),
            "valid_outputs": len(valid),
            "parse_or_validation_failures": len(rows) - len(valid),
            "mean_elapsed_s": round(sum(item["perf"].get("elapsed_s", 0.0) for item in rows) / len(rows), 3),
        }
        if skill == "ACTOR_ROLE" and valid:
            block.update({
                "actor_precision": sum(item["score"]["actor_precision"] for item in valid) / len(valid),
                "actor_recall": sum(item["score"]["actor_recall"] for item in valid) / len(valid),
                "sufficiency_accuracy": sum(bool(item["score"]["sufficiency_match"]) for item in valid) / len(valid),
                "dangerous_false_resolution_count": sum(bool(item["score"]["dangerous_false_resolution"]) for item in valid),
            })
        elif skill == "FACT_EXTRACTOR" and valid:
            block.update({
                "fact_precision": sum(item["score"]["fact_precision"] for item in valid) / len(valid),
                "fact_recall": sum(item["score"]["fact_recall"] for item in valid) / len(valid),
                "sufficiency_accuracy": sum(bool(item["score"]["sufficiency_match"]) for item in valid) / len(valid),
                "dangerous_status_upgrade_count": sum(bool(item["score"]["dangerous_status_upgrade"]) for item in valid),
            })
        elif skill == "CLAIM_REQUEST" and valid:
            block.update({
                "legal_position_precision": sum(item["score"]["legal_position_precision"] for item in valid) / len(valid),
                "legal_position_recall": sum(item["score"]["legal_position_recall"] for item in valid) / len(valid),
                "request_precision": sum(item["score"]["request_precision"] for item in valid) / len(valid),
                "request_recall": sum(item["score"]["request_recall"] for item in valid) / len(valid),
                "sufficiency_accuracy": sum(bool(item["score"]["sufficiency_match"]) for item in valid) / len(valid),
                "actor_mismatch_count": sum(item["score"]["actor_mismatch_count"] for item in valid),
            })
        elif skill == "EVIDENCE_MAPPER" and valid:
            block.update({
                "evidence_item_precision": sum(item["score"]["evidence_item_precision"] for item in valid) / len(valid),
                "evidence_item_recall": sum(item["score"]["evidence_item_recall"] for item in valid) / len(valid),
                "evidence_link_precision": sum(item["score"]["evidence_link_precision"] for item in valid) / len(valid),
                "evidence_link_recall": sum(item["score"]["evidence_link_recall"] for item in valid) / len(valid),
                "fact_state_accuracy": sum(item["score"]["fact_state_accuracy"] for item in valid) / len(valid),
                "sufficiency_accuracy": sum(bool(item["score"]["sufficiency_match"]) for item in valid) / len(valid),
                "dangerous_support_invention_count": sum(bool(item["score"]["dangerous_support_invention"]) for item in valid),
            })
        elif skill == "CONTRADICTION_DETECTOR" and valid:
            block.update({
                "fact_pair_precision": sum(item["score"]["fact_pair_precision"] for item in valid) / len(valid),
                "fact_pair_recall": sum(item["score"]["fact_pair_recall"] for item in valid) / len(valid),
                "sufficiency_accuracy": sum(bool(item["score"]["sufficiency_match"]) for item in valid) / len(valid),
                "dangerous_direct_invention_count": sum(bool(item["score"]["dangerous_direct_invention"]) for item in valid),
                "evidence_projection_accuracy": sum(bool(item["score"]["evidence_projection_match"]) for item in valid) / len(valid),
                "mixed_evidence_accuracy": sum(bool(item["score"]["mixed_evidence_match"]) for item in valid) / len(valid),
            })
        summary[skill] = block
    return summary


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", default="gemma4:e4b")
    ap.add_argument("--cases", default=str(Path(__file__).with_name("cases.jsonl")))
    ap.add_argument("--skill", action="append", dest="skills")
    ap.add_argument("--output", required=True)
    args = ap.parse_args()

    cases = [
        json.loads(line)
        for line in Path(args.cases).read_text(encoding="utf-8-sig").splitlines()
        if line.strip()
    ]
    if args.skills:
        wanted = {str(skill).strip().upper() for skill in args.skills}
        cases = [case for case in cases if str(case.get("skill") or "").upper() in wanted]
    results = []
    for index, case in enumerate(cases, 1):
        print(f"[{index}/{len(cases)}] {case['id']} {case['skill']}", flush=True)
        try:
            result = run_case(case, args.model)
        except Exception as exc:
            result = {
                "id": case.get("id"),
                "skill": case.get("skill"),
                "expected": case.get("expected"),
                "actual": None,
                "score": {},
                "error": f"{type(exc).__name__}: {exc}",
                "raw": "",
                "perf": {},
            }
        results.append(result)

    payload = {
        "model": args.model,
        "summary": summarize(results),
        "results": results,
    }
    Path(args.output).write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(json.dumps(payload["summary"], ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
