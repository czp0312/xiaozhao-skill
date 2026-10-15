"""HTML 报告渲染器的回归测试。"""
from pathlib import Path

import render_report as rr

TEMPLATE = Path(__file__).resolve().parent.parent / "references" / "report-template.html"


def test_template_has_placeholder_and_page_title():
    text = TEMPLATE.read_text(encoding="utf-8")
    assert rr.PLACEHOLDER in text
    assert "__PAGE_TITLE__" in text


def test_validate_requires_title_and_sections():
    assert "缺少 title" in " ".join(rr.validate({"sections": [{"title": "a"}]}))
    assert "缺少 sections" in " ".join(rr.validate({"title": "t"}))


def test_validate_rejects_unknown_block_type():
    payload = {"title": "t", "sections": [{"title": "s", "blocks": [{"type": "sparkles"}]}]}
    assert any("类型未知" in p for p in rr.validate(payload))


def test_validate_rejects_empty_bars():
    payload = {"title": "t", "sections": [{"title": "s", "blocks": [{"type": "bars"}]}]}
    assert any("缺少 rows" in p for p in rr.validate(payload))


def test_validate_accepts_minimal_payload():
    payload = {"title": "t", "sections": [{"title": "s", "blocks": [{"type": "prose", "html": "hi"}]}]}
    assert rr.validate(payload) == []


def test_render_injects_payload_and_page_title():
    payload = {"pageTitle": "我的报告", "title": "标题", "sections": [{"title": "s"}]}
    html = rr.render(payload, TEMPLATE.read_text(encoding="utf-8"))
    assert "<title>我的报告</title>" in html
    assert rr.PLACEHOLDER not in html
    assert '"title": "标题"' in html


def test_render_escapes_script_close_tag():
    payload = {"title": "t", "sections": [{"title": "s", "blocks": [{"type": "prose", "html": "</script>"}]}]}
    html = rr.render(payload, TEMPLATE.read_text(encoding="utf-8"))
    assert "</script><" not in html
    assert "<\\/script>" in html


def test_render_requires_placeholder():
    import pytest
    with pytest.raises(SystemExit):
        rr.render({"title": "t", "sections": []}, "<html></html>")


def test_scan_internal_flags_skill_run_status():
    payload = {
        "title": "岗位调研",
        "sections": [{"title": "本次调研暴露并已修复的问题",
                      "blocks": [{"type": "fixes", "items": [{"title": "修复前 x"}]}]}],
    }
    hits = rr.scan_internal(payload)
    assert "修复前" in hits


def test_scan_internal_flags_verdict_names_and_scripts():
    payload = {"title": "报告", "sections": [
        {"title": "入口核验", "sub": "68 个入口判定为 SHELL", "blocks": []},
        {"title": "脚本", "sub": "见 scripts/check_portals.py", "blocks": []},
    ]}
    hits = rr.scan_internal(payload)
    assert "SHELL" in hits
    assert "入口核验" in hits
    assert "scripts/" in hits


def test_scan_internal_passes_for_pure_job_report():
    payload = {
        "pageTitle": "具身智能岗位调研",
        "title": "具身智能岗位到底要什么",
        "lede": "基于真实校招 JD。",
        "chips": ["JD 正文样本 <b>7</b> 份"],
        "kpis": [{"value": 5, "suffix": "/7", "label": "JD 提到 VLA / 多模态大模型"}],
        "sections": [
            {"title": "岗位技能要求频次", "sub": "按有多少份 JD 提到计数",
             "blocks": [{"type": "bars", "rows": [{"label": "Python", "value": 4}]}]},
            {"title": "学历与专业门槛", "blocks": [{"type": "table", "rows": [["a", "b"]]}]},
        ],
    }
    assert rr.scan_internal(payload) == []


def test_lowercase_shell_in_jd_text_is_not_flagged():
    # JD 里出现 shell 脚本是正常岗位要求，不应被当成入口判定结论。
    payload = {"title": "岗位调研", "sections": [
        {"title": "技能要求", "sub": "熟悉 shell 脚本与 Linux 环境", "blocks": []}]}
    assert rr.scan_internal(payload) == []
