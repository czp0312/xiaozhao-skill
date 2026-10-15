#!/usr/bin/env python3
"""复核 references/company-portals.md 中的官方招聘入口是否仍然可用。

用法：
    python scripts/check_portals.py
    python scripts/check_portals.py --json
    python scripts/check_portals.py --strict
    python scripts/check_portals.py --update-date

判定标准（状态码 200 不再等于可用）：
    OK      页面可访问且能读到正文；
    SHELL   页面可访问，但只有前端外壳（ATS 常见），需用浏览器打开确认岗位；
    PARKED  命中域名停放 / 出售文案，入口已失效；
    NONHTML 落地地址不是网页（图片 / 文件），通常是域名过期被托管商接管；
    BLOCKED 401/403/405/429/468，反爬或权限拦截；
    HTTPxxx 其他非 200 状态；
    NETERR  网络不可达、TLS 失败或超时。

SHELL 默认不算失败（ATS 由前端渲染是正常现象），加 --strict 才会计入失败。
「待人工确认」分区本来就不保证可用，始终不计入失败。
存在失败入口时返回非零退出码，可直接用于 CI 或定期巡检。
"""

from __future__ import annotations

import argparse
import concurrent.futures
import json
import re
from datetime import date
from pathlib import Path

import _common

DEFAULT_FILE = Path(__file__).resolve().parent.parent / "references" / "company-portals.md"
ROW_RE = re.compile(r"^\|\s*(?P<company>[^|]+?)\s*\|\s*(?P<url>https?://\S+?)\s*\|\s*(?P<note>[^|]*?)\s*\|\s*$")
SECTION_RE = re.compile(r"^###\s+(?P<title>.+?)\s*$")
PENDING_SECTION = "待人工确认"


def parse_entries(path: Path) -> list[dict[str, str]]:
    entries: list[dict[str, str]] = []
    section = ""
    for line in path.read_text(encoding="utf-8").splitlines():
        heading = SECTION_RE.match(line)
        if heading:
            section = heading.group("title")
            continue
        row = ROW_RE.match(line)
        if row:
            entries.append(
                {
                    "section": section,
                    "company": row.group("company"),
                    "url": row.group("url"),
                    "note": row.group("note"),
                }
            )
    return entries


def _is_transient(verdict: str) -> bool:
    return verdict == "NETERR" or verdict.startswith("HTTP5")


def check(entry: dict[str, str], timeout: float, retries: int = 0) -> dict[str, object]:
    """抓取并判定入口。网络类失败默认重试，避免把抖动误判成入口失效。"""
    result = _common.fetch(entry["url"], timeout=timeout)
    attempts = 1
    # 网络抖动和 5xx 都可能瞬时出现，重试后再判定，避免误报入口失效。
    while _is_transient(result["verdict"]) and attempts <= retries:
        attempts += 1
        result = _common.fetch(entry["url"], timeout=timeout)
    return {
        **entry,
        "status": result["status"],
        "final_url": result["final_url"],
        "title": result["title"],
        "verdict": result["verdict"],
        "error": result["error"],
        "host_changed": result["final_url"].split("//")[-1].split("/")[0]
        != entry["url"].split("//")[-1].split("/")[0],
        "attempts": attempts,
    }


def update_verified_date(path: Path) -> None:
    text = path.read_text(encoding="utf-8")
    today = date.today().isoformat()
    new_text, count = re.subn(
        r"`\d{4}-\d{2}-\d{2}` 用真实 HTTP 请求核验过一次",
        f"`{today}` 用真实 HTTP 请求核验过一次",
        text,
    )
    if count:
        path.write_text(new_text, encoding="utf-8")
        print(f"已更新核验日期为 {today}")


def main() -> int:
    _common.configure_utf8_stdio()
    parser = argparse.ArgumentParser(description="复核官方招聘入口索引")
    parser.add_argument("--file", default=str(DEFAULT_FILE), help="入口索引 Markdown 路径")
    parser.add_argument("--timeout", type=float, default=20.0, help="单个请求超时秒数")
    parser.add_argument("--workers", type=int, default=8, help="并发数")
    parser.add_argument("--json", action="store_true", help="输出 JSON")
    parser.add_argument("--strict", action="store_true", help="把 SHELL 也视为失败")
    parser.add_argument("--retries", type=int, default=2, help="网络抖动 / 5xx 的重试次数，默认 2")
    parser.add_argument("--update-date", action="store_true", help="核验后把索引顶部日期更新为今天")
    args = parser.parse_args()

    path = Path(args.file)
    if not path.exists():
        raise SystemExit(f"找不到入口索引文件：{path}")

    entries = parse_entries(path)
    if not entries:
        raise SystemExit("没有从索引中解析到任何入口链接。")

    with concurrent.futures.ThreadPoolExecutor(max_workers=args.workers) as pool:
        results = list(pool.map(lambda entry: check(entry, args.timeout, args.retries), entries))

    # SHELL 默认只是提示：ATS 由前端渲染属正常现象。--strict 时才计入失败。
    ignored = set() if args.strict else {"SHELL"}
    failed = [
        r
        for r in results
        if r["verdict"] != "OK"
        and r["verdict"] not in ignored
        and PENDING_SECTION not in r["section"]
    ]
    pending = [r for r in results if PENDING_SECTION in r["section"]]
    shells = [r for r in results if r["verdict"] == "SHELL" and PENDING_SECTION not in r["section"]]

    if args.json:
        # JSON 模式只输出一个合法 JSON 文档，便于脚本直接解析。
        print(json.dumps(results, ensure_ascii=False, indent=2))
        return 1 if failed else 0

    if True:
        for result in results:
            flag = "" if result["verdict"] == "OK" else f'  <-- {result["verdict"]}'
            moved = (
                f'  (跳转至 {result["final_url"]})'
                if result["host_changed"] and result["verdict"] in {"OK", "SHELL"}
                else ""
            )
            print(f'[{result["verdict"]:<8}] {result["company"]:<14} {result["url"]}{flag}{moved}')
        usable = len(results) - len(failed)
        print(f'\n共 {len(results)} 个入口，可用 {usable} 个，异常 {len(failed)} 个。')
        if shells:
            print(
                f'另有 {len(shells)} 个前端渲染入口（SHELL）：状态码正常、页面可打开，'
                '但静态请求读不到岗位正文，需用浏览器打开确认。'
            )

    if pending:
        print(f'\n待人工确认分区共 {len(pending)} 条，需要在国内网络环境或人工打开确认：')
        for result in pending:
            print(f'  - {result["company"]}: {result["url"]} ({result["verdict"]})')

    if failed:
        print("\n需要人工处理的入口：")
        for result in failed:
            detail = result["error"] or f'HTTP {result["status"]}'
            print(f'  - {result["company"]}: {result["url"]} ({result["verdict"]}, {detail})')
        return 1

    if args.update_date:
        update_verified_date(path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
