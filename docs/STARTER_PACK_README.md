# SILATARA - Product & Claude Code Starter Pack

**Working product name:** SILATARA  
**Working descriptor:** AI-Powered Pencak Silat Heritage & Learning Platform  
**Core promise:** *Preserving the Heritage. Empowering the Next Generation.*  
**Document baseline:** 19 November 2026  
**Primary language:** Bahasa Indonesia; technical identifiers may use English.

This package is a product, design, research, technical, and execution brief for a team building SILATARA. It is intentionally more than a coding prompt: it gives the product/UI team and Claude Code the same context, constraints, research references, and acceptance criteria.

> Important: SILATARA is currently a product concept and planning package, not a claim that a working product or validated AI model already exists. Do not present proposed features, targets, partnerships, or research hypotheses as completed achievements.

## Start here

1. Read `PROJECT_CONTEXT.md`.
2. Read `PRD.md` and `DESIGN.md`.
3. Read `AGENTS.md` and `CLAUDE.md`.
4. Read `docs/RESEARCH_BRIEF.md`, `docs/COMPETITIVE_ANALYSIS.md`, and `docs/LITERATURE_REVIEW.md`.
5. Run Claude Code from the intended repository root and paste `execution/CLAUDE_CODE_MASTER_PROMPT.md`.
6. Use `execution/PHASE_PROMPTS.md` to run subsequent work in controlled phases.

## Package map

```text
SILATARA_Claude_Code_Pack/
├── README.md
├── PROJECT_CONTEXT.md
├── PRD.md
├── DESIGN.md
├── CLAUDE.md
├── AGENTS.md
├── SOURCES.md
├── docs/
│   ├── RESEARCH_BRIEF.md
│   ├── COMPETITIVE_ANALYSIS.md
│   ├── LITERATURE_REVIEW.md
│   ├── TRIA_CODE_AUDIT.md
│   ├── CULTURAL_PARTNER_PLAYBOOK.md
│   ├── USER_RESEARCH_AND_VALIDATION.md
│   ├── AI_MOVEMENT_ASSESSMENT.md
│   ├── TECHNICAL_ARCHITECTURE.md
│   ├── DATA_MODEL.md
│   ├── API_CONTRACTS.md
│   ├── PRIVACY_SAFETY_AND_ETHICS.md
│   ├── BUSINESS_MODEL.md
│   ├── METRICS_AND_ANALYTICS.md
│   └── ROADMAP_AND_BACKLOG.md
├── execution/
│   ├── CLAUDE_CODE_MASTER_PROMPT.md
│   ├── PHASE_PROMPTS.md
│   ├── ACCEPTANCE_CHECKLIST.md
│   ├── UI_HANDOFF.md
│   └── TEAM_WORKSTREAMS.md
├── .claude/agents/
│   ├── ui-ux-reviewer.md
│   ├── frontend-engineer.md
│   ├── computer-vision-engineer.md
│   ├── backend-engineer.md
│   ├── cultural-domain-reviewer.md
│   └── qa-accessibility-reviewer.md
└── reference-materials/
    ├── PETUNJUK PELAKSANAAN TEKNIS BUDAYA GO! 2026.pdf
    ├── Lampiran 1 dan 2 Panduan dan Format Penulisan Proposal.docx
    ├── BudayaGO_Riset_Pemenang_2025_dan_Ide_2026_2.xlsx
    └── TRIA_gitingest.md
```

## How to use with Claude Code

```bash
# 1. Extract this ZIP into a clean project folder or copy the docs into an existing repo.
# 2. Put any extra survey exports, interview notes, partner letters, and product assets
#    under reference-materials/user-evidence/ (create the folder if needed).
# 3. Open a terminal at the project root.
claude
```

Then paste the master prompt. Do not start with an instruction such as “build every feature now”. The master prompt requires Claude to audit the repo and evidence first, propose a phased implementation plan, then build a working vertical slice.

## Source and evidence discipline

- The BUDAYA GO! 2026 Juknis and proposal template are included as original files.
- The winner spreadsheet is included as an original research workbook. It explicitly says six projects have individual ranks (1-3 in two 2025 participant categories) and 14 are `Juara Bersama` without individual order.
- The TRIA repository digest is included as a benchmark source snapshot, not as a complete executable TRIA repository.
- The user's questionnaire, raw responses, interview transcripts, and partner commitments were mentioned in conversation but were not present among the source files available for this package. Add them before Claude writes quantitative research claims or claims a formal partnership.
- The product eligibility cutoff in the 2026 Juknis is 31 March 2026. If SILATARA did not exist as a functioning product by that date, a new build now must not be backdated or represented as eligible for BUDAYA GO! 2026.

## Working decisions already made

- Product name: **SILATARA** (working name; trademark/domain availability not checked).
- Cultural approach: partner-led; select the most ready and credible pencak silat school/instructor rather than choosing a style by assumption.
- Technology differentiation: integrated ecosystem, but MVP is narrow and validated.
- MVP category/subtheme fit: Inovasi Digital, subtheme 4 - Pembelajaran dan Edukasi Digital Berbasis Budaya (subject to final product and application fit).
- Initial scope: one partner tradition, one approved beginner curriculum, approximately 8-12 fundamental movements selected with the partner, browser-based practice, expert-validated feedback, learning progress, and a basic verified-partner directory.

## What this package is not

- It is not a completed application, production-ready codebase, confirmed partner agreement, or validated CV model.
- It is not legal advice about traditional knowledge/IP. Partner permissions and licensing must be agreed with qualified people.
- It is not a guarantee of competition eligibility, finalist selection, or winning.
