from core.documentos.procedural_acts_v1 import _group_piece_records


IDENTITY_A = ("ATOR A", "01/01/2026 10:00", "WPRC0001")
IDENTITY_B = ("ATOR B", "01/01/2026 11:00", "WPRC0002")


def piece(order, identity):
    actor = occurred_at = protocol = None
    if identity is not None:
        actor, occurred_at, protocol = identity
    return {
        "order": order,
        "identity": identity,
        "actor": actor,
        "occurred_at": occurred_at,
        "protocol": protocol,
        "provenance": {"source_kind": "synthetic"},
    }


def test_bounded_same_identity_gap_is_absorbed_into_one_movement():
    records = [
        piece(1, IDENTITY_A),
        piece(2, None),
        piece(3, None),
        piece(4, IDENTITY_A),
    ]
    groups = _group_piece_records(records)

    assert [[p["order"] for p in group] for group in groups] == [[1, 2, 3, 4]]
    for recovered in records[1:3]:
        assert recovered["identity"] == IDENTITY_A
        assert recovered["provenance"]["identity_recovery"]["method"] == "BOUNDED_SAME_IDENTITY_GAP"


def test_unattested_piece_between_different_identities_is_not_a_movement():
    records = [
        piece(1, IDENTITY_A),
        piece(2, None),
        piece(3, IDENTITY_B),
    ]
    groups = _group_piece_records(records)

    assert [[p["order"] for p in group] for group in groups] == [[1], [3]]
    assert records[1]["identity"] is None


def test_unbounded_unattested_pieces_are_not_promoted_to_movements():
    records = [
        piece(1, None),
        piece(2, IDENTITY_A),
        piece(3, None),
    ]
    groups = _group_piece_records(records)

    assert [[p["order"] for p in group] for group in groups] == [[2]]
