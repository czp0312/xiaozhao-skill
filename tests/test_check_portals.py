from pathlib import Path

import check_portals as cp


SAMPLE = """
# 官方招聘入口索引

### 互联网与平台

| 公司 | 官方招聘入口 | 说明 |
| --- | --- | --- |
| 腾讯 | https://join.qq.com/ | 官方招聘/校招入口 |

### 待人工确认

| 公司 | 候选入口 | 为什么未确认 |
| --- | --- | --- |
| 微博 | https://careers.weibo.com/ | 本机网络无法连接 |
"""


def test_parse_entries_reads_sections_and_urls(tmp_path):
    path = tmp_path / "portals.md"
    path.write_text(SAMPLE, encoding="utf-8")
    entries = cp.parse_entries(path)
    assert [e["company"] for e in entries] == ["腾讯", "微博"]
    assert entries[0]["url"] == "https://join.qq.com/"
    assert entries[0]["section"] == "互联网与平台"
    assert entries[1]["section"] == "待人工确认"


def test_real_index_has_no_duplicate_urls():
    index = Path(__file__).resolve().parent.parent / "references" / "company-portals.md"
    entries = cp.parse_entries(index)
    assert len(entries) > 100
    urls = [e["url"] for e in entries]
    assert len(urls) == len(set(urls))


def test_index_companies_are_unique():
    index = Path(__file__).resolve().parent.parent / "references" / "company-portals.md"
    entries = cp.parse_entries(index)
    verified = [e["company"] for e in entries if "待人工确认" not in e["section"]]
    assert len(verified) == len(set(verified))