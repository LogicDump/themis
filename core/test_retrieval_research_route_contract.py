"""Characterize Pesquisa's actual deterministic route without dashboard startup."""
import ast
import inspect
from pathlib import Path

from core.api import core_api
from core.retrieval.citations import synthesize_answer_with_citations


def test_pesquisa_route_uses_default_deterministic_answer():
    root = Path(__file__).resolve().parents[1]
    desktop = (root / "desktop/plugin.js").read_text(encoding="utf-8")
    assert 'mode === "rag" ? "/retrieval/answer" : "/retrieval/search"' in desktop
    module = ast.parse((root / "dashboard/plugin_api.py").read_text(encoding="utf-8"))
    handler = next(node for node in module.body if isinstance(node, ast.FunctionDef) and node.name == "retrieval_answer")
    call = handler.body[-1].value
    assert isinstance(call, ast.Call)
    assert ast.unparse(call.func) == "core_api.retrieval_answer"
    assert not call.args
    assert {item.arg for item in call.keywords} == {"process_id", "query", "top_k"}
    assert inspect.signature(core_api.retrieval_answer).parameters["llm_caller"].default is None
    assert inspect.signature(synthesize_answer_with_citations).parameters["llm_caller"].default is None


def test_default_synthesis_quotes_evidence_without_inventing_missing_fact():
    # Use the production default branch: no LLM caller or imitation is supplied.
    sources = [{
        "source_ref": {"process_id": "fixture", "document_id": "notice", "pdf_page": 1, "process_folio": 7},
        "movement_sequence": 2,
        "excerpt": "A vistoria foi requerida. O agendamento ainda não foi informado.",
    }]
    answer = synthesize_answer_with_citations("fixture", "Qual a data da vistoria?", sources)
    assert sources[0]["excerpt"] in answer["answer"]
    assert answer["citations"][0]["excerpt"] == sources[0]["excerpt"]
    assert answer["citations"][0]["process_folio"] == 7
    assert not any(char.isdigit() for char in sources[0]["excerpt"])
    # Any digits in the answer belong to the known process/movement/page/citation
    # framing, rather than an inferred date.
    import re
    assert not re.search(r"\d{1,2}[/.-]\d{1,2}[/.-]\d{2,4}", answer["answer"])
