"""fetch_jd 的提示文案测试：读不到正文时必须给出可执行建议。"""
import fetch_jd


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