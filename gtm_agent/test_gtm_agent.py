import os
from types import SimpleNamespace
from pathlib import Path
import sys

os.environ.setdefault("OPENAI_API_KEY", "test-key")
sys.path = [
    str(Path(__file__).parent.parent),
    *[path for path in sys.path if path not in ("", str(Path(__file__).parent))],
]
from gtm_agent import gtm_agent


def _runtime():
    return SimpleNamespace(config={})


def _prospect():
    return {
        "prospect_id": "LEAD-50001",
        "name": "Priya Nair",
        "email": "priya.nair@brightwaveapps.com",
    }


def test_send_prospect_email_blocks_disqualified_prospect(monkeypatch):
    monkeypatch.setattr(
        gtm_agent.data_service,
        "get_prospect_record",
        lambda prospect_id: {"prospect_id": prospect_id, "disqualified": True},
    )

    result = gtm_agent.send_prospect_email.func(
        _prospect(), "Demo", "Please book a demo.", _runtime(), {"email": "rep@example.com"}
    )

    assert result == {
        "status": "blocked",
        "reason": "prospect is flagged disqualified",
        "prospect_id": "LEAD-50001",
    }
    assert "message_id" not in result


def test_send_prospect_email_override_sends_to_disqualified_prospect(monkeypatch):
    monkeypatch.setattr(
        gtm_agent.data_service,
        "get_prospect_record",
        lambda prospect_id: {"prospect_id": prospect_id, "disqualified": True},
    )

    result = gtm_agent.send_prospect_email.func(
        _prospect(),
        "Demo",
        "Please book a demo.",
        _runtime(),
        {"email": "rep@example.com"},
        override_disqualified=True,
    )

    assert result["status"] == "sent"
    assert result["message_id"].startswith("msg-")
