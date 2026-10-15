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
    args = parser.parse_args()

    data_path = Path(args.input)
    if not data_path.exists():
        raise SystemExit(f"找不到报告数据：{data_path}")
    payload = json.loads(data_path.read_text(encoding="utf-8"))

    problems = validate(payload)
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
    out_path.write_text(html, encoding="utf-8")
    print(f"已生成报告：{out_path}（{len(html)} 字节）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())