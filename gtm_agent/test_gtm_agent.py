import json
import importlib.util
import os
import sys
import types
from pathlib import Path


os.environ.setdefault("OPENAI_API_KEY", "test-key")
os.environ["LANGSMITH_TRACING"] = "false"
repo_dir = Path(__file__).parent
package = types.ModuleType("gtm_agent")
package.__path__ = [str(repo_dir)]
sys.modules["gtm_agent"] = package
for module_name in ("gtm_records", "data_service", "gtm_agent"):
    module_path = repo_dir / f"{module_name}.py"
    spec = importlib.util.spec_from_file_location(
        f"gtm_agent.{module_name}", module_path
    )
    module = importlib.util.module_from_spec(spec)
    sys.modules[f"gtm_agent.{module_name}"] = module
    spec.loader.exec_module(module)

from gtm_agent.gtm_agent import build_prospect_profile, get_prospect
from gtm_agent import data_service


SENSITIVE_KEYS = (
    "billing_qualification",
    "tax_id",
    "date_of_birth",
    "card_on_file",
    "credit_check_ref",
)


def assert_no_sensitive_fields(value):
    serialized = json.dumps(value)
    for key in SENSITIVE_KEYS:
        assert key not in serialized


def test_get_prospect_excludes_billing_qualification(monkeypatch):
    record = {
        "prospect_id": "LEAD-SYNTHETIC-1",
        "name": "Synthetic Prospect",
        "email": "synthetic@example.com",
        "billing_qualification": {
            "tax_id": "000-00-0000",
            "date_of_birth": "1990-01-01",
            "card_on_file": "4111111111111111",
            "credit_check_ref": "credit-synthetic-1",
        },
    }
    monkeypatch.setattr(data_service, "get_prospect_record", lambda _: record)

    result = get_prospect.invoke({"prospect_id": "LEAD-SYNTHETIC-1"})

    assert_no_sensitive_fields(result)


def test_build_prospect_profile_persists_clean_profile(monkeypatch):
    prospect_id = "LEAD-SYNTHETIC-2"
    record = {
        "prospect_id": prospect_id,
        "name": "Synthetic Prospect",
        "email": "synthetic@example.com",
        "annual_revenue": 1000000,
        "billing_qualification": {
            "tax_id": "000-00-0001",
            "date_of_birth": "1991-02-02",
            "card_on_file": "5555555555554444",
            "credit_check_ref": "credit-synthetic-2",
        },
    }
    monkeypatch.setattr(data_service, "get_prospect_record", lambda _: record)
    monkeypatch.setattr(data_service, "fetch_engagement_history", lambda _: [])
    monkeypatch.setattr(data_service, "fetch_account_details", lambda _: [])
    monkeypatch.setattr(data_service, "fetch_tech_stack", lambda _: [])
    data_service._PROFILES.pop(prospect_id, None)

    result = build_prospect_profile.invoke({"prospect_id": prospect_id})
    stored = data_service.get_profile_from_db(prospect_id)

    assert_no_sensitive_fields(result)
    assert_no_sensitive_fields(stored)
