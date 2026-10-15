#!/usr/bin/env python3
"""将校招岗位 JSON 记录标准化、去重并输出 Markdown 表格。

输入：从标准输入或文件路径读取 JSON 对象数组（UTF-8）。
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

TRACKING_KEYS = {"from", "source", "token", "spm", "share", "ref"}

COMPANY_ALIASES = {
    "b站": "哔哩哔哩",
    "哔哩哔哩": "哔哩哔哩",
    "字节": "字节跳动",
    "字节跳动": "字节跳动",
    "蚂蚁": "蚂蚁集团",
    "腾讯": "腾讯",
    "阿里": "阿里巴巴",
    "淘天": "淘天集团",
    "米哈游": "米哈游",
    "大疆": "大疆",
    "华为": "华为",
    "美团": "美团",
    "百度": "百度",
    "京东": "京东",
    "网易": "网易",
    "快手": "快手",
    "小红书": "小红书",
    "拼多多": "拼多多",
    "滴滴": "滴滴",
    "中兴": "中兴通讯",
    "联想": "联想",
    "小米": "小米",
    "荣耀": "荣耀",
}

# 岗位族关键词，按“越具体越靠前”排序；命中顺序决定分类结果。
# 纯 ASCII 关键词按词边界匹配，含中文的关键词按子串匹配。
ROLE_KEYWORDS: list[tuple[str, list[str]]] = [
    ("embodied_ai", ["具身智能", "具身", "人形机器人", "灵巧手", "机器人算法", "机器人软件", "机器人学习", "vla", "抓取", "模仿学习"]),
    ("motion_control", ["运动控制", "运控", "伺服", "电机控制", "驱动控制", "控制算法", "轨迹规划", "力控", "液压", "电控", "运动规划"]),
    ("ic_design", ["数字ic", "ic设计", "ic验证", "芯片设计", "数字前端", "rtl", "verilog", "systemverilog", "uvm", "版图", "模拟ic", "dft", "后端实现", "fpga"]),
    ("embedded_hardware", ["嵌入式硬件", "嵌硬", "硬件工程师", "硬件开发", "硬件设计", "电路设计", "pcb", "原理图", "电源设计", "emc", "硬件"]),
    ("embedded_software", ["嵌入式软件", "嵌入式开发", "嵌软", "固件", "firmware", "bsp", "驱动开发", "单片机", "mcu", "rtos", "freertos", "autosar", "linux驱动", "嵌入式"]),
    ("computer_vision", ["计算机视觉", "视觉算法", "cv算法", "图像算法", "图像处理", "目标检测", "三维重建", "视觉感知", "点云", "slam"]),
    ("agent_development", ["agent开发", "智能体", "多智能体", "agent", "工具调用", "mcp", "工作流编排"]),
    ("llm_app", ["大模型应用", "大模型开发", "大模型算法", "大模型", "llm", "预训练", "sft", "微调", "推理优化", "prompt", "rag"]),
    ("ai_app", ["ai应用", "ai产品", "ai开发", "ai工程", "人工智能应用"]),
    ("algorithm", ["算法工程师", "算法", "推荐系统", "搜索算法", "nlp", "自然语言", "广告算法", "策略算法"]),
    ("machine_learning", ["机器学习", "深度学习", "模型训练", "数据挖掘"]),
    ("game_development", ["游戏开发", "游戏客户端", "游戏服务端", "unity", "unreal", "虚幻", "游戏引擎"]),
    ("graphics", ["图形", "渲染", "opengl", "vulkan", "shader"]),
    ("fullstack", ["全栈", "fullstack", "full-stack"]),
    ("frontend", ["前端", "javascript", "typescript", "react", "vue", "小程序"]),
    ("backend", ["后端", "服务端", "java", "golang", "go开发", "c++", "spring", "微服务"]),
    ("client", ["客户端", "android", "ios", "移动端", "flutter"]),
    ("data_engineering", ["数据开发", "数仓", "etl", "flink", "spark", "hadoop", "数据平台", "数据仓库"]),
    ("data_analysis", ["数据分析", "商业分析", "数据科学"]),
    ("test_development", ["测试开发", "测开", "自动化测试", "质量保障"]),
    ("sre", ["sre", "运维开发", "devops", "稳定性", "基础架构"]),
    ("security", ["安全", "攻防", "漏洞", "渗透"]),
]

TYPE_KEYWORDS: list[tuple[str, list[str]]] = [
    ("early_batch", ["提前批"]),
    ("summer_internship", ["暑期实习", "暑期"]),
    ("daily_internship", ["日常实习", "日常"]),
    ("spring_recruitment", ["春招", "春季招聘"]),
    ("fall_recruitment", ["秋招", "秋季招聘"]),
    ("off_cycle", ["补录", "补招", "扩招"]),
    ("internship", ["实习", "intern"]),
    ("campus", ["校招", "校园招聘", "应届"]),
]

DISPLAY_EMPTY = "未注明"


def _configure_utf8_stdio() -> None:
    """Windows 默认编码不是 UTF-8，显式固定标准流编码，避免输出乱码。"""
    for stream in (sys.stdin, sys.stdout):
        if hasattr(stream, "reconfigure"):
            try:
                stream.reconfigure(encoding="utf-8")
            except (ValueError, OSError):
                pass


def _is_ascii_token(keyword: str) -> bool:
    return bool(re.fullmatch(r"[a-z0-9+#.\-]+", keyword))


def _compact(text: str) -> str:
    return re.sub(r"\s+", "", (text or "").lower())


def keyword_hit(keyword: str, compact_text: str) -> bool:
    key = _compact(keyword)
    if not key:
        return False
    if _is_ascii_token(key):
        # 词边界匹配，避免 go 命中 django/google、java 命中 javascript。
        return re.search(rf"(?<![a-z0-9]){re.escape(key)}(?![a-z0-9])", compact_text) is not None
    return key in compact_text


def keyword_position(keyword: str, compact_text: str) -> int | None:
    key = _compact(keyword)
    if not key:
        return None
    if _is_ascii_token(key):
        match = re.search(rf"(?<![a-z0-9]){re.escape(key)}(?![a-z0-9])", compact_text)
        return match.start() if match else None
    return compact_text.find(key) if key in compact_text else None


def infer_from_keywords(text: str, mapping: list[tuple[str, list[str]]], default: str, mode: str = "priority") -> str:
    """mode="priority" 按列表顺序取第一个命中项；mode="position" 取出现位置最靠前的方向。

    岗位族用 position：主标题里的方向比括号补充说明更能代表岗位，例如
    “后端开发工程师（大模型平台）”应当归 backend。招聘类型用 priority，
    因为“春招提前批”这类写法需要固定优先级。
    """
    compact = _compact(text)
    if mode == "position":
        best: tuple[int, int, str] | None = None
        for priority, (value, keywords) in enumerate(mapping):
            for keyword in keywords:
                position = keyword_position(keyword, compact)
                if position is None:
                    continue
                if best is None or (position, priority) < (best[0], best[1]):
                    best = (position, priority, value)
        return best[2] if best else default
    for value, keywords in mapping:
        if any(keyword_hit(keyword, compact) for keyword in keywords):
            return value
    return default


def infer_role_family(role_title: str, body: str) -> str:
    """先看岗位标题，再看 JD 正文。

    标题比正文可靠：正文提到“大模型”不等于岗位是大模型方向，
    而“后端开发工程师（大模型平台）”应当归为 backend。
    """
    title_hit = infer_from_keywords(role_title, ROLE_KEYWORDS, "", mode="position")
    if title_hit:
        return title_hit
    return infer_from_keywords(body, ROLE_KEYWORDS, "other_technical", mode="position")


def strip_tracking(url: str) -> str:
    if not url:
        return url
    split = urlsplit(url)
    query = [
        (key, value)
        for key, value in parse_qsl(split.query, keep_blank_values=True)
        if key not in TRACKING_KEYS and not key.startswith("utm_")
    ]
    return urlunsplit((split.scheme, split.netloc, split.path, urlencode(query), split.fragment))


def normalize_company(name: str) -> str:
    raw = (name or "").strip()
    compact = re.sub(r"\s+", "", raw).lower()
    for alias, canonical in COMPANY_ALIASES.items():
        if compact == alias.lower():
            return canonical
    return raw


def normalize_locations(value: Any) -> list[str]:
    if isinstance(value, list):
        items = value
    else:
        items = re.split(r"[、,，/;；|]+", str(value or ""))
    locations = [str(item).strip() for item in items if str(item).strip()]
    return locations or [DISPLAY_EMPTY]


def normalize_record(record: dict[str, Any], verified_at: str) -> dict[str, Any]:
    role_title = str(record.get("role_title") or record.get("招聘岗位") or record.get("title") or "").strip()
    company = str(record.get("company_name") or record.get("公司名称") or record.get("company") or "").strip()
    body = " ".join(
        str(record.get(key) or "") for key in ["job_description", "requirements", "职责", "任职要求"]
    )

    return {
        "company_name": normalize_company(company),
        "role_title": role_title,
        "role_family": record.get("role_family") or infer_role_family(role_title, body),
        "recruiting_type": record.get("recruiting_type")
        or infer_from_keywords(" ".join([role_title, body, str(record.get("招聘对象") or "")]), TYPE_KEYWORDS, "unknown"),
        "target_graduation": record.get("target_graduation") or record.get("招聘对象") or "not_specified",
        "locations": normalize_locations(record.get("locations") or record.get("工作地点")),
        "deadline": record.get("deadline") or record.get("投递截止时间") or None,
        "apply_url": strip_tracking(str(record.get("apply_url") or record.get("投递链接") or "")),
        "source_url": strip_tracking(str(record.get("source_url") or record.get("来源链接") or "")),
        "source_level": record.get("source_level") or "B",
        "source_name": record.get("source_name") or record.get("来源") or "",
        "posted_at": record.get("posted_at") or record.get("更新时间") or None,
        "verified_at": record.get("verified_at") or verified_at,
        "job_description": record.get("job_description") or "",
        "requirements": record.get("requirements") or "",
        "status": record.get("status") or "unknown",
        "confidence_note": record.get("confidence_note") or "",
    }


def dedupe(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """按同公司、同岗位族、同招聘类型、城市重叠判定重复，并去除重复投递链接。

    缺少公司名的记录无法判定归属，直接保留，避免把不同公司的记录合并掉。
    城市信息只有一侧存在时也视为不同记录，去重宁可保守。
    """
    kept: list[dict[str, Any]] = []
    signatures: list[tuple[tuple[str, ...], set[str]]] = []
    seen_urls: set[str] = set()
    for record in records:
        url = record.get("apply_url") or ""
        if url and url in seen_urls:
            continue
        company = record.get("company_name", "")
        if not company:
            kept.append(record)
            continue
        cities = {city for city in record.get("locations", []) if city != DISPLAY_EMPTY}
        signature = (
            company,
            record.get("role_family", ""),
            record.get("recruiting_type", ""),
            str(record.get("target_graduation") or ""),
        )
        if any(
            other == signature
            and (cities == other_cities or bool(cities and other_cities and (cities & other_cities)))
            for other, other_cities in signatures
        ):
            continue
        if url:
            seen_urls.add(url)
        signatures.append((signature, cities))
        kept.append(record)
    return kept


def source_status(record: dict[str, Any]) -> str:
    if record["status"] == "expired":
        return "已过期"
    if record["status"] == "unverified_lead" or record["source_level"] == "C":
        return "未核验线索"
    if record["source_level"] == "S":
        return "官方已核验"
    if record["source_level"] == "A":
        return "近官方已核验"
    return "状态不明"


def _cell(value: Any) -> str:
    text = str(value if value is not None else "").strip()
    if not text:
        return DISPLAY_EMPTY
    if text == "not_specified":
        return DISPLAY_EMPTY
    return text.replace("|", "\\|")


def to_markdown(records: list[dict[str, Any]]) -> str:
    headers = ["更新时间", "公司名称", "招聘岗位", "招聘对象", "工作地点", "投递截止时间", "投递链接", "来源状态"]
    rows = ["| " + " | ".join(headers) + " |", "| " + " | ".join(["---"] * len(headers)) + " |"]
    for rec in records:
        rows.append(
            "| "
            + " | ".join(
                [
                    _cell(rec.get("posted_at") or rec.get("verified_at")),
                    _cell(rec.get("company_name")),
                    _cell(rec.get("role_title") or rec.get("role_family")),
                    _cell(rec.get("target_graduation")),
                    _cell("、".join(rec.get("locations") or [DISPLAY_EMPTY])),
                    _cell(rec.get("deadline")),
                    _cell(rec.get("apply_url")),
                    _cell(source_status(rec)),
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
    _configure_utf8_stdio()
    parser = argparse.ArgumentParser(description="校招岗位记录标准化与去重")
    parser.add_argument("path", nargs="?", help="JSON 文件路径，缺省从标准输入读取")
    parser.add_argument("--json", action="store_true", help="输出标准化 JSON，而不是 Markdown 表格。")
    parser.add_argument("--verified-at", default=date.today().isoformat(), help="核验日期，格式 YYYY-MM-DD")
    parser.add_argument("--no-dedup", action="store_true", help="跳过去重，保留全部输入记录。")
    args = parser.parse_args()

    normalized = [normalize_record(record, args.verified_at) for record in read_records(args.path)]
    if not args.no_dedup:
        normalized = dedupe(normalized)
    if args.json:
        print(json.dumps(normalized, ensure_ascii=False, indent=2))
    else:
        print(to_markdown(normalized))


if __name__ == "__main__":
    main()
