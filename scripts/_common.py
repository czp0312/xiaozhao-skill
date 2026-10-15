#!/usr/bin/env python3
"""脚本共用工具：UTF-8 输出、HTTP 抓取与页面内容判定。

本模块把本次调研中踩到的几个坑固化下来：

1. Windows 控制台默认不是 UTF-8，直接 print 中文会乱码或被截断；
2. 招聘官网大量使用前端渲染，静态请求只能拿到外壳，状态码 200 不代表能读到岗位内容；
3. 部分失效域名会跳转到域名停放页，状态码同样是 200；
4. 部分站点必须带 Cookie 才能完成 302 跳转。
"""

from __future__ import annotations

import http.cookiejar
import re
import ssl
import sys
import urllib.error
import urllib.request

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"
)

# 域名停放 / 出售页的典型文案。命中即判定入口无效，哪怕状态码是 200。
PARKED_MARKERS = (
    "域名售卖",
    "域名出售",
    "域名停放",
    "域名交易",
    "该域名可出售",
    "此域名出售",
    "domain for sale",
    "this domain is for sale",
    "buy this domain",
    "domain is parked",
    "domain parking",
    "parked domain",
    "sedoparking",
    "resources and information",
    "godaddy.com/domainsearch",
)

# 这些 ATS 域名由前端渲染，静态请求拿不到岗位正文，只能拿到外壳。
JS_SHELL_HOSTS = (
    "jobs.feishu.cn",
    "zhiye.com",
    "mokahr.com",
    "moka.com",
    "beisen.com",
    "hotjob.cn",
    "nowcoder.com",
    "liepin.com",
    "zhipin.com",
)

# 可见文本少于该长度时，判定为“只有外壳，没有正文”。
THIN_TEXT_LIMIT = 200

VERDICT_ORDER = ("PARKED", "NETERR", "BLOCKED", "HTTP", "SHELL", "OK")


def configure_utf8_stdio() -> None:
    """把 stdout / stderr 固定为 UTF-8，避免 Windows 控制台默认编码乱码。"""
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            try:
                stream.reconfigure(encoding="utf-8")
            except (ValueError, OSError):
                pass


def build_opener() -> urllib.request.OpenerDirector:
    """构造带 Cookie 容器、忽略证书校验的 opener。

    招聘站经常先下发 Cookie 再 302，没有 Cookie 容器会停在跳转页。
    """
    context = ssl.create_default_context()
    context.check_hostname = False
    context.verify_mode = ssl.CERT_NONE
    opener = urllib.request.build_opener(
        urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar()),
        urllib.request.HTTPSHandler(context=context),
    )
    opener.addheaders = [
        ("User-Agent", USER_AGENT),
        ("Accept", "text/html,application/xhtml+xml,*/*;q=0.8"),
        ("Accept-Language", "zh-CN,zh;q=0.9,en;q=0.8"),
    ]
    return opener


def page_title(html: str) -> str:
    match = re.search(r"<title[^>]*>(.*?)</title>", html, re.S | re.I)
    return re.sub(r"\s+", " ", match.group(1)).strip() if match else ""


def visible_text(html: str) -> str:
    """去掉 script / style / 注释和标签，得到近似可见文本。"""
    text = re.sub(r"<!--.*?-->", " ", html, flags=re.S)
    text = re.sub(r"<script.*?</script>", " ", text, flags=re.S | re.I)
    text = re.sub(r"<style.*?</style>", " ", text, flags=re.S | re.I)
    text = re.sub(r"<noscript.*?</noscript>", " ", text, flags=re.S | re.I)
    text = re.sub(r"<[^>]+>", " ", text)
    text = text.replace("&nbsp;", " ").replace("&amp;", "&")
    return re.sub(r"\s+", " ", text).strip()


def is_parked(title: str, text: str) -> bool:
    blob = f"{title} {text}".lower()
    return any(marker.lower() in blob for marker in PARKED_MARKERS)


def classify(status: int | None, final_url: str, title: str, text: str) -> str:
    """把一次请求归类为 OK / SHELL / PARKED / BLOCKED / HTTPxxx / NETERR。"""
    if status is None:
        return "NETERR"
    if status in (401, 403, 405, 429, 468):
        return "BLOCKED"
    if status != 200:
        return f"HTTP{status}"
    if is_parked(title, text):
        return "PARKED"
    host = final_url.split("//")[-1].split("/")[0].lower()
    thin = len(text) < THIN_TEXT_LIMIT
    if thin and (any(h in host for h in JS_SHELL_HOSTS) or len(title) < 40):
        return "SHELL"
    return "OK"


def fetch(url: str, timeout: float = 20.0, max_bytes: int = 2_000_000) -> dict:
    """抓取一个 URL，返回状态码、落地地址、标题、可见文本和判定结果。"""
    opener = build_opener()
    try:
        with opener.open(urllib.request.Request(url), timeout=timeout) as response:
            raw = response.read(max_bytes)
            charset = response.headers.get_content_charset() or "utf-8"
            try:
                html = raw.decode(charset, "ignore")
            except LookupError:
                html = raw.decode("utf-8", "ignore")
            title = page_title(html)
            text = visible_text(html)
            return {
                "status": response.status,
                "final_url": response.geturl(),
                "title": title,
                "text": text,
                "verdict": classify(response.status, response.geturl(), title, text),
                "error": "",
            }
    except urllib.error.HTTPError as exc:
        final = getattr(exc, "url", url)
        return {
            "status": exc.code,
            "final_url": final,
            "title": "",
            "text": "",
            "verdict": classify(exc.code, final, "", ""),
            "error": "",
        }
    except Exception as exc:  # 网络不可达、TLS 失败、超时等
        return {
            "status": None,
            "final_url": url,
            "title": "",
            "text": "",
            "verdict": "NETERR",
            "error": f"{type(exc).__name__}: {exc}",
        }