#!/usr/bin/env python3
"""候选人与岗位的轻量匹配评分工具。

输入 JSON：
{
  "candidate": {"year": "...", "degree": "...", "major": "...", "skills": [], "projects": [], "internships": [], "cities": []},
  "job": {"role_family": "backend", "target_graduation": "...", "requirements": "...", "locations": []}
}

输出为 7 个维度的评分和证据说明。评分只用于组织判断，最终结论必须由证据解释决定。
岗位族缺少内置技能画像时，返回 profile_missing=true，不要用总分代替判断。
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from typing import Any

ROLE_SKILLS: dict[str, list[str]] = {
    "frontend": ["javascript", "typescript", "react", "vue", "html", "css", "小程序", "工程化", "性能优化", "组件"],
    "backend": ["java", "go", "golang", "python", "c++", "mysql", "redis", "消息队列", "分布式", "微服务"],
    "client": ["android", "ios", "flutter", "kotlin", "swift", "性能优化", "移动端"],
    "fullstack": ["javascript", "typescript", "react", "vue", "node", "python", "java", "数据库"],
    "ai_app": ["python", "llm", "rag", "agent", "向量数据库", "prompt", "langchain", "后端", "前端"],
    "llm_app": ["python", "llm", "rag", "agent", "prompt", "工具调用", "评估", "微调", "大模型"],
    "agent_development": ["agent", "智能体", "工具调用", "mcp", "prompt", "编排", "多智能体", "python"],
    "algorithm": ["机器学习", "深度学习", "pytorch", "tensorflow", "论文", "竞赛", "算法", "推荐"],
    "machine_learning": ["机器学习", "深度学习", "pytorch", "tensorflow", "训练", "评估", "特征工程"],
    "computer_vision": ["opencv", "目标检测", "图像处理", "图像算法", "分割", "视觉", "slam", "点云", "pytorch"],
    "embodied_ai": ["具身智能", "机器人", "强化学习", "ros", "运动规划", "抓取", "vla", "仿真", "python", "c++"],
    "motion_control": ["运动控制", "伺服", "电机", "pid", "控制算法", "matlab", "simulink", "plc", "轨迹规划", "嵌入式"],
    "embedded_software": ["c语言", "c++", "单片机", "stm32", "rtos", "freertos", "驱动", "固件", "linux", "i2c", "spi", "can通信"],
    "embedded_hardware": ["电路", "pcb", "原理图", "altium", "cadence", "电源", "emc", "信号完整性", "硬件", "调试"],
    "ic_design": ["verilog", "systemverilog", "uvm", "rtl", "数字ic", "fpga", "验证", "时序", "综合", "tcl"],
    "data_engineering": ["sql", "spark", "flink", "数仓", "etl", "hive", "数据仓库", "数据平台"],
    "data_analysis": ["sql", "python", "数据分析", "指标", "实验", "可视化"],
    "test_development": ["自动化测试", "接口测试", "pytest", "质量平台", "ci", "测试开发"],
    "sre": ["linux", "kubernetes", "docker", "监控", "devops", "网络", "稳定性"],
    "security": ["web安全", "漏洞", "攻防", "安全工具", "渗透", "逆向"],
    "game_development": ["unity", "unreal", "虚幻", "游戏引擎", "c#", "游戏客户端", "图形"],
    "graphics": ["图形", "渲染", "opengl", "vulkan", "shader", "引擎"],
    "other_technical": ["编程", "开发", "项目", "实习"],
    "non_technical": ["沟通", "运营", "产品", "协作"],
}

BIG_TECH = ["腾讯", "阿里", "字节", "美团", "百度", "华为", "快手", "京东", "网易", "小米", "大疆", "蚂蚁"]
BONUS_WORDS = ["开源", "论文", "竞赛", "获奖", "专利", "线上", "用户", "性能", "指标", "专利"]


def _configure_utf8_stdio() -> None:
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


def text_blob(value: Any) -> str:
    if isinstance(value, list):
        return " ".join(text_blob(item) for item in value)
    if isinstance(value, dict):
        return " ".join(text_blob(item) for item in value.values())
    return str(value or "")


def matched_skills(skills: list[str], text: str) -> list[str]:
    compact = _compact(text)
    return [skill for skill in skills if keyword_hit(skill, compact)]


def _grad_year(value: Any) -> int | None:
    text = str(value or "")
    full = re.search(r"(20\d{2})", text)
    if full:
        return int(full.group(1))
    short = re.search(r"(\d{2})\s*届", text)
    if short:
        return 2000 + int(short.group(1))
    return None


def score_qualification(candidate: dict[str, Any], job: dict[str, Any]) -> tuple[int, str]:
    candidate_year = _grad_year(candidate.get("year") or candidate.get("graduation_year"))
    job_year = _grad_year(job.get("target_graduation") or job.get("招聘对象"))
    if candidate_year and job_year:
        if candidate_year == job_year:
            return 3, f"毕业年份匹配：{candidate_year} 届。"
        return 1, f"毕业年份不匹配：候选人 {candidate_year} 届，岗位面向 {job_year} 届。"
    if candidate_year or job_year:
        return 2, "只拿到一侧毕业年份，需要人工确认招聘对象是否覆盖。"
    return 2, "未提供毕业年份，需要结合招聘对象和年级人工确认。"


def score_skill(candidate: dict[str, Any], job: dict[str, Any]) -> tuple[int, str]:
    role = job.get("role_family", "other_technical")
    required = ROLE_SKILLS.get(role, [])
    if not required:
        return 1, "岗位族缺少内置技能画像，只能弱判断。"
    matched = matched_skills(required, text_blob(candidate))
    ratio = len(matched) / len(required)
    if ratio >= 0.5 or len(matched) >= 4:
        return 3, f"命中关键技能：{'、'.join(matched[:8])}"
    if ratio >= 0.25 or len(matched) >= 2:
        return 2, f"部分命中关键技能：{'、'.join(matched[:8])}"
    if matched:
        return 1, f"只命中少量技能：{'、'.join(matched[:5])}"
    return 0, "未看到目标岗位核心技能证据。"


def score_location(candidate: dict[str, Any], job: dict[str, Any]) -> tuple[int, str]:
    candidate_cities = {str(c) for c in (candidate.get("cities") or candidate.get("locations") or [])}
    job_cities = {str(c) for c in (job.get("locations") or [])}
    if not candidate_cities:
        return 1, "候选人未提供城市偏好。"
    if job_cities & {"全国", "远程"}:
        return 3, "岗位地点为全国或远程。"
    overlap = candidate_cities & job_cities
    if overlap:
        return 3, f"城市匹配：{'、'.join(sorted(overlap))}"
    if not job_cities:
        return 2, "岗位未公开城市，需要核验。"
    return 1, "城市偏好和岗位地点未匹配。"


def score_project(candidate: dict[str, Any], job: dict[str, Any]) -> tuple[int, str]:
    role = job.get("role_family", "other_technical")
    projects_text = text_blob(candidate.get("projects", []))
    signals = ROLE_SKILLS.get(role, [])
    if not signals:
        return 1, "岗位族缺少内置技能画像，无法判断项目相关度。"
    matched = matched_skills(signals, projects_text)
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
    if any(word in text for word in BIG_TECH):
        return 3, "有大厂或强相关实习经历。"
    return 2, "有实习经历，可作为工程证据。"


def score_bonus(candidate: dict[str, Any], job: dict[str, Any]) -> tuple[int, str]:
    text = text_blob(candidate)
    role = job.get("role_family", "")
    matched = [word for word in BONUS_WORDS if word in text]
    if role in {"algorithm", "machine_learning", "computer_vision", "embodied_ai"} and any(
        word in text for word in ["论文", "竞赛", "科研"]
    ):
        return 3, "算法/研究类方向有论文、竞赛或科研加分项。"
    if len(matched) >= 3:
        return 3, f"存在多项竞争力信号：{'、'.join(matched)}"
    if matched:
        return 2, f"存在部分加分信号：{'、'.join(matched)}"
    return 1, "暂未看到明显加分项。"


def score_match(candidate: dict[str, Any], job: dict[str, Any]) -> dict[str, Any]:
    role = job.get("role_family", "other_technical")
    profile_missing = role not in ROLE_SKILLS
    dimensions = {
        "基础资格匹配": score_qualification(candidate, job),
        "岗位技能匹配": score_skill(candidate, job),
        "项目相关度": score_project(candidate, job),
        "实习/工程经历": score_internship(candidate),
        "竞争力加分项": score_bonus(candidate, job),
        "城市与投递约束": score_location(candidate, job),
        "准备成本与时间窗口": (2, "默认准备成本中等；需要结合截止时间和当前准备情况确认。"),
    }
    total = sum(score for score, _ in dimensions.values())
    if profile_missing:
        layer = "需要人工判断"
    elif total >= 17:
        layer = "主投"
    elif total >= 12:
        layer = "冲刺"
    else:
        layer = "低优先级"
    result: dict[str, Any] = {
        "recommendation": layer,
        "total_score_for_reference": total,
        "profile_missing": profile_missing,
        "dimensions": {name: {"score": score, "reason": reason} for name, (score, reason) in dimensions.items()},
    }
    if profile_missing:
        result["note"] = (
            f"岗位族 {role} 没有内置技能画像，技能与项目维度不可用，总分仅作参考，必须由人工或模型按 JD 证据判断。"
        )
    return result


def main() -> None:
    _configure_utf8_stdio()
    parser = argparse.ArgumentParser(description="候选人与岗位轻量匹配评分")
    parser.add_argument("path", nargs="?", help="JSON 文件路径，缺省从标准输入读取")
    args = parser.parse_args()
    data = sys.stdin.read() if not args.path else open(args.path, encoding="utf-8").read()
    payload = json.loads(data)
    result = score_match(payload.get("candidate", {}), payload.get("job", {}))
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()