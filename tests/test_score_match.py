import score_match as sm


CANDIDATE = {
    "year": "2027届",
    "skills": ["Python", "RAG", "LLM"],
    "projects": ["RAG 问答系统，接入 Agent 工具调用"],
    "internships": [],
    "cities": ["北京"],
}


def test_no_false_positive_for_short_ascii_keyword():
    candidate = {"skills": ["Django", "Google Analytics", "MongoDB"], "projects": ["Django 后台系统"], "cities": ["北京"]}
    result = sm.score_match(candidate, {"role_family": "backend", "locations": ["北京"]})
    reason = result["dimensions"]["岗位技能匹配"]["reason"]
    assert "go" not in reason.split("：")[-1].split("、")


def test_all_role_families_have_profiles():
    families = [
        "frontend", "backend", "client", "fullstack", "ai_app", "llm_app", "agent_development",
        "algorithm", "machine_learning", "computer_vision", "embodied_ai", "motion_control",
        "embedded_software", "embedded_hardware", "ic_design", "data_engineering", "data_analysis",
        "test_development", "sre", "security", "game_development", "graphics",
    ]
    for family in families:
        result = sm.score_match(CANDIDATE, {"role_family": family, "locations": ["北京"]})
        assert result["profile_missing"] is False, family
        assert result["dimensions"]["岗位技能匹配"]["reason"] != "岗位族缺少内置技能画像，只能弱判断。"


def test_unknown_family_reports_profile_missing():
    result = sm.score_match(CANDIDATE, {"role_family": "unknown_family", "locations": ["北京"]})
    assert result["profile_missing"] is True
    assert result["recommendation"] == "需要人工判断"
    assert "note" in result


def test_graduation_year_mismatch_is_flagged():
    result = sm.score_match({"year": "2026届", "cities": ["北京"]}, {"role_family": "backend", "target_graduation": "2027届", "locations": ["北京"]})
    assert result["dimensions"]["基础资格匹配"]["score"] == 1

    matched = sm.score_match({"year": "2027届", "cities": ["北京"]}, {"role_family": "backend", "target_graduation": "27届实习", "locations": ["北京"]})
    assert matched["dimensions"]["基础资格匹配"]["score"] == 3


def test_embedded_profile_scores_mechanical_background_candidate():
    candidate = {
        "year": "2027届",
        "skills": ["C语言", "STM32", "FreeRTOS", "CAN通信", "PID 调试"],
        "projects": ["基于 STM32 的伺服驱动控制板，负责固件与驱动开发"],
        "cities": ["深圳"],
    }
    result = sm.score_match(candidate, {"role_family": "embedded_software", "locations": ["深圳"]})
    assert result["dimensions"]["岗位技能匹配"]["score"] == 3
    # 无实习经历时基础分被拉低，属于冲刺而非主投，但不应该掉到低优先级
    assert result["recommendation"] == "冲刺"
