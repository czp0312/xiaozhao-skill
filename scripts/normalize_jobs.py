#!/usr/bin/env python3
"""将校招岗位 JSON 记录标准化为 Markdown 表格。

输入：从标准输入或文件路径读取 JSON 对象数组。
输出：带 --json 时输出标准化 JSON，否则输出 Markdown 表格。
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import date
from typing import Any
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit


TRACKING_KEYS = {"from", "source", "token", "spm"}

COMPANY_ALIASES = {
    "b站": "Bilibili",
    "哔哩哔哩": "Bilibili",
    "字节": "字节跳动",
    "蚂蚁": "蚂蚁集团",
    "腾讯": "腾讯",
    "阿里": "阿里巴巴",
    "米哈游": "米哈游",
}

ROLE_KEYWORDS = [
    ("ai_app", ["ai应用", "ai 应用", "大模型应用", "llm应用", "agent", "rag"]),
    ("llm_app", ["大模型", "llm", "prompt", "智能体"]),
    ("frontend", ["前端", "web前端", "javascript", "typescript", "react", "vue"]),
    ("backend", ["后端", "服务端", "java", "golang", "go开发", "c++"]),
    ("client", ["客户端", "android", "ios", "移动端"]),
    ("fullstack", ["全栈", "full stack", "fullstack"]),
    ("algorithm", ["算法", "推荐", "搜索", "nlp", "cv"]),
    ("machine_learning", ["机器学习", "深度学习", "模型训练"]),
    ("data_engineering", ["数据开发", "数仓", "etl", "flink", "spark"]),
    ("data_analysis", ["数据分析", "商业分析"]),
    ("test_development", ["测试开发", "测开", "自动化测试"]),
    ("sre", ["sre", "运维开发", "devops", "稳定性"]),
    ("security", ["安全", "攻防", "漏洞"]),
    ("game_development", ["游戏开发", "unity", "ue", "客户端引擎"]),
    ("graphics", ["图形", "渲染", "opengl", "vulkan"]),
    ("embedded", ["嵌入式", "固件", "单片机"]),
]

TYPE_KEYWORDS = [
    ("summer_internship", ["暑期实习", "summer"]),
    ("daily_internship", ["日常实习"]),
    ("internship", ["实习", "intern"]),
    ("spring_recruitment", ["春招"]),
    ("fall_recruitment", ["秋招"]),
    ("early_batch", ["提前批"]),
    ("campus", ["校招", "校园招聘", "应届"]),
]


def strip_tracking(url: str) -> str:
    if not url:
        return url
    split = urlsplit(url)
    query = []
    for key, value in parse_qsl(split.query, keep_blank_values=True):
        if key in TRACKING_KEYS or key.startswith("utm_"):
            continue
        query.append((key, value))
    return urlunsplit((split.scheme, split.netloc, split.path, urlencode(query), split.fragment))


def normalize_company(name: str) -> str:
    raw = (name or "").strip()
    compact = re.sub(r"\s+", "", raw).lower()
    for alias, canonical in COMPANY_ALIASES.items():
        if compact == alias.lower():
            return canonical
    return raw


def infer_from_keywords(text: str, mapping: list[tuple[str, list[str]]], default: str) -> str:
    lowered = (text or "").lower()
    compact = lowered.replace(" ", "")
    for value, keywords in mapping:
        for keyword in keywords:
            key = keyword.lower().replace(" ", "")
            if key in compact:
                return value
    return default


def normalize_locations(value: Any) -> list[str]:
    if isinstance(value, list):
        items = value
    else:
        items = re.split(r"[、,，/;；\s]+", str(value or ""))
    locations = [item.strip() for item in items if item and item.strip()]
    return locations or ["未注明"]


def normalize_record(record: dict[str, Any], verified_at: str) -> dict[str, Any]:
    role_title = str(record.get("role_title") or record.get("招聘岗位") or record.get("title") or "").strip()
    company = str(record.get("company_name") or record.get("公司名称") or record.get("company") or "").strip()
    combined = " ".join(str(record.get(key, "")) for key in ["role_title", "招聘岗位", "job_description", "requirements"])

    normalized = {
        "company_name": normalize_company(company),
        "role_title": role_title,
        "role_family": record.get("role_family") or infer_from_keywords(combined, ROLE_KEYWORDS, "other_technical"),
        "recruiting_type": record.get("recruiting_type") or infer_from_keywords(combined, TYPE_KEYWORDS, "unknown"),
        "target_graduation": record.get("target_graduation") or record.get("招聘对象") or "not_specified",
        "locations": normalize_locations(record.get("locations") or record.get("工作地点")),
        "deadline": record.get("deadline") or record.get("投递截止时间") or None,
        "apply_url": strip_tracking(str(record.get("apply_url") or record.get("投递链接") or "")),
        "source_url": strip_tracking(str(record.get("source_url") or record.get("source") or record.get("投递链接") or "")),
        "source_level": record.get("source_level") or "B",
        "source_name": record.get("source_name") or record.get("来源") or "",
        "posted_at": record.get("posted_at") or record.get("更新时间") or None,
        "verified_at": record.get("verified_at") or verified_at,
        "job_description": record.get("job_description") or "",
        "requirements": record.get("requirements") or "",
        "status": record.get("status") or "unknown",
        "confidence_note": record.get("confidence_note") or "",
    }
    return normalized


def source_status(record: dict[str, Any]) -> str:
    if record["status"] == "expired":
        return "已过期"
    if record["status"] == "unverified_lead":
        return "未核验线索"
    if record["source_level"] == "S":
        return "官方已核验"
    if record["source_level"] == "A":
        return "近官方已核验"
    return "状态不明"


def to_markdown(records: list[dict[str, Any]]) -> str:
    headers = ["更新时间", "公司名称", "招聘岗位", "招聘对象", "工作地点", "投递截止时间", "投递链接", "来源状态"]
    rows = ["| " + " | ".join(headers) + " |", "| " + " | ".join(["---"] * len(headers)) + " |"]
    for rec in records:
        rows.append(
            "| "
            + " | ".join(
                [
                    str(rec.get("posted_at") or rec.get("verified_at") or ""),
                    rec.get("company_name", ""),
                    rec.get("role_title") or rec.get("role_family", ""),
                    str(rec.get("target_graduation") or ""),
                    "、".join(rec.get("locations") or ["未注明"]),
                    str(rec.get("deadline") or ""),
                    rec.get("apply_url", ""),
                    source_status(rec),
                ]
            )
            + " |"
        )
    return "\n".join(rows)


def read_records(path: str | None) -> list[dict[str, Any]]:
    data = sys.stdin.read() if not path else open(path, encoding="utf-8").read()
    records = json.loads(data)
    if not isinstance(records, list):
        raise SystemExit("输入必须是 JSON 数组。")
    return records


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("path", nargs="?")
    parser.add_argument("--json", action="store_true", help="输出标准化 JSON，而不是 Markdown 表格。")
    parser.add_argument("--verified-at", default=date.today().isoformat())
    args = parser.parse_args()

    normalized = [normalize_record(record, args.verified_at) for record in read_records(args.path)]
    if args.json:
        print(json.dumps(normalized, ensure_ascii=False, indent=2))
    else:
        print(to_markdown(normalized))


if __name__ == "__main__":
    main()
