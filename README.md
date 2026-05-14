# 校招.skill

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Language](https://img.shields.io/badge/Language-中文%20%7C%20English-green.svg)](README.en.md)
[![Codex Skill](https://img.shields.io/badge/Codex-Skill-2563EB.svg)](SKILL.md)

面向中国技术岗校招、实习和大厂求职的 Codex Skill。它把岗位检索、信息核验、JD 分析、岗位匹配、简历诊断、简历改写、面试准备和投递策略整理成一套可复用、可开源协作的工作流。

English documentation: [README.en.md](README.en.md)

## 目录

- [项目定位](#项目定位)
- [核心能力](#核心能力)
- [适用场景](#适用场景)
- [安装方式](#安装方式)
- [快速开始](#快速开始)
- [项目结构](#项目结构)
- [模块说明](#模块说明)
- [脚本工具](#脚本工具)
- [信息源策略](#信息源策略)
- [安全与边界](#安全与边界)
- [开发与校验](#开发与校验)
- [贡献指南](#贡献指南)
- [路线图](#路线图)
- [常见问题](#常见问题)
- [开源协议](#开源协议)

## 项目定位

`校招.skill` 不是一个岗位数据库，也不是一个“包过”求职工具。它是一套给 AI Agent 使用的校招求职操作手册：

- 面向中国技术岗校招和实习；
- 强调官方来源核验和事实边界；
- 将复杂任务拆成可维护的模块；
- 用脚本处理重复、结构化、容易出错的部分；
- 帮助用户形成可执行的投递、简历和面试准备方案。

## 核心能力

- **当前岗位检索**：按公司、岗位、毕业年份、城市、招聘批次检索当前可投岗位。
- **信息源核验**：优先使用公司官网、校园招聘站、官方招聘公众号和官方 ATS 页面。
- **JD 分析**：拆解岗位职责、硬性要求、加分项、技术关键词和潜在面试追问。
- **岗位匹配**：基于候选人的年级、技能、项目、实习、城市和时间窗口制定投递优先级。
- **简历诊断**：按 `P0` 到 `P3` 标注硬伤、强影响问题、中影响问题和细节优化项。
- **简历改写**：在不编造事实的前提下，提高项目经历和技术表达的匹配度。
- **面试准备**：生成技术面、HR 面、项目追问链路和模拟面试问题。
- **结构化输出**：提供可复制到表格、文档或知识库的稳定输出模板。

## 适用场景

适合处理：

- 校招、春招、秋招、提前批、暑期实习、日常实习、转正实习；
- 互联网大厂、AI 公司、云厂商、智能硬件、新能源、游戏、SaaS、金融科技等公司；
- 前端、后端、客户端、全栈、AI 应用、大模型应用、算法、数据、测试开发、SRE、安全、游戏开发、嵌入式等技术岗；
- 岗位清单整理、公司招聘流程查询、JD 拆解、岗位选择、投递排序、简历 review、模拟面试。

默认不处理泛社招、海外岗位、公务员、国企、银行、留学申请、保研和考研规划。确有需要时可以复用方法论，但要明确说明适用边界。

## 安装方式

前置要求：

- 已安装并配置支持 Skills 的 Codex 环境；
- Python 3.10+，用于运行 `scripts/` 中的辅助脚本；
- 如果要查询最新岗位，需要可用的联网搜索能力。

安装到本地 Codex Skills 目录：

```bash
mkdir -p ~/.codex/skills
git clone <your-github-repo-url> ~/.codex/skills/xiaozhao-skill
```

如果你从本地目录开发，可以直接保留本项目结构：

```text
~/.codex/skills/xiaozhao-skill/
├── SKILL.md
├── references/
├── scripts/
└── agents/
```

安装后可在对话中使用：

```text
使用 $校招.skill 帮我找现在可以投的 AI 应用开发实习。
```

## 快速开始

### 1. 查找当前可投岗位

```text
使用 $校招.skill 帮我整理 2027 届可以投的 AI 应用开发实习，优先北京、上海、杭州。
```

期望输出：

```text
更新时间 | 公司名称 | 招聘岗位 | 招聘对象 | 工作地点 | 投递截止时间 | 投递链接 | 来源状态
```

### 2. 分析 JD

```text
使用 $校招.skill 分析下面这个大模型应用开发实习 JD，告诉我简历应该突出什么，面试可能追问什么。
```

### 3. 做岗位匹配

```text
我是 2027 届本科，做过 RAG 问答系统和 React 管理后台，有一段小厂前端实习，适合投哪些大厂技术岗？
```

### 4. 简历诊断和改写

```text
使用 $校招.skill 按 AI 应用开发实习方向 review 我的项目经历，指出 P0-P3 问题，并给出不编造事实的改写版本。
```

### 5. 模拟面试

```text
使用 $校招.skill 给我做一次字节 AI 应用开发实习技术面模拟面试，一次只问一个问题。
```

## 项目结构

```text
.
├── SKILL.md
├── README.md
├── README.en.md
├── LICENSE
├── agents/
│   └── openai.yaml
├── references/
│   ├── source-system.md
│   ├── company-watchlist.md
│   ├── candidate-strategy.md
│   ├── jd-analysis.md
│   ├── resume.md
│   ├── interview.md
│   ├── output-formats.md
│   └── job-record.schema.json
└── scripts/
    ├── normalize_jobs.py
    ├── score_match.py
    └── extract_resume_text.py
```

## 模块说明

| 路径 | 作用 |
| --- | --- |
| `SKILL.md` | Skill 入口，包含触发场景、核心原则、任务路由和模块索引。 |
| `agents/openai.yaml` | Skill 在界面中的展示名称、简介和默认提示词。 |
| `references/source-system.md` | 信息源分级、时效性核验、岗位字段、去重规则和来源状态。 |
| `references/company-watchlist.md` | 首版公司池、行业分层和优先岗位范围。 |
| `references/candidate-strategy.md` | 候选人画像、岗位匹配、投递排序和短期行动计划。 |
| `references/jd-analysis.md` | JD 拆解、硬性要求、加分项、关键词和隐含能力推断。 |
| `references/resume.md` | 简历诊断、真实性约束、项目经历改写和不同岗位表达重点。 |
| `references/interview.md` | 技术面、HR 面、项目追问链路和模拟面试流程。 |
| `references/output-formats.md` | 岗位表、JD 分析、简历诊断、面试准备等输出模板。 |
| `references/job-record.schema.json` | 岗位记录 JSON Schema。 |
| `scripts/normalize_jobs.py` | 标准化岗位记录，输出 JSON 或 Markdown 表格。 |
| `scripts/score_match.py` | 对候选人与岗位做轻量匹配评分。 |
| `scripts/extract_resume_text.py` | 从 `.txt`、`.md`、`.docx` 简历中提取纯文本。 |

## 脚本工具

### 标准化岗位记录

```bash
python3 scripts/normalize_jobs.py jobs.json
```

输入示例：

```json
[
  {
    "公司名称": "字节",
    "招聘岗位": "AI 应用开发实习生",
    "招聘对象": "27届实习",
    "工作地点": "北京、上海",
    "投递链接": "https://example.com/job?utm_source=test",
    "source_level": "S",
    "status": "active"
  }
]
```

输出 Markdown 表格；如果需要 JSON：

```bash
python3 scripts/normalize_jobs.py jobs.json --json
```

### 候选人与岗位匹配评分

```bash
python3 scripts/score_match.py match.json
```

输入结构：

```json
{
  "candidate": {
    "year": "2027",
    "degree": "本科",
    "major": "软件工程",
    "skills": ["Python", "React", "RAG", "Agent"],
    "projects": ["RAG 知识库问答系统"],
    "internships": ["前端开发实习"],
    "cities": ["北京", "上海"]
  },
  "job": {
    "role_family": "ai_app",
    "target_graduation": "2027",
    "requirements": "熟悉 Python、LLM、RAG、Agent，有工程落地经验",
    "locations": ["北京"]
  }
}
```

### 提取简历文本

```bash
python3 scripts/extract_resume_text.py resume.docx
```

支持 `.txt`、`.md`、`.docx`。该脚本不依赖第三方包。

## 信息源策略

岗位、截止时间、投递链接和招聘流程必须优先核验：

1. 公司招聘官网；
2. 公司校园招聘或实习招聘页；
3. 官方招聘公众号或官方公告；
4. 官方 ATS 页面，例如 Moka、北森、Hotjob 等；
5. 搜索引擎定向查询；
6. 聚合平台和社区线索；
7. 回到官方或近官方来源复核。

来源状态使用：

```text
官方已核验
近官方已核验
状态不明
未核验线索
已过期
```

聚合平台信息不能直接混入已核验主表。如果无法找到官方来源，应单独标为 `未核验线索`。

## 安全与边界

本项目坚持以下边界：

- 不编造岗位、截止时间、投递链接、内推码、录用概率或简历事实；
- 不承诺“稳进”“必过”“保底”；
- 不提供笔试、在线测评、实时面试作弊协助；
- 不把个人经验、社区传闻包装成官方规则；
- 不建议用户伪造项目、夸大职责或虚构指标；
- 对不确定信息明确标注 `需要核验`、`状态不明` 或 `需要你确认`。

## 开发与校验

基础校验：

```bash
python3 -m py_compile scripts/normalize_jobs.py scripts/score_match.py scripts/extract_resume_text.py
python3 -m json.tool references/job-record.schema.json >/dev/null
```

运行样例：

```bash
printf '%s\n' '[{"公司名称":"字节","招聘岗位":"AI 应用开发实习生","招聘对象":"27届实习","工作地点":"北京、上海","投递链接":"https://example.com/job?utm_source=x","source_level":"S","status":"active"}]' \
  | python3 scripts/normalize_jobs.py --verified-at 2026-05-14
```

维护建议：

- `SKILL.md` 只放核心原则和任务路由；
- 详细规则放到 `references/`；
- 稳定、重复、结构化的处理放到 `scripts/`；
- 新增模块时同步更新 `README.md`、`README.en.md` 和 `SKILL.md` 的模块索引；
- 不要在仓库中提交真实简历、个人隐私、私有内推码或未授权招聘资料。

## 贡献指南

欢迎提交 Issue 和 Pull Request，尤其是以下方向：

- 新增公司池和官方招聘入口；
- 改进信息源核验规则；
- 补充岗位族和技能画像；
- 优化 JD 分析、简历诊断、面试追问模板；
- 增加脚本测试用例；
- 修复过期链接、错误公司别名或不准确的岗位分类；
- 改进英文文档和跨语言一致性。

提交 PR 前建议：

1. 说明你修改的是哪个模块。
2. 如果新增规则，给出一个真实但不含隐私的使用场景。
3. 如果改动脚本，附上输入输出样例。
4. 确认不会引入作弊、伪造经历或误导性求职建议。

## 路线图

- [ ] 增加更多公司官方招聘入口索引。
- [ ] 为 `normalize_jobs.py` 增加单元测试。
- [ ] 为常见岗位族补充更细的技能画像。
- [ ] 增加中英文文档一致性检查。
- [ ] 增加可选的岗位数据样例目录。
- [ ] 增加更多简历项目改写样例。

## 常见问题

### 这个项目会自动爬取岗位吗？

不会。它提供信息源策略、字段规范和辅助脚本。真正查询当前岗位时，AI Agent 仍需要按任务联网核验。

### 为什么不直接相信牛客、实习僧或社区表格？

这些平台适合发现线索，但经常存在过期、转述、链接失效或口径不清的问题。正式输出当前岗位时，应优先回到官方或近官方来源。

### 简历改写会不会帮我包装经历？

会优化表达，但不会编造事实。缺少指标或结果时，应该使用 `[真实指标]`、`[请确认]` 等占位，并让用户确认。

### 可以用于非技术岗吗？

可以临时复用部分方法，但本项目的岗位画像、简历判断和面试准备主要面向技术岗。

### Skill 名称为什么是中文？

本项目面向中文校招场景，展示名和触发名使用 `校招.skill`。如果你的运行环境不支持中文 Skill 名称，可以在 fork 中将 `SKILL.md` 和 `agents/openai.yaml` 同步改为英文或拼音名称。

## 开源协议

本项目使用 MIT License，详见 [LICENSE](LICENSE)。
