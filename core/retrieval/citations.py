"""Mecanismo de citações processuais verificáveis para o Themis.

 Gera referências [1], [2] vinculadas estritamente aos Autos (processo, documento, fólio,
página PDF e trecho literal), garantindo verificação e navegação direta ao PDF original.
"""
from __future__ import annotations

import json
import re
import sqlite3
from pathlib import Path
from typing import Any, Callable

CITATION_REGEX = re.compile(r"\[(?:Fonte\s*)?(\d+)(?:\s*,\s*(?:Fonte\s*)?(\d+))*\]", re.IGNORECASE)
SINGLE_CITATION_REGEX = re.compile(r"\[(\d+)\]")


def build_citation_prompt_context(sources: list[dict[str, Any]]) -> str:
    """Constrói o bloco textual de contexto enumerado para o LLM gerar citações [1], [2]."""
    context_parts: list[str] = []
    for idx, s in enumerate(sources, start=1):
        sref = s.get("source_ref", {})
        doc_id = sref.get("document_id") or s.get("document_id", "doc")
        folio = sref.get("process_folio")
        pdf_page = sref.get("pdf_page") or s.get("page_number") or "?"
        folio_str = f"Fls. {folio}" if folio is not None else f"Pág. PDF {pdf_page}"
        doc_str = f"Doc {doc_id[:8]}" if len(str(doc_id)) >= 8 else f"Doc {doc_id}"
        excerpt = s.get("excerpt", "").strip()
        movement_sequence = s.get("movement_sequence")
        movement_title = s.get("movement_title")
        movement_str = ""
        if movement_sequence is not None:
            movement_str = f" | Movement {movement_sequence}"
            if movement_title:
                movement_str += f": {movement_title}"

        context_parts.append(
            f"[{idx}] ({folio_str} | Pág. {pdf_page} | {doc_str}{movement_str}):\n{excerpt}"
        )
    return "\n\n".join(context_parts)


def resolve_verifiable_citations(
    answer_text: str,
    sources: list[dict[str, Any]],
    process_id: str,
) -> dict[str, Any]:
    """Extrai e valida todas as citações [1], [2] presentes no texto da resposta.

    Garante que cada afirmação citada corresponda estritamente a uma fonte recuperada,
    sem inventar referências não existentes.
    """
    source_map: dict[int, dict[str, Any]] = {idx: s for idx, s in enumerate(sources, start=1)}

    # Encontra todos os índices numéricos citados no texto
    cited_indices: list[int] = []
    for match in SINGLE_CITATION_REGEX.finditer(answer_text):
        try:
            num = int(match.group(1))
            if num not in cited_indices:
                cited_indices.append(num)
        except ValueError:
            pass

    citations: list[dict[str, Any]] = []
    invalid_citations: list[int] = []

    for idx in cited_indices:
        if idx in source_map:
            src = source_map[idx]
            sref = src.get("source_ref", {})
            doc_id = sref.get("document_id") or src.get("document_id", "")
            pdf_page = sref.get("pdf_page") or src.get("page_number") or 1
            folio = sref.get("process_folio")
            folio_res = sref.get("folio_resolution")
            excerpt = src.get("excerpt", "")
            evidence = src.get("evidence") or []

            autos_nav = src.get("autos_navigation") or {
                "process_id": process_id,
                "document_id": doc_id,
                "page": pdf_page,
                "folio": folio,
                "target_text": excerpt[:200],
                "autos_path": f"/processes/{process_id}/autos",
            }

            citations.append({
                "citation_ref": f"[{idx}]",
                "index": idx,
                "process_id": process_id,
                "document_id": doc_id,
                "pdf_page": pdf_page,
                "process_folio": folio,
                "folio_resolution": folio_res,
                "excerpt": excerpt,
                "evidence": evidence,
                "autos_navigation": autos_nav,
                "verified": True,
            })
        else:
            invalid_citations.append(idx)

    # Ordena as citações pelo índice numérico
    citations.sort(key=lambda c: c["index"])

    return {
        "citations": citations,
        "citation_count": len(citations),
        "invalid_citations": invalid_citations,
        "has_unverified_citations": len(invalid_citations) > 0,
        "all_citations_verified": len(invalid_citations) == 0,
    }


def synthesize_answer_with_citations(
    process_id: str,
    query: str,
    sources: list[dict[str, Any]],
    llm_caller: Callable[[str, str], str] | None = None,
) -> dict[str, Any]:
    """Gera síntese fundamentada com citações verificáveis e links para os Autos."""
    if not sources:
        return {
            "answer": "Os Autos recuperados não contêm contexto suficiente para responder com segurança.",
            "citations": [],
            "sources": [],
            "process_id": process_id,
            "query": query,
        }

    context_text = build_citation_prompt_context(sources)
    hierarchical_sources = any(source.get("movement_sequence") is not None for source in sources)

    system_prompt = (
        "Você é o assistente processual do sistema Jurídico. "
        "Responda à pergunta do usuário baseando-se estritamente nos trechos dos Autos fornecidos no contexto.\n"
        "REGRAS OBRIGATÓRIAS DE CITAÇÃO:\n"
        "1. Para toda afirmação baseada nos trechos, inclua imediatamente a citação correspondente no formato [1], [2], etc.\n"
        "2. Use exclusivamente os números de fonte fornecidos no contexto (ex: [1], [2]). Nunca invente fontes ou numerações.\n"
        "3. Se houver informações divergentes ou preliminares, aponte explicitamente indicando as respectivas fontes.\n"
        "4. Se o contexto não contiver dados suficientes, declare com clareza o que consta e o que não foi localizado nos Autos."
    )
    if hierarchical_sources:
        system_prompt += (
            "\n5. Quando Movements diferentes trouxerem pedidos/valores distintos sobre o mesmo tema, "
            "exponha a evolução na ordem processual indicada e cite a passagem própria de cada afirmação."
            "\n6. Se a pergunta delimitar inicial ou posterior, responda dentro desse recorte usando a passagem do Movement correspondente."
        )

    user_prompt = (
        f"Contexto dos Autos do Processo {process_id}:\n\n"
        f"{context_text}\n\n"
        f"Pergunta: {query}\n\n"
        "Resposta fundamentada com citações [1], [2]:"
    )

    if llm_caller is not None:
        raw_answer = llm_caller(system_prompt, user_prompt)
    else:
        lines = [f"Com base nos Autos do Processo {process_id}:"]
        if hierarchical_sources:
            # Keep process-order evolution explicit. Each separate request is
            # grounded by its own excerpt and citation.
            for idx, src in enumerate(sources, start=1):
                sref = src.get("source_ref", {})
                folio = sref.get("process_folio")
                folio_str = f"fls. {folio}" if folio is not None else f"pág. {sref.get('pdf_page', idx)}"
                excerpt = src.get("excerpt", "").strip()
                sequence = src.get("movement_sequence")
                title = src.get("movement_title")
                phase = "Na inicial" if int(sequence or 0) == 1 else f"Posteriormente, no Movement {sequence}"
                if title:
                    phase += f" ({title})"
                lines.append(f"- {phase}, {folio_str}, consta a seguinte passagem:")
                lines.extend(f"  > {line}" if line else "  >" for line in excerpt.splitlines())
                lines.append(f"  [{idx}]")
        else:
            # Preserve the established compact fallback for ordinary RRF sources.
            for idx, src in enumerate(sources[:3], start=1):
                sref = src.get("source_ref", {})
                folio = sref.get("process_folio")
                folio_str = f"fls. {folio}" if folio is not None else f"pág. {sref.get('pdf_page', idx)}"
                excerpt_short = src.get("excerpt", "").strip().replace("\n", " ")
                if len(excerpt_short) > 160:
                    excerpt_short = excerpt_short[:160] + "..."
                lines.append(f"- Conforme {folio_str} [{idx}]: \"{excerpt_short}\"")
        raw_answer = "\n".join(lines)

    citation_resolution = resolve_verifiable_citations(raw_answer, sources, process_id)

    return {
        "answer": raw_answer,
        "citations": citation_resolution["citations"],
        "sources": sources,
        "process_id": process_id,
        "query": query,
        "all_citations_verified": citation_resolution["all_citations_verified"],
    }
