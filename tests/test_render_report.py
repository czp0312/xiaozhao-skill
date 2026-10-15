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