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
| 5 | Claim / Request Mapper | posições jurídicas + pedidos | IMPLEMENTADO V1 — contrato + runner + testes + benchmark |
| 6 | Decision & Obligation Extractor | decisões/comandos/obrigações | PARCIAL — Event Layer cobre domínio específico |
| 7 | Chronology Builder | cronologia jurídica | PARCIAL — provider-first/Event Layer |
| 8 | Evidence Mapper | Fact ↔ evidência ↔ fonte | IMPLEMENTADO V1 — contrato + runner + testes + benchmark |
| 9 | Contradiction Detector | contradições materiais | IMPLEMENTADO V1 — protocolo + runner + guardrails + benchmark |
| 10 | Evidence Gap Analyzer | cobertura/lacunas evidenciais por fato | IMPLEMENTADO V1 — determinístico + testes + gold |
| 11 | Legal Issue Mapper | questões controvertidas jurídicas/factuais | IMPLEMENTADO V1 — separado do retrieval Issue Map |
| 12 | Burden of Proof Analyzer | ônus por questão/fato | IMPLEMENTADO V1 — seleção mínima de rule + derivação determinística |
| 13 | Legal Research Planner | consultas por issue | IMPLEMENTADO V1 — objetivos determinísticos + query LLM |
| 14 | Jurisprudence Retriever | precedentes candidatos | IMPLEMENTADO V1 — provider-neutral + determinístico + provenance/fail-closed |
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

### Claim / Request Mapper V1

Entrada:
- páginas canônicas do Movement;
- atores já resolvidos;
- `Movement.actor` quando disponível para autoria implícita segura.

Saída:
- `legal_positions[]`;
- `requests[]`;
- `actor_id`;
- `source_refs`;
- `source_actor` derivado deterministicamente;
- `unresolved_points`;
- `context_sufficiency`.

Regras críticas:
- alegação factual não vira posição jurídica;
- decisão judicial não vira pedido da parte;
- pedido que contém uma tese não é duplicado como posição sem argumento independente;
- `Movement.actor` só resolve autoria implícita se apontar inequivocamente para um único participante;
- múltiplos participantes no mesmo papel mantêm autoria `AMBIGUOUS`;
- provenance continua estrito e não é relaxado por erro de encoding do modelo/runtime.

### Evidence Mapper V1

Entrada:
- facts já extraídos e validados;
- evidence_sources explícitos e separados do texto que originou o fato;
- source_kind, actor_id e páginas/provenance de cada fonte disponível.

Saída:
- evidence_items[];
- links Fact ↔ Evidence com SUPPORTS / CONTRADICTS / INCONCLUSIVE;
- directness DIRECT / INDIRECT / UNKNOWN;
- scope FULL / PARTIAL;
- limitations objetivas;
- fact_states derivados deterministicamente;
- unresolved_points e context_sufficiency.

Regras críticas:
- não decide PROVEN / NOT_PROVEN nem suficiência jurídica da prova;
- ausência significa NO_EVIDENCE_IN_CONTEXT, nunca inexistência de prova no processo;
- PARTY_SUBMISSION não é evidência do próprio fato subjacente; anexos devem entrar como fontes separadas;
- documento apenas referido e não disponível gera REFERENCED_EVIDENCE_NOT_AVAILABLE;
- placeholder de VISUAL_ASSET sem conteúdo analisável não vira evidence_item;
- provenance e vínculo entre source_id, página e quote são validados deterministicamente;
- outputs perigosos são rejeitados antes de persistência.

### Contradiction Detector V1

Entrada interna:
- facts[] já validados;
- evidence_items[]/evidence_links[] apenas para projeção determinística.

Entrada do LLM:
- somente facts[]; evidência fica deliberadamente fora do modelo.

Saída:
- fact_pairs[] com DIRECT/POTENTIAL e dimensões materiais;
- fact_contradictions derivados com provenance;
- evidence_contradictions projetadas deterministicamente de Evidence Mapper CONTRADICTS;
- mixed_evidence_fact_ids derivados;
- unresolved_points para incompatibilidades POTENTIAL.

Guardrails:
- proposições idênticas não geram contradição;
- evento indefinido não pode virar DIRECT apenas por semelhança;
- negação sobre evento indefinido sem identidade suficiente é no máximo POTENTIAL;
- estados mutáveis em períodos não sobrepostos não geram contradição;
- falta de suporte/prova nunca é contradição;
- skill nunca decide qual versão é verdadeira.

Baseline E4B 6,6 GB: 10/10 válidos; fact-pair precision/recall 1,00/1,00; suficiência 1,00; evidence projection 1,00; mixed evidence 1,00; 0 DIRECT perigosos.

### Evidence Gap Analyzer V1

Executação: **100% determinística; sem LLM**.

Entrada:
- facts[] já validados;
- Evidence Mapper outputs;
- Contradiction Detector outputs.

Saída por fato:
- support_coverage: NONE / PARTIAL / FULL / SELF_DOCUMENTED;
- gap_open;
- gap_codes;
- evidence IDs de suporte, contradição e inconclusão;
- limitações + provenance.

Gap codes principais:
- NO_EVIDENCE_IN_CONTEXT / NO_SUPPORT_IN_CONTEXT;
- PARTIAL_SUPPORT / INCONCLUSIVE_EVIDENCE / CONFLICTING_EVIDENCE;
- REFERENCED_EVIDENCE_NOT_AVAILABLE / VISUAL_CONTENT_NOT_AVAILABLE;
- AMBIGUOUS_EVIDENCE_REFERENCE / UNRESOLVED_EVIDENCE;
- FACTUAL_CONTRADICTION_UNRESOLVED.

Regras:
- ausência significa apenas ausência no contexto fornecido;
- FULL não significa fato provado nem suficiência jurídica;
- JUDICIAL_FINDING e DOCUMENTED_EVENT podem ser SELF_DOCUMENTED sem exigir evidência externa adicional;
- conflito de evidência/contradição factual mantém lacuna aberta;
- materialidade jurídica e ônus da prova NÃO pertencem a esta skill; entram em Issue/Burden;
- os facts analisados devem ser selecionados upstream para a tarefa corrente.

Gold EG01–EG10: cobertura 1,00; gap codes 1,00; open-gap 1,00; suficiência 1,00; 0 fechamento perigoso; tempo efetivo ~0 ms.

### Legal Issue Mapper V1

É uma skill jurídica própria e NÃO substitui `core/drafting/issue_map_v1.py`, que continua existindo apenas para gerar queries de retrieval a partir do ato-alvo.

Entrada:
- facts[] validados;
- legal_positions[] e requests[] do Claim/Request Mapper;
- fact_contradictions[];
- Evidence Gap state apenas como contexto auxiliar.

Saída:
- issues[] com questão neutra;
- kind FACTUAL / LEGAL / MIXED / PROCEDURAL;
- vínculos canônicos fact_ids / legal_position_ids / request_ids;
- actor_ids, contradiction_ids, evidence_gap_codes e provenance derivados pelo Themis;
- unresolved_points quando a issue depende de fact com evidence gap aberto.

Regras:
- evidence gap isolado não vira issue;
- background fact sem controvérsia não vira issue;
- FACTUAL isolada exige fact_contradiction upstream;
- request material deve ser coberto por uma issue, mesmo sem oposição já apresentada;
- o LLM não inventa IDs/provenance;
- FACTUAL/LEGAL/MIXED são normalizados deterministicamente pelos vínculos; PROCEDURAL permanece subtipo semântico;
- não decide mérito, ônus da prova, estratégia, precedentes ou nova base legal.

Baseline E4B 6,6 GB: 10/10 válidos; issue precision/recall 1,00/1,00; 0 kind mismatches; 0 link mismatches; suficiência 1,00; 0 issues sem vínculo.

### Burden of Proof Analyzer V1

Contrato mínimo:
- LLM escolhe somente issue_id + fact_ids[] + rule_id;
- burden_side, allocation_type, reason_code, authority e regime vêm deterministicamente da rule fornecida;
- regra CONDITIONAL só produz efeito com precondition_status=SATISFIED;
- ausência de rule aplicável gera unresolved determinístico;
- evidence gap/contradiction não desloca ônus por si.

Baseline E4B 6,6 GB: BP01–BP10 10/10 válidos; precision/recall/suficiência 1,00; 0 rule inventions; 0 SHIFTED/DYNAMIC não autorizados.

### Legal Research Planner V1

Contrato mínimo:
- código deriva objetivos obrigatórios por kind da issue;
- LEGAL/MIXED => CONTROLLING_RULE + PRECEDENT_LANDSCAPE;
- PROCEDURAL => PROCEDURAL_RULE + PRECEDENT_LANDSCAPE;
- FACTUAL puro => nenhuma pesquisa jurídica;
- LLM emite somente issue_id + objective + query_text;
- source_types/jurisdição/contexto e query_id são derivados;
- autoridade específica só pode aparecer se já fornecida upstream em known_authorities;
- planner nunca responde a issue nem afirma regra/holding.

Baseline E4B 6,6 GB: RP01–RP10 10/10 válidos; query precision/recall 1,00/1,00; suficiência 1,00; 0 authority inventions.

### Jurisprudence Retriever V1

Execução: **100% determinística; sem LLM**.

Entrada:
- `Legal Research Planner.queries[]`;
- apenas queries com `BINDING_AUTHORITY` e/ou `JURISPRUDENCE`;
- respostas normalizadas de providers externos, agrupadas por `query_id`.

Saída:
- `candidates[]` de precedentes;
- identidade judicial mínima `court + identifier`;
- `query_ids[]` e `source_types[]`;
- `retrieval_hits[]` preservando rank/score do provider e provenance;
- status por query: FOUND / NO_RESULTS / FAILED / INVALID_RESULTS / NOT_ATTEMPTED;
- rejected_results, provider_failures, unresolved_points e context_sufficiency.

Regras:
- não decide ratio, aderência, distinguishing, força persuasiva ou mérito;
- legislação pura é ignorada por esta skill;
- resultado exige tribunal, identificador, data, excerpt e locator verificável;
- provenance exige provider, provider_result_id, retrieved_at e content_sha256;
- resultado incompleto é rejeitado fail-closed, nunca promovido a candidato;
- deduplicação V1 usa identidade judicial `court + identifier`; múltiplas queries/providers preservam todos os retrieval_hits;
- rank/score permanecem dados do provider; o Retriever V1 não cria ranking jurídico entre precedentes.

Gold JR01–JR10: 10/10 válidos; candidate precision/recall 1,00/1,00; status/suficiência/rejeições/falhas 1,00; 0 candidatos sem provenance aceitos; tempo efetivo ~0 ms.

## Ordem de implementação vigente

1. Compreensão/pesquisa fechada em V1 até Jurisprudence Retriever.
2. Implementar Precedent / Ratio Analyzer V1.
3. Depois Adversarial Reviewer + Strategy Synthesizer.
4. Só então Draft Planner/Drafting/QA.

## Baselines sem fine-tuning

Benchmark/gold V1: 100 casos — 10 por skill para Actor/Role, Fact Extractor, Claim/Request, Evidence Mapper, Contradiction Detector, Evidence Gap Analyzer, Legal Issue Mapper, Burden of Proof Analyzer, Legal Research Planner e Jurisprudence Retriever. Evidence Gap e Jurisprudence Retriever são determinísticos e não executam LLM.

### Gemma 4 E4B antigo (~9,6 GB)
- Actor/Role: 10/10 outputs válidos; precisão 0,90; recall 0,55; suficiência 1,00; 0 falsas resoluções perigosas.
- Fact Extractor: 8/10 outputs válidos; precisão 0,50; recall 0,50; suficiência 1,00; 0 upgrades epistêmicos perigosos aceitos.

### Gemma 4 E4B atual (6,6 GB, Q4_K_M, 131072)
- Actor/Role: 10/10 válidos; precisão 0,70; recall 0,45; suficiência 0,80; 1 falsa resolução perigosa (`Seu patrono` tratado como ator resolvido).
- Fact Extractor: 8/10 válidos; precisão/recall 0,625/0,625; suficiência 1,00; 0 upgrades epistêmicos perigosos aceitos.
- Claim/Request: 10/10 válidos; legal position 1,00/1,00; requests 1,00/1,00; suficiência 1,00; 0 actor mismatches.
- Evidence Mapper após guardrails determinísticos: 7/10 válidos; 3 outputs perigosos rejeitados antes de persistência (petição como prova, documento apenas citado e visual asset sem conteúdo); evidence items 0,857/0,857; links 0,571/0,571; fact state 0,571; suficiência 1,00; 1 support perigoso ainda aceito no caso de transferência sem beneficiário identificado.

Leitura dos baselines:
- o E4B de 6,6 GB melhorou Fact e foi excelente em Claim/Request, mas regrediu em Actor/Role;
- Evidence Mapper é semanticamente mais difícil e já expôs alvos claros para SFT/hardening;
- o caso de transferência sem beneficiário identificado deve permanecer INCONCLUSIVE + IDENTITY_UNCLEAR; tratá-lo como SUPPORTS é erro de segurança;
- schemas redundantes degradam desempenho; IDs, papéis, suficiência e estados derivados continuam determinísticos.

Correção de diagnóstico: os rejects com caracteres `�` observados num benchmark intermediário não eram evidência de corrupção do modelo/runtime. O recorte de casos havia sido regravado pelo Windows PowerShell 5 e corrompido UTF-8. O runner agora filtra skills diretamente com `--skill`, sem regravar o JSONL gold.

## Protocolo de inferência

Skill Themis não é prompt narrativo; é protocolo de inferência.

Cada skill deve separar:
1. input contract mínimo;
2. procedimento decisório ordenado;
3. output contract estrito;
4. hard guards determinísticos.

Regras vigentes:
- linguagem operacional compacta, orientada à IA;
- precedência explícita entre decisões;
- o LLM executa apenas decisões semânticas que não podem ser derivadas por código;
- IDs, papéis, suficiência, autoria e estados derivados ficam fora do LLM sempre que possível;
- outputs semanticamente perigosos devem ser rejeitados ou normalizados deterministicamente antes de persistir.

Revisão V1 aplicada a Actor/Role, Fact, Claim/Request, Evidence Mapper, Contradiction Detector, Evidence Gap Analyzer e Legal Issue Mapper:
- Actor/Role: referências relacionais/pronominais abertas são forçadas deterministicamente a AMBIGUOUS;
- Claim/Request: o LLM não emite mais actor_id; Themis deriva autoria por menção explícita resolvida ou Movement.actor seguro;
- Evidence: PARTY_SUBMISSION autoafirmativa não pode ser promovida a ADMISSION; identidade material ausente força INCONCLUSIVE + IDENTITY_UNCLEAR.

Baseline do E4B 6,6 GB após protocolos:
- Actor/Role: precisão 0,90; recall 0,75; suficiência 1,00 na regressão completa de 70 casos; 0 falsas resoluções perigosas;
- Fact: precisão/recall 0,625/0,625; suficiência 1,00; 0 upgrades perigosos;
- Claim/Request: 1,00/1,00 em posições e pedidos; suficiência 1,00; 0 actor mismatches;
- Evidence Mapper: 8/10 outputs aceitos; items 0,875/0,75; links variaram entre 0,875/0,75 no teste isolado e 0,75/0,625 na regressão completa; fact state 0,75; suficiência 1,00; 0 support inventions perigosos.
- Contradiction Detector: 10/10 válidos; fact pairs 1,00/1,00; suficiência 1,00; evidence projection 1,00; mixed evidence 1,00; 0 DIRECT inventions perigosos.
- Evidence Gap Analyzer: determinístico; 10/10 gold; cobertura/gap codes/open-gap/suficiência 1,00; 0 fechamento perigoso.
- Legal Issue Mapper: 10/10 válidos; issue precision/recall 1,00/1,00; 0 kind mismatches; 0 link mismatches; suficiência 1,00; 0 issues sem vínculo.
- Jurisprudence Retriever: determinístico; 10/10 gold; candidate precision/recall 1,00/1,00; status/suficiência/rejeições/falhas 1,00; 0 candidatos sem provenance aceitos.
- Regressão completa de 70 casos confirmou Legal Issue Mapper e Contradiction Detector em 1,00/1,00, Claim/Request em 1,00/1,00, Evidence Gap em 1,00 determinístico e 0 erros perigosos aceitos nas métricas de segurança.
- Evidence residual para treino/hardening sem heurística ad hoc: inferência indireta de quitação (EV07) e suporte parcial por valor menor (EV08).

## Regra de treinamento

O benchmark gold nunca entra no treinamento. Fine-tuning deve ser construído a partir de erros observados em conjuntos separados. Um único adapter jurídico pode servir várias skills; não criar um modelo por skill sem evidência de necessidade.

## Burden of Proof Analyzer V1

Protocolo mínimo: LLM emite apenas `allocations[{issue_id, fact_ids, rule_id}]`.
Cada regra fornecida declara consequências unívocas: `burden_side`, `allocation_type`,
`reason_code`, `authority` e `regime`; código copia esses campos sem decisão do modelo.
Listas `allowed_sides`/`allowed_types` não substituem esse contrato.

`CONDITIONAL` exige `precondition_status=SATISFIED`. Status ausente é `UNKNOWN`;
`UNKNOWN`/`UNSATISFIED` omitem a seleção e deixam os fatos descobertos unresolved.
IDs inventados, campos extras, fatos externos à issue e alocações sobrepostas são rejeitados.
Todo fato da issue sem cobertura recebe `RULE_NOT_SUPPLIED` deterministicamente.
Issues sem fatos não recebem allocation. Evidence gaps e contradictions não mudam ônus.
Sem regras elegíveis ou sem fatos, o runner resolve sem chamar LLM.

BP01–BP10 preservam fatos, questões e expectativas; regras agora declaram consequências
singulares e status explícito. BP05 tem condição satisfeita, BP06/BP09 desconhecida.
Gold é exclusivamente avaliação e nunca entra em treinamento.
O benchmark conta invenções de regra e SHIFTED/DYNAMIC não autorizados na resposta bruta,
inclusive rejeitada, e retorna falha se houver esses erros ou outputs inválidos.
Implementação source; sem deploy ou homologação de runtime.

Validação source: pytest legal skills + drafting context; benchmark `gemma4:e4b`
BP01–BP10: 10/10 válidos, precisão/recall/suficiência 1,00, 0 rule inventions,
0 SHIFTED/DYNAMIC não autorizados e nenhum erro residual observado no gold.
