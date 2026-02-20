"""Tests for specialist crew registry and output validation."""

from utils.specialist_output import (
    ALL_SPECIALIST_LABELS,
    LABEL_TO_CREW,
    SPECIALIST_CREWS,
    autodetect_crews,
    get_all_output_files,
    get_crew_for_label,
    validate_specialist_output,
)


class TestSpecialistRegistry:
    def test_registry_has_ten_crews(self):
        assert len(SPECIALIST_CREWS) == 10

    def test_all_crews_have_required_keys(self):
        required = {
            "label",
            "output_file",
            "agent_key",
            "id_prefix",
            "crew_class",
            "module",
            "description",
        }
        for key, info in SPECIALIST_CREWS.items():
            missing = required - set(info.keys())
            assert not missing, f"Crew '{key}' missing keys: {missing}"

    def test_labels_are_unique(self):
        labels = [v["label"] for v in SPECIALIST_CREWS.values()]
        assert len(labels) == len(set(labels))

    def test_output_files_are_unique(self):
        files = [v["output_file"] for v in SPECIALIST_CREWS.values()]
        assert len(files) == len(set(files))

    def test_id_prefixes_are_unique(self):
        prefixes = [v["id_prefix"] for v in SPECIALIST_CREWS.values()]
        assert len(prefixes) == len(set(prefixes))

    def test_all_labels_start_with_crewai(self):
        for key, info in SPECIALIST_CREWS.items():
            assert info["label"].startswith("crewai:"), (
                f"Crew '{key}' label doesn't start with 'crewai:'"
            )

    def test_all_output_files_end_with_json(self):
        for key, info in SPECIALIST_CREWS.items():
            assert info["output_file"].endswith(".json"), f"Crew '{key}' output not .json"

    def test_label_reverse_lookup(self):
        for key, info in SPECIALIST_CREWS.items():
            assert LABEL_TO_CREW[info["label"]] == key

    def test_all_specialist_labels_list(self):
        assert len(ALL_SPECIALIST_LABELS) == 10
        for label in ALL_SPECIALIST_LABELS:
            assert label.startswith("crewai:")

    def test_get_crew_for_label_found(self):
        assert get_crew_for_label("crewai:security") == "security"
        assert get_crew_for_label("crewai:legal") == "legal"
        assert get_crew_for_label("crewai:strategy") == "strategy"
        assert get_crew_for_label("crewai:data-engineering") == "data_engineering"

    def test_get_crew_for_label_not_found(self):
        assert get_crew_for_label("crewai:nonexistent") is None
        assert get_crew_for_label("") is None

    def test_get_all_output_files(self):
        files = get_all_output_files()
        assert len(files) == 10
        assert "security_review.json" in files
        assert "legal_review.json" in files
        assert "strategic_review.json" in files
        assert "data_engineering_review.json" in files


class TestSpecialistOutputValidation:
    def _valid_output(self, prefix="SEC"):
        return {
            "summary": "No significant security issues found in the changed code.",
            "severity_counts": {"critical": 0, "high": 0, "medium": 1, "low": 0, "info": 0},
            "findings": [
                {
                    "id": f"{prefix}-001",
                    "title": "Hardcoded timeout value",
                    "severity": "medium",
                    "file": "src/api.py",
                    "description": "Timeout is hardcoded to 30s",
                    "recommendation": "Use config value",
                    "verification": "Check config loading",
                }
            ],
        }

    def test_valid_output_passes(self):
        errors = validate_specialist_output(self._valid_output(), "security")
        assert errors == []

    def test_missing_summary(self):
        data = self._valid_output()
        del data["summary"]
        errors = validate_specialist_output(data, "security")
        assert any("summary" in e for e in errors)

    def test_short_summary(self):
        data = self._valid_output()
        data["summary"] = "Short."
        errors = validate_specialist_output(data, "security")
        assert any("20 characters" in e for e in errors)

    def test_missing_severity_counts(self):
        data = self._valid_output()
        del data["severity_counts"]
        errors = validate_specialist_output(data, "security")
        assert any("severity_counts" in e for e in errors)

    def test_missing_severity_level(self):
        data = self._valid_output()
        del data["severity_counts"]["info"]
        errors = validate_specialist_output(data, "security")
        assert any("info" in e for e in errors)

    def test_severity_counts_must_be_int(self):
        data = self._valid_output()
        data["severity_counts"]["critical"] = "none"
        errors = validate_specialist_output(data, "security")
        assert any("integer" in e for e in errors)

    def test_missing_findings(self):
        data = self._valid_output()
        del data["findings"]
        errors = validate_specialist_output(data, "security")
        assert any("findings" in e for e in errors)

    def test_findings_must_be_list(self):
        data = self._valid_output()
        data["findings"] = "not a list"
        errors = validate_specialist_output(data, "security")
        assert any("list" in e for e in errors)

    def test_finding_missing_required_key(self):
        data = self._valid_output()
        del data["findings"][0]["title"]
        errors = validate_specialist_output(data, "security")
        assert any("title" in e for e in errors)

    def test_finding_invalid_severity(self):
        data = self._valid_output()
        data["findings"][0]["severity"] = "urgent"
        errors = validate_specialist_output(data, "security")
        assert any("severity" in e for e in errors)

    def test_finding_wrong_id_prefix(self):
        data = self._valid_output(prefix="WRONG")
        errors = validate_specialist_output(data, "security")
        assert any("SEC-" in e for e in errors)

    def test_legal_prefix(self):
        data = self._valid_output(prefix="LEGAL")
        errors = validate_specialist_output(data, "legal")
        assert errors == []

    def test_empty_findings_valid(self):
        data = {
            "summary": "No issues detected in the changed code for this domain.",
            "severity_counts": {"critical": 0, "high": 0, "medium": 0, "low": 0, "info": 0},
            "findings": [],
        }
        errors = validate_specialist_output(data, "security")
        assert errors == []


class TestAutodetect:
    def test_security_detection(self):
        files = ["src/auth/login.py", "src/utils.py"]
        results = autodetect_crews(files)
        assert "security" in results

    def test_legal_license_file(self):
        files = ["LICENSE", "src/main.py"]
        results = autodetect_crews(files)
        assert "legal" in results

    def test_legal_lockfile(self):
        files = ["pnpm-lock.yaml", "src/app.ts"]
        results = autodetect_crews(files)
        assert "legal" in results

    def test_finance_detection(self):
        files = ["src/billing/invoice.py", "src/api.py"]
        results = autodetect_crews(files)
        assert "finance" in results

    def test_docs_detection(self):
        files = ["README.md", "src/main.py"]
        results = autodetect_crews(files)
        assert "documentation" in results

    def test_agentic_detection(self):
        files = ["AGENTS.md", "src/main.py"]
        results = autodetect_crews(files)
        assert "agentic" in results

    def test_science_detection(self):
        files = ["notebooks/analysis.ipynb", "src/main.py"]
        results = autodetect_crews(files)
        assert "science" in results

    def test_government_ui_trigger(self):
        files = ["src/components/Form.tsx", "src/api.py"]
        results = autodetect_crews(files)
        assert "government" in results

    def test_no_detections_for_plain_python(self):
        files = ["src/utils.py", "src/helpers.py"]
        results = autodetect_crews(files)
        assert "finance" not in results
        assert "science" not in results

    def test_multiple_detections(self):
        files = ["src/auth/login.py", "LICENSE", "README.md"]
        results = autodetect_crews(files)
        assert "security" in results
        assert "legal" in results
        assert "documentation" in results

    def test_data_engineering_detection(self):
        files = ["data/sql/model.sql", "dbt/models/staging.sql"]
        results = autodetect_crews(files)
        assert "data_engineering" in results

    def test_empty_file_list(self):
        results = autodetect_crews([])
        assert results == {}

    def test_case_insensitive(self):
        files = ["src/Auth/Login.py"]
        results = autodetect_crews(files)
        assert "security" in results
