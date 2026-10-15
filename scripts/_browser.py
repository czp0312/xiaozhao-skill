#!/usr/bin/env python3
"""用无头浏览器渲染前端渲染的招聘页，把「读不到正文」变成「读得到正文」。

为什么需要这个模块：

飞书招聘、北森 zhiye.com、Moka 这些 ATS 都是前端渲染。静态请求只能拿到
一个空外壳（SHELL），所以早期只能把这类页面标成「读不到正文」。
实际上它们的岗位数据就在浏览器渲染出来的 DOM 里，用无头浏览器打开即可读到。

设计取舍：

1. 不逆向各家的私有接口。Moka 的列表接口返回的是加密串
   （`{"data":"...","necromancer":"..."}`），跟着它做解密会随前端发版随时失效；
   渲染 DOM 对所有 ATS 一视同仁，维护成本最低。
2. Playwright 是可选依赖。没装时抛 BrowserUnavailable，调用方降级为静态抓取，
   不会让整个 skill 挂掉。
3. 单个 Renderer 复用同一个浏览器实例，批量渲染时不要每个 URL 都冷启动。
"""

from __future__ import annotations

import re
import sys

import _common

DEFAULT_TIMEOUT_MS = 45_000
DEFAULT_WAIT_MS = 2_500
VIEWPORT = {"width": 1400, "height": 1000}


class BrowserUnavailable(RuntimeError):
    """没有可用的 playwright / chromium，调用方应降级为静态抓取。"""


def available() -> bool:
    """检查 playwright 与 chromium 是否可用，不抛异常。"""
    try:
        from playwright.sync_api import sync_playwright  # noqa: F401
    except Exception:
        return False
    return True


def _require_playwright():
    try:
        from playwright.sync_api import sync_playwright
    except Exception as exc:  # pragma: no cover - 取决于本机是否安装
        raise BrowserUnavailable(
            "未安装 playwright，无法渲染前端页面。安装方式："
            "pip install playwright && python -m playwright install chromium"
        ) from exc
    return sync_playwright


def _tidy(text: str) -> str:
    text = text.replace("\u00a0", " ")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


class Renderer:
    """复用一个 chromium 实例，逐个渲染页面。建议用 with 语句。"""

    def __init__(self, timeout_ms: int = DEFAULT_TIMEOUT_MS, wait_ms: int = DEFAULT_WAIT_MS):
        self.timeout_ms = timeout_ms
        self.wait_ms = wait_ms
        self._pw = None
        self._browser = None
        self._context = None

    def __enter__(self) -> "Renderer":
        sync_playwright = _require_playwright()
        self._pw = sync_playwright().start()
        try:
            self._browser = self._pw.chromium.launch()
        except Exception as exc:  # pragma: no cover - 取决于本机浏览器
            self._pw.stop()
            self._pw = None
            raise BrowserUnavailable(
                "chromium 未安装或无法启动。安装方式：python -m playwright install chromium"
            ) from exc
        self._context = self._browser.new_context(
            viewport=VIEWPORT, locale="zh-CN", user_agent=_common.USER_AGENT
        )
        return self

    def __exit__(self, *exc_info) -> None:
        for closer in (self._context, self._browser):
            try:
                if closer is not None:
                    closer.close()
            except Exception:
                pass
        try:
            if self._pw is not None:
                self._pw.stop()
        except Exception:
            pass
        self._context = self._browser = self._pw = None

    def render(self, url: str, wait_ms: int | None = None) -> dict:
        """渲染一个页面，返回与 _common.fetch 同构的结果。"""
        if self._context is None:
            raise BrowserUnavailable("Renderer 必须在 with 语句中使用")
        page = self._context.new_page()
        error = ""
        status: int | None = None
        final_url = url
        title = ""
        text = ""
        try:
            response = page.goto(url, wait_until="domcontentloaded", timeout=self.timeout_ms)
            if response is not None:
                status = response.status
                final_url = response.url
            # 前端渲染要等接口回填，固定等一小段时间再取 DOM。
            try:
                page.wait_for_load_state("networkidle", timeout=min(self.timeout_ms, 15_000))
            except Exception:
                pass
            page.wait_for_timeout(wait_ms if wait_ms is not None else self.wait_ms)
            title = page.title() or ""
            try:
                text = page.inner_text("body")
            except Exception:
                text = _common.visible_text(page.content())
        except Exception as exc:
            error = f"{type(exc).__name__}: {exc}"
        finally:
            try:
                page.close()
            except Exception:
                pass

        text = _tidy(text)
        if status is None and not error:
            status = 200
        verdict = "NETERR" if status is None else _common.classify(status, final_url, title, text)
        return {
            "status": status,
            "final_url": final_url,
            "title": title,
            "text": text,
            "content_type": "text/html (rendered)",
            "verdict": verdict,
            "error": error,
            "rendered": True,
        }


def render(url: str, timeout_ms: int = DEFAULT_TIMEOUT_MS, wait_ms: int = DEFAULT_WAIT_MS) -> dict:
    """渲染单个页面（一次性启动浏览器，适合单页调用）。"""
    with Renderer(timeout_ms=timeout_ms, wait_ms=wait_ms) as renderer:
        return renderer.render(url)
