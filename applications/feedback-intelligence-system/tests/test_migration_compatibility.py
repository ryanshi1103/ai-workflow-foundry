"""Public compatibility contracts for the Feedback Intelligence rename."""

from __future__ import annotations

import importlib
from pathlib import Path

from feedback_intelligence.adapters import application_contract


def test_legacy_modules_alias_canonical_module_objects():
    module_names = (
        "config",
        "database",
        "models",
        "schemas",
        "connectors.csv_connector",
        "repositories.feedback_repo",
        "services.analysis_service",
        "services.export_service",
    )

    for module_name in module_names:
        legacy = importlib.import_module(f"src.{module_name}")
        canonical = importlib.import_module(f"feedback_intelligence.{module_name}")
        assert legacy is canonical


def test_flowfoundry_application_contract_is_stable_and_isolated():
    first = application_contract()
    second = application_contract()

    assert first["id"] == "feedback-intelligence-system"
    assert first["entrypoint"] == "app:main"
    assert first["workflow"] == [
        "import",
        "deduplicate",
        "analyze",
        "human_review",
        "export",
    ]
    assert "feedback-analysis-system" in first["aliases"]
    first["aliases"].append("mutated")
    assert "mutated" not in second["aliases"]


def test_legacy_streamlit_component_ids_remain_present():
    project_root = Path(__file__).resolve().parent.parent
    expected_ids = {
        "csv_uploader",
        "btn_csv_import",
        "json_uploader",
        "btn_json_import",
        "dl_csv",
        "dl_json",
        "orig_content",
        "corr_feedback_type",
        "corr_sentiment",
        "corr_category",
        "corr_severity",
        "corr_requires_action",
        "corr_action_priority",
        "corr_action_status",
        "is_misjudged",
        "review_notes",
    }
    page_source = "\n".join(
        path.read_text(encoding="utf-8") for path in (project_root / "pages").glob("*.py")
    )

    missing = {component_id for component_id in expected_ids if f'"{component_id}"' not in page_source}
    assert not missing
    assert 'key=f"content_{item.id}"' in page_source


def test_legacy_database_environment_variable_is_supported(monkeypatch):
    monkeypatch.delenv("FEEDBACK_DB_URL", raising=False)
    monkeypatch.setenv("APP_DB_URL", "sqlite:///legacy/location.db")

    import feedback_intelligence.config as config

    importlib.reload(config)
    assert config.APP_DB_URL == "sqlite:///legacy/location.db"


def test_canonical_database_environment_variable_takes_precedence(monkeypatch):
    monkeypatch.setenv("APP_DB_URL", "sqlite:///legacy/location.db")
    monkeypatch.setenv("FEEDBACK_DB_URL", "sqlite:///canonical/location.db")

    import feedback_intelligence.config as config

    importlib.reload(config)
    assert config.APP_DB_URL == "sqlite:///canonical/location.db"
