from core.documentos.deadline_resolution_pipeline_v1 import _date_key


def test_date_key_normalizes_esaj_and_iso_dates_for_antecedent_ordering():
    assert _date_key("30/09/2026 18:18") == "2026-09-30"
    assert _date_key("2026-10-02") == "2026-10-02"
    assert _date_key("30/09/2026 18:18") < _date_key("2026-10-02")
