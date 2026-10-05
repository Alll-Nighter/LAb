# M4 LLM Service and Analytics

> **Last updated:** 2026-10-05
> **Scope:** M4 only — local LLM calls, analytics, prompts, and the HTTP contract below.

## Purpose and ownership boundary

This directory contains an independently runnable FastAPI service for PPE
violation analytics, daily incident reports, and natural-language questions.
It uses the local Ollama HTTP API and never calls a cloud LLM. Treat this file
as the source of truth when implementing or integrating M4.

M4 owns `llm_service/`, `tests/test_analytics.py`, `tests/test_llm_service.py`,
and `scripts/run_llm.sh` / `scripts/run_llm.bat`. Keep prompt construction in
`prompts.py`, aggregation in `analytics.py`, and Ollama HTTP handling in
`client.py`. Endpoints in `main.py` validate input and connect those modules.
M4 must run on its own and must not import or depend on `api/`, `cv_engine/`, or
`ui/`. Do not edit those directories, `configs/`, or `requirements.txt` as part
of M4 work. Do not assume another team member has implemented any module.

## Data flow

```text
HTTP request
  -> extract_violations(data)
  -> compute_kpis(violations)
  -> build prompt from KPIs
  -> chat_with_ollama(messages)
  -> Ollama at OLLAMA_URL/api/chat
  -> HTTP response with text and KPIs
```

Raw violation rows are used only by `analytics.py`; the model receives the KPI
dictionary, never the raw rows. Calls are synchronous and non-streaming.

## Violation record contract

Send one JSON object for each event. Extra fields are ignored. Missing values
are tolerated; see the behavior column rather than inferring that every field
appears in every response.

| Field | Type | Example | Behavior when missing or invalid |
|---|---|---|---|
| `camera_id` | integer | `0` | Accepted as input; not part of the KPI output. |
| `zone` | string | `"Workbench-1"` | Counted under `"UNKNOWN"`. |
| `track_id` | integer or string | `7` | Not included in repeat-violator counts. |
| `violation_type` | string | `"NO_HELMET"` | Counted under `"UNKNOWN"`. |
| `timestamp` | ISO-8601 string | `"2026-10-01T11:42:10Z"` | Invalid/missing timestamps do not increment an hourly bucket. A trailing `Z` is supported. |
| `confidence` | number from 0 to 1 | `0.87` | Accepted as input; not part of the KPI output. |

`extract_violations(data)` accepts either a list of records or an object with a
`violations` list. Non-dictionary records are filtered out. Other input shapes
return an empty list.

## KPI contract

`compute_kpis(violations)` returns these fields:

| Field | Meaning |
|---|---|
| `total` | Number of accepted violation records. |
| `by_type` | Count per `violation_type`, including `UNKNOWN` when needed. |
| `by_zone` | Count per `zone`, including `UNKNOWN` when needed. |
| `by_hour` | Counts for every string key from `00` through `23`. Invalid timestamps increment none. |
| `top_type` | Most frequent type; alphabetical order breaks ties; `null` for no data. |
| `top_zone` | Most frequent zone; alphabetical order breaks ties; `null` for no data. |
| `peak_hour` | Most frequent hour formatted `HH:00-(HH+1):00`; earlier hour breaks ties; `null` for no valid timestamps. |
| `repeat_violators` | Track IDs with more than one record, sorted by count descending then string form of ID. Each item is `{"track_id": 7, "count": 3}`. |

For an empty list, `total` is `0`, both breakdowns are empty, all 24 hourly
counts are zero, the three top/peak fields are `null`, and
`repeat_violators` is empty.

## HTTP endpoints

The service listens on port `8001`.

### `GET /ping`

No request body. Returns `{"status":"ok","service":"llm_service"}`.

### `POST /generate_report`

Request body:

```json
{
  "violations": [
    {
      "camera_id": 0,
      "zone": "Workbench-1",
      "track_id": 7,
      "violation_type": "NO_HELMET",
      "timestamp": "2026-10-01T11:42:10Z",
      "confidence": 0.87
    }
  ]
}
```

Successful response uses `status: "ok"` and returns `report` and `kpis`:

```json
{
  "status": "ok",
  "report": "A 5–7 line summary based only on the supplied data.",
  "kpis": {
    "total": 1,
    "by_type": {"NO_HELMET": 1},
    "by_zone": {"Workbench-1": 1},
    "by_hour": {
      "00": 0, "01": 0, "02": 0, "03": 0, "04": 0, "05": 0,
      "06": 0, "07": 0, "08": 0, "09": 0, "10": 0, "11": 1,
      "12": 0, "13": 0, "14": 0, "15": 0, "16": 0, "17": 0,
      "18": 0, "19": 0, "20": 0, "21": 0, "22": 0, "23": 0
    },
    "top_type": "NO_HELMET",
    "top_zone": "Workbench-1",
    "peak_hour": "11:00-12:00",
    "repeat_violators": []
  }
}
```

When `total` is zero, the service returns HTTP 200 with `status: "ok"`,
report text `No violations were recorded in the supplied data.`, and the KPI
object defined above; it does not call Ollama. If Ollama fails, it returns HTTP 200 with
`status: "fallback"`, the same KPI object, and this report text:
`Ollama is unavailable; make sure Ollama is running and llama3.2 is pulled.`

### `POST /answer_query`

Request body accepts either a list or the `{"violations": [...]}` envelope in
`data`:

```json
{
  "query": "Which zone had the most violations?",
  "data": {
    "violations": [
      {"zone": "Workbench-1", "violation_type": "NO_HELMET", "timestamp": "2026-10-01T11:42:10Z", "track_id": 7}
    ]
  }
}
```

Response fields are `status`, `answer`, and `kpis`:

```json
{
  "status": "ok",
  "answer": "Workbench-1 had the most violations.",
  "kpis": {"total": 1, "by_type": {"NO_HELMET": 1}, "by_zone": {"Workbench-1": 1}, "by_hour": {"00": 0, "01": 0, "02": 0, "03": 0, "04": 0, "05": 0, "06": 0, "07": 0, "08": 0, "09": 0, "10": 0, "11": 1, "12": 0, "13": 0, "14": 0, "15": 0, "16": 0, "17": 0, "18": 0, "19": 0, "20": 0, "21": 0, "22": 0, "23": 0}, "top_type": "NO_HELMET", "top_zone": "Workbench-1", "peak_hour": "11:00-12:00", "repeat_violators": []}
}
```

Blank/whitespace-only queries return HTTP 400. Invalid JSON or missing/wrongly
typed required values return FastAPI HTTP 422. If Ollama fails, the endpoint
returns HTTP 200 with `status: "fallback"`, the KPI object, and the same
unavailable message in `answer`. The query prompt tells the model to say
`I don't have that information` when the supplied KPIs cannot answer.

## Module responsibilities

- `analytics.py`: `extract_violations` and deterministic KPI aggregation.
- `prompts.py`: `build_daily_report_prompt(kpis)` and `build_query_prompt(query, kpis)`; all system/user prompt text lives here. Reports request 5–7 separate plain-language lines, the listed KPIs, and one practical recommendation. Both prompts forbid invented facts/numbers.
- `client.py`: environment-configurable Ollama HTTP client, non-streaming `llama3.2` request, timeout, low temperature, and `OllamaError` for connection/status/JSON/empty-response failures.
- `main.py`: Pydantic request models, `/ping`, `/generate_report`, and `/answer_query`; delegates KPI/prompt/client work to the modules above.
- `tests/test_analytics.py`: analytics and input-shape cases.
- `tests/test_llm_service.py`: prompts and mocked Ollama client/endpoint cases.
- `scripts/run_llm.sh` and `scripts/run_llm.bat`: launch Uvicorn from the project root on port 8001.

## Configuration and running

Set these in the process environment before starting the service. Defaults are
shown; the client reads environment variables and does not parse `.env` files.

| Variable | Default | Purpose |
|---|---|---|
| `OLLAMA_URL` | `http://localhost:11434` | Ollama base URL. |
| `OLLAMA_MODEL` | `llama3.2` | Local model name. |
| `OLLAMA_TIMEOUT_SECONDS` | `120` | HTTP request timeout. |
| `OLLAMA_TEMPERATURE` | `0.3` | Low sampling temperature. |

Start Ollama and pull the model once:

```powershell
ollama serve
ollama pull llama3.2
```

Then, from `smart-lab-safety/`, run `scripts\run_llm.bat` on Windows or
`bash scripts/run_llm.sh` on Linux/macOS. The scripts run:
`uvicorn llm_service.main:app --host 0.0.0.0 --port 8001 --reload`.

## Checks and smoke requests

From the repository root, with the project environment active:

```powershell
python -m black --check smart-lab-safety
python -m ruff check smart-lab-safety
python -m pytest smart-lab-safety/tests -q
```

PowerShell smoke request (the service must already be running):

```powershell
$body = @{ violations = @() } | ConvertTo-Json -Compress
Invoke-RestMethod -Uri http://127.0.0.1:8001/generate_report -Method Post -ContentType 'application/json' -Body $body
```

For an outage check, point a separate service process at an unused local port,
then send a non-empty `violations` list. Expect `status: "fallback"`. Do not
stop another process unless you intend to stop that Ollama instance.

## What other modules need to send / expect

Call `GET /ping` to check service availability. Send report requests in the
`{"violations": [...]}` form and Q&A requests in the
`{"query": "...", "data": [...]}` or
`{"query": "...", "data": {"violations": [...]}}` form. Read the endpoint
response fields and `status`; consumers must handle `fallback` as a valid
HTTP 200 result. This contract defines the integration format without assuming
that any other project module already exists or is complete.

## Changelog

| Date | Change | Breaking? |
|---|---|---|
| 2026-10-01 | Added health check, Ollama client, analytics, tests, and prompts. | No |
| 2026-10-05 | Added report/Q&A routes, validation, fallback behavior, launch scripts, and Ollama environment settings. | No |
| 2026-10-05 | Reorganized this guide as an explicit M4 implementation and integration handoff; no code or interface changes. | No |
