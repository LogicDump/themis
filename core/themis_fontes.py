"""Módulo de fontes públicas e sincronização oficial DataJud/CNJ do Jurídico."""
from __future__ import annotations

import html
import json
import os
import re
import sqlite3
import sys
import time
import unicodedata
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from core.runtime_paths import index_db_path

SERVER_NAME = "juridico-fontes"
SERVER_VERSION = "0.2.0"
MAX_LIMIT = 20
USER_AGENT = "juridico-fontes/0.2 (local legal research)"
DATAJUD_BASE_URL = "https://api-publica.datajud.cnj.jus.br"

TR_UF = {
    "01": "ac", "02": "al", "03": "ap", "04": "am", "05": "ba", "06": "ce",
    "07": "dft", "08": "es", "09": "go", "10": "ma", "11": "mt", "12": "ms",
    "13": "mg", "14": "pa", "15": "pb", "16": "pr", "17": "pe", "18": "pi",
    "19": "rj", "20": "rn", "21": "rs", "22": "ro", "23": "rr", "24": "sc",
    "25": "se", "26": "sp", "27": "to",
}


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def normalize_name(text: str) -> str:
    if not text:
        return ""
    normalized = unicodedata.normalize("NFKD", str(text))
    ascii_text = normalized.encode("ascii", "ignore").decode("ascii")
    return " ".join(re.sub(r"[^A-Za-z0-9\s]", " ", ascii_text).upper().split())


def generate_entity_id(display_name: str) -> str:
    import hashlib
    norm = normalize_name(display_name)
    h = hashlib.sha256(norm.encode("utf-8")).hexdigest()[:16]
    return f"entity_{h}"


def datajud_alias(cnj_digits: str) -> str | None:
    if not re.fullmatch(r"\d{20}", cnj_digits):
        return None
    segment, tribunal = cnj_digits[13], cnj_digits[14:16]
    number, uf = int(tribunal), TR_UF.get(tribunal)
    if segment == "8": return f"api_publica_tj{uf}" if uf else None
    if segment == "4": return f"api_publica_trf{number}" if 1 <= number <= 6 else None
    if segment == "5": return "api_publica_tst" if tribunal == "00" else (f"api_publica_trt{number}" if 1 <= number <= 24 else None)
    if segment == "6": return "api_publica_tse" if tribunal == "00" else (f"api_publica_tre-{uf}" if uf else None)
    if segment == "3": return "api_publica_stj" if tribunal == "00" else None
    if segment == "7": return "api_publica_stm" if tribunal == "00" else None
    if segment == "9" and uf in {"mg", "rs", "sp"}: return f"api_publica_tjm{uf}"
    return None


def datajud_settings() -> tuple[str, int]:
    configured_key = ""
    timeout = 35
    try:
        from core.runtime_paths import fontes_config_path, themis_data_root
        primary_cfg = fontes_config_path()
        fallback_cfg = themis_data_root() / "config" / "fontes.json"
    except Exception:
        primary_cfg = Path("config/fontes.json")
        fallback_cfg = primary_cfg

    candidate_paths = [
        primary_cfg,
        fallback_cfg,
        Path(__file__).resolve().parent.parent / "config" / "fontes.json",
    ]
    for cfg_path in candidate_paths:
        if cfg_path.is_file():
            try:
                config = json.loads(cfg_path.read_text(encoding="utf-8"))
                if isinstance(config, dict) and "datajud" in config:
                    dj = config["datajud"]
                    val = dj.get("api_key")
                    if isinstance(val, str) and val.strip():
                        configured_key = val.strip()
                    cand_t = dj.get("timeout_seconds")
                    if isinstance(cand_t, int) and 5 <= cand_t <= 60:
                        timeout = cand_t
                    break
            except Exception:
                pass

    env_key = (os.environ.get("THEMIS_DATAJUD_API_KEY") or os.environ.get("JURIDICO_DATAJUD_API_KEY", "")).strip()
    return env_key or configured_key, timeout


def format_cnj(digits: str) -> str:
    digits = re.sub(r"\D", "", digits)
    if len(digits) != 20:
        return digits
    return f"{digits[:7]}-{digits[7:9]}.{digits[9:13]}.{digits[13]}.{digits[14:16]}.{digits[16:]}"


def normalize_movement(item: Any) -> dict[str, Any]:
    item = item if isinstance(item, dict) else {}
    national = item.get("movimentoNacional") if isinstance(item.get("movimentoNacional"), dict) else {}
    return {
        "date": item.get("dataHora"),
        "name": item.get("nome") or national.get("nome") or "Movimentação registrada",
        "code": item.get("codigo") or national.get("codigo"),
        "content": item.get("texto") or item.get("descricao") or None,
    }


def normalize_participant(item: Any, default_role: str) -> dict[str, Any]:
    item = item if isinstance(item, dict) else {}
    tipo = str(item.get("tipoPessoa") or item.get("tipo") or "").upper()
    entity_type = "PERSON" if "FIS" in tipo else ("ORGANIZATION" if "JUR" in tipo else "PERSON")
    display_name = str(item.get("nome") or item.get("nomePessoa") or "").strip()
    doc_id = item.get("numeroDocumentoPrincipal") or item.get("documento") or item.get("cpf") or item.get("cnpj")
    identifiers: dict[str, str] = {}
    if doc_id:
        clean_doc = re.sub(r"\D", "", str(doc_id))
        if len(clean_doc) == 11:
            identifiers["CPF"] = str(doc_id)
            entity_type = "PERSON"
        elif len(clean_doc) == 14:
            identifiers["CNPJ"] = str(doc_id)
            entity_type = "ORGANIZATION"
        else:
            identifiers["DOC"] = str(doc_id)

    advogados: list[dict[str, Any]] = []
    for adv in item.get("advogados") or []:
        if isinstance(adv, dict) and adv.get("nome"):
            adv_name = str(adv["nome"]).strip()
            adv_oab = adv.get("numeroOAB") or adv.get("oab")
            adv_ids = {"OAB": str(adv_oab)} if adv_oab else {}
            advogados.append({
                "role": "ADVOGADO",
                "display_name": adv_name,
                "entity_type": "PERSON",
                "identifiers": adv_ids,
            })

    return {
        "role": default_role,
        "display_name": display_name,
        "entity_type": entity_type,
        "identifiers": identifiers,
        "advogados": advogados,
    }


def process_lookup(cnj_value: str) -> dict[str, Any]:
    digits = re.sub(r"\D", "", str(cnj_value).strip())
    if len(digits) != 20:
        raise ValueError("process_id deve conter 20 dígitos CNJ")
    alias = datajud_alias(digits)
    if not alias:
        raise ValueError("Tribunal não mapeado para DataJud")
    key, timeout = datajud_settings()
    if not key:
        raise ValueError("Chave de API do DataJud não configurada")

    url = f"{DATAJUD_BASE_URL}/{alias}/_search"
    body = {"size": 1, "query": {"match": {"numeroProcesso": digits}}}
    req = Request(
        url,
        data=json.dumps(body).encode("utf-8"),
        headers={
            "Authorization": f"APIKey {key}",
            "Content-Type": "application/json",
            "User-Agent": USER_AGENT,
        },
        method="POST",
    )
    with urlopen(req, timeout=timeout) as resp:
        raw = resp.read()
    response = json.loads(raw.decode("utf-8"))

    hits = response.get("hits", {}).get("hits", [])
    if not hits:
        return {
            "source_type": "OFFICIAL_SOURCE",
            "source_name": "DataJud / Conselho Nacional de Justiça",
            "official": True,
            "jurisdiction": "BR",
            "identifier": format_cnj(digits),
            "retrieved_at": utc_now(),
            "source_reference": url,
            "data": {
                "process_id": format_cnj(digits),
                "found": False,
                "tribunal_alias": alias,
            },
        }

    source = hits[0].get("_source", {})
    classe = source.get("classe") if isinstance(source.get("classe"), dict) else {}
    orgao = source.get("orgaoJulgador") if isinstance(source.get("orgaoJulgador"), dict) else {}
    assuntos = source.get("assuntos") if isinstance(source.get("assuntos"), list) else []
    movements = [normalize_movement(item) for item in source.get("movimentos", []) if isinstance(item, dict)]
    movements.sort(key=lambda item: str(item.get("date") or ""), reverse=True)

    participants: list[dict[str, Any]] = []
    for polo in source.get("poloAtivo") or []:
        p = normalize_participant(polo, "AUTOR")
        if p["display_name"]:
            advs = p.pop("advogados", [])
            participants.append(p)
            participants.extend(advs)
    for polo in source.get("poloPassivo") or []:
        p = normalize_participant(polo, "REU")
        if p["display_name"]:
            advs = p.pop("advogados", [])
            participants.append(p)
            participants.extend(advs)
    for polo in source.get("outrosParticipantes") or []:
        role = str(polo.get("polo") or polo.get("tipoParticipacao") or "TERCEIRO").upper()
        p = normalize_participant(polo, role)
        if p["display_name"]:
            advs = p.pop("advogados", [])
            participants.append(p)
            participants.extend(advs)

    return {
        "source_type": "OFFICIAL_SOURCE",
        "source_name": "DataJud / Conselho Nacional de Justiça",
        "official": True,
        "jurisdiction": "BR",
        "identifier": format_cnj(digits),
        "retrieved_at": utc_now(),
        "source_reference": url,
        "data": {
            "process_id": format_cnj(digits),
            "numeroProcesso": source.get("numeroProcesso"),
            "found": True,
            "tribunal": source.get("tribunal"),
            "tribunal_alias": alias,
            "class": classe.get("nome") or source.get("classe"),
            "system": source.get("sistema"),
            "format": source.get("formato"),
            "filing_date": source.get("dataAjuizamento"),
            "subjects": [{"code": item.get("codigo"), "name": item.get("nome")} for item in assuntos if isinstance(item, dict)],
            "judging_body": orgao.get("nome") or source.get("orgaoJulgador"),
            "degree": source.get("grau"),
            "updated_at": source.get("dataHoraUltimaAtualizacao"),
            "participants": participants,
            "movements": movements,
        },
    }


def extract_participants_from_initial_petition(text: str) -> list[dict[str, Any]]:
    """Extrai partes e identificadores qualificadas a partir da petição inicial (Folha 1)."""
    if not text:
        return []

    participants: list[dict[str, Any]] = []

    # Autor / Requerente
    autor_match = re.search(
        r"([A-Z\u00C0-\u00DF\s]{4,60}),\s*(?:brasileir[oa]|solteir[oa]|casad[oa]|divorciad[oa]|aposentad[oa]|maior|menor)",
        text,
    )
    if autor_match:
        nome_autor = autor_match.group(1).strip()
        nome_autor = re.sub(r"^(?:EXCELENTISSIMO|AO|A|VARA|COMARCA|DE DIREITO)\b.*?\n+", "", nome_autor, flags=re.I).strip()
        nome_autor = nome_autor.split("\n")[-1].strip()
        nome_autor = re.sub(r"^[^A-Za-z\u00C0-\u00DF]+", "", nome_autor).strip()
        if len(nome_autor) >= 4 and not any(k in nome_autor for k in ["JUIZ", "DIREITO", "VARA", "COMARCA", "ESTADO"]):
            ids: dict[str, str] = {}
            cpf_m = re.search(r"CPF(?:/MF)?\s*(?:sob\s*o\s*n[ºo.]?\s*)?(\d{3}\.?\d{3}\.?\d{3}-?\d{2})", text[autor_match.start():autor_match.start()+400], re.I)
            if cpf_m: ids["CPF"] = cpf_m.group(1)
            rg_m = re.search(r"RG\s*(?:n[ºo.]?\s*)?([\d.-]+(?:\s*[A-Za-z0-9/]+)?)", text[autor_match.start():autor_match.start()+400], re.I)
            if rg_m:
                ids["RG"] = re.sub(r"\s+(?:e|SSP|inscrit[oa]|devidamente|portador).*$", "", rg_m.group(1), flags=re.I).strip()
            participants.append({
                "role": "AUTOR",
                "display_name": nome_autor,
                "entity_type": "PERSON",
                "identifiers": ids,
            })

    # Réu / Requerido
    reu_match = re.search(
        r"(?:Em face de|em face de|contra|CONTRA|movida em face de)\s+([A-Z\u00C0-\u00DF\s]{4,60})",
        text,
    )
    if reu_match:
        nome_reu = reu_match.group(1).strip()
        nome_reu = re.split(r",|\s+(?:menor|maior|brasileir|representad)", nome_reu)[0].strip()
        if len(nome_reu) >= 4:
            participants.append({
                "role": "REU",
                "display_name": nome_reu,
                "entity_type": "PERSON",
                "identifiers": {},
            })

    # Representante / Genitora / Advogada
    rep_match = re.search(
        r"(?:representad[ao]\s+por\s+(?:sua\s+genitora\s+)?)([A-Z\u00C0-\u00DF\s]{4,60}),",
        text,
    )
    if rep_match:
        nome_rep = rep_match.group(1).strip()
        if len(nome_rep) >= 4:
            rep_ids: dict[str, str] = {}
            cpf_rep = re.search(r"CPF(?:/MF)?\s*(?:sob\s*o\s*n[ºo.]?\s*)?(\d{3}\.?\d{3}\.?\d{3}-?\d{2})", text[rep_match.start():rep_match.start()+400], re.I)
            if cpf_rep: rep_ids["CPF"] = cpf_rep.group(1)
            rg_rep = re.search(r"RG\s*(?:n[ºo.]?\s*)?([\d.-]+(?:\s*[A-Za-z0-9/]+)?)", text[rep_match.start():rep_match.start()+400], re.I)
            if rg_rep:
                rep_ids["RG"] = re.sub(r"\s+(?:e|SSP/SP|SSP|inscrit[oa]|devidamente|portador).*$", "", rg_rep.group(1), flags=re.I).strip()
            oab_rep = re.search(r"OAB\s*(?:n[ºo.]?\s*|/SP\s*)?(\d{5,8})", text[rep_match.start():rep_match.start()+400], re.I)
            if oab_rep: rep_ids["OAB"] = oab_rep.group(1)

            role = "REPRESENTANTE / ADVOGADA" if "OAB" in rep_ids else "REPRESENTANTE"
            participants.append({
                "role": role,
                "display_name": nome_rep,
                "entity_type": "PERSON",
                "identifiers": rep_ids,
            })

    return participants


def extract_movements_from_autos(conn: sqlite3.Connection, process_id: str) -> list[dict[str, Any]]:
    """Extrai cronologia de atos judiciais a partir dos autos indexados do processo."""
    rows = conn.execute(
        """SELECT p.page_number, p.content FROM pages p
        JOIN documents d USING(document_id)
        WHERE d.process_id=? AND p.quality != 'BAD'
        ORDER BY p.page_number""",
        (process_id,),
    ).fetchall()

    meses = {
        "janeiro": "01", "fevereiro": "02", "marco": "03", "março": "03",
        "abril": "04", "maio": "05", "junho": "06", "julho": "07",
        "agosto": "08", "setembro": "09", "outubro": "10", "novembro": "11", "dezembro": "12"
    }

    def parse_ptbr_date(date_str: str) -> str | None:
        if not date_str:
            return None
        m = re.match(r"(\d{1,2})\s+de\s+([a-zç]+)\s+de\s+(\d{4})", date_str.lower().strip())
        if m:
            day, mes, year = int(m.group(1)), m.group(2), m.group(3)
            mm = meses.get(mes, "01")
            return f"{year}-{mm}-{day:02d}"
        m2 = re.match(r"(\d{2})/(\d{2})/(\d{4})", date_str.strip())
        if m2:
            return f"{m2.group(3)}-{m2.group(2)}-{m2.group(1)}"
        return None

    movements: list[dict[str, Any]] = []
    seen: set[tuple[str, str | None, int]] = set()

    for r in rows:
        pno = r["page_number"]
        content = r["content"] or ""
        if len(content.strip()) < 30 or content.startswith("*[Página digitalizada"):
            continue
        lines = [line.strip() for line in content.split("\n") if line.strip()]
        if not lines:
            continue

        if pno == 1:
            date_m = re.search(r"(\d{1,2}\s+de\s+[a-zç]+\s+de\s+\d{4}|\d{2}/\d{2}/\d{4})", content)
            d_str = parse_ptbr_date(date_m.group(1)) if date_m else None
            movements.append({
                "movement_type": "Distribuição / Petição Inicial",
                "occurred_at": d_str,
                "content": f"Petição Inicial protocolada (fls. {pno}).",
                "page": pno,
            })
            continue

        act_title = None
        for l in lines[:10]:
            clean_l = re.sub(r"^[#*\s-]+", "", l).strip()
            if re.fullmatch(
                r"(?:DESPACHO|DECIS[ÃA]O|DECIS[ÃA]O-MANDADO|SENTEN[ÇC]A|ATO ORDINAT[ÓO]RIO|"
                r"CERTID[ÃA]O DE REMESSA(?: DE RELA[ÇC][ÃA]O)?|"
                r"CERTID[ÃA]O DE REMESSA PARA O PORTAL ELETR[ÔO]NICO|"
                r"CERTID[ÃA]O DE PUBLICA[ÇC][ÃA]O|CERTID[ÃA]O DE TR[ÂA]NSITO EM JULGADO|"
                r"CERTID[ÃA]O\s*[\-\–]\s*DECURSO DE PRAZO|MANIFESTA[ÇC][ÃA]O(?: DO MINIST[ÉE]RIO P[ÚU]BLICO)?|"
                r"TERMO DE AUDI[ÊE]NCIA)",
                clean_l,
                re.I,
            ):
                act_title = clean_l
                break

        if act_title:
            date_matches = list(re.finditer(r"(\d{1,2}\s+de\s+[a-zç]+\s+de\s+\d{4}|\d{2}/\d{2}/\d{4})", content, re.I))
            date_str = None
            if date_matches:
                for dm in reversed(date_matches):
                    d_parsed = parse_ptbr_date(dm.group(1))
                    if d_parsed:
                        date_str = d_parsed
                        break
            desc_lines = [l for l in lines if not re.match(r"^(?:TRIBUNAL|COMARCA|FORO|Processo|Classe|Juiz|Horário|##|#)", l, re.I)]
            snippet = " ".join(desc_lines[:2])[:250] if desc_lines else f"{act_title} proferido nos autos."
            k = (act_title.upper(), date_str, pno)
            if k not in seen:
                seen.add(k)
                movements.append({
                    "movement_type": act_title,
                    "occurred_at": date_str,
                    "content": f"{act_title} (fls. {pno}): {snippet}",
                    "page": pno,
                })

    return movements


def sync_process_from_datajud(process_id: str, db_path: Path | str | None = None) -> dict[str, Any]:
    """Sincroniza metadados e partes do processo no process.db do CNJ."""
    from core.runtime_paths import process_db_path
    target_db = Path(db_path or process_db_path(process_id)).resolve()
    if not target_db.is_file():
        raise FileNotFoundError(f"Banco de dados não encontrado em {target_db}")

    conn = sqlite3.connect(str(target_db))
    conn.row_factory = sqlite3.Row
    now = utc_now()

    try:
        # 1. Consulta DataJud
        datajud_payload = {}
        source_id = "api_publica_tjsp"
        participants: list[dict[str, Any]] = []
        source_type = "DATAJUD"

        try:
            lookup = process_lookup(process_id)
            d_data = lookup.get("data", {})
            source_id = d_data.get("tribunal_alias") or "api_publica_tjsp"
            if d_data.get("found"):
                datajud_payload = d_data
                participants = d_data.get("participants", [])
        except Exception as err:
            print(f"Aviso na consulta DataJud: {err}", file=sys.stderr)

        # 2. Se DataJud não retornou partes, extrai da Petição Inicial indexada
        if not participants:
            row_p1 = conn.execute(
                """SELECT p.content FROM pages p
                JOIN documents d USING(document_id)
                WHERE d.process_id=? AND p.page_number=1 LIMIT 1""",
                (process_id,),
            ).fetchone()
            if row_p1 and row_p1["content"]:
                extracted = extract_participants_from_initial_petition(row_p1["content"])
                if extracted:
                    participants = extracted
                    source_type = "AUTOS_PETICAO_INICIAL"

        # 3. Inserção Transacional em legal_entities e party_relations (Canônico)
        import uuid
        from core.documentos.knowledge_objects_v1 import (
            ID_NAMESPACE,
            _fingerprint,
            _json,
            migrate as migrate_knowledge,
        )

        migrate_knowledge(target_db)

        entities_created = 0
        participants_linked = 0
        identifiers_saved = 0

        for part in participants:
            d_name = " ".join(str(part.get("display_name", "")).split())
            if not d_name:
                continue
            e_type = str(part.get("entity_type", "UNKNOWN")).upper()
            if e_type not in {"PERSON", "ORGANIZATION", "UNKNOWN"}:
                e_type = "UNKNOWN"
            norm = normalize_name(d_name)
            identifiers = part.get("identifiers") or {}
            identity_fp = _fingerprint(e_type, _json(identifiers) if identifiers else norm)

            row = conn.execute(
                "SELECT entity_id FROM legal_entities WHERE identity_fingerprint=?",
                (identity_fp,),
            ).fetchone()
            if row:
                e_id = row[0]
                conn.execute(
                    "UPDATE legal_entities SET display_name=?, normalized_name=?, identifiers_json=?, updated_at=? WHERE entity_id=?",
                    (d_name, norm, _json(identifiers), now, e_id),
                )
            else:
                e_id = "entity_" + uuid.uuid5(ID_NAMESPACE, identity_fp).hex
                conn.execute(
                    """INSERT INTO legal_entities(entity_id, entity_type, display_name, normalized_name, identifiers_json, identity_fingerprint, created_at, updated_at)
                    VALUES(?, ?, ?, ?, ?, ?, ?, ?)""",
                    (e_id, e_type, d_name, norm, _json(identifiers), identity_fp, now, now),
                )
                entities_created += 1

            if identifiers:
                identifiers_saved += len(identifiers)

            role_raw = part.get("role") or "PARTE"
            role = str(role_raw).strip() or "PARTE"
            rel_fp = _fingerprint("process", process_id, e_id, role, role_raw)
            rel_id = "party_" + uuid.uuid5(ID_NAMESPACE, rel_fp).hex

            conn.execute(
                """INSERT INTO party_relations(party_relation_id, entity_id, owner_type, owner_id, role, role_raw, status, confidence, relation_fingerprint, extraction_run_id, created_at, updated_at)
                VALUES(?, ?, 'PROCESS', ?, ?, ?, 'CONFIRMED', 'HIGH', ?, NULL, ?, ?)
                ON CONFLICT(relation_fingerprint) DO UPDATE SET status=excluded.status, confidence=excluded.confidence, updated_at=excluded.updated_at""",
                (rel_id, e_id, process_id, role, role_raw, rel_fp, now, now),
            )
            participants_linked += 1

        # 4. Registra proveniência em process_sources
        conn.execute(
            """INSERT OR REPLACE INTO process_sources(process_id, source_type, source_id, created_at)
            VALUES(?, ?, ?, ?)""",
            (process_id, source_type, source_id, now),
        )

        # 5. Se houver movimentações do DataJud ou extrai dos autos
        movements_inserted = 0
        mov_count = conn.execute("SELECT count(*) FROM process_movements WHERE process_id=?", (process_id,)).fetchone()[0]
        if mov_count == 0:
            import hashlib
            raw_movements = datajud_payload.get("movements") or []
            if not raw_movements:
                raw_movements = extract_movements_from_autos(conn, process_id)
            for m in raw_movements:
                m_date = m.get("date") or m.get("occurred_at")
                m_name = m.get("name") or m.get("movement_type") or "Movimentação"
                m_text = m.get("content") or m_name
                m_id = "mov_" + hashlib.sha256(f"{process_id}_{m_date}_{m_name}_{m.get('page', '')}".encode("utf-8")).hexdigest()[:16]
                conn.execute(
                    """INSERT OR IGNORE INTO process_movements(movement_id, process_id, movement_type, occurred_at, content)
                    VALUES(?, ?, ?, ?, ?)""",
                    (m_id, process_id, m_name, m_date, m_text),
                )
                movements_inserted += 1

        conn.commit()
        return {
            "status": "OK",
            "process_id": process_id,
            "source_type": source_type,
            "source_id": source_id,
            "entities_count": entities_created,
            "participants_linked": participants_linked,
            "identifiers_saved": identifiers_saved,
            "movements_inserted": movements_inserted,
            "participants": participants,
        }
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
