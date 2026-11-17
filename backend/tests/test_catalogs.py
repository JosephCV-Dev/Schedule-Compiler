from dataclasses import replace
import hashlib
import json

import pytest

from schedule_compiler.application.catalogs import overlay_offers
from schedule_compiler.domain.models import FieldValue, ValueState
from schedule_compiler.domain.rooms import room_identity
from schedule_compiler.infrastructure.catalogs import DataRepository


def test_loads_real_catalog_without_inventing_metadata(working):
    assert len(working.offers) == 66
    assert sum(len(o.sessions) for o in working.offers) == 131
    assert all(o.teacher.state == ValueState.UNKNOWN for o in working.offers)
    assert all(r.capacity is None and r.type is None for r in working.rooms)
    assert all(g.students is None for g in working.groups)


def test_working_changes_only_two_rooms_and_preserves_provenance(repository, working):
    original = repository.load_catalog("isc-26-1-original")
    before = {s.id: s for o in original.offers for s in o.sessions}
    pending = [s for o in working.offers for s in o.sessions if s.room.state == ValueState.UNASSIGNED]
    assert len(pending) == len(working.adjustments) == 2
    assert {s.day.value for s in pending} == {"VIERNES"}
    for session in pending:
        assert session.interval.start_minute == 780 and session.interval.end_minute == 900
        assert before[session.id].room.value == "FIE1-AUL28"
        assert session.origins[0].kind == "EXCEL"
        assert session.origins[1].kind == "JSON"
    assert working.source == original.source
    assert working.snapshot_sha256 != original.snapshot_sha256
    assert working.source_audit_scope == "FUENTE_ORIGINAL"


def test_loading_does_not_modify_source_files(repository):
    paths = sorted(repository.data_dir.glob("*.json"))
    before = {p: hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}
    repository.load_catalog()
    repository.load_policy()
    assert before == {p: hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}


@pytest.mark.parametrize("a,b", [
    ("FIE2AUL032", "FIE2-AUL32"),
    ("FIE1-AUL025", "FIE1-AUL25"),
    ("FIE1AC0001", "FIE1-AC0001"),
    (" Aula nueva ", "AULA NUEVA"),
])
def test_room_keys_reconcile_only_documented_format_variants(a, b):
    assert room_identity(a).key == room_identity(b).key
    assert room_identity(a).original == a


def test_room_identity_does_not_invent_physical_equivalences():
    assert room_identity("CENTRO DE CÓMPUTO").key != room_identity("FIE1AC0001").key
    assert room_identity("FIE1AC001").key != room_identity("FIE1AC0001").key


def test_proposal_replaces_same_id_without_mutating_original(working):
    previous = working.offers[0]
    proposed = replace(previous, teacher=FieldValue(ValueState.KNOWN, "Cualquier profesor"))
    overlay = overlay_offers(working, (proposed,))
    assert len(overlay.offers) == len(working.offers)
    assert next(o for o in overlay.offers if o.id == previous.id) is proposed
    assert working.offers[0] is previous
    with pytest.raises(ValueError, match="DECLARACION_DUPLICADA"):
        overlay_offers(working, (proposed, proposed))


def test_policy_preserves_user_choices(repository):
    policy = repository.load_policy()
    assert not policy.teacher_rules_enabled and policy.allow_new_rooms
    assert policy.check_room_occupancy and not policy.auto_assign_rooms
    assert policy.unassigned_room_status == "PENDIENTE"


def test_invalid_policy_does_not_silently_enable_teacher_rules(repository, tmp_path):
    policy = json.loads((repository.data_dir / "politica_proyecto.json").read_text())
    policy["docente"]["validar_cruces"] = True
    (tmp_path / "politica_proyecto.json").write_text(json.dumps(policy))
    with pytest.raises(ValueError, match="desactivadas"):
        DataRepository(tmp_path).load_policy()


def test_resource_ids_are_not_file_paths(repository):
    with pytest.raises(ValueError, match="Recurso no reconocido"):
        repository.load_catalog("../../README.md")
