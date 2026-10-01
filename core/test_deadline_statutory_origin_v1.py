from __future__ import annotations

import json
import sqlite3

from core.documentos.deadline_obligation_store_v1 import _source_role
from core.documentos.deadline_resolution_pipeline_v1 import _movement_rule_features
from core.documentos.participant_context_store_v1 import _role


def test_execution_cover_roles_map_to_canonical_poles():
    assert _role("Exeqte") == "CLAIMANT"
    assert _role("Exequente") == "CLAIMANT"
    assert _role("Exectdo") == "RESPONDENT"
    assert _role("Executado") == "RESPONDENT"


def test_ato_ordinatorio_is_native_originating_order():
    assert _source_role("Ato Ordinatório", "Ato Ordinatório", "Manifeste-se a parte contrária") == "ORIGINATING_ORDER"


def test_generic_petition_pages_reveal_declaratory_embargos_feature():
    db = sqlite3.connect(":memory:")
    db.row_factory = sqlite3.Row
    db.execute("CREATE TABLE pages(document_id TEXT,page_number INTEGER,content TEXT)")
    db.execute(
        "INSERT INTO pages VALUES('doc1',1,?)",
        ("O executado opõe EMBARGOS DE DECLARAÇÃO com fundamento no art. 1.022 do CPC.",),
    )
    row = {
        "movement_type": "Petição (Outras)",
        "title": "Petição (Outras)",
        "summary_text": None,
        "payload_json": json.dumps({"components": [{"document_id": "doc1"}]}),
    }
    features = _movement_rule_features(db, row)
    assert features["is_declaratory_embargos"] is True
