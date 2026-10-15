"""入口索引安全写入的回归测试：防止文件被写空或误删。"""
from pathlib import Path

import update_portals as up

INDEX = Path(__file__).resolve().parent.parent / "references" / "company-portals.md"


def test_merge_is_idempotent_on_real_index():
    text = INDEX.read_text(encoding="utf-8")
    merged, added, replaced = up.merge(text, {"具身智能与机器人": [["宇树科技", "https://unitree.zhiye.com/campus", "x"]]}, replace=False)
    assert added == 0
    assert replaced == 0
    assert merged == text


def test_replace_swaps_existing_link():
    text = INDEX.read_text(encoding="utf-8")
    merged, added, replaced = up.merge(text, {"具身智能与机器人": [["宇树科技", "https://example.com/new", "新入口"]]}, replace=True)
    assert replaced == 1
    assert "https://example.com/new" in merged
    assert "https://unitree.zhiye.com/campus" not in merged


def test_guard_rejects_heavy_deletion():
    old = INDEX.read_text(encoding="utf-8")
    problems = up.validate(old, "# 官方招聘入口索引\n\n## 覆盖情况\n")
    assert any("拒绝写入" in p for p in problems)


def test_guard_rejects_duplicate_urls():
    text = INDEX.read_text(encoding="utf-8")
    duplicated = text + "\n| 重复公司 | https://join.qq.com/ | 重复 |\n"
    problems = up.validate(text, duplicated)
    assert any("重复 URL" in p for p in problems)


def test_refresh_coverage_recounts():
    text = INDEX.read_text(encoding="utf-8")
    refreshed = up.refresh_coverage(text)
    assert "- 已核验入口：" in refreshed
    assert "- 待人工确认：" in refreshed


def test_validate_accepts_unchanged_index():
    text = INDEX.read_text(encoding="utf-8")
    assert up.validate(text, text) == []