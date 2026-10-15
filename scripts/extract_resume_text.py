#!/usr/bin/env python3
"""无外部依赖地从 .txt、.md、.docx 简历中提取纯文本。

.docx 通过直接解析 OOXML 实现，因此不依赖 python-docx；
正文段落、表格单元格和文本框中的文字都会被提取。
"""

from __future__ import annotations

import argparse
import re
import sys
import zipfile
from pathlib import Path
from xml.etree import ElementTree

WORD_NS = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
SUPPORTED = {".txt", ".md", ".docx"}


def _configure_utf8_stdio() -> None:
    """Windows 默认编码不是 UTF-8，显式固定输出编码，避免管道读取时乱码。"""
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            try:
                stream.reconfigure(encoding="utf-8")
            except (ValueError, OSError):
                pass


def extract_docx(path: Path) -> str:
    with zipfile.ZipFile(path) as archive:
        xml = archive.read("word/document.xml")
    root = ElementTree.fromstring(xml)
    paragraphs: list[str] = []
    for paragraph in root.iter(f"{WORD_NS}p"):
        # 制表符和换行在 OOXML 里是独立元素，转成空格避免文字粘连。
        pieces: list[str] = []
        for node in paragraph.iter():
            if node.tag == f"{WORD_NS}t":
                pieces.append(node.text or "")
            elif node.tag in (f"{WORD_NS}tab", f"{WORD_NS}br"):
                pieces.append(" ")
        line = re.sub(r"\s+", " ", "".join(pieces)).strip()
        if line:
            paragraphs.append(line)
    return "\n".join(paragraphs)


def normalize_text(text: str) -> str:
    text = text.replace("\u00a0", " ")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def extract(path: Path) -> str:
    suffix = path.suffix.lower()
    if suffix in {".txt", ".md"}:
        return path.read_text(encoding="utf-8")
    if suffix == ".docx":
        return extract_docx(path)
    raise SystemExit(f"不支持的文件类型：{suffix}。支持：.txt、.md、.docx")


def main() -> None:
    _configure_utf8_stdio()
    parser = argparse.ArgumentParser(description="从简历文件提取纯文本")
    parser.add_argument("path", help="简历文件路径，支持 .txt、.md、.docx")
    args = parser.parse_args()
    path = Path(args.path)
    if not path.exists():
        raise SystemExit(f"文件不存在：{path}")
    if path.suffix.lower() not in SUPPORTED:
        raise SystemExit(f"不支持的文件类型：{path.suffix}。支持：.txt、.md、.docx")
    sys.stdout.write(normalize_text(extract(path)))


if __name__ == "__main__":
    main()