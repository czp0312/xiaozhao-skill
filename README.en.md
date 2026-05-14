# Xiaozhao.skill

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Language](https://img.shields.io/badge/Language-English%20%7C%20中文-green.svg)](README.md)
[![Codex Skill](https://img.shields.io/badge/Codex-Skill-2563EB.svg)](SKILL.md)

An AI Skill for China software engineering campus recruiting, internships, and big-tech job preparation. It turns job research, source verification, JD analysis, role matching, application strategy, resume review, resume rewriting, interview preparation, and mock interviews into a reusable AI workflow.

中文文档: [README.md](README.md)

**Personal official account**: Programmer Sunday shares knowledge about frontend and AI

![image-20260514104246530](README.assets/image-20260514104246530.png)

## Table Of Contents

- [Positioning](#positioning)
- [Core Capabilities](#core-capabilities)
- [Use Cases](#use-cases)
- [Installation](#installation)
- [Usage Examples](#usage-examples)
- [Workflow Modules](#workflow-modules)
- [Source Principles](#source-principles)
- [Safety Boundaries](#safety-boundaries)
- [Maintenance And Contribution](#maintenance-and-contribution)
- [Roadmap](#roadmap)
- [FAQ](#faq)
- [License](#license)

## Positioning

`校招.skill` is not a job database and does not promise job offers. It is an operational guide for AI tools, designed to make campus recruiting assistance for software engineering roles more reliable, verifiable, and actionable.

It is useful for:

- verifying active openings from official or near-official sources;
- breaking down job descriptions and identifying real preparation priorities;
- matching candidates to roles and application priorities;
- diagnosing resumes and improving wording without inventing facts;
- preparing technical interviews, HR interviews, project follow-ups, and mock interviews.

## Core Capabilities

| Capability | Description |
| --- | --- |
| Current opening research | Organizes active opportunities by company, role, graduation year, city, and recruiting batch. |
| Source verification | Prioritizes company career sites, campus portals, official recruiting accounts, and official hiring systems. |
| JD analysis | Extracts responsibilities, hard requirements, nice-to-haves, technical keywords, and likely follow-ups. |
| Role matching | Ranks applications by year, skills, projects, internships, city constraints, and preparation window. |
| Resume diagnosis | Identifies blockers, major issues, medium-impact issues, and polish items by priority. |
| Resume rewriting | Improves truth-preserving expression around personal actions, technical solutions, tradeoffs, and results. |
| Interview preparation | Generates technical interview, HR interview, project follow-up, and mock interview flows. |
| Structured output | Produces stable tables, conclusions, rewrites, and action plans. |

## Use Cases

Best suited for:

- campus recruiting, spring recruiting, fall recruiting, early batches, summer internships, daily internships, and conversion internships;
- internet platforms, AI companies, cloud vendors, smart hardware, new energy, gaming, SaaS, and fintech companies in China;
- frontend, backend, client, full-stack, AI application, LLM application, algorithm, data, test development, SRE, security, game development, embedded, and other software-related technical roles;
- job list research, company hiring process lookup, JD breakdown, role selection, application ordering, resume review, and mock interviews.

Not the default target:

- general experienced hiring, overseas roles, civil service exams, public-sector roles, banking-only recruiting, study abroad applications, graduate school recommendation, or postgraduate entrance exam planning;
- parts of the workflow may be adapted, but the scope limit should be stated clearly.

## Installation

This Skill is meant to be installed through natural language inside AI tools. Users do not need to run any code manually.

Recommended prompt for AI tools that support Skill installation:

> Install this Skill from the root of this GitHub repository: https://github.com/lgd8981289/ocr-skill

If the AI tool asks for an installation location, choose the repository root. The repository root already contains the complete Skill entry file.

After installation, restart or refresh the AI tool so the new Skill can be loaded.

### Installation Verification Status

- The GitHub repository is publicly accessible.
- The default branch is `master`.
- The repository root contains the Skill entry file.
- The current repository uses a root-as-Skill layout. If an AI tool only supports installing from a subdirectory, ask it to read from the repository root explicitly.

## Usage Examples

After installation, call the Skill with natural language:

> Use $校招.skill to find active AI application development internships, prioritizing Beijing, Shanghai, and Hangzhou.

> Use $校招.skill to analyze this LLM application development intern JD and tell me what my resume should emphasize and what the interview may ask.

> I graduate in 2027. I have built a RAG QA system and a React admin dashboard, and I have one frontend internship. Which big-tech technical roles should I prioritize?

> Use $校招.skill to review my project experience for AI application development internships. Mark P0 to P3 issues and rewrite it without inventing facts.

> Use $校招.skill to run a ByteDance AI application development intern technical mock interview. Ask one question at a time.

## Workflow Modules

| Module | Purpose |
| --- | --- |
| Skill entry | Defines trigger scope, principles, supported tasks, and task routing. |
| Source system | Defines official sources, near-official sources, lead sources, freshness checks, and deduplication rules. |
| Company watchlist | Maintains the initial company scope, industry groups, and priority technical roles. |
| Candidate strategy | Supports role matching, application ordering, short-term improvement, and action planning. |
| JD analysis | Breaks down requirements, hard constraints, nice-to-haves, and inferred capabilities. |
| Resume module | Supports resume diagnosis, project rewriting, and truthfulness constraints. |
| Interview module | Supports technical interviews, HR interviews, project follow-ups, and mock interviews. |
| Output templates | Keeps job tables, analysis conclusions, review feedback, and action plans consistent. |

## Source Principles

Questions about “current”, “latest”, deadlines, application links, or whether a role is still open require freshness verification.

Source priority:

1. company career site;
2. company campus or internship portal;
3. official recruiting account or announcement;
4. officially delegated hiring system;
5. targeted search engine queries;
6. aggregators and community leads;
7. back to official or near-official sources for verification.

Formal opening tables should only include verified information or clearly labeled uncertain information. Aggregators, screenshots, personal notes, and community spreadsheets should be treated as leads, not verified facts.

## Safety Boundaries

This project follows these boundaries:

- Do not invent jobs, deadlines, application links, referral codes, offer chances, or resume facts.
- Do not promise guaranteed outcomes.
- Do not assist with cheating in written tests, online assessments, or live interviews.
- Do not present personal experience or community rumors as official rules.
- Do not advise users to fake projects, inflate responsibilities, or fabricate metrics.
- Mark uncertain information as “needs verification”, “status unknown”, or “needs your confirmation”.

## Maintenance And Contribution

Issues and pull requests are welcome, especially for:

- adding official recruiting entry points;
- fixing expired links, company aliases, or inaccurate role classification;
- improving source verification rules;
- expanding role families and skill signals;
- improving JD analysis, resume diagnosis, and interview follow-up templates;
- improving bilingual documentation consistency.

When contributing, please explain:

- which module changed;
- what real usage problem it solves;
- whether it depends on current recruiting information or external sources;
- whether it affects factual reliability, safety boundaries, or user privacy.

Do not submit real resumes, personal data, private referral codes, unauthorized recruiting material, or anything that helps cheating.

## Roadmap

- Add more official recruiting entry points.
- Expand software engineering role profiles.
- Add more JD analysis and resume rewriting examples.
- Improve bilingual documentation consistency.
- Maintain source verification strategy for active recruiting seasons.
- Adapt to more AI tools that support natural-language Skill installation.

## FAQ

### Does this Skill maintain an automatic job database?

No. It provides job research, verification, and output methodology. Whenever users ask for latest openings, the AI tool should verify current information again.

### Why not trust Nowcoder, Shixiseng, or community spreadsheets directly?

They are useful for discovery, but they can be stale, second-hand, broken, or ambiguous. Current-opening outputs should prioritize official or near-official sources.

### Will it help users embellish resumes?

No. It improves wording but should not invent facts. Missing metrics or outcomes should be represented as placeholders and confirmed by the user.

### Can it be used for non-technical roles?

Parts of the workflow can be adapted, but the role profiles, resume criteria, and interview preparation logic are designed primarily for software-related technical roles.

### Why is the repository named `ocr-skill`?

The current GitHub repository is named `ocr-skill`, but the Skill display name and actual purpose are `校招.skill`. If the repository is renamed later, update the repository links in the README files.

## License

This project is licensed under the MIT License. See [LICENSE](LICENSE).
