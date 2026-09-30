from __future__ import annotations

import hashlib
import json
import os
import random
import time
import urllib.request
from collections import Counter
from pathlib import Path

import numpy as np

from core.retrieval.onnx_embed import generate_embeddings_batch_onnx

SEED = 20260929
random.seed(SEED)
np.random.seed(SEED)

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
CASES = HERE / "cases.jsonl"
MODEL_DIR = ROOT / ".benchmark-model"
MODEL = MODEL_DIR / "model_int8.onnx"
TOKENIZER = MODEL_DIR / "tokenizer.json"

REVISION = "21c18bde7134255900b90d771036f93261a268f5"
BASE = "https://huggingface.co/srigf/themis-embeddinggemma-300m-onnx-int8/resolve/" + REVISION
FILES = {
    MODEL: (
        BASE + "/model_int8.onnx",
        "1b477e4439d33c26fa925f17fa5901d524daf9487a9f39b38e6d84ba7301f0ea",
        310016659,
    ),
    TOKENIZER: (
        BASE + "/tokenizer.json",
        "6852f8d561078cc0cebe70ca03c5bfdd0d60a45f9d2e0e1e4cc05b68e9ec329e",
        33385008,
    ),
}

TASK_LABELS = {
    "operative_instruction": [False, True],
    "context_sufficiency": ["SUFFICIENT", "NEEDS_CONTEXT", "AMBIGUOUS_REVIEW"],
    "recipient_role": ["PLAINTIFF", "DEFENDANT", "BOTH_PARTIES", "THIRD_PARTY", "UNRESOLVED"],
    "procedural_act_type": [
        "PROVIDE_DOCUMENTS", "PROVIDE_INFORMATION", "RESPOND_TO_OPPOSING_SUBMISSION",
        "SPECIFY_EVIDENCE", "MANIFEST_AFTER_MEASURE", "FILE_MEMORIALS", "FILE_DEFENSE", "NONE",
    ],
}


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def download_verified() -> None:
    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    for path, (url, expected_sha, expected_size) in FILES.items():
        if not path.exists() or sha256(path) != expected_sha:
            print(f"Downloading {path.name} from pinned revision {REVISION}...", flush=True)
            urllib.request.urlretrieve(url, path)
        actual_sha = sha256(path)
        actual_size = path.stat().st_size
        print(f"{path.name}: bytes={actual_size} sha256={actual_sha}", flush=True)
        if actual_sha != expected_sha:
            raise RuntimeError(f"SHA-256 mismatch for {path.name}")
        if actual_size != expected_size:
            raise RuntimeError(f"size mismatch for {path.name}: {actual_size} != {expected_size}")


def row(text, op, suff, role, act, context=""):
    full = text if not context else text + "\nContexto processual: " + context
    return {
        "text": full,
        "operative_instruction": op,
        "context_sufficiency": suff,
        "recipient_role": role,
        "procedural_act_type": act,
    }


def synthetic_rows():
    rows = []
    defendants = ["parte demandada", "ré", "executada", "requerida"]
    plaintiffs = ["parte demandante", "autora", "exequente", "requerente"]
    thirds = ["empresa oficiada", "instituição destinatária", "terceiro oficiado", "empregadora consultada"]
    doc_verbs = ["junte", "apresente", "traga aos autos", "encaminhe ao juízo"]
    info_verbs = ["informe", "esclareça", "preste informações sobre", "comunique ao juízo"]
    proof_verbs = ["especifiquem as provas", "indiquem as provas", "digam quais provas pretendem produzir"]
    memorial_verbs = ["apresentem memoriais", "ofereçam alegações finais por memoriais", "juntem memoriais finais"]
    defense_verbs = ["apresente contestação", "ofereça defesa", "responda à demanda"]
    terms = ["em 5 dias", "no prazo de 10 dias", "em 15 dias úteis", "no prazo assinalado de 20 dias"]

    for role_text in defendants:
        for verb in doc_verbs:
            for term in terms[:3]:
                rows.append(row(f"Determino que a {role_text} {verb} os documentos pertinentes {term}.",
                                True, "SUFFICIENT", "DEFENDANT", "PROVIDE_DOCUMENTS"))
        for verb in defense_verbs:
            rows.append(row(f"Cite-se a {role_text} para que {verb}.",
                            True, "SUFFICIENT", "DEFENDANT", "FILE_DEFENSE"))

    for role_text in plaintiffs:
        for verb in doc_verbs[:3]:
            rows.append(row(f"Intime-se a {role_text} para que {verb} os comprovantes mencionados {terms[1]}.",
                            True, "SUFFICIENT", "PLAINTIFF", "PROVIDE_DOCUMENTS"))
        rows.append(row(f"Após o cumprimento da diligência, dê-se vista à {role_text} para manifestação {terms[3]}.",
                        True, "SUFFICIENT", "PLAINTIFF", "MANIFEST_AFTER_MEASURE"))

    for third in thirds:
        for verb in info_verbs:
            rows.append(row(f"Oficie-se à {third} para que {verb} dados funcionais e pagamentos {terms[1]}.",
                            True, "SUFFICIENT", "THIRD_PARTY", "PROVIDE_INFORMATION"))

    for verb in proof_verbs:
        for term in terms[:2]:
            rows.append(row(f"Intimem-se autor e réu para que {verb} {term}.",
                            True, "SUFFICIENT", "BOTH_PARTIES", "SPECIFY_EVIDENCE"))

    for verb in memorial_verbs:
        rows.append(row(f"As partes deverão {verb} até a data designada.",
                        True, "SUFFICIENT", "BOTH_PARTIES", "FILE_MEMORIALS"))

    opposing_phrases = [
        "Ouça-se a parte adversa em cinco dias.",
        "Dê-se vista à parte contrária para resposta.",
        "Intime-se o polo oposto para manifestação sobre o requerimento.",
        "Abra-se prazo à parte adversária para dizer sobre a petição.",
    ]
    for text in opposing_phrases:
        for suffix in ["", " O ato anterior não foi fornecido.", " Não há identificação da petição antecedente."]:
            rows.append(row(text + suffix, True, "NEEDS_CONTEXT", "UNRESOLVED",
                            "RESPOND_TO_OPPOSING_SUBMISSION"))

    for actor, recipient in [("autora", "DEFENDANT"), ("ré", "PLAINTIFF")]:
        for text in ["Ouça-se a parte adversa em cinco dias.", "Vista à parte contrária para resposta."]:
            ctx = f"A petição imediatamente relacionada foi apresentada pela parte {actor} e provocou este despacho."
            rows.append(row(text, True, "SUFFICIENT", recipient,
                            "RESPOND_TO_OPPOSING_SUBMISSION", ctx))

    for ctx in [
        "Há uma petição da autora e outra da ré, ambas imediatamente anteriores e sobre o mesmo tema.",
        "Dois requerimentos opostos, um de cada polo, podem ter provocado o despacho e a origem não está indicada.",
    ]:
        for text in ["Manifeste-se a parte adversa em cinco dias.", "Vista à parte contrária."]:
            rows.append(row(text, True, "AMBIGUOUS_REVIEW", "UNRESOLVED",
                            "RESPOND_TO_OPPOSING_SUBMISSION", ctx))

    for ref in ["o terceiro indicado na capa", "a interessada cadastrada no polo auxiliar",
                "a empresa mencionada apenas no cadastro"]:
        rows.append(row(f"Intime-se {ref} para juntar comprovantes em dez dias.",
                        True, "NEEDS_CONTEXT", "THIRD_PARTY", "PROVIDE_DOCUMENTS"))

    for requester in ["autora", "ré", "exequente", "requerente"]:
        rows.extend([
            row(f"A parte {requester} requer prazo adicional para juntar documentos.",
                False, "SUFFICIENT", "UNRESOLVED", "NONE"),
            row(f"A {requester} pede que seja intimada a empresa para prestar informações.",
                False, "SUFFICIENT", "UNRESOLVED", "NONE"),
            row(f"Requer a parte {requester} a concessão de quinze dias para manifestação.",
                False, "SUFFICIENT", "UNRESOLVED", "NONE"),
        ])

    for text in [
        "Junte-se aos autos e certifique-se.",
        "Anote-se no sistema. Após, conclusos.",
        "Cumpra a serventia as anotações necessárias.",
        "Certifique o cartório o trânsito e arquive-se.",
        "Remetam-se os autos ao contador judicial.",
        "Publique-se. Registre-se. Intimem-se conforme cadastro.",
    ]:
        rows.append(row(text, False, "SUFFICIENT", "UNRESOLVED", "NONE"))

    expanded = []
    prefixes = ["", "Em decisão, ", "Consta do despacho: "]
    suffixes = ["", " Cumpra-se.", " Sem prejuízo das demais determinações."]
    for item in rows:
        for p in prefixes:
            for s in suffixes:
                x = dict(item)
                x["text"] = p + item["text"] + s
                expanded.append(x)
    random.shuffle(expanded)
    return expanded


def benchmark_rows():
    out = []
    for line in CASES.read_text(encoding="utf-8-sig").splitlines():
        if not line.strip():
            continue
        c = json.loads(line)
        ctx = " ".join(str(x.get("text", "")) for x in c.get("context", []))
        text = c["excerpt"] + (("\nContexto processual: " + ctx) if ctx else "")
        e = c["expected"]
        out.append({
            "id": c["id"],
            "text": text,
            "operative_instruction": e["operative_instruction"],
            "context_sufficiency": e["context_sufficiency"],
            "recipient_role": e.get("recipient_role", "UNRESOLVED"),
            "procedural_act_type": e.get("procedural_act_type") or "NONE",
        })
    return out


def softmax(z):
    z = z - z.max(axis=1, keepdims=True)
    e = np.exp(z)
    return e / e.sum(axis=1, keepdims=True)


def train_head(x, labels, classes, epochs=700, lr=0.25, weight_decay=1e-3):
    class_index = {str(v): i for i, v in enumerate(classes)}
    y = np.array([class_index[str(v)] for v in labels], dtype=np.int64)
    n, d = x.shape
    k = len(classes)
    w = np.zeros((d, k), dtype=np.float32)
    b = np.zeros((k,), dtype=np.float32)
    y_onehot = np.eye(k, dtype=np.float32)[y]

    counts = np.bincount(y, minlength=k).astype(np.float32)
    weights = np.where(counts > 0, n / (k * counts), 0.0)
    sample_w = weights[y][:, None]

    for step in range(epochs):
        logits = x @ w + b
        p = softmax(logits)
        diff = (p - y_onehot) * sample_w
        gw = (x.T @ diff) / n + weight_decay * w
        gb = diff.mean(axis=0)
        rate = lr / (1.0 + step / 500.0)
        w -= rate * gw
        b -= rate * gb
    return w, b


def embed(texts, batch=32):
    result = []
    for i in range(0, len(texts), batch):
        vecs = generate_embeddings_batch_onnx(
            texts[i:i + batch],
            is_query=False,
            model_path=MODEL,
            tokenizer_path=TOKENIZER,
        )
        if any(v is None for v in vecs):
            raise RuntimeError("embedding inference returned None")
        result.extend(vecs)
    return np.asarray(result, dtype=np.float32)


def main():
    os.environ["THEMIS_ONNX_THREADS"] = "4"
    download_verified()

    train = synthetic_rows()
    test = benchmark_rows()
    print("train_examples=", len(train))
    for task in TASK_LABELS:
        print(task, Counter(str(r[task]) for r in train))

    t0 = time.perf_counter()
    x_train = embed([r["text"] for r in train])
    train_embed_s = time.perf_counter() - t0

    t0 = time.perf_counter()
    x_test = embed([r["text"] for r in test])
    test_embed_s = time.perf_counter() - t0

    summary = {
        "model_revision": REVISION,
        "model_sha256": sha256(MODEL),
        "tokenizer_sha256": sha256(TOKENIZER),
        "train_examples": len(train),
        "test_examples": len(test),
        "embedding_train_seconds": train_embed_s,
        "embedding_test_seconds": test_embed_s,
        "embedding_test_ms_per_case": test_embed_s * 1000.0 / len(test),
        "tasks": {},
        "rows": [],
    }

    predictions = {}
    for task, classes in TASK_LABELS.items():
        w, b = train_head(x_train, [r[task] for r in train], classes)
        idx = np.argmax(x_test @ w + b, axis=1)
        pred = [classes[int(i)] for i in idx]
        predictions[task] = pred
        correct = sum(str(p) == str(r[task]) for p, r in zip(pred, test))
        summary["tasks"][task] = {
            "correct": correct,
            "total": len(test),
            "accuracy": correct / len(test),
        }

    for i, r in enumerate(test):
        summary["rows"].append({
            "id": r["id"],
            "pred": {task: predictions[task][i] for task in TASK_LABELS},
            "expected": {task: r[task] for task in TASK_LABELS},
        })

    print("\n=== PUBLIC THEMIS EMBEDDINGGEMMA SPECIALIST PROBE ===")
    print(f"model_sha256={summary['model_sha256']}")
    print(f"tokenizer_sha256={summary['tokenizer_sha256']}")
    print(f"embedding_test_ms_per_case={summary['embedding_test_ms_per_case']:.2f}")
    for task, m in summary["tasks"].items():
        print(f"{task}: {m['correct']}/{m['total']} = {m['accuracy']:.3f}")
    print("\n=== CASES ===")
    for r in summary["rows"]:
        print(r["id"], "PRED=", r["pred"], "EXPECTED=", r["expected"])

    out = HERE / "public_embeddinggemma_results.json"
    out.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nWrote {out}")


if __name__ == "__main__":
    main()
