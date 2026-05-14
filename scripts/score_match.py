#!/usr/bin/env python3
"""候选人与岗位的轻量匹配评分工具。

输入 JSON：
{
  "candidate": {"year": "...", "degree": "...", "major": "...", "skills": [], "projects": [], "internships": [], "cities": []},
  "job": {"role_family": "frontend", "target_graduation": "...", "requirements": "...", "locations": []}
}
"""

from __future__ import annotations

import argparse
import json
import sys
from typing import Any


ROLE_SKILLS = {
    "frontend": ["javascript", "typescript", "react", "vue", "html", "css", "小程序", "工程化", "性能优化", "组件"],
    "backend": ["java", "go", "golang", "python", "c++", "mysql", "redis", "消息队列", "分布式"],
    "client": ["android", "ios", "flutter", "kotlin", "swift", "性能优化"],
    "fullstack": ["javascript", "typescript", "react", "vue", "node", "python", "java", "数据库"],
    "ai_app": ["python", "llm", "rag", "agent", "向量数据库", "prompt", "langchain", "后端", "前端"],
    "llm_app": ["python", "llm", "rag", "agent", "prompt", "工具调用", "评估"],
    "algorithm": ["机器学习", "深度学习", "pytorch", "tensorflow", "论文", "竞赛", "算法"],
    "machine_learning": ["机器学习", "深度学习", "pytorch", "tensorflow", "训练", "评估"],
    "data_engineering": ["sql", "spark", "flink", "数仓", "etl", "hive"],
    "data_analysis": ["sql", "python", "数据分析", "指标", "实验"],
    "test_development": ["自动化测试", "接口测试", "pytest", "质量平台", "ci"],
    "sre": ["linux", "kubernetes", "docker", "监控", "devops", "网络"],
    "security": ["web安全", "漏洞", "攻防", "安全工具"],
}


def text_blob(value: Any) -> str:
    if isinstance(value, list):
        return " ".join(text_blob(item) for item in value)
    if isinstance(value, dict):
        return " ".join(text_blob(item) for item in value.values())
    return str(value or "")


def score_skill(candidate: dict[str, Any], job: dict[str, Any]) -> tuple[int, str]:
    role = job.get("role_family", "other_technical")
    required = ROLE_SKILLS.get(role, [])
    candidate_text = text_blob(candidate).lower()
    matched = [skill for skill in required if skill.lower() in candidate_text]
    if not required:
        return 1, "岗位族缺少内置技能画像，只能弱判断。"
    ratio = len(matched) / len(required)
    if ratio >= 0.5 or len(matched) >= 4:
        return 3, f"命中关键技能：{'、'.join(matched[:8])}"
    if ratio >= 0.25 or len(matched) >= 2:
        return 2, f"部分命中关键技能：{'、'.join(matched[:8])}"
    if matched:
        return 1, f"只命中少量技能：{'、'.join(matched[:5])}"
    return 0, "未看到目标岗位核心技能证据。"


def score_location(candidate: dict[str, Any], job: dict[str, Any]) -> tuple[int, str]:
    candidate_cities = set(candidate.get("cities") or candidate.get("locations") or [])
    job_cities = set(job.get("locations") or [])
    if not candidate_cities:
        return 1, "候选人未提供城市偏好。"
    if "全国" in job_cities or "远程" in job_cities:
        return 3, "岗位地点为全国或远程。"
    overlap = candidate_cities & job_cities
    if overlap:
        return 3, f"城市匹配：{'、'.join(sorted(overlap))}"
    return 1, "城市偏好和岗位地点未匹配。"


def score_project(candidate: dict[str, Any], job: dict[str, Any]) -> tuple[int, str]:
    role = job.get("role_family", "other_technical")
    projects_text = text_blob(candidate.get("projects", [])).lower()
    signals = ROLE_SKILLS.get(role, [])
    matched = [signal for signal in signals if signal.lower() in projects_text]
    if len(matched) >= 4:
        return 3, f"项目能体现岗位相关能力：{'、'.join(matched[:8])}"
    if len(matched) >= 2:
        return 2, f"项目有部分相关证据：{'、'.join(matched[:6])}"
    if projects_text.strip():
        return 1, "有项目经历，但与目标岗位的直接证据偏少。"
    return 0, "未提供项目经历。"


def score_internship(candidate: dict[str, Any]) -> tuple[int, str]:
    internships = candidate.get("internships") or []
    if not internships:
        return 1, "未提供实习经历，需要用项目补强。"
    text = text_blob(internships)
    if any(word in text for word in ["腾讯", "阿里", "字节", "美团", "百度", "华为", "大厂"]):
        return 3, "有大厂或强相关实习经历。"
    return 2, "有实习经历，可作为工程证据。"


def score_bonus(candidate: dict[str, Any], job: dict[str, Any]) -> tuple[int, str]:
    text = text_blob(candidate)
    role = job.get("role_family", "")
    bonus_words = ["开源", "论文", "竞赛", "获奖", "专利", "线上", "用户", "性能", "指标"]
    matched = [word for word in bonus_words if word in text]
    if role in {"algorithm", "machine_learning"} and any(word in text for word in ["论文", "竞赛", "科研"]):
        return 3, "算法/机器学习方向有论文、竞赛或科研加分项。"
    if len(matched) >= 3:
        return 3, f"存在多项竞争力信号：{'、'.join(matched)}"
    if matched:
        return 2, f"存在部分加分信号：{'、'.join(matched)}"
    return 1, "暂未看到明显加分项。"


def score_match(candidate: dict[str, Any], job: dict[str, Any]) -> dict[str, Any]:
    dimensions = {
        "基础资格匹配": (2, "需要结合招聘对象和年级进一步人工确认。"),
        "岗位技能匹配": score_skill(candidate, job),
        "项目相关度": score_project(candidate, job),
        "实习/工程经历": score_internship(candidate),
        "竞争力加分项": score_bonus(candidate, job),
        "城市与投递约束": score_location(candidate, job),
        "准备成本与时间窗口": (2, "默认准备成本中等；需要结合截止时间和当前准备情况确认。"),
    }
    total = sum(score for score, _ in dimensions.values())
    if total >= 17:
        layer = "主投"
    elif total >= 12:
        layer = "冲刺"
    else:
        layer = "低优先级"
    return {
        "recommendation": layer,
        "total_score_for_reference": total,
        "dimensions": {name: {"score": score, "reason": reason} for name, (score, reason) in dimensions.items()},
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("path", nargs="?")
    args = parser.parse_args()
    data = sys.stdin.read() if not args.path else open(args.path, encoding="utf-8").read()
    payload = json.loads(data)
    result = score_match(payload.get("candidate", {}), payload.get("job", {}))
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
