# Deadline Specialist Benchmark V1

## Purpose

The specialist never calculates a due date. It extracts semantic facts from the current act and declares which additional process context, if any, is still required by later deterministic stages.

The benchmark rewards both correct extraction and calibrated retrieval: models must ask for missing context when it is genuinely necessary, but must not over-request irrelevant process material.

## Semantic sufficiency states

- `SUFFICIENT`: the supplied excerpt/context is enough to understand the operative act and fill the specialist semantic fields. This state may still carry downstream `TRIGGER_RESOLUTION` or `RULE_RESOLUTION` requests.
- `NEEDS_CONTEXT`: another process source is required to resolve the semantics of the act itself. At least one `SEMANTIC_RESOLUTION` request is mandatory.
- `AMBIGUOUS_REVIEW`: multiple plausible semantic interpretations remain after the available context; preserve candidates and require review.

`SUFFICIENT` must never contain a `SEMANTIC_RESOLUTION` request.

## Context request purposes

Every request has both a `kind` and a `purpose`.

Purposes:

- `SEMANTIC_RESOLUTION`: needed to understand the act, recipient, relation, or antecedent.
- `TRIGGER_RESOLUTION`: needed to locate the communication/fact that starts deadline counting; this does not make the act semantically insufficient.
- `RULE_RESOLUTION`: needed to select the applicable legal rule/regime; this does not make the act semantically insufficient.

Kinds:

`ANTECEDENT_PLEADING`, `COMMUNICATION_EVENT`, `PROCESS_PARTICIPANTS`, `LEGAL_CONTEXT`, `PROCEDURAL_ACT_CONTEXT`, `SOURCE_DOCUMENT`.

Examples:

- `"Manifeste-se a parte contrária"` without the relevant antecedent → `NEEDS_CONTEXT` + `SEMANTIC_RESOLUTION/ANTECEDENT_PLEADING`.
- A third-party order with an explicit 10-day term but no proof of receipt → semantic `SUFFICIENT` + `TRIGGER_RESOLUTION/COMMUNICATION_EVENT`.
- `"Cite-se para apresentar contestação"` without the process legal regime → semantic `SUFFICIENT` + `RULE_RESOLUTION/LEGAL_CONTEXT`.

These requests are retrieval intents, not answers. A future retrieval loop may satisfy them from ProcessEvent, participants, Autos metadata, communications, or other process sources and rerun only the stage that still lacks evidence.

## Safety invariants

A model receives no credit for inventing a communication date, antecedent, canonical participant, legal rule, or due date. It must not infer that a document date or file-release date is the communication trigger unless evidence says so.

A false semantic `SUFFICIENT` when the golden requires `NEEDS_CONTEXT` is recorded as `dangerous_false_resolution`. Missing or unnecessary downstream requests are measured separately through context-request precision/recall.

The model must also distinguish judicial/court instructions from a request merely made by a party.

## Evaluation families

The same semantic contract is used for deterministic baselines, Legal-BERTimbau/task heads, PTT5, EmbeddingGemma/task heads, Gemma 4 E2B, and Gemma 4 E4B. Generative models may emit constrained JSON; encoder models populate the same contract through trained heads.

Zero-shot prototype similarity and zero-shot small seq2seq generation are exploratory baselines only; they are not equivalent to a trained specialist.

## Public repository rule

Goldens committed to this repository must be synthetic or irreversibly sanitized. Real process text, names, CPF/CNPJ, case numbers, addresses, and confidential facts remain local/private and are never committed to the public repository.
