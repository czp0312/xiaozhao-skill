#!/usr/bin/env python3
"""把新核验的入口安全地合并进 references/company-portals.md。

用法：
    python scripts/update_portals.py --input entries.json --dry-run
    python scripts/update_portals.py --input entries.json --replace
    python scripts/update_portals.py --input entries.json

entries.json 格式（与 references/company-portals.md 的分区标题一致）：

    {
      "具身智能与机器人": [
        ["宇树科技", "https://unitree.zhiye.com/campus", "官方 ATS（北森）校招入口"]
      ]
    }

写入前会做安全校验，校验不通过直接拒绝写入，避免出现“文件被写空”这类事故：
    1. 入口总数不得低于原文件的 90%；
    2. 必须仍然包含文件头与「覆盖情况」小节；
    3. 结果中不允许出现重复的公司名或重复 URL（同一家公司可跨分区出现时除外）。
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

import _common

DEFAULT_FILE = Path(__file__).resolve().parent.parent / "references" / "company-portals.md"
PENDING_SECTION = "待人工确认"
ROW_RE = re.compile(r"^\|\s*(?P<company>[^|]+?)\s*\|\s*(?P<url>https?://\S+?)\s*\|\s*(?P<note>[^|]*?)\s*\|\s*$")
SECTION_RE = re.compile(r"^###\s+(?P<title>.+?)\s*$")
HEADER_REQUIRED = "# 官方招聘入口索引"
COVERAGE_REQUIRED = "## 覆盖情况"


def render(company: str, url: str, note: str) -> str:
    return f"| {company} | {url} | {note} |"


def load_entries(path: Path) -> dict[str, list[list[str]]]:
    raw = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise SystemExit("entries.json 顶层必须是 {分组: [[公司, URL, 说明], ...]} 结构")
    out: dict[str, list[list[str]]] = {}
    for section, rows in raw.items():
        cleaned = []
        for row in rows:
            if not isinstance(row, (list, tuple)) or len(row) != 3:
                raise SystemExit(f"分组「{section}」存在格式错误的条目：{row!r}")
            company, url, note = (str(x) for x in row)
            if not url.startswith(("http://", "https://")):
                raise SystemExit(f"分组「{section}」的 {company} 缺少 http(s) 链接：{url}")
            cleaned.append([company, url, note])
        out[section] = cleaned
    return out


def merge(text: str, entries: dict[str, list[list[str]]], replace: bool) -> tuple[str, int, int]:
    lines = text.splitlines()
    result: list[str] = []
    added = replaced = 0
    i = 0
    while i < len(lines):
        line = lines[i]
        heading = SECTION_RE.match(line)
        if not heading:
            result.append(line)
            i += 1
            continue

        section = heading.group("title")
        result.append(line)
        j = i + 1
        block: list[str] = []
        while j < len(lines) and not lines[j].startswith("###") and not lines[j].startswith("## "):
            block.append(lines[j])
            j += 1

        source = entries.get(section)
        if not source:
            result.extend(block)
            i = j
            continue

        # 同公司已存在时：--replace 才覆盖，否则跳过，避免误改已核验链接。
        if replace:
            index = {
                ROW_RE.match(b).group("company"): k
                for k, b in enumerate(block)
                if ROW_RE.match(b)
            }
            for company, url, note in source:
                k = index.get(company)
                if k is not None and ROW_RE.match(block[k]).group("url") != url:
                    block[k] = render(company, url, note)
                    replaced += 1

        present = {ROW_RE.match(b).group("company") for b in block if ROW_RE.match(b)}
        last_row = max((k for k, b in enumerate(block) if b.startswith("| ")), default=None)
        new_rows = [render(*row) for row in source if row[0] not in present]
        if last_row is not None and new_rows:
            block = block[: last_row + 1] + new_rows + block[last_row + 1 :]
            added += len(new_rows)

        result.extend(block)
        i = j
    return "\n".join(result) + "\n", added, replaced


def refresh_coverage(text: str) -> str:
    """按实际解析结果重算「覆盖情况」里的两个数字。"""
    verified = pending = 0
    section = ""
    for line in text.splitlines():
        heading = SECTION_RE.match(line)
        if heading:
            section = heading.group("title")
        if ROW_RE.match(line):
            if PENDING_SECTION in section:
                pending += 1
            else:
                verified += 1
    text = re.sub(r"- 已核验入口：\d+ 家公司。", f"- 已核验入口：{verified} 家公司。", text)
    text = re.sub(r"- 待人工确认：\d+ 家。", f"- 待人工确认：{pending} 家。", text)
    return text


def validate(old_text: str, new_text: str) -> list[str]:
    problems: list[str] = []
    old_rows = sum(1 for line in old_text.splitlines() if ROW_RE.match(line))
    new_rows = sum(1 for line in new_text.splitlines() if ROW_RE.match(line))
    if new_rows < old_rows * 0.9:
        problems.append(f"入口数量从 {old_rows} 降到 {new_rows}，疑似误删，拒绝写入")
    if HEADER_REQUIRED not in new_text:
        problems.append("结果缺少文件头，拒绝写入")
    if COVERAGE_REQUIRED not in new_text:
        problems.append("结果缺少「覆盖情况」小节，拒绝写入")
    urls = [ROW_RE.match(line).group("url") for line in new_text.splitlines() if ROW_RE.match(line)]
    duplicates = sorted({url for url in urls if urls.count(url) > 1})
    if duplicates:
        problems.append(f"存在重复 URL：{', '.join(duplicates[:5])}")
    return problems


def main() -> int:
    _common.configure_utf8_stdio()
    parser = argparse.ArgumentParser(description="安全合并招聘入口索引")
    parser.add_argument("--file", default=str(DEFAULT_FILE), help="入口索引 Markdown 路径")
    parser.add_argument("--input", required=True, help="待合并条目的 JSON 文件")
    parser.add_argument("--replace", action="store_true", help="同公司已存在时用新链接覆盖")
    parser.add_argument("--dry-run", action="store_true", help="只展示将要发生的改动，不写文件")
    args = parser.parse_args()

    target = Path(args.file)
    if not target.exists():
        raise SystemExit(f"找不到入口索引文件：{target}")
    old_text = target.read_text(encoding="utf-8")
    if not old_text.strip():
        raise SystemExit("入口索引文件为空，拒绝在空文件上继续写入。")

    entries = load_entries(Path(args.input))
    merged, added, replaced = merge(old_text, entries, replace=args.replace)
    merged = refresh_coverage(merged)

    problems = validate(old_text, merged)
    if problems:
        print("安全校验未通过：")
        for problem in problems:
            print(f"  - {problem}")
        return 1

    print(f"新增 {added} 条，覆盖 {replaced} 条。")
    if args.dry_run:
        print("--dry-run：未写入文件。")
        return 0

    target.write_text(merged, encoding="utf-8")
    print(f"已写入 {target}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())