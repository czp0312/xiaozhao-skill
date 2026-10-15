import subprocess
import sys
import zipfile
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent.parent / "scripts"
WORD_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"


def _make_docx(path: Path, body: str) -> None:
    document = f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?><w:document xmlns:w="{WORD_NS}"><w:body>{body}</w:body></w:document>'
    with zipfile.ZipFile(path, "w") as archive:
        archive.writestr(
            "[Content_Types].xml",
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Default Extension="xml" ContentType="application/xml"/><Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/><Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/></Types>',
        )
        archive.writestr(
            "_rels/.rels",
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/></Relationships>',
        )
        archive.writestr("word/document.xml", document)


def _run(path: Path) -> str:
    result = subprocess.run(
        [sys.executable, str(SCRIPTS / "extract_resume_text.py"), str(path)],
        capture_output=True,
        check=True,
    )
    return result.stdout.decode("utf-8")


def test_extracts_paragraphs_and_tables(tmp_path):
    docx = tmp_path / "resume.docx"
    _make_docx(
        docx,
        "<w:p><w:r><w:t>张三 机械工程</w:t></w:r></w:p>"
        "<w:tbl><w:tr>"
        "<w:tc><w:p><w:r><w:t>项目：基于 STM32 的伺服驱动板</w:t></w:r></w:p></w:tc>"
        "<w:tc><w:p><w:r><w:t>技能：C、FreeRTOS</w:t></w:r></w:p></w:tc>"
        "</w:tr></w:tbl>",
    )
    text = _run(docx)
    assert "张三 机械工程" in text
    assert "基于 STM32 的伺服驱动板" in text
    assert "技能：C、FreeRTOS" in text


def test_extracts_plain_text_resume(tmp_path):
    resume = tmp_path / "resume.md"
    resume.write_text("# 李四\n\n项目：RAG 问答系统\n", encoding="utf-8")
    assert "RAG 问答系统" in _run(resume)