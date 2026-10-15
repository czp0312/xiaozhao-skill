#!/usr/bin/env python3
"""复核 references/company-portals.md 中的官方招聘入口是否仍然可用。

用法：
    python scripts/check_portals.py
    python scripts/check_portals.py --json
    python scripts/check_portals.py --update-date

判定标准：HTTP 200 视为可用；跳转到其他域名会单独标出，方便确认是否为官方 ATS。
存在失效入口时返回非零退出码，可直接用于 CI 或定期巡检。
"""

from __future__ import annotations

import argparse
import concurrent.futures
import http.cookiejar
import json
import re
import ssl
import sys
import urllib.error
import urllib.request
from datetime import date
from pathlib import Path

DEFAULT_FILE = Path(__file__).resolve().parent.parent / "references" / "company-portals.md"
ROW_RE = re.compile(r"^\|\s*(?P<company>[^|]+?)\s*\|\s*(?P<url>https?://\S+?)\s*\|\s*(?P<note>[^|]*?)\s*\|\s*$")
SECTION_RE = re.compile(r"^###\s+(?P<title>.+?)\s*$")
UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"
)


def _configure_utf8_stdio() -> None:
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            try:
                stream.reconfigure(encoding="utf-8")
            except (ValueError, OSError):
                pass


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


def fetch(url: str, timeout: float) -> dict[str, object]:
    context = ssl.create_default_context()
    context.check_hostname = False
    context.verify_mode = ssl.CERT_NONE
    # 部分招聘站依赖 Cookie 才能完成跳转，没有 Cookie 容器会停在 302。
    opener = urllib.request.build_opener(
        urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar()),
        urllib.request.HTTPSHandler(context=context),
    )
    opener.addheaders = [
        ("User-Agent", UA),
        ("Accept", "text/html,application/xhtml+xml,*/*;q=0.8"),
        ("Accept-Language", "zh-CN,zh;q=0.9,en;q=0.8"),
    ]
    request = urllib.request.Request(url)
    try:
        with opener.open(request, timeout=timeout) as response:
            return {"status": response.status, "final_url": response.geturl(), "error": ""}
    except urllib.error.HTTPError as exc:
        return {"status": exc.code, "final_url": getattr(exc, "url", url), "error": ""}
    except Exception as exc:  # 网络不可达、TLS 失败、超时等
        return {"status": None, "final_url": url, "error": f"{type(exc).__name__}: {exc}"}


def check(entry: dict[str, str], timeout: float) -> dict[str, object]:
    result = fetch(entry["url"], timeout)
    status = result["status"]
    final_url = str(result["final_url"])
    if status == 200:
        verdict = "OK"
    elif status in (401, 403, 405, 429):
        verdict = "BLOCKED"
    elif status is None:
        verdict = "NETERR"
    else:
        verdict = f"HTTP{status}"
    return {
        **entry,
        **result,
        "verdict": verdict,
        "host_changed": final_url.split("//")[-1].split("/")[0] != entry["url"].split("//")[-1].split("/")[0],
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
    _configure_utf8_stdio()
    parser = argparse.ArgumentParser(description="复核官方招聘入口索引")
    parser.add_argument("--file", default=str(DEFAULT_FILE), help="入口索引 Markdown 路径")
    parser.add_argument("--timeout", type=float, default=20.0, help="单个请求超时秒数")
    parser.add_argument("--workers", type=int, default=8, help="并发数")
    parser.add_argument("--json", action="store_true", help="输出 JSON")
    parser.add_argument("--update-date", action="store_true", help="核验后把索引顶部日期更新为今天")
    args = parser.parse_args()

    path = Path(args.file)
    if not path.exists():
        raise SystemExit(f"找不到入口索引文件：{path}")

    entries = parse_entries(path)
    if not entries:
        raise SystemExit("没有从索引中解析到任何入口链接。")

    with concurrent.futures.ThreadPoolExecutor(max_workers=args.workers) as pool:
        results = list(pool.map(lambda entry: check(entry, args.timeout), entries))

    # “待人工确认”分区本来就不保证可用，不计入失败，只单独提示。
    pending_section = "待人工确认"
    failed = [r for r in results if r["verdict"] != "OK" and pending_section not in r["section"]]
    pending = [r for r in results if pending_section in r["section"]]
    if args.json:
        print(json.dumps(results, ensure_ascii=False, indent=2))
    else:
        for result in results:
            flag = "" if result["verdict"] == "OK" else f'  <-- {result["verdict"]}'
            moved = f'  (跳转至 {result["final_url"]})' if result["host_changed"] and result["verdict"] == "OK" else ""
            print(f'[{result["verdict"]:<8}] {result["company"]:<12} {result["url"]}{flag}{moved}')
        print(f'\n共 {len(results)} 个入口，可用 {len(results) - len(failed)} 个，异常 {len(failed)} 个。')

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
