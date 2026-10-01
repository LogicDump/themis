from __future__ import annotations

import sqlite3
from pathlib import Path

from core.migration_manager import migrate_all
from core.process_relations import list_relations, relations_from_cpopg, upsert_relation
from core.process_storage import catalog_discovery, register_discovery

P_ACTIVE = "1111111-11.2025.8.26.0001"
P_PRINCIPAL = "2222222-22.2020.8.26.0001"
P_ROOT = "3333333-33.2017.8.26.0001"
P_SIBLING = "4444444-44.2019.8.26.0001"
P_INCIDENT = "5555555-55.2024.8.26.0001"
P_APPEAL = "6666666-66.2025.8.26.0001"

def test_catalog_process_relations_migration_is_idempotent(tmp_path: Path):
    first = migrate_all(root=tmp_path)
    second = migrate_all(root=tmp_path)
    assert first["catalog"]["changed"] is True
    assert second["catalog"]["changed"] is False
    assert "catalog-process-relations-v1" in second["catalog"]["versions"]
    db = sqlite3.connect(tmp_path / "catalog.db")
    try:
        tables = {r[0] for r in db.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        assert "process_relations" in tables
        assert "process_relation_evidence" in tables
    finally:
        db.close()

def test_cpopg_relations_create_reference_nodes_without_downgrading_known(tmp_path: Path):
    migrate_all(root=tmp_path)
    register_discovery(P_ACTIVE, root=tmp_path, provider="pastadigital_esaj", tribunal="TJSP", discovery_status="KNOWN")
    cpopg = {
        "captured_at": "2026-10-01T12:00:00+00:00",
        "basic_data": {"processo_principal": P_PRINCIPAL},
        "related_processes": [{"tipo": "Apenso", "numero": P_SIBLING}],
        "incidents": [
            {"tipo": "Cumprimento de sentença", "numero": P_INCIDENT, "descricao": "Cumprimento"},
            {"tipo": "Agravo de Instrumento", "numero": P_APPEAL, "descricao": "Recurso"},
        ],
    }
    created = relations_from_cpopg(P_ACTIVE, cpopg, root=tmp_path)
    assert len(created) == 4
    rels = list_relations(P_ACTIVE, root=tmp_path)
    signatures = {(r["from_process_id"], r["to_process_id"], r["relation_kind"]) for r in rels}
    assert (P_ACTIVE, P_PRINCIPAL, "HAS_PRINCIPAL") in signatures
    assert (P_SIBLING, P_ACTIVE, "ATTACHED_TO") in signatures
    assert (P_INCIDENT, P_ACTIVE, "ENFORCEMENT_OF") in signatures
    assert (P_APPEAL, P_ACTIVE, "APPEAL_OF") in signatures
    assert catalog_discovery(P_ACTIVE, root=tmp_path)["discovery_status"] == "KNOWN"
    assert catalog_discovery(P_PRINCIPAL, root=tmp_path)["discovery_status"] == "REFERENCE"

def test_relation_and_evidence_are_idempotent_but_accept_new_evidence(tmp_path: Path):
    migrate_all(root=tmp_path)
    first = upsert_relation(P_ACTIVE, P_PRINCIPAL, "HAS_PRINCIPAL", root=tmp_path, source_type="PROCESS_COVER", source_process_id=P_ACTIVE, source_ref={"field": "processo_principal"}, excerpt=P_PRINCIPAL, observed_at="2026-10-01T12:00:00+00:00")
    second = upsert_relation(P_ACTIVE, P_PRINCIPAL, "HAS_PRINCIPAL", root=tmp_path, source_type="PROCESS_COVER", source_process_id=P_ACTIVE, source_ref={"field": "processo_principal"}, excerpt=P_PRINCIPAL, observed_at="2026-10-02T12:00:00+00:00")
    third = upsert_relation(P_ACTIVE, P_PRINCIPAL, "HAS_PRINCIPAL", root=tmp_path, source_type="LEGACY_DJE", source_process_id=P_ACTIVE, source_ref={"edition_date": "2024-05-01", "page": 123}, excerpt="Referência histórica sintética", observed_at="2026-10-02T12:00:00+00:00")
    assert first["relation_id"] == second["relation_id"] == third["relation_id"]
    db = sqlite3.connect(tmp_path / "catalog.db")
    try:
        assert db.execute("SELECT COUNT(*) FROM process_relations").fetchone()[0] == 1
        assert db.execute("SELECT COUNT(*) FROM process_relation_evidence").fetchone()[0] == 2
    finally:
        db.close()

def test_graph_can_represent_unmaterialized_intermediate_and_multiple_children(tmp_path: Path):
    migrate_all(root=tmp_path)
    upsert_relation(P_ACTIVE, P_PRINCIPAL, "HAS_PRINCIPAL", root=tmp_path, source_type="PROCESS_COVER", source_process_id=P_ACTIVE, source_ref={"field": "processo_principal"})
    upsert_relation(P_PRINCIPAL, P_ROOT, "ATTACHED_TO", root=tmp_path, source_type="PROCESS_COVER", source_process_id=P_PRINCIPAL, source_ref={"section": "apensos"})
    upsert_relation(P_SIBLING, P_ROOT, "ATTACHED_TO", root=tmp_path, source_type="PROCESS_COVER", source_process_id=P_ROOT, source_ref={"section": "apensos"})
    all_rels = list_relations(root=tmp_path)
    assert len(all_rels) == 3
    assert not (tmp_path / "processos" / P_PRINCIPAL / "process.db").exists()
    assert catalog_discovery(P_PRINCIPAL, root=tmp_path)["discovery_status"] == "REFERENCE"

def test_tree_keeps_reference_only_nodes_out_of_materialized_processes(tmp_path: Path, monkeypatch):
    monkeypatch.setenv("THEMIS_DATA_ROOT", str(tmp_path))
    migrate_all(root=tmp_path)
    upsert_relation(
        P_ACTIVE,
        P_PRINCIPAL,
        "HAS_PRINCIPAL",
        root=tmp_path,
        source_type="PROCESS_COVER",
        source_process_id=P_ACTIVE,
        source_ref={"field": "processo_principal"},
    )

    from core.api import core_api
    result = core_api.tree()

    assert result["processes"] == []
    rows = {row["process_id"]: row for row in result["process_structure"]}
    assert rows[P_PRINCIPAL]["depth"] == 0
    assert rows[P_ACTIVE]["depth"] == 1
    assert rows[P_ACTIVE]["parent_process_id"] == P_PRINCIPAL
    assert rows[P_ACTIVE]["materialized"] is False


def test_visual_parent_prefers_explicit_principal_and_preserves_other_edge(tmp_path: Path, monkeypatch):
    monkeypatch.setenv("THEMIS_DATA_ROOT", str(tmp_path))
    migrate_all(root=tmp_path)
    upsert_relation(
        P_ACTIVE,
        P_ROOT,
        "ATTACHED_TO",
        root=tmp_path,
        source_type="PROCESS_COVER",
        source_process_id=P_ACTIVE,
        source_ref={"section": "apensos"},
    )
    upsert_relation(
        P_ACTIVE,
        P_PRINCIPAL,
        "HAS_PRINCIPAL",
        root=tmp_path,
        source_type="PROCESS_COVER",
        source_process_id=P_ACTIVE,
        source_ref={"field": "processo_principal"},
    )

    from core.api import core_api
    rows = {row["process_id"]: row for row in core_api.tree()["process_structure"]}
    active = rows[P_ACTIVE]

    assert active["parent_process_id"] == P_PRINCIPAL
    assert active["relation_kind"] == "HAS_PRINCIPAL"
    assert any(
        item["relation_kind"] == "ATTACHED_TO"
        and item["other_process_id"] == P_ROOT
        for item in active["secondary_relations"]
    )

def test_explicit_attached_to_field_points_current_process_to_parent(tmp_path: Path):
    migrate_all(root=tmp_path)
    cpopg = {
        "captured_at": "2026-10-01T12:00:00+00:00",
        "basic_data": {"apensado_ao": P_ROOT},
        "related_processes": [],
        "incidents": [],
    }
    relations_from_cpopg(P_ACTIVE, cpopg, root=tmp_path)
    signatures = {
        (r["from_process_id"], r["to_process_id"], r["relation_kind"])
        for r in list_relations(P_ACTIVE, root=tmp_path)
    }
    assert (P_ACTIVE, P_ROOT, "ATTACHED_TO") in signatures


def test_related_process_row_labeled_attached_to_preserves_direction(tmp_path: Path):
    migrate_all(root=tmp_path)
    cpopg = {
        "captured_at": "2026-10-01T12:00:00+00:00",
        "basic_data": {},
        "related_processes": [{"tipo": "Apensado ao", "numero": P_ROOT}],
        "incidents": [],
    }
    relations_from_cpopg(P_ACTIVE, cpopg, root=tmp_path)
    signatures = {
        (r["from_process_id"], r["to_process_id"], r["relation_kind"])
        for r in list_relations(P_ACTIVE, root=tmp_path)
    }
    assert (P_ACTIVE, P_ROOT, "ATTACHED_TO") in signatures


def test_visual_tree_projects_principal_under_attached_root(tmp_path: Path, monkeypatch):
    monkeypatch.setenv("THEMIS_DATA_ROOT", str(tmp_path))
    migrate_all(root=tmp_path)
    upsert_relation(P_ACTIVE, P_PRINCIPAL, "HAS_PRINCIPAL", root=tmp_path, source_type="PROCESS_COVER", source_process_id=P_ACTIVE, source_ref={"field": "processo_principal"})
    upsert_relation(P_ACTIVE, P_ROOT, "ATTACHED_TO", root=tmp_path, source_type="PROCESS_COVER", source_process_id=P_ACTIVE, source_ref={"field": "apensado_ao"})

    from core.api import core_api
    rows = {row["process_id"]: row for row in core_api.tree()["process_structure"]}

    assert rows[P_ROOT]["depth"] == 0
    assert rows[P_PRINCIPAL]["parent_process_id"] == P_ROOT
    assert rows[P_PRINCIPAL]["depth"] == 1
    assert rows[P_ACTIVE]["parent_process_id"] == P_PRINCIPAL
    assert rows[P_ACTIVE]["depth"] == 2
