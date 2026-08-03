from types import SimpleNamespace
from unittest.mock import Mock

from app.application.knowledge.service import KnowledgeService


def _fact(**overrides):
    values = {
        "id": 1,
        "value": "true",
        "confidence": 0.8,
        "source": "worker",
        "source_detail": None,
        "value_type": "string",
        "status": "active",
        "manual_override": False,
        "updated_by": None,
        "updated_at": None,
    }
    values.update(overrides)
    return SimpleNamespace(**values)


def test_set_fact_noop_does_not_emit_update_event():
    existing = _fact()
    db = Mock()
    db.scalar.return_value = existing
    service = KnowledgeService(db)
    service.record_event = Mock()

    result = service.set_fact(
        "company", 7, "buying_signal", "true",
        source="worker", confidence=0.8,
    )

    assert result is existing
    db.flush.assert_not_called()
    service.record_event.assert_not_called()


def test_set_fact_material_change_emits_one_update_event():
    existing = _fact(value="false")
    db = Mock()
    db.scalar.return_value = existing
    service = KnowledgeService(db)
    service.record_event = Mock()

    service.set_fact(
        "company", 7, "buying_signal", "true",
        source="worker", confidence=0.8,
    )

    assert existing.value == "true"
    db.flush.assert_called_once()
    service.record_event.assert_called_once()
