# Deadline Specialist Benchmark V1

## Purpose

The specialist does not calculate a due date. It extracts semantic facts and decides whether the supplied process context is sufficient for deterministic downstream resolution.

The benchmark explicitly rewards safe requests for additional context and penalizes false resolution from an isolated excerpt.

## Output states

- `SUFFICIENT`: supplied evidence is enough for the specialist fields it is responsible for.
- `NEEDS_CONTEXT`: another process source is required. The model must name the missing context class and explain why.
- `AMBIGUOUS_REVIEW`: multiple plausible interpretations remain after the available context; preserve candidates and require review.

## Context request classes

`ANTECEDENT_PLEADING`, `COMMUNICATION_EVENT`, `PROCESS_PARTICIPANTS`, `LEGAL_CONTEXT`, `PROCEDURAL_ACT_CONTEXT`, `SOURCE_DOCUMENT`.

These are retrieval intents, not answers. A future retrieval loop may satisfy them from ProcessEvent/Autos metadata and rerun the specialist.

## Safety invariant

A model receives no credit for inventing a communication date, antecedent, recipient, legal rule, or due date. A false `SUFFICIENT` when the golden requires more context is recorded as `dangerous_false_resolution`.

## Evaluation families

The same contract must be used for deterministic baseline, Legal-BERTimbau, PTT5, EmbeddingGemma task heads, Gemma 4 E2B, and Gemma 4 E4B. Generative models may emit structured JSON; encoder models may populate the same contract through task heads.

## Public-repository rule

Goldens committed to this repository must be synthetic or irreversibly sanitized. Real process text, names, CPF/CNPJ, case numbers, addresses, and confidential facts remain local/private and are never committed to the public repository.
