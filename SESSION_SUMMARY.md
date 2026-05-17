# RTL Debug Analyzer — Session Summary

## What Was Built

Three specialist agents collaboratively built a full-stack RTL (Register Transfer Level) debug analysis tool that accepts an AXI-Lite protocol specification (YAML) and a simulation trace (CSV), runs automated protocol rule checking and FSM transition validation, then calls the Claude API in a three-turn conversation to produce AI-powered root-cause analysis and actionable fix recommendations. The result is surfaced in a React/Vite single-page application with structured violation cards, FSM issue panels, and collapsible AI recommendation sections rendered as Markdown.

---

## Architecture Overview (4-Layer Pipeline)

```
┌─────────────────────────────────────────────────────────┐
│  Layer 1 — Parsers                                       │
│  spec_parser.py  →  Specification (YAML → dataclass)    │
│  sim_parser.py   →  SignalDatabase (CSV → dataclass)    │
└────────────────────────┬────────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────────┐
│  Layer 2 — Engines                                       │
│  rule_engine.py  →  List[RuleViolation]                 │
│  fsm_engine.py   →  List[FSMTransition]                 │
└────────────────────────┬────────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────────┐
│  Layer 3 — AI Analyzer                                   │
│  claude_analyzer.py                                      │
│    AnalysisContext.to_prompt_context() → prompt text    │
│    3-turn Claude conversation (prompt-cached Turn 1)    │
│    Returns AnalysisResult (Pydantic)                    │
└────────────────────────┬────────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────────┐
│  Layer 4 — Frontend                                      │
│  FastAPI POST /api/analyze → AnalysisResult JSON        │
│  React + Vite SPA                                       │
│    ViolationList  — rule violations + FSM issues        │
│    InsightPanel   — AI summary + recommendations        │
└─────────────────────────────────────────────────────────┘
```

---

## Agent Work Breakdown

| Agent | Responsibility | Files Owned |
|-------|---------------|-------------|
| **Agent 1 — Backend Models & Parsers** | Defined all data models (spec, sim, analysis) and the two parsers. Implemented `to_prompt_context()` fully. | `backend/models/spec_models.py`, `backend/models/sim_models.py`, `backend/models/analysis_models.py`, `backend/parsers/spec_parser.py`, `backend/parsers/sim_parser.py` |
| **Agent 2 — Engines & API** | Implemented both checking engines and wired up the FastAPI application. | `backend/engine/rule_engine.py`, `backend/engine/fsm_engine.py`, `backend/main.py`, `backend/__init__.py`, `backend/requirements.txt`, `.env.example` |
| **Agent 3 — AI Analyzer & Frontend** | Built the three-turn Claude conversation with prompt caching, and the full React UI. | `backend/ai/claude_analyzer.py`, `frontend/src/App.jsx`, `frontend/src/App.css`, `frontend/src/components/FileUpload.jsx`, `frontend/src/components/ViolationList.jsx`, `frontend/src/components/InsightPanel.jsx`, `frontend/package.json`, `frontend/vite.config.js`, `frontend/index.html` |

---

## Interface Audit — Issues Found and Fixed

The Manager Agent performed a full cross-layer interface audit covering:

- Relative import paths in all backend modules
- `AnalysisContext.to_prompt_context()` implementation completeness
- `ClaudeAnalyzer.analyze()` return type and field-name mapping in `_build_violations()` / `_build_fsm_issues()`
- `run_rule_engine` / `run_fsm_engine` return types and import sources
- Frontend field-name alignment against Pydantic response models

**Result: No issues were found.** All interfaces are fully compatible:

- `main.py` relative imports match actual module locations.
- `to_prompt_context()` is a complete implementation — not a stub.
- `_build_violations()` correctly maps every `RuleViolation` field to `ViolationOut`.
- `_build_fsm_issues()` correctly filters invalid transitions and maps all fields to `FSMIssueOut`.
- Both engines import `RuleViolation` / `FSMTransition` from `analysis_models`, not `spec_models`.
- `App.jsx` accesses `result.violations`, `result.fsm_issues`, `result.ai_summary`, `result.ai_recommendations` — exact match to `AnalysisResult`.
- `ViolationList.jsx` accesses `violation.rule_id`, `.rule_name`, `.severity`, `.trigger_cycle`, `.details`, `.relevant_cycles` and `issue.from_state`, `.to_state`, `.cycle`, `.allowed_next` — exact match to `ViolationOut` / `FSMIssueOut`.
- `InsightPanel.jsx` accesses `recommendation.title` and `recommendation.body` — exact match to `RecommendationOut`.

No files were modified.

---

## How to Run the App

### Prerequisites
- Python 3.10+
- Node.js 18+
- An Anthropic API key

### Backend

```bash
# From the project root
cd C:\debug_rtl
pip install -r backend/requirements.txt

# Copy the example env file and add your Anthropic API key
copy .env.example .env
# Edit .env and replace "your_api_key_here" with your real key

# Start the API server
uvicorn backend.main:app --reload
```

The backend will be available at http://localhost:8000. Interactive API docs at http://localhost:8000/docs.

### Frontend (new terminal)

```bash
cd C:\debug_rtl\frontend
npm install
npm run dev
```

### Open the app

Open http://localhost:5173 in your browser.

Upload `write_channel_controller_spec.yml` as the spec file and `write_channel_controller_sim.csv` as the simulation file (both included in the project root) and click **Analyze** to run the full pipeline.
