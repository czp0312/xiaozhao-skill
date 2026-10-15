"""防止文档漂移：references/ 与 scripts/ 下的文件必须出现在 SKILL.md 的模块索引里。"""
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SKILL = (ROOT / "SKILL.md").read_text(encoding="utf-8")


def test_every_reference_is_listed_in_skill_md():
    missing = [
        path.name
        for path in sorted((ROOT / "references").iterdir())
        if path.is_file() and path.name not in SKILL
    ]
    assert missing == []


def test_every_script_is_listed_in_skill_md():
    missing = [
        path.name
        for path in sorted((ROOT / "scripts").iterdir())
        if path.suffix == ".py" and path.name not in SKILL
    ]
    assert missing == []


def test_role_profiles_covers_core_families():
    text = (ROOT / "references" / "role-profiles.md").read_text(encoding="utf-8")
    for family in (
        "embodied_ai",
        "motion_control",
        "computer_vision",
        "embedded_software",
        "embedded_hardware",
        "llm_app",
        "agent_development",
        "ic_design",
    ):
        assert f"### {family}" in text