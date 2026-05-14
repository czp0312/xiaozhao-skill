# Xiaozhao.skill

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Language](https://img.shields.io/badge/Language-English%20%7C%20中文-green.svg)](README.md)
[![Codex Skill](https://img.shields.io/badge/Codex-Skill-2563EB.svg)](SKILL.md)

A Codex Skill for China campus recruiting, internships, and technical job preparation. It turns job research, source verification, JD analysis, role matching, resume review, resume rewriting, interview preparation, and application strategy into a reusable open-source workflow.

中文文档: [README.md](README.md)

## Table Of Contents

- [Positioning](#positioning)
- [Core Capabilities](#core-capabilities)
- [Use Cases](#use-cases)
- [Installation](#installation)
- [Quick Start](#quick-start)
- [Project Structure](#project-structure)
- [Modules](#modules)
- [Scripts](#scripts)
- [Source Verification Policy](#source-verification-policy)
- [Safety Boundaries](#safety-boundaries)
- [Development And Validation](#development-and-validation)
- [Contributing](#contributing)
- [Roadmap](#roadmap)
- [FAQ](#faq)
- [License](#license)

## Positioning

`校招.skill` is not a job database, and it does not promise job offers. It is an operational guide for AI agents working on China campus recruiting tasks:

- focused on China technical campus roles and internships;
- designed around official-source verification and clear factual boundaries;
- split into maintainable modules;
- backed by scripts for repetitive and structured operations;
- intended to help users create actionable application, resume, and interview plans.

## Core Capabilities

- **Current opening research**: search active roles by company, role family, graduation year, city, and recruiting batch.
- **Source verification**: prioritize company career sites, campus portals, official recruiting accounts, and official ATS pages.
- **JD analysis**: extract responsibilities, hard requirements, nice-to-haves, technical keywords, and likely interview follow-ups.
- **Role matching**: prioritize applications based on year, skills, projects, internships, location constraints, and preparation window.
- **Resume diagnosis**: classify issues from `P0` to `P3`, from critical blockers to minor polish.
- **Resume rewriting**: improve role alignment without inventing facts.
- **Interview preparation**: prepare technical interviews, HR interviews, project follow-up chains, and mock interviews.
- **Structured outputs**: provide stable templates that can be copied into spreadsheets, documents, or knowledge bases.

## Use Cases

This Skill is designed for:

- campus recruiting, spring recruiting, fall recruiting, early batches, summer internships, daily internships, and conversion internships;
- internet platforms, AI companies, cloud vendors, smart hardware, new energy, gaming, SaaS, and fintech companies in China;
- frontend, backend, client, full-stack, AI application, LLM application, algorithm, data, test development, SRE, security, game development, and embedded software roles;
- job list research, company process lookup, JD breakdown, role selection, application ordering, resume review, and mock interviews.

It is not primarily designed for general experienced hiring, overseas roles, civil service exams, public-sector roles, banking-only recruiting, study abroad applications, graduate school recommendation, or postgraduate entrance exam planning. The workflow may be adapted, but the scope limit should be stated clearly.

## Installation

Requirements:

- a Codex environment with Skills support;
- Python 3.10+ for helper scripts in `scripts/`;
- internet access when researching latest openings.

Install into your local Codex Skills directory:

```bash
mkdir -p ~/.codex/skills
git clone <your-github-repo-url> ~/.codex/skills/xiaozhao-skill
```

For local development, keep this structure:

```text
~/.codex/skills/xiaozhao-skill/
├── SKILL.md
├── references/
├── scripts/
└── agents/
```

After installation, use it in a conversation:

```text
Use $校招.skill to find active AI application development internships I can apply to now.
```

## Quick Start

### 1. Find active openings

```text
Use $校招.skill to list 2027 AI application development internships, prioritizing Beijing, Shanghai, and Hangzhou.
```

Expected table header:

```text
更新时间 | 公司名称 | 招聘岗位 | 招聘对象 | 工作地点 | 投递截止时间 | 投递链接 | 来源状态
```

### 2. Analyze a JD

```text
Use $校招.skill to analyze this LLM application development intern JD. Tell me what my resume should emphasize and what interview follow-ups are likely.
```

### 3. Match a candidate to roles

```text
I graduate in 2027. I have built a RAG QA system and a React admin dashboard, and I have one frontend internship. Which technical internship roles should I prioritize?
```

### 4. Review and rewrite a resume

```text
Use $校招.skill to review my project experience for AI application development internships. Mark P0-P3 issues and rewrite it without inventing facts.
```

### 5. Run a mock interview

```text
Use $校招.skill to run a ByteDance AI application development intern technical mock interview. Ask one question at a time.
```

## Project Structure

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

## Modules

| Path | Purpose |
| --- | --- |
| `SKILL.md` | Skill entry point with trigger scope, principles, task routing, and module index. |
| `agents/openai.yaml` | Display name, short description, and default prompt for the UI. |
| `references/source-system.md` | Source levels, freshness checks, job fields, deduplication rules, and source status labels. |
| `references/company-watchlist.md` | Initial company watchlist, industry groups, and prioritized role families. |
| `references/candidate-strategy.md` | Candidate profiling, role matching, application ordering, and short-term action plans. |
| `references/jd-analysis.md` | JD breakdown, hard requirements, nice-to-haves, keywords, and inferred capabilities. |
| `references/resume.md` | Resume diagnosis, truthfulness constraints, project rewriting, and role-specific emphasis. |
| `references/interview.md` | Technical interviews, HR interviews, project follow-up chains, and mock interview flow. |
| `references/output-formats.md` | Output templates for openings, JD analysis, resume review, interview prep, and strategy. |
| `references/job-record.schema.json` | JSON Schema for normalized job records. |
| `scripts/normalize_jobs.py` | Normalize job records and output JSON or Markdown tables. |
| `scripts/score_match.py` | Lightweight candidate-job matching score. |
| `scripts/extract_resume_text.py` | Extract plain text from `.txt`, `.md`, and `.docx` resumes. |

## Scripts

### Normalize job records

```bash
python3 scripts/normalize_jobs.py jobs.json
```

Input example:

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

The default output is a Markdown table. To output JSON:

```bash
python3 scripts/normalize_jobs.py jobs.json --json
```

### Score candidate-job fit

```bash
python3 scripts/score_match.py match.json
```

Input shape:

```json
{
  "candidate": {
    "year": "2027",
    "degree": "Bachelor",
    "major": "Software Engineering",
    "skills": ["Python", "React", "RAG", "Agent"],
    "projects": ["RAG knowledge-base QA system"],
    "internships": ["Frontend development internship"],
    "cities": ["Beijing", "Shanghai"]
  },
  "job": {
    "role_family": "ai_app",
    "target_graduation": "2027",
    "requirements": "Python, LLM, RAG, Agent, and engineering implementation experience",
    "locations": ["Beijing"]
  }
}
```

### Extract resume text

```bash
python3 scripts/extract_resume_text.py resume.docx
```

Supported formats: `.txt`, `.md`, `.docx`. No third-party Python packages are required.

## Source Verification Policy

Openings, deadlines, application links, and hiring processes should be verified in this order:

1. company career site;
2. company campus or internship portal;
3. official recruiting account or announcement;
4. official ATS pages such as Moka, Beisen, or Hotjob;
5. targeted search engine queries;
6. aggregators and community leads;
7. back to official or near-official sources for confirmation.

Use these source status labels:

```text
官方已核验
近官方已核验
状态不明
未核验线索
已过期
```

Aggregator information should not be mixed into the verified openings table. If no official source is found, keep it separate as `未核验线索`.

## Safety Boundaries

This project follows these boundaries:

- Do not invent jobs, deadlines, application links, referral codes, offer chances, or resume facts.
- Do not promise guaranteed outcomes.
- Do not assist with cheating in written tests, online assessments, or live interviews.
- Do not present personal anecdotes or community rumors as official rules.
- Do not advise users to fake projects, inflate responsibilities, or fabricate metrics.
- Mark uncertain information as `需要核验`, `状态不明`, or `需要你确认`.

## Development And Validation

Basic checks:

```bash
python3 -m py_compile scripts/normalize_jobs.py scripts/score_match.py scripts/extract_resume_text.py
python3 -m json.tool references/job-record.schema.json >/dev/null
```

Run a sample:

```bash
printf '%s\n' '[{"公司名称":"字节","招聘岗位":"AI 应用开发实习生","招聘对象":"27届实习","工作地点":"北京、上海","投递链接":"https://example.com/job?utm_source=x","source_level":"S","status":"active"}]' \
  | python3 scripts/normalize_jobs.py --verified-at 2026-05-14
```

Maintenance guidelines:

- Keep `SKILL.md` focused on principles and task routing.
- Put detailed rules in `references/`.
- Put stable, repetitive, structured processing in `scripts/`.
- When adding a module, update `README.md`, `README.en.md`, and the module index in `SKILL.md`.
- Do not commit real resumes, personal data, private referral codes, or unauthorized recruiting material.

## Contributing

Issues and pull requests are welcome, especially for:

- adding official recruiting entry points;
- improving source verification rules;
- expanding role families and skill signals;
- improving JD analysis, resume diagnosis, and interview follow-up templates;
- adding script tests;
- fixing expired links, company aliases, or role classification errors;
- improving English documentation and bilingual consistency.

Before submitting a PR:

1. Explain which module you changed.
2. If you add a rule, include a realistic non-private use case.
3. If you change a script, include input and output examples.
4. Make sure the change does not introduce cheating, fake experience, or misleading career advice.

## Roadmap

- [ ] Add more official recruiting entry points.
- [ ] Add unit tests for `normalize_jobs.py`.
- [ ] Expand skill profiles for common role families.
- [ ] Add bilingual documentation consistency checks.
- [ ] Add optional sample job records.
- [ ] Add more resume project rewriting examples.

## FAQ

### Does this project automatically crawl jobs?

No. It provides source strategy, field standards, and helper scripts. When answering latest-opening questions, the AI agent still needs to verify current sources online.

### Why not trust Nowcoder, Shixiseng, or community spreadsheets directly?

They are useful for discovery, but they can be stale, second-hand, broken, or ambiguous. Current-opening outputs should prioritize official or near-official sources.

### Will it help me embellish my resume?

It improves wording, but it should not invent facts. Missing metrics or outcomes should be represented with placeholders such as `[真实指标]` or `[请确认]`.

### Can it be used for non-technical roles?

Parts of the workflow can be adapted, but the role profiles, resume criteria, and interview preparation logic are designed primarily for technical roles.

### Why is the Skill name Chinese?

The project targets Chinese campus recruiting, so the display and trigger name is `校招.skill`. If your runtime does not support Chinese Skill names, you can rename it in your fork by updating both `SKILL.md` and `agents/openai.yaml`.

## License

This project is licensed under the MIT License. See [LICENSE](LICENSE).
