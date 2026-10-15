#!/usr/bin/env python3
"""抓取岗位 / 招聘页正文；静态读不到时自动用无头浏览器渲染。

用法：
    python scripts/fetch_jd.py https://career.nankai.edu.cn/correcruit/content/id/116497.html
    python scripts/fetch_jd.py URL1 URL2 --json
    python scripts/fetch_jd.py URL1 --out ./jd_dump
    python scripts/fetch_jd.py https://unitree.zhiye.com/campus --render
    python scripts/fetch_jd.py https://unitree.zhiye.com/campus --no-render

为什么需要这个脚本：
官方招聘官网（飞书招聘、北森 zhiye.com、Moka）几乎都是前端渲染，
静态请求只能拿到外壳，标题正常但正文为空。直接把这种页面当 JD 会写出错误结论。

处理顺序：
1. 先做静态请求，能读到正文就直接用（快）；
2. 判定为 SHELL（只有外壳）时，自动用无头浏览器渲染同一地址，从渲染后的 DOM
   取正文，把「读不到」变成「读得到」；
3. 没装 playwright 时降级为提示，不会让脚本失败。

注意：渲染只解决「页面读得到」。渲染后仍要区分岗位列表页与岗位详情页，
列表页的文本不能直接当成某一条 JD 的原文。
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

import _common
import _browser

SHELL_HINT = "该页面为前端渲染（SHELL）：静态请求读不到正文，已尝试用无头浏览器渲染。"
RENDER_FAILED_HINT = (
    "静态与无头浏览器都读不到正文。请确认本机已安装 chromium"
    "（python -m playwright install chromium），或改从高校就业网 / 聚合平台取 JD 后再回官方来源核验。"
)
PARKED_HINT = "该地址命中域名停放 / 出售文案，入口已失效，请重新查找官方招聘站。"
NETERR_HINT = "网络不可达、TLS 失败或超时，需在国内网络环境重试。"
BLOCKED_HINT = "站点反爬或权限拦截，需人工打开确认。"


def tidy(text: str) -> str:
    text = text.replace("\u00a0", " ")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def slug(url: str) -> str:
    name = re.sub(r"^https?://", "", url)
    name = re.sub(r"[^0-9A-Za-z\u4e00-\u9fff]+", "_", name)
    return name.strip("_")[:80] or "page"


def hint_for(verdict: str) -> str:
    if verdict == "SHELL":
        return RENDER_FAILED_HINT
    if verdict == "PARKED":
        return PARKED_HINT
    if verdict == "NETERR":
        return NETERR_HINT
    if verdict == "BLOCKED":
        return BLOCKED_HINT
    if verdict.startswith("HTTP"):
        return "返回非 200 状态，入口可能已失效，请重新查找官方招聘站。"
    return ""


class _LazyRenderer:
    """按需启动浏览器：只有真的遇到 SHELL 才付启动成本。"""

    def __init__(self) -> None:
        self._renderer: _browser.Renderer | None = None
        self.error = ""

    def render(self, url: str, wait_ms: int | None) -> dict | None:
        if self._renderer is None:
            try:
                self._renderer = _browser.Renderer()
                self._renderer.__enter__()
            except _browser.BrowserUnavailable as exc:
                self.error = str(exc)
                self._renderer = None
                return None
        try:
            return self._renderer.render(url, wait_ms=wait_ms)
        except Exception as exc:  # 单页渲染失败不应中断整批
            self.error = f"{type(exc).__name__}: {exc}"
            return None

    def close(self) -> None:
        if self._renderer is not None:
            self._renderer.__exit__(None, None, None)
            self._renderer = None


def collect(url: str, timeout: float, mode: str, renderer: _LazyRenderer,
            wait_ms: int | None) -> dict:
    """先静态抓取，必要时回落到无头浏览器渲染。"""
    static = _common.fetch(url, timeout=timeout)
    result, method, render_error = static, "static", ""

    should_render = mode == "force" or (mode == "auto" and static["verdict"] == "SHELL")
    if should_render:
        rendered = renderer.render(url, wait_ms)
        if rendered is None:
            render_error = renderer.error
        elif len(rendered["text"]) > len(static["text"]):
            result, method = rendered, "render"
        else:
            # 渲染没拿到更多内容，保留静态结果，但记录渲染判定供排查。
            render_error = rendered["error"]

    return {
        "url": url,
        "status": result["status"],
        "final_url": result["final_url"],
        "verdict": result["verdict"],
        "title": result["title"],
        "text": tidy(result["text"]),
        "method": method,
        "error": result["error"] or render_error,
        "hint": hint_for(result["verdict"]) if result["verdict"] != "OK" else "",
    }


def main() -> int:
    _common.configure_utf8_stdio()
    parser = argparse.ArgumentParser(description="抓取岗位 / 招聘页正文")
    parser.add_argument("urls", nargs="+", help="一个或多个页面地址")
    parser.add_argument("--json", action="store_true", help="输出 JSON")
    parser.add_argument("--out", help="把每个页面的正文写到该目录下的 .txt 文件")
    parser.add_argument("--timeout", type=float, default=25.0, help="单个请求超时秒数")
    parser.add_argument("--render", dest="mode", action="store_const", const="force",
                        help="强制用无头浏览器渲染，跳过静态优先")
    parser.add_argument("--no-render", dest="mode", action="store_const", const="off",
                        help="关闭自动渲染，只看静态请求结果")
    parser.add_argument("--wait-ms", type=int, default=None, help="渲染后额外等待毫秒数")
    parser.set_defaults(mode="auto")
    args = parser.parse_args()

    out_dir = Path(args.out) if args.out else None
    if out_dir:
        out_dir.mkdir(parents=True, exist_ok=True)

    renderer = _LazyRenderer()
    records = []
    try:
        for url in args.urls:
            record = collect(url, args.timeout, args.mode, renderer, args.wait_ms)
            records.append(record)
            if out_dir and record["text"]:
                (out_dir / f"{slug(url)}.txt").write_text(record["text"], encoding="utf-8")
    finally:
        renderer.close()

    if args.json:
        print(json.dumps(records, ensure_ascii=False, indent=2))
        return 0 if all(r["verdict"] == "OK" for r in records) else 1

    for record in records:
        print(f"=== [{record['verdict']}] {record['url']}")
        print(f"    取正文方式：{'无头浏览器渲染' if record['method'] == 'render' else '静态请求'}")
        if record["final_url"] != record["url"]:
            print(f"    落地地址：{record['final_url']}")
        if record["title"]:
            print(f"    标题：{record['title']}")
        if record["hint"]:
            print(f"    提示：{record['hint']}")
        if record["error"]:
            print(f"    错误：{record['error']}")
        if record["text"]:
            print("    ---- 正文 ----")
            print("    " + record["text"].replace("\n", "\n    ")[:8000])
        print()

    bad = [r for r in records if r["verdict"] != "OK"]
    if bad:
        print(f"共 {len(records)} 个页面，{len(bad)} 个未能直接读到正文。")
        return 1
    print(f"共 {len(records)} 个页面，全部可直接读取正文。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
