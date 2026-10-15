from pathlib import Path

import check_portals as cp
import _browser


SAMPLE = """
# 官方招聘入口索引

### 互联网与平台

| 公司 | 官方招聘入口 | 说明 |
| --- | --- | --- |
| 腾讯 | https://join.qq.com/ | 官方招聘/校招入口 |

### 待人工确认

| 公司 | 候选入口 | 为什么未确认 |
| --- | --- | --- |
| 微博 | https://careers.weibo.com/ | 本机网络无法连接 |
"""


def test_parse_entries_reads_sections_and_urls(tmp_path):
    path = tmp_path / "portals.md"
    path.write_text(SAMPLE, encoding="utf-8")
    entries = cp.parse_entries(path)
    assert [e["company"] for e in entries] == ["腾讯", "微博"]
    assert entries[0]["url"] == "https://join.qq.com/"
    assert entries[0]["section"] == "互联网与平台"
    assert entries[1]["section"] == "待人工确认"


def test_real_index_has_no_duplicate_urls():
    index = Path(__file__).resolve().parent.parent / "references" / "company-portals.md"
    entries = cp.parse_entries(index)
    assert len(entries) > 100
    urls = [e["url"] for e in entries]
    assert len(urls) == len(set(urls))


def test_index_companies_are_unique():
    index = Path(__file__).resolve().parent.parent / "references" / "company-portals.md"
    entries = cp.parse_entries(index)
    verified = [e["company"] for e in entries if "待人工确认" not in e["section"]]
    assert len(verified) == len(set(verified))

def test_transient_verdicts_are_retried():
    assert cp._is_transient("NETERR") is True
    assert cp._is_transient("HTTP502") is True
    assert cp._is_transient("HTTP503") is True
    assert cp._is_transient("OK") is False
    assert cp._is_transient("PARKED") is False
    assert cp._is_transient("HTTP404") is False


def test_check_retries_transient_failures(monkeypatch):
    calls = []

    def fake_fetch(url, timeout=20.0, max_bytes=2_000_000):
        calls.append(url)
        verdict = "NETERR" if len(calls) == 1 else "OK"
        return {"status": 200, "final_url": url, "title": "t", "text": "x" * 300,
                "verdict": verdict, "error": ""}

    monkeypatch.setattr(cp._common, "fetch", fake_fetch)
    result = cp.check({"section": "s", "company": "c", "url": "https://a.com/", "note": "n"}, 5.0, retries=2)
    assert len(calls) == 2
    assert result["verdict"] == "OK"
    assert result["attempts"] == 2


def test_check_does_not_retry_ok(monkeypatch):
    calls = []

    def fake_fetch(url, timeout=20.0, max_bytes=2_000_000):
        calls.append(url)
        return {"status": 200, "final_url": url, "title": "t", "text": "x" * 300,
                "verdict": "OK", "error": ""}

    monkeypatch.setattr(cp._common, "fetch", fake_fetch)
    cp.check({"section": "s", "company": "c", "url": "https://a.com/", "note": "n"}, 5.0, retries=2)
    assert len(calls) == 1


def _row(company, verdict, section="互联网与平台"):
    return {"section": section, "company": company, "url": f"https://{company}.com/",
            "note": "n", "status": 200, "final_url": f"https://{company}.com/",
            "title": "", "verdict": verdict, "error": "", "host_changed": False, "attempts": 1}


def test_upgrade_shells_promotes_renderable_entries(monkeypatch):
    class _FakeRenderer:
        def __init__(self, *a, **k):
            pass

        def __enter__(self):
            return self

        def __exit__(self, *exc):
            return False

        def render(self, url, wait_ms=None):
            if "bad" in url:
                return {"status": 200, "final_url": url, "title": "", "text": "",
                        "content_type": "text/html", "verdict": "SHELL", "error": "", "rendered": True}
            return {"status": 200, "final_url": url, "title": "渲染标题", "text": "岗位职责 " * 80,
                    "content_type": "text/html", "verdict": "OK", "error": "", "rendered": True}

    monkeypatch.setattr(cp._browser, "Renderer", _FakeRenderer)
    rows = [_row("good", "SHELL"), _row("bad", "SHELL"), _row("static", "OK")]

    upgraded, reason = cp.upgrade_shells(rows, None, 0)

    assert (upgraded, reason) == (1, "")
    assert rows[0]["verdict"] == "OK" and rows[0]["rendered"] is True
    assert rows[1]["verdict"] == "SHELL"
    assert rows[2]["verdict"] == "OK"  # 静态 OK 不受影响


def test_upgrade_shells_skips_pending_section(monkeypatch):
    class _FakeRenderer:
        def __init__(self, *a, **k):
            pass

        def __enter__(self):
            return self

        def __exit__(self, *exc):
            return False

        def render(self, url, wait_ms=None):
            raise AssertionError("待人工确认分区不应被渲染")

    monkeypatch.setattr(cp._browser, "Renderer", _FakeRenderer)
    rows = [_row("pending", "SHELL", section="待人工确认")]

    assert cp.upgrade_shells(rows, None, 0) == (0, "")


def test_upgrade_shells_degrades_without_browser(monkeypatch):
    class _Boom:
        def __init__(self, *a, **k):
            raise _browser.BrowserUnavailable("未安装 playwright")

    monkeypatch.setattr(cp._browser, "Renderer", _Boom)
    rows = [_row("good", "SHELL")]

    upgraded, reason = cp.upgrade_shells(rows, None, 0)

    assert upgraded == 0
    assert "playwright" in reason
    assert rows[0]["verdict"] == "SHELL"
