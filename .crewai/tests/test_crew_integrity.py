"""Tests for crew file integrity and YAML cross-references.

Validates that all crew Python files, agent configs, and task configs
are properly wired together without requiring CrewAI runtime.
"""

import re
from pathlib import Path

import yaml

CREWAI_ROOT = Path(__file__).parent.parent
AGENTS_YAML = CREWAI_ROOT / "config" / "agents.yaml"
TASKS_DIR = CREWAI_ROOT / "config" / "tasks"
CREWS_DIR = CREWAI_ROOT / "crews"


def _load_agents():
    with open(AGENTS_YAML) as f:
        return yaml.safe_load(f)


def _load_task_yaml(filename):
    with open(TASKS_DIR / filename) as f:
        return yaml.safe_load(f)


def _read_crew_file(filename):
    with open(CREWS_DIR / filename) as f:
        return f.read()


SPECIALIST_CREW_FILES = [
    ("security_review_crew.py", "security_review_tasks.yaml"),
    ("legal_review_crew.py", "legal_review_tasks.yaml"),
    ("finance_review_crew.py", "finance_review_tasks.yaml"),
    ("data_engineering_review_crew.py", "data_engineering_review_tasks.yaml"),
    ("documentation_review_crew.py", "documentation_review_tasks.yaml"),
    ("agentic_review_crew.py", "agentic_review_tasks.yaml"),
    ("marketing_review_crew.py", "marketing_review_tasks.yaml"),
    ("science_review_crew.py", "science_review_tasks.yaml"),
    ("government_review_crew.py", "government_review_tasks.yaml"),
    ("strategy_review_crew.py", "strategy_review_tasks.yaml"),
]

ALL_CREW_FILES = SPECIALIST_CREW_FILES + [
    ("router_crew.py", "router_tasks.yaml"),
    ("quick_review_crew.py", "quick_review_tasks.yaml"),
    ("full_review_crew.py", "full_review_tasks.yaml"),
    ("ci_log_analysis_crew.py", "ci_log_analysis_tasks.yaml"),
    ("final_summary_crew.py", "final_summary_tasks.yaml"),
]


class TestAgentsYaml:
    def test_agents_yaml_parses(self):
        agents = _load_agents()
        assert isinstance(agents, dict)
        assert len(agents) >= 27

    def test_all_agents_have_role_goal_backstory(self):
        agents = _load_agents()
        for key, config in agents.items():
            assert "role" in config, f"Agent '{key}' missing 'role'"
            assert "goal" in config, f"Agent '{key}' missing 'goal'"
            assert "backstory" in config, f"Agent '{key}' missing 'backstory'"

    def test_specialist_agents_exist(self):
        agents = _load_agents()
        expected = [
            "owasp_sentinel",
            "license_counsel",
            "us_regulatory_analyst",
            "intl_trade_counsel",
            "global_privacy_counsel",
            "revenue_auditor",
            "data_engineering_reviewer",
            "docs_curator",
            "agentic_steward",
            "brand_editor",
            "global_market_strategist",
            "growth_compliance_reviewer",
            "repro_scientist",
            "public_sector_compliance",
            "strategy_consultant",
            "global_expansion_analyst",
            "competitive_intel_analyst",
        ]
        for agent_key in expected:
            assert agent_key in agents, f"Agent '{agent_key}' not in agents.yaml"


class TestTaskYamls:
    def test_all_task_yamls_parse(self):
        for yaml_file in TASKS_DIR.glob("*.yaml"):
            with open(yaml_file) as f:
                data = yaml.safe_load(f)
            assert isinstance(data, dict), f"{yaml_file.name} did not parse to dict"
            assert len(data) > 0, f"{yaml_file.name} is empty"

    def test_all_tasks_have_description_and_expected_output(self):
        for yaml_file in TASKS_DIR.glob("*.yaml"):
            with open(yaml_file) as f:
                data = yaml.safe_load(f)
            for task_key, task_config in data.items():
                assert "description" in task_config, (
                    f"{yaml_file.name}:{task_key} missing 'description'"
                )
                assert "expected_output" in task_config, (
                    f"{yaml_file.name}:{task_key} missing 'expected_output'"
                )

    def test_legal_tasks_are_pipeline(self):
        data = _load_task_yaml("legal_review_tasks.yaml")
        assert len(data) == 4
        expected_keys = [
            "analyze_oss_licenses",
            "analyze_us_regulatory",
            "analyze_intl_trade",
            "synthesize_legal_review",
        ]
        assert list(data.keys()) == expected_keys

    def test_marketing_tasks_are_pipeline(self):
        data = _load_task_yaml("marketing_review_tasks.yaml")
        assert len(data) == 3
        expected_keys = [
            "analyze_brand_copy",
            "analyze_global_market",
            "synthesize_marketing_review",
        ]
        assert list(data.keys()) == expected_keys

    def test_strategy_tasks_are_pipeline(self):
        data = _load_task_yaml("strategy_review_tasks.yaml")
        assert len(data) == 3
        expected_keys = [
            "analyze_strategic_impact",
            "analyze_global_expansion",
            "synthesize_strategic_review",
        ]
        assert list(data.keys()) == expected_keys

    def test_single_agent_crews_have_one_task(self):
        single_agent_yamls = [
            "security_review_tasks.yaml",
            "finance_review_tasks.yaml",
            "documentation_review_tasks.yaml",
            "agentic_review_tasks.yaml",
            "science_review_tasks.yaml",
            "government_review_tasks.yaml",
        ]
        for yaml_name in single_agent_yamls:
            data = _load_task_yaml(yaml_name)
            assert len(data) == 1, f"{yaml_name} should have 1 task, has {len(data)}"


class TestCrewCrossReferences:
    def test_all_crew_files_exist(self):
        for crew_file, _ in ALL_CREW_FILES:
            path = CREWS_DIR / crew_file
            assert path.exists(), f"Crew file missing: {crew_file}"

    def test_all_task_yamls_exist(self):
        for _, task_yaml in ALL_CREW_FILES:
            path = TASKS_DIR / task_yaml
            assert path.exists(), f"Task YAML missing: {task_yaml}"

    def test_crew_agent_refs_exist_in_yaml(self):
        agents = _load_agents()
        for crew_file, _ in ALL_CREW_FILES:
            content = _read_crew_file(crew_file)
            refs = re.findall(r'self\.agents_config\["(\w+)"\]', content)
            for ref in refs:
                assert ref in agents, f"{crew_file} references agent '{ref}' not in agents.yaml"

    def test_crew_task_refs_exist_in_yaml(self):
        for crew_file, task_yaml in ALL_CREW_FILES:
            content = _read_crew_file(crew_file)
            task_data = _load_task_yaml(task_yaml)
            refs = re.findall(r'self\.tasks_config\["(\w+)"\]', content)
            for ref in refs:
                assert ref in task_data, (
                    f"{crew_file} references task '{ref}' not in {task_yaml} "
                    f"(available: {list(task_data.keys())})"
                )

    def test_crew_files_reference_correct_task_yaml(self):
        for crew_file, task_yaml in ALL_CREW_FILES:
            content = _read_crew_file(crew_file)
            expected_path = f"../config/tasks/{task_yaml}"
            assert expected_path in content, f"{crew_file} doesn't reference {expected_path}"

    def test_crew_files_reference_agents_yaml(self):
        for crew_file, _ in ALL_CREW_FILES:
            content = _read_crew_file(crew_file)
            assert "../config/agents.yaml" in content, f"{crew_file} doesn't reference agents.yaml"


class TestCrewPythonStructure:
    def test_all_crew_files_compile(self):
        import py_compile

        for crew_file, _ in ALL_CREW_FILES:
            path = CREWS_DIR / crew_file
            py_compile.compile(str(path), doraise=True)

    def test_all_crew_files_have_crew_method(self):
        for crew_file, _ in ALL_CREW_FILES:
            content = _read_crew_file(crew_file)
            assert "def crew(self)" in content, f"{crew_file} missing crew() method"
            assert "@crew" in content, f"{crew_file} missing @crew decorator"

    def test_all_crew_files_have_crewbase_decorator(self):
        for crew_file, _ in ALL_CREW_FILES:
            content = _read_crew_file(crew_file)
            assert "@CrewBase" in content, f"{crew_file} missing @CrewBase decorator"

    def test_all_crew_files_use_workspace_tool(self):
        for crew_file, _ in ALL_CREW_FILES:
            content = _read_crew_file(crew_file)
            assert "WorkspaceTool" in content, f"{crew_file} doesn't use WorkspaceTool"

    def test_specialist_crews_use_selective_repo_tools(self):
        for crew_file, _ in SPECIALIST_CREW_FILES:
            content = _read_crew_file(crew_file)
            assert "FileContentTool" in content, f"{crew_file} doesn't use FileContentTool"
            assert "RelatedFilesTool" in content, f"{crew_file} doesn't use RelatedFilesTool"
            assert "CommitInfoTool" in content, f"{crew_file} doesn't use CommitInfoTool"

    def test_all_crew_files_use_get_llm(self):
        for crew_file, _ in ALL_CREW_FILES:
            content = _read_crew_file(crew_file)
            assert "get_llm()" in content, f"{crew_file} doesn't use get_llm()"

    def test_all_crew_files_use_rate_limiter(self):
        for crew_file, _ in ALL_CREW_FILES:
            content = _read_crew_file(crew_file)
            assert "get_rate_limiter()" in content, f"{crew_file} doesn't use get_rate_limiter()"

    def test_multi_agent_crews_have_correct_agent_count(self):
        legal = _read_crew_file("legal_review_crew.py")
        legal_agents = re.findall(r"@agent\n\s+def (\w+)", legal)
        assert len(legal_agents) == 4, f"Legal crew should have 4 agents, has {len(legal_agents)}"

        marketing = _read_crew_file("marketing_review_crew.py")
        mkt_agents = re.findall(r"@agent\n\s+def (\w+)", marketing)
        assert len(mkt_agents) == 3, f"Marketing crew should have 3 agents, has {len(mkt_agents)}"

        strategy = _read_crew_file("strategy_review_crew.py")
        strat_agents = re.findall(r"@agent\n\s+def (\w+)", strategy)
        assert len(strat_agents) == 3, (
            f"Strategy crew should have 3 agents, has {len(strat_agents)}"
        )

    def test_multi_agent_crews_have_matching_task_count(self):
        for crew_file in [
            "legal_review_crew.py",
            "marketing_review_crew.py",
            "strategy_review_crew.py",
        ]:
            content = _read_crew_file(crew_file)
            agents = re.findall(r"@agent\n\s+def (\w+)", content)
            tasks = re.findall(r"@task\n\s+def (\w+)", content)
            assert len(agents) == len(tasks), (
                f"{crew_file}: {len(agents)} agents but {len(tasks)} tasks"
            )


class TestOutputSchemaInTasks:
    def test_specialist_tasks_reference_output_files(self):
        from utils.specialist_output import SPECIALIST_CREWS

        final_output_files = {v["output_file"] for v in SPECIALIST_CREWS.values()}

        for _, task_yaml in SPECIALIST_CREW_FILES:
            data = _load_task_yaml(task_yaml)
            content = yaml.dump(data)
            found = False
            for output_file in final_output_files:
                if output_file in content:
                    found = True
                    break
            assert found, f"{task_yaml} doesn't reference any specialist output file"

    def test_final_summary_reads_all_specialist_outputs(self):
        from utils.specialist_output import SPECIALIST_CREWS

        data = _load_task_yaml("final_summary_tasks.yaml")
        content = yaml.dump(data)
        for crew_key, info in SPECIALIST_CREWS.items():
            assert info["output_file"] in content, (
                f"final_summary_tasks.yaml doesn't read {info['output_file']} ({crew_key})"
            )

    def test_router_tasks_reference_all_labels(self):
        from utils.specialist_output import SPECIALIST_CREWS

        data = _load_task_yaml("router_tasks.yaml")
        content = yaml.dump(data)
        for crew_key, info in SPECIALIST_CREWS.items():
            assert info["label"] in content, (
                f"router_tasks.yaml doesn't reference label {info['label']} ({crew_key})"
            )
