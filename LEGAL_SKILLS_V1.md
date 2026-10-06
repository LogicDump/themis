# Themis — Legal Skills V1

## Princípio

A inteligência jurídica do Themis é um pipeline de skills com contratos explícitos, provenance conferível e abstenção segura. O modelo é um executor compartilhado; a skill é a unidade funcional do pipeline.

Cada skill deve ter:
- input estruturado e mínimo;
- output JSON estrito;
- provenance obrigatório para conteúdo semântico;
- estado explícito de suficiência;
- proibição documentada de inferências perigosas;
- benchmark gold separado de qualquer dataset de treino;
- scorer determinístico para erros críticos.

## Pipeline-alvo

`Task → Target → Context → Actors → Facts → Claims/Requests → Decisions → Chronology → Evidence → Gaps/Contradictions → Issues → Burden of Proof → Legal Research → Precedents → Adversarial → Strategy → Draft Plan → Draft → Provenance → Final QA`

## Catálogo

| # | Skill | Saída principal | Estado |
|---|---|---|---|
| 1 | Task & Target Resolver | tarefa + ato-alvo | PARCIAL — DraftingTask/Context Builder |
| 2 | Legal Context Builder | LegalContextPack | PARCIAL — V1 existente |
| 3 | Actor & Role Resolver | atores canônicos/resoluções | IMPLEMENTADO V1 — contrato + runner + testes |
| 4 | Fact Extractor | FactMap inicial | IMPLEMENTADO V1 — contrato + runner + testes |
| 5 | Claim / Request Mapper | alegações jurídicas + pedidos | NÃO IMPLEMENTADO |
| 6 | Decision & Obligation Extractor | decisões/comandos/obrigações | PARCIAL — Event Layer cobre domínio específico |
| 7 | Chronology Builder | cronologia jurídica | PARCIAL — provider-first/Event Layer |
| 8 | Evidence Mapper | Fact ↔ prova ↔ fonte | NÃO IMPLEMENTADO |
| 9 | Contradiction Detector | contradições materiais | NÃO IMPLEMENTADO |
| 10 | Evidence Gap Analyzer | fatos relevantes sem suporte | NÃO IMPLEMENTADO |
| 11 | Issue Mapper | questões controvertidas | PARCIAL — issue_map_v1 orientado a retrieval |
| 12 | Burden of Proof Analyzer | ônus por questão/fato | NÃO IMPLEMENTADO |
| 13 | Legal Research Planner | consultas por issue | NÃO IMPLEMENTADO |
| 14 | Jurisprudence Retriever | precedentes candidatos | NÃO IMPLEMENTADO |
| 15 | Precedent / Ratio Analyzer | ratio/aderência/distinguishing | NÃO IMPLEMENTADO |
| 16 | Adversarial Reviewer | melhor argumento contrário/objeções | NÃO IMPLEMENTADO |
| 17 | Strategy Synthesizer | tese principal/subsidiárias/riscos | NÃO IMPLEMENTADO |
| 18 | Draft Planner | estrutura lógica da peça | NÃO IMPLEMENTADO |
| 19 | Legal Draft Writer | minuta condicionada à estratégia | PARCIAL — uso de LLM sem skill formal |
| 20 | Provenance Verifier | conferência factual/citações | PARCIAL — infraestrutura, sem skill final |
| 21 | Final Legal QA | coerência/omissões/alucinações | NÃO IMPLEMENTADO |

## Primeira fatia implementada

### Actor & Role Resolver V1

Entrada:
- páginas canônicas do Movement;
- participantes estruturados do Process;
- representações estruturadas.

Saída:
- actor_id local;
- menção textual;
- actor_kind;
- participant_id quando resolvido;
- process_role;
- resolution_status;
- source_refs;
- unresolved_points;
- context_sufficiency.

Regras críticas:
- nunca inventar participante;
- `parte contrária`, `parte adversa`, pronomes ou relações equivalentes não autorizam resolução nominal sem vínculo inequívoco;
- participant_id só pode vir do Process Frame;
- toda resolução semântica exige quote conferível.

### Fact Extractor V1

Entrada:
- mesmas páginas canônicas;
- atores já resolvidos pela skill anterior.

Saída:
- fact_id;
- statement;
- epistemic_status;
- actor_id resolvido quando aplicável;
- temporal_text apenas quando explícito;
- source_refs;
- unresolved_points;
- context_sufficiency.

Estados epistêmicos V1:
- `ALLEGED`;
- `ADMITTED`;
- `JUDICIAL_FINDING`;
- `DOCUMENTED_EVENT`.

Regra crítica: não existe `PROVEN` nesta skill. Força probatória pertence ao futuro Evidence Mapper.

## Ordem de implementação vigente

1. Consolidar Actor/Role + Fact com benchmark gold.
2. Implementar Claim / Request Mapper.
3. Implementar Evidence Mapper.
4. Implementar Contradiction Detector.
5. Implementar Evidence Gap Analyzer.
6. Só então avançar para Issue/Burden/Research/Strategy.

## Baseline inicial — gemma4:e4b sem fine-tuning

Benchmark sintético gold V1: 20 casos, 10 Actor/Role + 10 Fact Extractor.

- Actor/Role: 10/10 outputs estruturalmente válidos; precisão 0,90; recall 0,55; suficiência 1,00; 0 falsas resoluções perigosas.
- Fact Extractor: 8/10 outputs válidos; precisão 0,50; recall 0,50; suficiência 1,00; 0 upgrades epistêmicos perigosos aceitos.
- Falhas factuais relevantes observadas e bloqueadas:
  - posição jurídica ("incidência do art. 300") tratada pelo modelo como fato;
  - proposição atribuída a ator que permaneceu ambíguo.
- O Actor Resolver mostrou boa precisão quando resolve, mas omite atores expressos apenas por papel ("autora", "requerido", "juízo") em parte dos casos. Esse recall é alvo claro de treinamento.
- Os primeiros baselines também demonstraram que campos redundantes no schema degradavam artificialmente o resultado. V1 final deixa ao LLM somente decisões semânticas mínimas e deriva IDs/papéis/suficiência deterministicamente.

## Regra de treinamento

O benchmark gold nunca entra no treinamento. Fine-tuning deve ser construído a partir de erros observados em conjuntos separados. Um único adapter jurídico pode servir várias skills; não criar um modelo por skill sem evidência de necessidade.
