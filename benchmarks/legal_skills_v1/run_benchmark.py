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
        "actor": None,
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
    else:
        raise ValueError(f"skill desconhecida: {skill}")

    raw, perf = call_ollama(
        model,
        system,
        json.dumps(skill_input, ensure_ascii=False),
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
        summary[skill] = block
    return summary


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", default="gemma4:e4b")
    ap.add_argument("--cases", default=str(Path(__file__).with_name("cases.jsonl")))
    ap.add_argument("--output", required=True)
    args = ap.parse_args()

    cases = [
        json.loads(line)
        for line in Path(args.cases).read_text(encoding="utf-8-sig").splitlines()
        if line.strip()
    ]
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
