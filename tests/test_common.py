"""页面内容判定的回归测试：状态码 200 不等于可用。"""
import _common


def test_parked_domain_is_not_ok():
    html = "<title>example.com - example Resources and Information.</title>"
    assert _common.classify(200, "https://example.com/", _common.page_title(html), _common.visible_text(html)) == "PARKED"


def test_chinese_parked_marker_is_detected():
    assert _common.is_parked("域名售卖", "") is True
    assert _common.is_parked("", "该域名可出售") is True


def test_thin_page_is_shell():
    html = '<title>某公司招聘官网</title><div id="app"></div>'
    assert _common.classify(200, "https://x.zhiye.com/campus", _common.page_title(html), _common.visible_text(html)) == "SHELL"


def test_expired_domain_redirecting_to_image_is_not_ok():
    # 域名过期后被托管商接管，200 但落到一张 404 图片，正文其实是二进制垃圾。
    garbage = "\ufffd" * 4000
    assert _common.classify(
        200, "https://ayuda.crea-tuweb.es/404-graphic_es.png", "", garbage, "image/png"
    ) == "NONHTML"


def test_binary_final_url_is_detected_without_content_type():
    assert _common.classify(200, "https://example.com/404.pdf", "", "") == "NONHTML"
    # 没有二进制扩展名时仍走原有逻辑（空页面判为 SHELL），不会误判成 NONHTML。
    assert _common.classify(200, "https://example.com/", "", "") == "SHELL"


def test_html_content_type_is_still_evaluated_normally():
    body = "岗位职责与任职要求 " * 60
    html = f"<title>某公司校园招聘</title><div>{body}</div>"
    assert _common.classify(
        200, "https://example.com/job", _common.page_title(html), _common.visible_text(html), "text/html; charset=utf-8"
    ) == "OK"


def test_content_rich_page_is_ok():
    body = "岗位职责与任职要求 " * 60
    html = f"<title>某公司校园招聘 - 具身智能算法工程师</title><div>{body}</div>"
    assert _common.classify(200, "https://example.com/job", _common.page_title(html), _common.visible_text(html)) == "OK"


def test_status_codes_map_to_expected_verdicts():
    assert _common.classify(403, "https://a.com/", "", "") == "BLOCKED"
    assert _common.classify(468, "https://a.com/", "", "") == "BLOCKED"
    assert _common.classify(404, "https://a.com/", "", "") == "HTTP404"
    assert _common.classify(None, "https://a.com/", "", "") == "NETERR"


def test_visible_text_strips_scripts_and_styles():
    html = "<style>a{b:c}</style><script>var x=1;</script><p>正文</p>"
    assert _common.visible_text(html) == "正文"
