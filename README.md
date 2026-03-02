# BenchLab

LLM evaluation engine for local models. Run prompts against multiple Ollama models, collect performance metrics, and score outputs using LLM-as-judge evaluation.

## Quick Start

```bash
cp .env.example .env        # optional: customize models pulled on startup
docker compose up -d --build
```

This starts four services:

| Service           | URL                     | Description                     |
|-------------------|-------------------------|---------------------------------|
| Frontend          | http://localhost:3000    | React dashboard                 |
| API               | http://localhost:8000    | FastAPI backend                 |
| Elasticsearch     | http://localhost:9200    | Results storage                 |
| Ollama            | http://localhost:11434   | LLM inference server            |

Wait for Ollama to finish pulling models (check with `docker compose logs -f ollama`), then run your first benchmark:

```bash
docker compose exec api benchlab run
```

Results appear in the dashboard at http://localhost:3000.

## Architecture

```
frontend/          React + TypeScript + Tailwind CSS + TanStack Query
  src/pages/         Dashboard, Leaderboard, BatchDetail, OllamaModels, ...
  src/hooks/         React Query hooks for data fetching
  src/lib/api.ts     API client

benchlab/          Python package
  api/               FastAPI app with routers (batches, models, runs, metrics, prompts)
  runner/            Batch execution engine and Ollama HTTP client
  evaluation/        LLM-as-judge scoring with Krippendorff's alpha agreement
  prompts/           Prompt loader and schema validation
  storage/           Elasticsearch storage layer
  cli.py             Typer CLI

config/            YAML configuration
prompts/examples/  Sample prompts (reasoning, creative, coding)
docker/            Dockerfiles and entrypoints
```

## Configuration

Copy and edit `config/benchlab.example.yaml` to `config/benchlab.yaml`:

```yaml
target_models:
  - name: "llama3.2:3b"
    display_name: "Llama 3.2 3B"
  - name: "mistral:7b"
    display_name: "Mistral 7B"

evaluation:
  enabled: true
  evaluator_models:
    - "llama3.2:3b"
  scoring_dimensions:
    - name: coherence
      weight: 1.0
    - name: accuracy
      weight: 1.5
    - name: relevance
      weight: 1.0
    - name: completeness
      weight: 1.0
    - name: conciseness
      weight: 0.8
    - name: helpfulness
      weight: 1.2
```

Environment variable overrides: `OLLAMA_BASE_URL`, `ES_HOSTS`, `ES_USERNAME`, `ES_PASSWORD`.

## CLI

All commands are available inside the API container (`docker compose exec api benchlab <command>`):

```
benchlab run                    Run benchmark batch against configured models
  -p, --prompts <dir>             Prompts directory (default: prompts/examples)
  -c, --config <file>             Config file path
  -b, --batch-id <id>             Custom batch ID

benchlab validate-prompts       Validate prompt JSON files
benchlab list-batches            List recent batches
benchlab show-batch <batch_id>  Show batch details and results
benchlab list-models             List available Ollama models
benchlab export <batch_id>      Export results to JSON
  -o, --output <file>             Output path (default: export.json)
```

## Evaluation Pipeline

1. **Load** prompt JSON files from the prompts directory
2. **Pull** any missing models from Ollama
3. **Execute** each prompt against each target model (concurrent, with configurable parallelism)
4. **Evaluate** successful outputs using LLM-as-judge evaluator models, scoring across configurable dimensions (1-10)
5. **Aggregate** scores with mean/median/std-dev, composite scores (weighted), and Krippendorff's alpha inter-rater agreement
6. **Store** all results and batch summaries in Elasticsearch
7. **Display** in the web dashboard with rankings, comparisons, and per-result drill-down

## Writing Prompts

Add JSON files to `prompts/examples/` (or a custom directory):

```json
{
  "schema_version": "1.0",
  "prompts": [
    {
      "id": "my-prompt-001",
      "name": "My Test Prompt",
      "category": "reasoning",
      "input_text": "Explain why the sky is blue.",
      "system_prompt": "You are a helpful science teacher.",
      "difficulty": "easy",
      "tags": ["science", "explanation"],
      "max_tokens": 1024,
      "temperature": 0.7
    }
  ]
}
```

## GPU Support

The `docker-compose.override.yml` enables NVIDIA GPU passthrough for Ollama. Remove or rename this file if you don't have an NVIDIA GPU.

## API Endpoints

| Method   | Path                              | Description                          |
|----------|-----------------------------------|--------------------------------------|
| GET      | `/api/health`                     | Service health check                 |
| POST     | `/api/runs`                       | Start a benchmark run                |
| GET      | `/api/runs/{batch_id}`            | Check run status                     |
| GET      | `/api/batches`                    | List batches                         |
| GET      | `/api/batches/{id}`               | Batch summary                        |
| GET      | `/api/batches/{id}/results`       | Batch results                        |
| GET      | `/api/batches/{id}/compare`       | Compare models in a batch            |
| GET      | `/api/models`                     | Models with benchmark data           |
| GET      | `/api/models/available`           | Installed Ollama models              |
| POST     | `/api/models/pull`                | Pull a model from Ollama             |
| GET      | `/api/models/pull/{name}/status`  | Pull progress                        |
| DELETE   | `/api/models/{name}`              | Delete an Ollama model               |
| GET      | `/api/metrics/leaderboard`        | Model leaderboard                    |
| GET      | `/api/prompts`                    | List prompts                         |

## License

MIT
