# THEMIS — PRAZO RESOLVER V1: DESIGN CANÔNICO & PIPELINE TEMPORAL

**Versão do Documento:** 1.1.0
**Data:** 2026-09-29
**Status:** DESIGN CANÔNICO / ESPECIFICAÇÃO DE ENGENHARIA
**Escopo:** Pipeline Temporal, DJEN Publications, Resolução de Antecedente/Destinatário, Separação ML/Determinístico e Catálogo de Regras de Prazo.

---

## 1. ESTADO ATUAL DO PIPELINE TEMPORAL NO THEMIS

A auditoria completa das fontes de dados, schemas SQLite e módulos do Core revela a seguinte topologia operacional:

```text
Fontes Brutas / Captura
├── Movements (movements, movement_pieces, movement_summaries)
├── Hearings (hearings, hearing_participants)
├── Process Metadata (process_metadata)
└── Publications (publications — DJEN ComunicaAPI / CNJ)
       │
       ▼
ProcessEvent V1 (process_event_store_v1.py)
[Normalização de fatos observados brutos: data, hora, precisão, fonte, sem cálculo]
       │
       ▼
DeadlineInstruction V1 (deadline_instruction_store_v1.py)
[Regex determinístico sobre texto do 1º componente de cada Movement]
       │
       ▼
DeadlineObligation V1 (deadline_obligation_store_v1.py)
[Consolidação de ordens originárias + suportes via sequence de movements]
       │
       ▼
Deadlines Canônicos (domain_objects_v1.py)
[Tabela 'deadlines' com due_at, term, priority, fingerprint e provenance]
       │
       ▼
LegalEventProjection V1 (legal_event_projection_v1.py)
[Read model unificado: DEADLINE, HEARING, PENDING, PUBLICATION]
```

### 1.1. Mapeamento de Entidades, Chaves e Provenance

| Entidade / Tabela | Chave Primária | Foreign Keys Atuais | Gerador de ID / Namespace | Função no Pipeline |
|---|---|---|---|---|
| `movements` | `movement_id` | `process_id -> processes` | Informado pelo provider | Registra a linha do tempo processual dos autos |
| `publications` | `publication_id` | `process_id -> processes` | `pub_` + UUIDv5(`4ef8d6ea...`, `provider\|identity`) | Armazena comunicações oficiais do DJEN de forma idempotente |
| `process_events` | `event_id` | Nenhuma FK rígida; `UNIQUE(process_id, source_entity, source_id)` | `pe_` + UUIDv5(`5f49cb37...`, `process_id\0source_entity\0source_id`) | Fatos temporais neutros observados nas fontes |
| `deadline_instructions` | `instruction_id` | `movement_id -> movements(movement_id)` | `di_` + UUIDv5(`f9abf7bb...`, `process_id\0movement_id\0basis`) | Determinações temporais explícitas encontradas em texto |
| `deadline_obligations` | `obligation_id` | `originating_instruction_id -> deadline_instructions`, `origin_movement_id -> movements` | `do_` + UUIDv5(`2e6bdc8c...`, `process_id\0basis`) | Obrigação jurídica consolidada |
| `deadlines` | `deadline_id` | Nenhuma FK rígida; `owner_type='PROCESS'`, `owner_id=process_id` | `deadline_` + UUIDv5(`b79b9bf0...`, `fingerprint`) | Prazos finais com vencimento e termo |
| `process_participants` | `participant_id` | `process_id -> processes`, `entity_id -> legal_entities` | `part_` + UUIDv5 | Cadastro objetivo dos polos e sujeitos processuais |
| `representations` | `representation_id` | `process_id`, `representative_participant_id`, `represented_participant_id` | `rep_` + UUIDv5 | Vínculos de patrono/representante a representados |
| `user_process_contexts` | `context_id` | `process_id`, `profile_id`, `participant_id` | UUIDv5 | Contexto subjetivo local do usuário (atuando por polo X) |

---

## 2. GAPS E LIMITAÇÕES CONCRETAS DE DEADLINEINSTRUCTION V1

A auditoria identificou os seguintes bloqueios técnicos na estrutura V1:

1. **Acoplamento Rígido a `Movement` na Tabela `deadline_instructions`:**
   - A coluna `movement_id TEXT NOT NULL` e a constraint `FOREIGN KEY(movement_id) REFERENCES movements(movement_id) ON DELETE CASCADE` impedem fisicamente a inserção de qualquer determinação cuja fonte seja uma `PUBLICATION`.

2. **Extração Baseada Exclusivamente em Páginas de Documentos Locais:**
   - O extrator `extract_for_movement()` depende de `movement_summary_store_v1.source_text_and_hash()`, que lê `canonical_pages` e `pages` do PDF dos autos. Publicações do DJEN (que chegam como payloads JSON da API pública do CNJ contendo texto no atributo `texto`/`full_text`) não possuem páginas em `pages` e são ignoradas.

3. **Incapacidade Estrutural de `DeadlineObligation V1` em Vincular Publicações:**
   - `deadline_obligation_store_v1.py` classifica instruções por `_source_role()` a partir do `movement_type` e `title` da tabela `movements`. O casamento de suporte (`_supports()`) baseia-se na ordem `sequence` de `movements`. Uma publicação pura não possui `sequence` na tabela de movimentos dos autos.

4. **Extrator Puramente Regex Determinístico:**
   - Expressões regulares (`_ORDER_RE`, `_PORTAL_RE`, `_UNTIL_RE`) só identificam prazos com numerais expressos adjacentes a palavras-chave (ex: *"no prazo de 15 dias"*).
   - Falham categoricamente diante de:
     - Comandos tácitos ou indeterminados: *"Manifeste-se a parte contrária"*, *"Digam as partes em provas"*, *"Ao autor para réplica"*;
     - Expressões relacionais de destinatário: *"ao réu"*, *"ao executado"*, *"à contraparte"*;
     - Casos onde a lei processual fixa o prazo e o juiz apenas emite a intimação.

---

## 3. ARQUITETURA PROPOSTA: PIPELINE TEMPORAL INTEGRADO

O fluxo canônico para evolução de publicações e movimentos até prazos auditáveis é estruturado em camadas com **separação epistêmica estrita**:

```text
┌─────────────────────────────────────────────────────────────────────────────────────────────────┐
│ 1. AQUISIÇÃO E NORMALIZAÇÃO DE FATOS OBSERVADOS                                                  │
│    • Publication (DJEN ComunicaAPI) / Movement (Autos / e-SAJ / PJe / eproc)                    │
│    • ProcessEvent V1 (registro cronológico bruto: datas de disponibilização, publicação, etc.)  │
└────────────────────────────────────────────────┬────────────────────────────────────────────────┘
                                                 │
                                                 ▼
┌─────────────────────────────────────────────────────────────────────────────────────────────────┐
│ 2. RECONHECIMENTO DE INSTRUÇÃO OPERATIVA (DeadlineInstruction V2)                               │
│    • Extração de texto operativo a partir de fonte genérica (MOVEMENT ou PUBLICATION)           │
│    • Âncora estrutural em ProcessEvent + provenance da fonte original                           │
└────────────────────────────────────────────────┬────────────────────────────────────────────────┘
                                                 │
                                                 ▼
┌─────────────────────────────────────────────────────────────────────────────────────────────────┐
│ 3. ESPECIALISTA LOCAL: PRAZO RESOLVER (SLM / Classificador Local CPU-Friendly)                  │
│    • Verifica se o ato contém comando operativo (is_operative_instruction)                      │
│    • Localiza o ATO ANTECEDENTE RELEVANTE (pela cronologia e polo nos autos)                   │
│    • Resolve o DESTINATÁRIO JURÍDICO de forma estritamente relacional (autor vs réu)            │
│    • Mapeia para os IDs de process_participants                                                 │
│    • Classifica o TIPO DE ATO PROCEDIMENTAL (procedural_act_type)                               │
│    • Identifica prazo explícito e ranqueia REGRAS JURÍDICAS CANDIDATAS                           │
└────────────────────────────────────────────────┬────────────────────────────────────────────────┘
                                                 │
                                                 ▼
┌─────────────────────────────────────────────────────────────────────────────────────────────────┐
│ 4. CONSOLIDAÇÃO DA OBRIGAÇÃO (DeadlineObligation V2)                                            │
│    • Vincula a instrução atual ao ato antecedente relevante e aos destinatários resolvidos       │
│    • RuleResolver determinístico resolve a regra; obrigação registra resolved_rule_id           │
└────────────────────────────────────────────────┬────────────────────────────────────────────────┘
                                                 │
                                                 ▼
┌─────────────────────────────────────────────────────────────────────────────────────────────────┐
│ 5. MOTOR DETERMINÍSTICO DE CÁLCULO DE PRAZOS (Python / Calendário / CPC)                        │
│    • Recebe: data do ato/disponibilização, regra de contagem da fonte (DJEN vs autos)           │
│    • Aplica: disponibilização (D) → publicação (D+1) → termo inicial (1º dia útil seguinte)     │
│    • Computa: dias úteis (art. 219 CPC) sobre calendário do Tribunal/Comarca (feriados/recessos)│
│    • Produz: due_at exato e auditável                                                           │
└────────────────────────────────────────────────┬────────────────────────────────────────────────┘
                                                 │
                                                 ▼
┌─────────────────────────────────────────────────────────────────────────────────────────────────┐
│ 6. PERSISTÊNCIA E PROJEÇÃO                                                                      │
│    • Gravação em 'deadlines' (fingerprint, status CANDIDATE/CONFIRMED, provenance)              │
│    • Disponibilização na timeline unificada via LegalEventProjection                             │
└─────────────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 4. CONTRATO DE DADOS: DEADLINEINSTRUCTION V2

Para suportar fontes genéricas sem perda de integridade nem quebra de compatibilidade, a tabela `deadline_instructions` evolui para V2:

### 4.1. Schema SQLite Proposto

```sql
CREATE TABLE IF NOT EXISTS deadline_instructions_v2(
  instruction_id TEXT PRIMARY KEY,
  process_id TEXT NOT NULL,
  source_event_id TEXT NOT NULL,
  source_entity TEXT NOT NULL CHECK(source_entity IN ('MOVEMENT', 'PUBLICATION', 'DOCUMENT', 'MANUAL')),
  source_id TEXT NOT NULL,
  action_text TEXT,
  recipient_text TEXT,
  term_value INTEGER,
  term_unit TEXT NOT NULL CHECK(term_unit IN ('DAYS', 'BUSINESS_DAYS', 'HOURS', 'MONTHS', 'DATE_CERTAIN', 'UNSPECIFIED')),
  counting_qualifier TEXT,
  trigger_text TEXT,
  trigger_status TEXT NOT NULL CHECK(trigger_status IN ('EXPLICIT', 'PARTIAL', 'UNSPECIFIED')),
  source_excerpt TEXT NOT NULL,
  source_refs_json TEXT NOT NULL DEFAULT '[]',
  source_hash TEXT NOT NULL,
  extraction_method TEXT NOT NULL,
  status TEXT NOT NULL CHECK(status IN ('EXPLICIT', 'AMBIGUOUS', 'INFERRED', 'REJECTED')),
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL,
  UNIQUE(process_id, instruction_id),
  FOREIGN KEY(process_id) REFERENCES processes(process_id) ON DELETE CASCADE,
  FOREIGN KEY(source_event_id) REFERENCES process_events(event_id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_deadline_instructions_v2_source_event
  ON deadline_instructions_v2(process_id, source_event_id);

CREATE INDEX IF NOT EXISTS idx_deadline_instructions_v2_source
  ON deadline_instructions_v2(process_id, source_entity, source_id);

CREATE INDEX IF NOT EXISTS idx_deadline_instructions_v2_status
  ON deadline_instructions_v2(process_id, status, trigger_status);
```

### 4.2. Âncora Canônica em `ProcessEvent`

`source_event_id` é o vínculo estrutural obrigatório da instrução com a cronologia normalizada do processo. `source_entity` e `source_id` permanecem como provenance/denormalização útil, mas não substituem a integridade referencial. Assim, uma `PUBLICATION` participa do pipeline sem fingir ser `MOVEMENT`, e toda instrução aponta para um fato temporal existente em `process_events`.

O evento de comunicação também deve ser preservado separadamente como `trigger_event_id` quando o fato que inicia a contagem não for o mesmo evento que contém a ordem. Texto como *"Intimem-se"* é conteúdo da determinação, não o marco temporal por si só; o marco é resolvido a partir do evento oficial de comunicação correspondente.

### 4.3. Identidade Determinística (ID_NAMESPACE)
O `instruction_id` permanece idempotente via UUIDv5:
```python
ID_NAMESPACE = uuid.UUID("f9abf7bb-c7d8-4e53-bf16-6e87e4a4df64")

def candidate_instruction_id(process_id: str, source_entity: str, source_id: str, candidate: dict) -> str:
    basis = "\x00".join(str(candidate.get(k) or "") for k in (
        "source_excerpt", "action_text", "recipient_text", "term_value", "term_unit", "trigger_text"
    ))
    seed = f"{process_id}\x00{source_entity}\x00{source_id}\x00{basis}"
    return f"di_{uuid.uuid5(ID_NAMESPACE, seed).hex}"
```

---

## 5. CONTRATO DE SAÍDA DO PRAZO RESOLVER (ESPECIALISTA LOCAL)

O especialista local (modelo SLM / pipeline local CPU-friendly) processa o contexto do processo, o ato atual e os atos anteriores, gerando o seguinte schema estruturado:

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "title": "PrazoResolverOutputV1",
  "type": "object",
  "required": [
    "is_operative_instruction",
    "action_type",
    "action_text",
    "recipient_text",
    "recipient_role",
    "recipient_participant_ids",
    "recipient_resolution_method",
    "antecedent_source_entity",
    "antecedent_source_id",
    "explicit_term_value",
    "explicit_term_unit",
    "procedural_act_type",
    "candidate_rule_ids",
    "model_preferred_rule_id",
    "confidence",
    "review_required"
  ],
  "properties": {
    "is_operative_instruction": {
      "type": "boolean",
      "description": "Indica se o texto contém uma ordem, intimação ou determinação de providência processual ativa."
    },
    "action_type": {
      "type": "string",
      "enum": ["MANIFESTATION", "RESPONSE", "PAYMENT", "SPECIFICATION_OF_PROOFS", "APPEAL", "CLARIFICATION", "COMPLIANCE", "OTHER"],
      "description": "Categoria macro da providência exigida."
    },
    "action_text": {
      "type": ["string", "null"],
      "description": "Texto normalizado do comando operativo (ex: 'Manifestar-se sobre a petição e documentos juntados')."
    },
    "recipient_text": {
      "type": ["string", "null"],
      "description": "Expressão literal do destinatário no texto (ex: 'parte contrária', 'ao autor', 'à ré')."
    },
    "recipient_role": {
      "type": "string",
      "enum": ["CLAIMANT", "RESPONDENT", "BOTH", "THIRD_PARTY", "EXPERT", "PUBLIC_PROSECUTOR", "UNKNOWN"],
      "description": "Polo processual jurídico resolvido do destinatário."
    },
    "recipient_participant_ids": {
      "type": "array",
      "items": { "type": "string" },
      "description": "participant_id dos destinatários no contexto deste processo. A identidade global permanece acessível por process_participants.entity_id; ela não substitui o destinatário processual."
    },
    "recipient_resolution_method": {
      "type": "string",
      "enum": ["ANTECEDENT_RELATION", "EXPLICIT_NAME", "EXPLICIT_ROLE", "ALL_PARTIES", "RESIDUAL"],
      "description": "Método utilizado para resolver o destinatário."
    },
    "antecedent_source_entity": {
      "type": "string",
      "enum": ["MOVEMENT", "PUBLICATION", "PROCEDURAL_ACT", "DOCUMENT", "NONE"],
      "description": "Tipo de entidade do ato antecedente que motivou o despacho/publicação."
    },
    "antecedent_source_id": {
      "type": ["string", "null"],
      "description": "Identificador do ato antecedente relevante resolvido."
    },
    "explicit_term_value": {
      "type": ["integer", "null"],
      "description": "Valor numérico do prazo explicitado no texto pelo magistrado, se houver."
    },
    "explicit_term_unit": {
      "type": "string",
      "enum": ["DAYS", "BUSINESS_DAYS", "HOURS", "MONTHS", "DATE_CERTAIN", "UNSPECIFIED"],
      "description": "Unidade temporal do prazo explícito."
    },
    "procedural_act_type": {
      "type": "string",
      "description": "Classificação canônica do ato procedimental exigido (ex: REPLICA, CONTESTACAO, ESPECIFICACAO_PROVAS, MANIFESTACAO_DOCUMENTOS, EMBARGOS_DECLARACAO, APELACAO)."
    },
    "candidate_rule_ids": {
      "type": "array",
      "items": { "type": "string" },
      "description": "Lista de regras jurídicas potencialmente aplicáveis do catálogo."
    },
    "model_preferred_rule_id": {
      "type": ["string", "null"],
      "description": "Hipótese preferida do modelo entre candidate_rule_ids. Não é decisão jurídica final; o RuleResolver determinístico produz resolved_rule_id após aplicar precedência, vigência, rito e hard constraints."
    },
    "confidence": {
      "type": "number",
      "minimum": 0.0,
      "maximum": 1.0,
      "description": "Grau de confiança probabilística da resolução (0.0 a 1.0)."
    },
    "review_required": {
      "type": "boolean",
      "description": "Flag indicando se é necessária revisão humana prévia antes da consolidação."
    }
  }
}
```

---

## 6. A INVARIANTE RELACIONAL DE "PARTE CONTRÁRIA" E A BUSCA DO ANTECEDENTE

### 6.1. Invariante Canônica
> **"Parte contrária", "parte adversa", "ao ex adverso" e expressões equivalentes são estritamente RELACIONAIS ao polo do ATO ANTECEDENTE RELEVANTE.**
> **O Themis NUNCA deve usar a identidade do usuário logado ou seu perfil profissional para inferir quem é a "parte contrária".**

### 6.2. Algoritmo de Localização do Ato Antecedente Relevante
Não basta buscar o "último documento" inserido nos autos, pois o último registro frequentemente é uma certidão de juntada genérica, uma certidão de publicação ou um termo cartorário sem carga dispositiva.

O algoritmo executa a seguinte triagem determinístico-estruturada:

```text
Entrada: Ato Atual (Despacho / Publicação DJEN) no instante T
Passo 1: Coleta dos atos anteriores (t < T) em ordem cronológica reversa.
Passo 2: Filtragem de ruído cartorário:
         - Descartar certidões de publicação, certidões de remessa, termos de conclusão,
           e atos de mero expediente sem manifestação de polo.
Passo 3: Identificação do último ato postulatório/substancial:
         - Petições das partes (Petição Inicial, Contestação, Emenda, Juntada de Documentos,
           Embargos, Apelação, Manifestação);
         - Laudo pericial ou manifestação do Ministério Público.
Passo 4: Resolução de Autoria e Polo do Antecedente:
         - Consultar tabela 'movements' (actor) e 'procedural_acts_v1' (signer, protocol);
         - Cruzar com 'process_participants' e 'representations' para identificar o base_role:
           • Se autor do ato antecedente pertence a CLAIMANT (Polo Ativo);
           • Se autor do ato antecedente pertence a RESPONDENT (Polo Passivo);
           • Se autor é EXPERT (Perito) ou THIRD_PARTY (Terceiro).
Passo 5: Inversão Relacional:
         - Se texto da ordem diz "parte contrária":
           • Antecedente = CLAIMANT  ==> Destinatário Resolvido = RESPONDENT
           • Antecedente = RESPONDENT ==> Destinatário Resolvido = CLAIMANT
         - Se texto da ordem diz "ambas as partes" ou "às partes":
           • Destinatário Resolvido = BOTH (gera obrigações para CLAIMANT e RESPONDENT)
Passo 6: Associação de Entidades:
         - Resolver recipient_participant_ids buscando os participant_id correspondentes
           ao polo determinado em 'process_participants'.
```

---

## 7. SEPARAÇÃO RIGOROSA DE RESPONSABILIDADES: ML vs. MOTOR DETERMINÍSTICO

Para garantir precisão jurídica, auditabilidade e eliminação de alucinações, as responsabilidades são rigidamente delimitadas:

```
┌──────────────────────────────────────────────┐       ┌──────────────────────────────────────────────┐
│       MODELO ESPECIALISTA LOCAL (ML/SLM)      │       │        MOTOR DETERMINÍSTICO (PYTHON/CPC)     │
├──────────────────────────────────────────────┤       ├──────────────────────────────────────────────┤
│ • Reconhecer se o texto é instrução operativa│       │ • Aplicar a contagem de dias úteis/corridos  │
│ • Classificar o tipo de providência exigida  │       │ • Converter termo da regra em número de dias │
│ • Localizar o ato antecedente motivador      │       │ • Obter marco de disponibilização / pub.     │
│ • Resolver polo destinatário (autor/réu/ambos│       │ • Computar termo inicial (art. 224 CPC)      │
│ • Mapear participantes envolvidos             │       │ • Cruzar feriados nacionais/locais/forenses  │
│ • Identificar prazo fixado pelo juiz         │       │ • Aplicar suspensões e recesso forense (220) │
│ • Selecionar / ranquear a regra aplicável    │       │ • Calcular a data final exata (due_at)       │
└──────────────────────┬───────────────────────┘       └──────────────────────▲───────────────────────┘
                       │                                                      │
                       │             Contrato Estruturado                     │
                       └──────────────────────────────────────────────────────┘
                         (rule_id, explicit_term, recipient_role, antecedent_id)
```

> [!IMPORTANT]
> **O modelo de linguagem NUNCA calcula datas, NUNCA soma dias, NUNCA consulta feriados e NUNCA inventa a data de vencimento (`due_at`). Toda a matemática temporal é puramente determinística e baseada no Código de Processo Civil e calendários oficiais.**

---

### 7.1. `RuleResolver` Determinístico

O modelo especialista não possui autoridade para escolher definitivamente a regra jurídica. Ele produz `candidate_rule_ids`, scores/confiança e, opcionalmente, `model_preferred_rule_id`. Um `RuleResolver` determinístico recebe essas hipóteses e aplica constraints estruturadas: prazo judicial expresso, classe/rito, natureza do ato, polo destinatário, jurisdição, vigência e precedência normativa. Somente esta etapa emite `resolved_rule_id`, que pode alimentar o motor temporal.

## 8. CATÁLOGO VERSIONADO DE REGRAS JURÍDICAS DE PRAZO (`legal_deadline_rules_v1`)

O catálogo de regras é versionado, declarativo e auditável, estruturado para suportar a seguinte **hierarquia de precedência estrita**:

1. **Prazo Judicial Expresso (`JUDICIAL_EXPLICIT_TERM`):**
   Quando o juiz expressamente fixa um número de dias no despacho (ex: *"no prazo de 5 dias"*, *"dentro de 10 dias"*), essa fixação prevalece sobre o prazo legal genérico, salvo se contrária a norma cogente.
2. **Regra Legal Específica (`STATUTORY_SPECIFIC`):**
   Prazo fixado em lei processual para o ato específico (ex: Contestação = 15 dias úteis, art. 335 CPC; Embargos de Declaração = 5 dias úteis, art. 1.023 CPC; Apelação = 15 dias úteis, art. 1.003, § 5º CPC; Réplica sobre preliminares = 15 dias úteis, art. 351 CPC).
3. **Regra de Procedimento Especial (`SPECIAL_PROCEDURE`):**
   Procedimentos com prazos diferenciados (Juizados Especiais Lei 9.099/95, Execução Fiscal Lei 6.830/80, Mandado de Segurança Lei 12.016/09).
4. **Regra Geral Residual (`RESIDUAL_DEFAULT`):**
   Quando a lei é omissa e o juiz não estipulou prazo (art. 218, § 3º, CPC — **5 dias úteis**).

### 8.1. Estrutura Canônica do Catálogo

**Nota de implementação da Fase 1:** o módulo inicial publica o contrato versionado
do catálogo sem ativar regras materiais. Os exemplos abaixo dependem de confirmação
jurídica e de fonte oficial/versionada por regra; até essa verificação, o catálogo
permanece vazio e o resolver retorna `UNRESOLVED` quando não houver candidato
validado. Esta limitação evita tratar exemplos conceituais como regra vigente.

Cada regra deve carregar provenance jurídico verificável, no mínimo: `effective_from`, `effective_to`, `jurisdiction_scope`, `authority`, `official_source`, `verified_at`, `rule_version` e fundamento legal estruturado. Alteração legislativa ou administrativa cria nova versão/intervalo de vigência; não se sobrescreve silenciosamente a regra histórica.

```json
[
  {
    "rule_id": "JUDICIAL_EXPLICIT_TERM",
    "category": "JUDICIAL_ORDER",
    "name": "Prazo Fixado pelo Magistrado",
    "description": "Prazo determinado explicitamente na decisão judicial.",
    "default_term_value": null,
    "term_unit": "BUSINESS_DAYS",
    "counting_type": "CPC_BUSINESS_DAYS",
    "legal_basis": "Art. 218, § 1º, CPC",
    "precedence": 100,
    "allow_explicit_override": true,
    "applicable_act_types": ["*"]
  },
  {
    "rule_id": "CPC_ART_335_CONTESTACAO",
    "category": "STATUTORY_SPECIFIC",
    "name": "Contestação",
    "description": "Prazo para o réu oferecer contestação.",
    "default_term_value": 15,
    "term_unit": "BUSINESS_DAYS",
    "counting_type": "CPC_BUSINESS_DAYS",
    "legal_basis": "Art. 335, caput, CPC",
    "precedence": 80,
    "allow_explicit_override": false,
    "applicable_act_types": ["CONTESTACAO"]
  },
  {
    "rule_id": "CPC_ART_350_REPLICA",
    "category": "STATUTORY_SPECIFIC",
    "name": "Manifestação sobre Contestação (Réplica)",
    "description": "Prazo para o autor manifestar-se sobre fato impeditivo, modificativo ou extintivo ou preliminares.",
    "default_term_value": 15,
    "term_unit": "BUSINESS_DAYS",
    "counting_type": "CPC_BUSINESS_DAYS",
    "legal_basis": "Art. 350 e Art. 351, CPC",
    "precedence": 80,
    "allow_explicit_override": true,
    "applicable_act_types": ["REPLICA", "MANIFESTACAO_CONTESTACAO"]
  },
  {
    "rule_id": "CPC_ART_437_MANIFESTACAO_DOCUMENTOS",
    "category": "STATUTORY_SPECIFIC",
    "name": "Manifestação sobre Documentos Novos",
    "description": "Prazo para manifestação sobre documentos juntados pela parte contrária.",
    "default_term_value": 15,
    "term_unit": "BUSINESS_DAYS",
    "counting_type": "CPC_BUSINESS_DAYS",
    "legal_basis": "Art. 437, § 1º, CPC",
    "precedence": 70,
    "allow_explicit_override": true,
    "applicable_act_types": ["MANIFESTACAO_DOCUMENTOS"]
  },
  {
    "rule_id": "CPC_ART_1023_EMBARGOS_DECLARACAO",
    "category": "STATUTORY_SPECIFIC",
    "name": "Embargos de Declaração",
    "description": "Prazo para oposição de embargos de declaração.",
    "default_term_value": 5,
    "term_unit": "BUSINESS_DAYS",
    "counting_type": "CPC_BUSINESS_DAYS",
    "legal_basis": "Art. 1.023, caput, CPC",
    "precedence": 80,
    "allow_explicit_override": false,
    "applicable_act_types": ["EMBARGOS_DECLARACAO"]
  },
  {
    "rule_id": "CPC_ART_1003_APELACAO",
    "category": "STATUTORY_SPECIFIC",
    "name": "Apelação / Recurso Adesivo",
    "description": "Prazo para interposição de apelação ou resposta.",
    "default_term_value": 15,
    "term_unit": "BUSINESS_DAYS",
    "counting_type": "CPC_BUSINESS_DAYS",
    "legal_basis": "Art. 1.003, § 5º, CPC",
    "precedence": 80,
    "allow_explicit_override": false,
    "applicable_act_types": ["APELACAO", "CONTRARRAZOES_APELACAO"]
  },
  {
    "rule_id": "CPC_ART_218_P3_RESIDUAL",
    "category": "RESIDUAL_DEFAULT",
    "name": "Prazo Legal Residual Geral",
    "description": "Prazo geral aplicável quando a lei for omissa e o juiz não tiver assinado prazo.",
    "default_term_value": 5,
    "term_unit": "BUSINESS_DAYS",
    "counting_type": "CPC_BUSINESS_DAYS",
    "legal_basis": "Art. 218, § 3º, CPC",
    "precedence": 10,
    "allow_explicit_override": true,
    "applicable_act_types": ["MANIFESTACAO_GERAL", "PROCURACAO", "ESCLARECIMENTOS"]
  }
]
```

---

## 9. SCHEMA DE DATASET GOLDEN PARA TREINAMENTO E BENCHMARK

Para o fine-tuning e avaliação contínua do especialista local (SLM / Classificador), define-se o schema canônico de Golden Dataset:

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "title": "PrazoResolverGoldenRecordV1",
  "type": "object",
  "required": [
    "sample_id",
    "process_cnj",
    "tribunal",
    "process_class",
    "current_act",
    "historical_acts",
    "ground_truth"
  ],
  "properties": {
    "sample_id": { "type": "string" },
    "process_cnj": { "type": "string" },
    "tribunal": { "type": "string" },
    "process_class": { "type": "string" },
    "current_act": {
      "type": "object",
      "required": ["source_entity", "source_id", "act_type", "available_date", "full_text"],
      "properties": {
        "source_entity": { "type": "string", "enum": ["PUBLICATION", "MOVEMENT"] },
        "source_id": { "type": "string" },
        "act_type": { "type": "string" },
        "available_date": { "type": "string" },
        "full_text": { "type": "string" }
      }
    },
    "historical_acts": {
      "type": "array",
      "items": {
        "type": "object",
        "required": ["source_id", "sequence", "act_type", "author_name", "author_role", "occurred_at", "summary"],
        "properties": {
          "source_id": { "type": "string" },
          "sequence": { "type": "integer" },
          "act_type": { "type": "string" },
          "author_name": { "type": "string" },
          "author_role": { "type": "string", "enum": ["CLAIMANT", "RESPONDENT", "EXPERT", "PUBLIC_PROSECUTOR", "COURT", "THIRD_PARTY"] },
          "occurred_at": { "type": "string" },
          "summary": { "type": "string" }
        }
      }
    },
    "ground_truth": {
      "type": "object",
      "required": [
        "is_operative",
        "action_type",
        "action_text",
        "recipient_text",
        "recipient_role",
        "recipient_resolution_method",
        "antecedent_source_id",
        "explicit_term_value",
        "explicit_term_unit",
        "procedural_act_type",
        "expected_rule_id",
        "is_hard_negative",
        "review_required"
      ],
      "properties": {
        "is_operative": { "type": "boolean" },
        "action_type": { "type": "string" },
        "action_text": { "type": "string" },
        "recipient_text": { "type": "string" },
        "recipient_role": { "type": "string", "enum": ["CLAIMANT", "RESPONDENT", "BOTH", "THIRD_PARTY", "EXPERT", "PUBLIC_PROSECUTOR", "NONE"] },
        "recipient_resolution_method": { "type": "string" },
        "antecedent_source_id": { "type": ["string", "null"] },
        "explicit_term_value": { "type": ["integer", "null"] },
        "explicit_term_unit": { "type": "string" },
        "procedural_act_type": { "type": "string" },
        "expected_rule_id": { "type": "string" },
        "is_hard_negative": { "type": "boolean" },
        "review_required": { "type": "boolean" },
        "notes": { "type": "string" }
      }
    }
  }
}
```

---

## 10. CASO CANÔNICO OBRIGATÓRIO: "MANIFESTE-SE A PARTE CONTRÁRIA." (DJEN)

Demonstração passo a passo do fluxo operacional completo diante de uma publicação do DJEN com comando puramente relacional e sem prazo explícito:

### 10.1. Entrada Bruta
- **Fonte:** DJEN ComunicaAPI (`publications_v1.py`)
- **Processo:** `1234567-89.2026.8.26.0001` (fixture integralmente sintética; nenhuma referência a processo real)
- **Data de Disponibilização (`available_on`):** `2026-10-01` (Quinta-feira; data sintética do cenário de teste)
- **Teor da Publicação:**
  > *"Teor do ato: Fls. 142/150: Manifeste-se a parte contrária. Intimem-se."*

### 10.2. Passo 1: Extração da Instrução (`DeadlineInstruction V2`)
- `source_entity`: `"PUBLICATION"`
- `source_event_id`: `"pe_fixture_publication_001"`
- `source_id`: `"pub_fixture_001"`
- `source_excerpt`: `"Fls. 142/150: Manifeste-se a parte contrária. Intimem-se."`
- `action_text`: `"Manifeste-se a parte contrária"`
- `recipient_text`: `"parte contrária"`
- `term_value`: `None` (omissão judicial)
- `term_unit`: `"UNSPECIFIED"`
- `trigger_text`: `"Intimem-se"` (`trigger_status="EXPLICIT"`)
- `status`: `"AMBIGUOUS"` (pois exige resolução de polo e regra)

### 10.3. Passo 2: Execução do Especialista Local (Prazo Resolver)
1. **Localização do Antecedente:**
   - O especialista analisa o histórico cronológico de `movements` e `procedural_acts_v1`.
   - Identifica o movimento antecedente em `Fls. 142/150`:
     - `movement_id`: `"mov_seq_42"`
     - `title`: `"Juntada de Petição de Manifestação sobre Laudo com Novos Documentos"`
     - `actor`: Patrono do Autor (`CLAIMANT`).
2. **Resolução de "Parte Contrária":**
   - Antecedente praticado pelo Autor (`CLAIMANT`).
   - Inversão relacional: Destinatário = Réu (`RESPONDENT`).
   - Mapeamento: `recipient_role="RESPONDENT"`, `recipient_participant_ids=["part_re_empresa_x"]`.
   - `recipient_resolution_method="ANTECEDENT_RELATION"`.
3. **Classificação do Ato e Seleção de Regra:**
   - `procedural_act_type`: `"MANIFESTACAO_DOCUMENTOS"`.
   - Não há prazo judicial expresso (`explicit_term_value=None`).
   - Consulta ao catálogo de regras:
     - Regra específica: `CPC_ART_437_MANIFESTACAO_DOCUMENTOS` (Art. 437, § 1º, CPC: 15 dias úteis para manifestação sobre documentos novos).
     - `model_preferred_rule_id`: `"CPC_ART_437_MANIFESTACAO_DOCUMENTOS"` (hipótese do modelo).
     - O `RuleResolver` determinístico valida precedência, vigência, rito e hard constraints e somente então emite `resolved_rule_id="CPC_ART_437_MANIFESTACAO_DOCUMENTOS"`.
     - Duração legal: **15 dias úteis**.

### 10.4. Passo 3: Execução do Motor Determinístico de Prazos
1. **Gatilho e Datas Oficiais (Lei 11.419/2006 e CPC):**
   - Disponibilização no DJEN: `2026-10-01` (Quinta-feira).
   - Publicação oficial considerada (art. 4º, § 3º): `2026-10-02` (Sexta-feira).
   - Termo Inicial de contagem (art. 224, caput e § 2º): `2026-10-05` (Segunda-feira — 1º dia útil seguinte).
2. **Contagem de Dias Úteis (art. 219 CPC) com Calendário TJSP / Santo André:**
   - Dia 1: 05/10/2026 (Segunda)
   - Dia 2: 06/10/2026 (Terça)
   - Dia 3: 07/10/2026 (Quarta)
   - Dia 4: 08/10/2026 (Quinta)
   - Dia 5: 09/10/2026 (Sexta)
   - *Fim de semana: 10/10 e 11/10 (ignorado)*
   - *Feriado Nacional: 12/10/2026 (N. Sra. Aparecida — ignorado)*
   - Dia 6: 13/10/2026 (Terça)
   - Dia 7: 14/10/2026 (Quarta)
   - Dia 8: 15/10/2026 (Quinta)
   - Dia 9: 16/10/2026 (Sexta)
   - *Fim de semana: 17/10 e 18/10 (ignorado)*
   - Dia 10: 19/10/2026 (Segunda)
   - Dia 11: 20/10/2026 (Terça)
   - Dia 12: 21/10/2026 (Quarta)
   - Dia 13: 22/10/2026 (Quinta)
   - Dia 14: 23/10/2026 (Sexta)
   - *Fim de semana: 24/10 e 25/10 (ignorado)*
   - Dia 15 (Vencimento): **26/10/2026 (Segunda-feira)**.

### 10.5. Passo 4: Persistência Canônica
- Registro gravado na tabela `deadlines`:
  - `deadline_id`: `"deadline_..."`
  - `title`: `"Manifestação sobre Documentos (Réu)"`
  - `deadline_type`: `"LEGAL"`
  - `term`: `"15 dias úteis"`
  - `due_at`: `"2026-10-26T23:59:59"`
  - `responsible`: `"Empresa X (Ré)"`
  - `legal_basis`: `"Art. 437, § 1º, CPC c/c DJEN de 01/10/2026"`
  - `status`: `"CANDIDATE"` (ou `"CONFIRMED"` conforme parametrização)
  - `fingerprint`: SHA256 do prazo consolidado
  - `provenance_json`: Rastreamento completo (DJEN -> pub_id -> mov_id antecedente -> rule_id).

---

## 11. AVALIAÇÃO DE IMPACTO E MODELAGEM DE EVOLUÇÃO

### 11.1. Opções de Arquitetura Avaliadas
- **Opção A (Apenas Evoluir Tabelas Atuais):**
  Modificar in-place as colunas de `deadline_instructions` e `deadline_obligations`.
  *Vantagem:* sem tabelas extras.
  *Risco:* quebra de migração em bancos existentes de usuários ou processos em andamento se não houver backward-compatibility.
- **Opção B (Criar Entidades Paralelas Novas):**
  Criar `publication_deadlines`, `publication_instructions`, etc.
  *Desvantagem:* duplicação de conceitos e bifurcação de read models.
- **Opção C (Combinação Mínima Evolutiva — RECOMENDADA):**
  1. Evoluir `deadline_instructions` e `deadline_obligations` de forma não-destrutiva, ancorando instruções em `source_event_id -> process_events(event_id)` e preservando `source_entity/source_id` como provenance, mantendo compatibilidade com registros originados de `movements`.
  2. Adicionar tabela de referência declarativa `legal_deadline_rules_v1`.
  3. Manter intactas as tabelas `deadlines`, `process_events`, `publications` e `process_participants`.
  4. Preservar `LegalEventProjection` como único Read Model unificado.

---

## 12. HARDWARE TARGET E REQUISITOS DE EXECUÇÃO LOCAL

- **Ambiente de Destino:** Laptop comum / Desktop comercial (~16 GB RAM, CPU Intel/AMD ou iGPU, sem dependência de GPU dedicada RTX).
- **Modelo Especialista Local:**
  - Baseline/teacher preferencial: encoder jurídico em português na ordem de ~100M parâmetros, não LLM generativa de bilhões como requisito de runtime.
  - Objetivo de produto: destilação para encoder/classificador especializado de aproximadamente 20–65M parâmetros se o golden demonstrar manutenção de qualidade.
  - Execução ONNX/INT8 em CPU; embeddings e grafo processual podem atuar como features auxiliares.
  - LLM de 1B+ pode ser usada apenas como teacher, ferramenta de rotulagem assistida ou fallback experimental, nunca como dependência obrigatória.
  - Meta de RAM do especialista: muito abaixo de 2 GB; meta de latência: subsegundo por ato em CPU típica, a validar por benchmark real.

---

## 13. RISCOS E MITIGAÇÕES

| Risco Identificado | Impacto | Mitigação Arquitetural |
|---|---|---|
| Ambiguidade no Antecedente (múltiplas petições recentes de polos distintos) | Seleção incorreta de destinatário ou regra | Classificar `review_required=True`, `confidence < 0.70`, e marcar status como `AMBIGUOUS` para conferência do advogado na UI |
| Erro em Feriado Local da Comarca | Cálculo de vencimento divergente | Cache local versionado alimentado por fontes oficiais, com provenance, validade e atualização periódica/sob demanda; correções não exigem reprocessar IA |
| Cancelamento / Retificação de Publicação no DJEN | Prazo gerado sobre ato revogado | `publications_v1.py` já suporta `publication_status`, `canceled_on` e `active`; exclusão em cascata / atualização para `CANCELED` no store |
| Dependência de Usuário Logado para Inferência de Polo | Violação grave da neutralidade documental | Invariante relacional estrita: autoria do antecedente determina o polo destinatário independentemente de quem está usando o Themis |

---

## 13.1. DECISÕES FECHADAS NESTA REVISÃO

- **Antecedentes concorrentes:** quando o comando explicita pluralidade (`às partes`, `ambas as partes`), materializam-se obrigações para os polos alcançados. Quando houver mais de um antecedente semanticamente plausível de polos distintos e o texto não resolver a relação, manter candidatos e marcar `review_required=true`; não promover silenciosamente um deles.
- **Feriados e suspensões:** usar cache local versionado alimentado exclusivamente por fontes oficiais, com provenance, validade e atualização periódica/sob demanda. O cálculo funciona offline após sincronização, sem depender de tabela estática eterna nem consulta online a cada prazo.

---

## 14. SEQUÊNCIA CONCRETA DE IMPLEMENTAÇÃO

```text
Fase 1: Schemas e Core Store (Não-destrutivo)
├── 1.1. Implementar migração de deadline_instructions_v2.py (source_event_id + provenance source_entity/source_id)
├── 1.2. Implementar migração de deadline_obligations_v2.py (antecedent_source_event_id + resolved_rule_id)
├── 1.3. Implementar legal_deadline_rules_v1.py (catálogo declarativo versionado)
└── 1.4. Implementar deadline_rule_resolver_v1.py determinístico (precedência, vigência, rito e hard constraints)

Fase 2: Motor Determinístico de Prazos
├── 2.1. Implementar cpc_deadline_calculator_v1.py (regras DJEN, D+1, CPC 219/220/224)
└── 2.2. Implementar calendário base (feriados nacionais e tabela de comarcas TJSP)

Fase 3: Especialista Local & Resolução de Antecedente
├── 3.1. Implementar procedural_antecedent_resolver_v1.py (grafo de atos e resolução de polo)
├── 3.2. Implementar pipeline de inferência local (Prazo Resolver: classificação + ranking de regras)
└── 3.3. Integrar com o fluxo de sincronização do DJEN (publications_v1.py -> ProcessEvent -> instrução -> obrigação -> deadline)

Fase 4: Validação Golden & UI
├── 4.1. Criar fixture golden com 50 casos canônicos (incluindo "Manifeste-se a parte contrária")
├── 4.2. Validar projeção em LegalEventProjection e endpoint /api/legal_events
└── 4.3. Homologação visual na aba EVENTOS do Themis Desktop
```
