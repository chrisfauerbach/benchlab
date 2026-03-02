# CLAUDE.md

Project-specific guidance for Claude Code working on BenchLab.

## What is this project?

BenchLab is a local LLM evaluation engine. It runs prompts against Ollama models, measures performance (TTFT, tokens/sec, generation time), evaluates output quality using LLM-as-judge, and displays results in a web dashboard.

## Tech stack

- **Backend:** Python 3.12, FastAPI, Pydantic, httpx, Elasticsearch 8, Typer CLI
- **Frontend:** React 19, TypeScript, Tailwind CSS v4, TanStack Query, Recharts, Vite, lucide-react icons
- **Infrastructure:** Docker Compose (Ollama, Elasticsearch, API, Frontend/nginx)

## Project layout

```
benchlab/                 Python package (installed as "benchlab")
  api/                    FastAPI app, routers in api/routers/, schemas in api/schemas/
  runner/                 BatchRunner orchestration, OllamaClient HTTP client, MetricsCalculator
  evaluation/             LLM-as-judge: EvaluationOrchestrator, agreement (Krippendorff's alpha), templates
  prompts/                Prompt loader and JSON schema validation
  storage/                ElasticsearchStorage with index mappings
  cli.py                  Typer CLI entrypoint
  config.py               Pydantic settings (BenchLabConfig, OllamaConfig, etc.)
  models.py               Shared Pydantic models (ResultDocument, EvaluationScore, etc.)

frontend/src/
  pages/                  Route-level components (Dashboard, BatchDetail, Leaderboard, OllamaModels, etc.)
  hooks/                  TanStack Query hooks (use-batches, use-metrics, use-models, use-ollama)
  components/             Shared UI (Card, Badge, StatCard, ScoreBar, Layout)
  lib/api.ts              API client with typed fetch wrapper
  lib/utils.ts            cn() helper, formatters

config/                   benchlab.yaml configuration
prompts/examples/         Sample prompts: reasoning.json, creative.json, coding.json
docker/                   api.Dockerfile, ollama entrypoint
```

## Key patterns

- **Backend dependencies:** `benchlab/api/dependencies.py` provides singleton `get_ollama()` and `get_storage()` via `@lru_cache` / globals. Routers import these directly (not FastAPI `Depends`).
- **Frontend data fetching:** All API calls go through `api` object in `lib/api.ts`. Hooks in `hooks/` wrap these with `useQuery`/`useMutation`. Pages consume hooks, never call `api` directly.
- **Frontend styling:** Tailwind CSS v4 with CSS-variable-based theme (bg-card, text-primary, border-border, etc.). Use `cn()` from `lib/utils` for conditional classes.
- **Config loading:** `benchlab/config.py` loads YAML from `config/benchlab.yaml` with env var overrides (`OLLAMA_BASE_URL`, `ES_HOSTS`).
- **No tests yet.** There is no test suite.

## Build and run

```bash
docker compose up -d --build          # full stack
docker compose up api -d --build      # rebuild API only
docker compose exec api benchlab run  # run benchmarks
```

Frontend dev server (outside Docker): `cd frontend && npm install && npm run dev`

## Common tasks

- **Add a new API endpoint:** Create route in `benchlab/api/routers/<router>.py`, it gets auto-mounted via `benchlab/api/app.py`.
- **Add a frontend page:** Create `frontend/src/pages/MyPage.tsx`, add route in `App.tsx`, add nav item in `components/Layout.tsx`.
- **Add a frontend hook:** Create in `frontend/src/hooks/`, follow existing pattern with `useQuery`/`useMutation` from TanStack Query.
- **Modify config schema:** Edit `benchlab/config.py` Pydantic models, update `config/benchlab.example.yaml`.

## Style guidelines

- Backend: standard Python, type hints everywhere, `from __future__ import annotations`.
- Frontend: functional React components, named exports, no default exports (except App). Tailwind for all styling.
- Use existing UI components (Card, Badge, StatCard) rather than creating new ones when possible.
