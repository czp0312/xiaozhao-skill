"""fetch_jd 的提示文案测试：读不到正文时必须给出可执行建议。"""
import fetch_jd
import _browser


def test_shell_hint_mentions_browser_and_official_source():
    hint = fetch_jd.hint_for("SHELL")
    assert "浏览器" in hint
    assert "核验" in hint


def test_parked_hint_marks_entry_invalid():
    assert "失效" in fetch_jd.hint_for("PARKED")


def test_ok_has_no_hint():
    assert fetch_jd.hint_for("OK") == ""


def test_tidy_collapses_blank_lines():
    assert fetch_jd.tidy("a\n\n\n\nb") == "a\n\nb"


def test_slug_is_filesystem_safe():
    assert "/" not in fetch_jd.slug("https://a.com/x/y?z=1")
    assert fetch_jd.slug("https://a.com/") != ""


def _static(verdict, text, url="https://a.com/"):
    return {
        "status": 200, "final_url": url, "title": "静态标题", "text": text,
        "content_type": "text/html", "verdict": verdict, "error": "",
    }


class _FakeRenderer:
    """模拟 _browser.Renderer，返回预设的渲染结果。"""

    def __init__(self, rendered):
        self.error = ""
        self._rendered = rendered
        self.calls = 0

    def render(self, url, wait_ms=None):
        self.calls += 1
        return self._rendered


def test_collect_renders_when_static_reads_only_shell(monkeypatch):
    monkeypatch.setattr(fetch_jd._common, "fetch", lambda url, timeout=25.0: _static("SHELL", ""))
    rendered = {"status": 200, "final_url": "https://a.com/", "title": "渲染标题",
                "text": "岗位职责与任职要求 " * 40, "content_type": "text/html (rendered)",
                "verdict": "OK", "error": "", "rendered": True}
    renderer = _FakeRenderer(rendered)

    record = fetch_jd.collect("https://a.com/", 5.0, "auto", renderer, None)

    assert renderer.calls == 1
    assert record["method"] == "render"
    assert record["verdict"] == "OK"
    assert "岗位职责" in record["text"]


def test_collect_keeps_static_when_render_adds_nothing(monkeypatch):
    monkeypatch.setattr(fetch_jd._common, "fetch", lambda url, timeout=25.0: _static("OK", "静态正文 " * 60))
    renderer = _FakeRenderer({"status": 200, "final_url": "https://a.com/", "title": "",
                              "text": "短", "content_type": "text/html", "verdict": "SHELL",
                              "error": "", "rendered": True})

    record = fetch_jd.collect("https://a.com/", 5.0, "auto", renderer, None)

    assert renderer.calls == 0  # OK 页面不触发渲染
    assert record["method"] == "static"
    assert record["verdict"] == "OK"


def test_no_render_mode_never_opens_browser(monkeypatch):
    monkeypatch.setattr(fetch_jd._common, "fetch", lambda url, timeout=25.0: _static("SHELL", ""))
    renderer = _FakeRenderer({"status": 200, "final_url": "https://a.com/", "title": "",
                              "text": "x" * 500, "content_type": "text/html", "verdict": "OK",
                              "error": "", "rendered": True})

    record = fetch_jd.collect("https://a.com/", 5.0, "off", renderer, None)

    assert renderer.calls == 0
    assert record["method"] == "static"
    assert record["verdict"] == "SHELL"


def test_force_mode_renders_even_when_static_is_ok(monkeypatch):
    monkeypatch.setattr(fetch_jd._common, "fetch", lambda url, timeout=25.0: _static("OK", "静态正文 " * 60))
    renderer = _FakeRenderer({"status": 200, "final_url": "https://a.com/", "title": "",
                              "text": "渲染正文 " * 200, "content_type": "text/html",
                              "verdict": "OK", "error": "", "rendered": True})

    record = fetch_jd.collect("https://a.com/", 5.0, "force", renderer, None)

    assert renderer.calls == 1
    assert record["method"] == "render"


def test_lazy_renderer_degrades_when_browser_missing(monkeypatch):
    class _Boom:
        def __init__(self, *a, **k):
            raise _browser.BrowserUnavailable("未安装 playwright")

    monkeypatch.setattr(fetch_jd._browser, "Renderer", _Boom)
    renderer = fetch_jd._LazyRenderer()

    assert renderer.render("https://a.com/", None) is None
    assert "playwright" in renderer.error
    renderer.close()  # 不应抛异常
