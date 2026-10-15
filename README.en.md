# Xiaozhao.skill

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Language](https://img.shields.io/badge/Language-English%20%7C%20中文-green.svg)](README.md)
[![Codex Skill](https://img.shields.io/badge/Codex-Skill-2563EB.svg)](SKILL.md)

An AI Skill for China software engineering campus recruiting, internships, and big-tech job preparation. It turns official recruiting portal lookup, job research, source verification, JD analysis, role matching, application strategy, resume review, resume rewriting, interview preparation, and mock interviews into a reusable AI workflow.

Coverage goes beyond classic software roles: LLM, agent development, embodied AI, computer vision, embedded software and hardware, IC design, and motion control are all in scope. It also supports direction mapping for mechanical, automation, and electronics majors moving into software and hardware engineering roles.

中文文档: [README.md](README.md)

## Table Of Contents

- [Positioning](#positioning)
- [Core Capabilities](#core-capabilities)
- [Official Recruiting Portal Index](#official-recruiting-portal-index)
- [Use Cases](#use-cases)
- [Installation](#installation)
- [Usage Examples](#usage-examples)
- [Workflow Modules](#workflow-modules)
- [Repository Layout](#repository-layout)
- [Scripts And Tests](#scripts-and-tests)
- [Source Principles](#source-principles)
- [Safety Boundaries](#safety-boundaries)
- [Maintenance And Contribution](#maintenance-and-contribution)
- [Roadmap](#roadmap)
- [FAQ](#faq)
- [Origin And Credits](#origin-and-credits)
- [License](#license)

## Positioning

`校招.skill` is not a job database and does not promise job offers. It is an operational guide for AI tools, designed to make campus recruiting assistance for software engineering roles more reliable, verifiable, and actionable.

It is useful for:

- finding official recruiting portals for major tech companies instead of detouring through aggregators;
- verifying active openings from official or near-official sources;
- breaking down job descriptions and identifying real preparation priorities;
- matching candidates to roles and application priorities, including cross-major transitions into engineering roles;
- diagnosing resumes and improving wording without inventing facts;
- preparing technical interviews, HR interviews, project follow-ups, and mock interviews.

## Core Capabilities

| Capability | Description |
| --- | --- |
| Official portal index | 132 companies with verified official recruiting entry points, grouped by 15 industry segments with a verification date. |
| Current opening research | Organizes active opportunities by company, role, graduation year, city, and recruiting batch. |
| Source verification | Prioritizes company career sites, campus portals, official recruiting accounts, and official hiring systems. |
| JD analysis | Extracts responsibilities, hard requirements, nice-to-haves, technical keywords, and likely follow-ups. |
| Role matching | Ranks applications by year, skills, projects, internships, city constraints, and preparation window. |
| Cross-major transition | Direction mapping, skill gaps, and project suggestions for mechanical, automation, vehicle, and electronics backgrounds. |
| Resume diagnosis | Identifies blockers, major issues, medium-impact issues, and polish items by priority. |
| Resume rewriting | Improves truth-preserving expression around personal actions, technical solutions, tradeoffs, and results. |
| Interview preparation | Generates technical interview, HR interview, project follow-up, and mock interview flows. |
| Structured output | Produces stable tables, conclusions, rewrites, and action plans. |

## Official Recruiting Portal Index

`references/company-portals.md` lists official recruiting entry points for 132 companies across internet platforms, AI and LLM companies, computer vision and security, embodied AI and robotics, motion control and industrial automation, autonomous driving and smart vehicles, chips and computing, telecom and ICT, smart hardware and consumer electronics, gaming, enterprise services and cloud, cybersecurity, and fintech.

Every link was verified with a real HTTP request: the request succeeded and the landing page title or domain belongs to that company. Entries that redirect to an official ATS (Beisen, Feishu Hire, Moka) are labeled separately.

Portals expire, so the index carries its own freshness date and should be re-verified after each recruiting season. Batch re-check:

```bash
python scripts/check_portals.py
```

## Use Cases

Best suited for:

- campus recruiting, spring recruiting, fall recruiting, early batches, summer internships, daily internships, and conversion internships;
- internet platforms, AI companies, cloud vendors, smart hardware, new energy, gaming, SaaS, and fintech companies in China;
- frontend, backend, client, full-stack, AI application, LLM application, agent development, algorithm, computer vision, embodied AI, motion control, embedded software, embedded hardware, IC design, data, test development, SRE, security, and game development roles;
- mechanical, automation, vehicle, materials, and electronics majors moving into engineering roles;
- job list research, official portal lookup, company hiring process lookup, JD breakdown, role selection, application ordering, resume review, and mock interviews.

Not the default target:

- general experienced hiring, overseas roles, civil service exams, public-sector roles, banking-only recruiting, study abroad applications, graduate school recommendation, or postgraduate entrance exam planning;
- parts of the workflow may be adapted, but the scope limit should be stated clearly.

## Installation

This Skill is meant to be installed through natural language inside AI tools. Users do not need to run any code manually.

Recommended prompt for AI tools that support Skill installation:

> Install this Skill from the root of this GitHub repository: https://github.com/czp0312/xiaozhao-skill

If the AI tool asks for an installation location, choose the repository root. The repository root already contains the complete Skill entry file.

After installation, restart or refresh the AI tool so the new Skill can be loaded.

## Usage Examples

After installation, call the Skill with natural language:

> Use $xiaozhao-skill to find active embodied AI internships, prioritizing Beijing, Shanghai, and Shenzhen.

> Use $xiaozhao-skill to give me the official recruiting portals for DJI, Unitree, Inovance, and Horizon Robotics, and tell me which ones are still hiring.

> I major in mechanical engineering and built an STM32 servo drive project. Which engineering roles should I target?

> Use $xiaozhao-skill to analyze this agent development intern JD and tell me what my resume should emphasize and what the interview may ask.

> Use $xiaozhao-skill to review my project experience for computer vision internships. Mark P0 to P3 issues and rewrite it without inventing facts.

> Use $xiaozhao-skill to run an embedded software mock interview. Ask one question at a time.

## Workflow Modules

| Module | Purpose |
| --- | --- |
| Skill entry | Defines trigger scope, principles, supported tasks, and task routing. |
| Official portal index | Maintains official recruiting entry points by industry, with a verification date. |
| Source system | Defines official sources, near-official sources, lead sources, freshness checks, and deduplication rules. |
| Candidate strategy | Supports role matching, cross-major direction mapping, application ordering, and action planning. |
| JD analysis | Breaks down requirements, hard constraints, nice-to-haves, and inferred capabilities. |
| Resume module | Supports resume diagnosis, project rewriting, truthfulness constraints, and engineering-background translation. |
| Interview module | Supports technical interviews, HR interviews, project follow-ups, and mock interviews. |
| Output templates | Keeps job tables, analysis conclusions, review feedback, and action plans consistent. |

## Repository Layout

```text
xiaozhao-skill/
├── SKILL.md                      Skill entry: principles, scope, task routing
├── agents/openai.yaml            UI metadata and invocation policy
├── references/
│   ├── company-portals.md        Official recruiting portal index by industry
│   ├── source-system.md          Source tiers, freshness checks, fields, dedup rules
│   ├── candidate-strategy.md     Matching dimensions, cross-major mapping, application order
│   ├── jd-analysis.md            JD breakdown and role family judgement
│   ├── resume.md                 Resume diagnosis, rewriting, background translation
│   ├── interview.md              Technical, HR, project follow-ups, mock interviews
│   ├── output-formats.md         Reusable output templates
│   └── job-record.schema.json    Job record JSON Schema
├── scripts/
│   ├── check_portals.py          Batch re-check recruiting portal availability
│   ├── normalize_jobs.py         Normalize, dedupe, and render job records
│   ├── score_match.py            Lightweight candidate-to-role scoring
│   └── extract_resume_text.py    Extract text from .txt/.md/.docx resumes
└── tests/                        pytest cases
```

## Scripts And Tests

Scripts depend only on the Python standard library.

```bash
# Normalize, dedupe, and render job records as a Markdown table
python scripts/normalize_jobs.py jobs.json

# Emit normalized JSON instead
python scripts/normalize_jobs.py jobs.json --json

# Re-check the recruiting portal index
python scripts/check_portals.py

# Score a candidate against a role
python scripts/score_match.py match.json

# Extract resume text
python scripts/extract_resume_text.py resume.docx
```

Run the tests:

```bash
pip install -r requirements-dev.txt
python -m pytest tests
```

## Source Principles

Questions about "current", "latest", deadlines, application links, or whether a role is still open require freshness verification.

Source priority:

1. the verified official portal index in this repository;
2. company career site;
3. company campus or internship portal;
4. official recruiting account or announcement;
5. officially delegated hiring system;
6. targeted search engine queries;
7. aggregators and community leads;
8. back to official or near-official sources for verification.

Formal opening tables should only include verified information or clearly labeled uncertain information. Aggregators, screenshots, personal notes, and community spreadsheets should be treated as leads, not verified facts.

## Safety Boundaries

This project follows these boundaries:

- Do not invent jobs, deadlines, application links, referral codes, offer chances, or resume facts.
- Do not promise guaranteed outcomes.
- Do not assist with cheating in written tests, online assessments, or live interviews.
- Do not present personal experience or community rumors as official rules.
- Do not advise users to fake projects, inflate responsibilities, or fabricate metrics.
- Mark uncertain information as "needs verification", "status unknown", or "needs your confirmation".

## Maintenance And Contribution

Issues and pull requests are welcome, especially for:

- adding official recruiting entry points or fixing dead links;
- fixing company aliases or inaccurate role classification;
- improving source verification rules;
- expanding role families and skill signals;
- improving JD analysis, resume diagnosis, and interview follow-up templates;
- improving bilingual documentation consistency.

Maintaining the portal index:

1. Edit `references/company-portals.md` to add or replace an entry;
2. Run `python scripts/check_portals.py` to confirm the link works;
3. Run `python scripts/check_portals.py --update-date` to refresh the verification date;
4. Run `python -m pytest tests` to confirm the index format and script behavior still hold.

When contributing, please explain:

- which module changed;
- what real usage problem it solves;
- whether it depends on current recruiting information or external sources;
- whether it affects factual reliability, safety boundaries, or user privacy.

Do not submit real resumes, personal data, private referral codes, unauthorized recruiting material, or anything that helps cheating.

## Roadmap

- Keep expanding official recruiting portals, including smaller hardware and robotics companies.
- Expand role profiles for hardware-adjacent fields, especially embodied AI, motion control, and chips.
- Add more JD analysis and resume rewriting examples.
- Add a project-strengthening checklist for cross-major candidates.
- Improve bilingual documentation consistency.
- Add scheduled automation for portal index checks.

## FAQ

### Does this Skill maintain an automatic job database?

No. It provides job research, verification, and output methodology, plus an official portal index. Whenever users ask for latest openings, the AI tool should verify current information again.

### Why not trust Nowcoder, Shixiseng, or community spreadsheets directly?

They are useful for discovery, but they can be stale, second-hand, broken, or ambiguous. Current-opening outputs should prioritize official or near-official sources.

### Will it help users embellish resumes?

No. It improves wording but should not invent facts. Missing metrics or outcomes should be represented as placeholders and confirmed by the user.

### Are non-CS engineering majors at a disadvantage?

Not if the direction is chosen well. Motion control, embodied AI, embedded software and hardware, and smart vehicle roles need software-hardware co-design and real-world debugging, where mechanical and automation backgrounds are an advantage. Pure algorithm and LLM roles are more competitive and usually need papers, competitions, or measurable project results.

### Can it be used for non-technical roles?

Parts of the workflow can be adapted, but the role profiles, resume criteria, and interview preparation logic are designed primarily for software-related technical roles.

### What if a recruiting portal does not open?

Run `python scripts/check_portals.py` first to tell whether the entry is dead or just unreachable from your network. If it is really dead, re-search the official portal using the order in `references/source-system.md` and update `references/company-portals.md`.

## Origin And Credits

This project continues the `校招.skill` work from [lgd8981289/ocr-skill](https://github.com/lgd8981289/ocr-skill) under the same MIT license. The current maintained repository is [czp0312/xiaozhao-skill](https://github.com/czp0312/xiaozhao-skill).

## License

This project is licensed under the MIT License. See [LICENSE](LICENSE).