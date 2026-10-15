import json

import normalize_jobs as nj


def test_role_family_prefers_specific_direction():
    cases = {
        "大模型算法工程师（NLP）": "llm_app",
        "大模型应用开发实习生": "llm_app",
        "Agent 开发工程师": "agent_development",
        "具身智能算法工程师": "embodied_ai",
        "运动控制算法工程师": "motion_control",
        "数字IC验证工程师": "ic_design",
        "嵌入式硬件工程师": "embedded_hardware",
        "嵌入式软件工程师（C/C++）": "embedded_software",
        "计算机视觉算法工程师": "computer_vision",
        "游戏客户端开发（Unity）": "game_development",
        "数据平台开发（Hadoop）": "data_engineering",
        "前端开发实习生（React）": "frontend",
        "后端开发（Go）": "backend",
        "全栈开发工程师": "fullstack",
    }
    for title, expected in cases.items():
        assert nj.infer_role_family(title, "") == expected, title


def test_title_beats_body_text():
    # 正文提到大模型，不代表岗位方向是大模型
    assert nj.infer_role_family("后端开发工程师（大模型平台）", "负责大模型推理服务接入") == "backend"


def test_keyword_matching_respects_word_boundaries():
    assert nj.keyword_hit("go", nj._compact("django google mongodb")) is False
    assert nj.keyword_hit("go", nj._compact("Go 语言后端开发")) is True
    assert nj.keyword_hit("java", nj._compact("javascript typescript")) is False
    assert nj.keyword_hit("c++", nj._compact("熟悉 C/C++ 与 Linux")) is True


def test_strip_tracking_params():
    url = "https://jobs.example.com/apply/1?utm_source=x&spm=a.b&jobId=7&token=abc"
    assert nj.strip_tracking(url) == "https://jobs.example.com/apply/1?jobId=7"


def test_normalize_locations_and_display_defaults():
    assert nj.normalize_locations("北京、上海 / 深圳") == ["北京", "上海", "深圳"]
    assert nj.normalize_locations(None) == ["未注明"]


def test_dedupe_by_company_family_city_and_url():
    records = [
        nj.normalize_record({"company_name": "字节跳动", "role_title": "AI应用开发实习生", "locations": ["北京"], "apply_url": "https://a/1"}, "2026-10-15"),
        # 同公司同岗位族同招聘类型且城市重叠 -> 重复
        nj.normalize_record({"company_name": "字节", "role_title": "AI应用开发实习生", "locations": ["北京"], "apply_url": "https://a/2"}, "2026-10-15"),
        # 不同城市 -> 不算重复
        nj.normalize_record({"company_name": "字节", "role_title": "AI应用开发实习生", "locations": ["上海"], "apply_url": "https://a/3"}, "2026-10-15"),
        # 相同链接 -> 重复
        nj.normalize_record({"company_name": "美团", "role_title": "后端开发", "locations": ["北京"], "apply_url": "https://a/1"}, "2026-10-15"),
    ]
    kept = nj.dedupe(records)
    assert [r["apply_url"] for r in kept] == ["https://a/1", "https://a/3"]
    assert kept[0]["company_name"] == "字节跳动"


def test_markdown_replaces_empty_values_with_placeholder():
    record = nj.normalize_record({"company_name": "某公司", "role_title": "后端开发", "locations": ["北京"]}, "2026-10-15")
    table = nj.to_markdown([record])
    assert "not_specified" not in table
    assert "未注明" in table
    assert "状态不明" in table


def test_unverified_lead_from_source_level_c():
    record = nj.normalize_record({"company_name": "某公司", "role_title": "嵌入式软件", "source_level": "C"}, "2026-10-15")
    assert nj.source_status(record) == "未核验线索"


def test_normalized_record_matches_schema_shape():
    import pathlib

    schema_path = pathlib.Path(nj.__file__).resolve().parent.parent / "references" / "job-record.schema.json"
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    allowed = set(schema["properties"])
    required = set(schema["required"])
    record = nj.normalize_record({"company_name": "腾讯", "role_title": "大模型应用开发", "locations": ["深圳"]}, "2026-10-15")
    assert set(record) <= allowed
    assert required <= set(record)
    assert record["role_family"] in schema["properties"]["role_family"]["enum"]
    assert record["recruiting_type"] in schema["properties"]["recruiting_type"]["enum"]
