#!/usr/bin/env python3
"""抓取岗位 / 招聘页正文，并明确区分“页面打不开”和“读不到正文”。

用法：
    python scripts/fetch_jd.py https://career.nankai.edu.cn/correcruit/content/id/116497.html
    python scripts/fetch_jd.py URL1 URL2 --json
    python scripts/fetch_jd.py URL1 --out ./jd_dump

为什么需要这个脚本：
官方招聘官网（飞书招聘、北森 zhiye.com、Moka）几乎都是前端渲染，
静态请求只能拿到外壳，标题正常但正文为空。直接把这种页面当 JD 会写出错误结论。
本脚本会返回 SHELL 判定并提示改用浏览器或高校就业网等可静态读取的来源。
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

import _common

SHELL_HINT = (
    "该页面为前端渲染（SHELL）：状态码正常、浏览器可打开，但静态请求读不到正文。"
    "请用浏览器打开确认，或改从高校就业网 / 聚合平台取 JD 后再回官方来源核验。"
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
        return SHELL_HINT
    if verdict == "PARKED":
        return PARKED_HINT
    if verdict == "NETERR":
        return NETERR_HINT
    if verdict == "BLOCKED":
        return BLOCKED_HINT
    if verdict.startswith("HTTP"):
        return "返回非 200 状态，入口可能已失效，请重新查找官方招聘站。"
    return ""


def main() -> int:
    _common.configure_utf8_stdio()
    parser = argparse.ArgumentParser(description="抓取岗位 / 招聘页正文")
    parser.add_argument("urls", nargs="+", help="一个或多个页面地址")
    parser.add_argument("--json", action="store_true", help="输出 JSON")
    parser.add_argument("--out", help="把每个页面的正文写到该目录下的 .txt 文件")
    parser.add_argument("--timeout", type=float, default=25.0, help="单个请求超时秒数")
    args = parser.parse_args()

    out_dir = Path(args.out) if args.out else None
    if out_dir:
        out_dir.mkdir(parents=True, exist_ok=True)

    records = []
    for url in args.urls:
        result = _common.fetch(url, timeout=args.timeout)
        record = {
            "url": url,
            "status": result["status"],
            "final_url": result["final_url"],
            "verdict": result["verdict"],
            "title": result["title"],
            "text": tidy(result["text"]),
            "error": result["error"],
            "hint": hint_for(result["verdict"]),
        }
        records.append(record)
        if out_dir and record["text"]:
            (out_dir / f"{slug(url)}.txt").write_text(record["text"], encoding="utf-8")

    if args.json:
        print(json.dumps(records, ensure_ascii=False, indent=2))
        return 0 if all(r["verdict"] == "OK" for r in records) else 1

    for record in records:
        print(f"=== [{record['verdict']}] {record['url']}")
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