from copy import deepcopy
import sys
import types
from pathlib import Path

package = types.ModuleType("gtm_agent")
package.__path__ = [str(Path(__file__).parent)]
sys.modules.setdefault("gtm_agent", package)
from gtm_agent import data_service


def _build_profile(prospect_id):
    cached = data_service.get_profile_from_db(prospect_id)["prospect_profile"]
    if cached is not None:
        return cached
    profile = {
        "prospect_id": prospect_id,
        "tech_stack": data_service.fetch_tech_stack(prospect_id),
    }
    data_service.save_profile_to_db(prospect_id, profile)
    return profile


def test_update_prospect_info_persists_technology():
    prospect_id = "LEAD-12853"
    original_record = deepcopy(data_service.PROSPECTS[prospect_id])
    try:
        result = data_service.update_prospect_info(prospect_id, "Okta")

        assert result["updated"] is True
        assert "Okta" in data_service.fetch_tech_stack(prospect_id)
    finally:
        data_service.PROSPECTS[prospect_id] = original_record
        data_service._PROFILES.pop(prospect_id, None)


def test_update_prospect_info_invalidates_cached_profile():
    prospect_id = "LEAD-12853"
    original_record = deepcopy(data_service.PROSPECTS[prospect_id])
    original_profile = data_service._PROFILES.get(prospect_id)
    try:
        initial_profile = _build_profile(prospect_id)
        assert "Okta" not in initial_profile["tech_stack"]

        data_service.update_prospect_info(prospect_id, "Okta")
        rebuilt_profile = _build_profile(prospect_id)

        assert rebuilt_profile is not initial_profile
        assert "Okta" in rebuilt_profile["tech_stack"]
    finally:
        data_service.PROSPECTS[prospect_id] = original_record
        if original_profile is None:
            data_service._PROFILES.pop(prospect_id, None)
        else:
            data_service._PROFILES[prospect_id] = original_profile
