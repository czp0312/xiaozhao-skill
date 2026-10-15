#!/usr/bin/env python3
"""把岗位调研数据渲染成自包含的 HTML 报告（含图表与文字）。

用法：
    python scripts/render_report.py report.json
    python scripts/render_report.py report.json --out 报告.html
    python scripts/render_report.py report.json --check

输入 JSON 结构（除 title / sections 外均可省略）：

    {
      "pageTitle": "浏览器标题",
      "eyebrow": "顶部小字",
      "title": "主标题，可含 <em>高亮</em>",
      "lede": "导语",
      "chips": ["标签 <b>值</b>"],
      "kpis": [{"value": 42, "suffix": "/100", "label": "说明"}],
      "sections": [
        {"num": "01", "title": "小节标题", "sub": "小节说明", "blocks": [ {...} ]}
      ],
      "footerLeft": "...", "footerRight": "..."
    }

可用 block 类型：prose / bars / donut / table / skillcards / matrix /
transfer / timeline / fixes / legend / cards / columns。

报告内容契约（重要）：
HTML 报告只呈现**找到的岗位相关情况**——岗位、公司、技能要求、学历门槛、
投递入口、流程与来源。**不要**把 skill 自身的运行情况写进报告：脚本报错、
入口判定结果、抓取失败、修复记录、测试数量等一律不进报告。
这些内容属于 agent 与用户之间的对话，应由 agent 在后台汇总后单独告知用户。
校验默认会拦截此类内容；确需生成 skill 变更记录时用 --allow-internal。

模板是 references/report-template.html，其中的 __PAYLOAD__ 会被替换成数据。
报告不依赖任何第三方库，也不需要联网（字体加载失败时会回退到系统字体）。
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

import _common

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_TEMPLATE = ROOT / "references" / "report-template.html"
PLACEHOLDER = "__PAYLOAD__"
BLOCK_TYPES = {
    "prose", "bars", "donut", "table", "skillcards", "matrix",
    "transfer", "timeline", "fixes", "legend", "cards", "columns",
}

# skill 内部信息特征。报告只讲岗位，这些词一旦出现就说明混进了运行情况。
SKILL_INTERNAL_MARKERS = (
    "xiaozhao-skill", "scripts/",
    "_common.py", "_browser.py", "render_report", "check_portals",
    "fetch_jd", "update_portals", "normalize_jobs", "score_match", "extract_resume_text",
    "回归测试", "测试用例", "pytest",
    "修复前", "修复后", "已修复",
    "判定口径", "入口核验", "状态码",
    "无头浏览器", "无头渲染",
)
# 入口判定结论属于运行情况，且大小写敏感（避免误伤 JD 里的 shell 脚本等词）。
SKILL_INTERNAL_VERDICTS = ("SHELL", "PARKED", "NONHTML", "BLOCKED", "NETERR")


def scan_internal(payload: dict) -> list[str]:
    """扫描报告数据里是否混入了 skill 自身的运行情况。"""
    blob = json.dumps(payload, ensure_ascii=False)
    plain = re.sub(r"<[^>]+>", "", blob).lower()
    hits: list[str] = []
    for marker in SKILL_INTERNAL_MARKERS:
        if marker.lower() in plain:
            hits.append(marker)
    for verdict in SKILL_INTERNAL_VERDICTS:
        if verdict in blob:
            hits.append(verdict)
    return sorted(set(hits))


def validate(payload: dict) -> list[str]:
    problems: list[str] = []
    if not isinstance(payload, dict):
        return ["报告数据顶层必须是 JSON 对象"]
    if not payload.get("title"):
        problems.append("缺少 title（主标题）")
    sections = payload.get("sections")
    if not isinstance(sections, list) or not sections:
        problems.append("缺少 sections（至少一个小节）")
        return problems
    for i, section in enumerate(sections, 1):
        if not section.get("title"):
            problems.append(f"第 {i} 个小节缺少 title")
        for j, block in enumerate(section.get("blocks") or [], 1):
            btype = block.get("type")
            if btype not in BLOCK_TYPES:
                problems.append(f"第 {i} 个小节第 {j} 个 block 类型未知：{btype!r}")
            if btype == "bars" and not block.get("rows"):
                problems.append(f"第 {i} 个小节第 {j} 个 bars 缺少 rows")
            if btype == "table" and not block.get("rows"):
                problems.append(f"第 {i} 个小节第 {j} 个 table 缺少 rows")
            if btype == "donut" and not block.get("segments"):
                problems.append(f"第 {i} 个小节第 {j} 个 donut 缺少 segments")
    return problems


def render(payload: dict, template: str) -> str:
    if PLACEHOLDER not in template:
        raise SystemExit(f"模板缺少占位符 {PLACEHOLDER}")
    # 防止数据里的 </script> 提前闭合脚本块。
    blob = json.dumps(payload, ensure_ascii=False).replace("</", "<\\/")
    page_title = payload.get("pageTitle") or re.sub(r"<[^>]+>", "", str(payload.get("title", "报告")))
    return template.replace("__PAGE_TITLE__", page_title).replace(PLACEHOLDER, blob)


def main() -> int:
    _common.configure_utf8_stdio()
    parser = argparse.ArgumentParser(description="渲染 HTML 调研报告")
    parser.add_argument("input", help="报告数据 JSON 路径")
    parser.add_argument("--template", default=str(DEFAULT_TEMPLATE), help="HTML 模板路径")
    parser.add_argument("--out", help="输出 HTML 路径，默认与输入同名的 .html")
    parser.add_argument("--check", action="store_true", help="只校验数据，不写文件")
    parser.add_argument("--allow-internal", action="store_true",
                        help="允许报告包含 skill 运行情况（仅用于生成 skill 变更记录，不用于岗位报告）")
    args = parser.parse_args()

    data_path = Path(args.input)
    if not data_path.exists():
        raise SystemExit(f"找不到报告数据：{data_path}")
    payload = json.loads(data_path.read_text(encoding="utf-8"))

    problems = validate(payload)
    if not args.allow_internal:
        internal = scan_internal(payload)
        if internal:
            problems.append(
                "报告里混入了 skill 自身的运行情况："
                + "、".join(internal)
                + "。岗位报告只呈现岗位相关情况；这些内容请在对话里单独告知用户。"
                + "确需生成 skill 变更记录时加 --allow-internal。"
            )
    if problems:
        print("报告数据校验未通过：")
        for problem in problems:
            print(f"  - {problem}")
        return 1
    print("报告数据校验通过。")
    if args.check:
        return 0

    template_path = Path(args.template)
    if not template_path.exists():
        raise SystemExit(f"找不到模板：{template_path}")
    html = render(payload, template_path.read_text(encoding="utf-8"))

    out_path = Path(args.out) if args.out else data_path.with_suffix(".html")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    # 固定用 \n 写入，避免 Windows 把换行翻译成 \r\n，让文件字节数与跨平台结果一致。
    out_path.write_text(html, encoding="utf-8", newline="\n")
    print(f"已生成报告：{out_path}（{out_path.stat().st_size} 字节）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
