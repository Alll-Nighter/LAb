# LLM Service (`llm_service/`)

> **Last updated:** 2026-10-05

## What It Does

The LLM Service is a standalone FastAPI microservice (port **8001**) that provides
AI-powered daily safety reports and natural-language Q&A over PPE-violation data.
It receives violation records from any caller (typically the UI or backend API),
aggregates them into KPIs using `analytics.py`, builds structured prompts via
`prompts.py`, and forwards them to a **locally running Ollama** instance for
inference. No cloud LLM APIs are used.

## How to Run

1. **Start Ollama** (must be running on `http://localhost:11434`):
   ```bash
   ollama serve            # if not already running as a service
   ollama pull llama3.2    # one-time model download
   ```
2. **Start the LLM Service** from the `smart-lab-safety/` directory:
   ```bash
   # Linux / macOS
   bash scripts/run_llm.sh

   # Windows
   scripts\run_llm.bat
   ```
   The service listens on `http://localhost:8001`.

## Endpoints

### `GET /ping`

Health check.

**Request:** no body.

**Response:**
```json
{"status": "ok", "service": "llm_service"}
```

### `POST /generate_report`

Aggregates violation records and returns a daily summary. If there are no valid
records, a fixed no-violations message is returned without calling Ollama.
The message describes the supplied data and does not claim the lab is safe.

**Request:**
```json
{"violations": [{"camera_id": 0, "zone": "Workbench-1", "track_id": 7, "violation_type": "NO_HELMET", "timestamp": "2026-10-01T11:42:10", "confidence": 0.87}]}
```

**Response (Ollama available):**
```json
{"status": "ok", "report": "The lab recorded 1 violation.", "kpis": {"total": 1, "by_type": {"NO_HELMET": 1}, "by_zone": {"Workbench-1": 1}, "by_hour": {"00": 0, "01": 0, "02": 0, "03": 0, "04": 0, "05": 0, "06": 0, "07": 0, "08": 0, "09": 0, "10": 0, "11": 1, "12": 0, "13": 0, "14": 0, "15": 0, "16": 0, "17": 0, "18": 0, "19": 0, "20": 0, "21": 0, "22": 0, "23": 0}, "top_type": "NO_HELMET", "top_zone": "Workbench-1", "peak_hour": "11:00-12:00", "repeat_violators": []}}
```

The `by_hour` object always includes all keys from `"00"` through `"23"`.
When Ollama is unavailable, the response remains HTTP 200 with
`{"status":"fallback","report":"Ollama is unavailable; make sure Ollama is running and llama3.2 is pulled.","kpis":{...}}`.
Malformed request bodies receive FastAPI's HTTP 422 validation response.

### `POST /answer_query`

Answers a question using only computed KPIs. `data` may be a violation list or
an object containing a `violations` list.

**Request:**
```json
{"query": "Which zone had the most violations?", "data": {"violations": [{"zone": "Workbench-1", "violation_type": "NO_HELMET", "timestamp": "2026-10-01T11:42:10", "track_id": 7}]}}
```

**Response:**
```json
{"status": "ok", "answer": "Workbench-1 had the most violations, with 1.", "kpis": {"total": 1, "by_type": {"NO_HELMET": 1}, "by_zone": {"Workbench-1": 1}, "by_hour": {"00": 0, "01": 0, "02": 0, "03": 0, "04": 0, "05": 0, "06": 0, "07": 0, "08": 0, "09": 0, "10": 0, "11": 1, "12": 0, "13": 0, "14": 0, "15": 0, "16": 0, "17": 0, "18": 0, "19": 0, "20": 0, "21": 0, "22": 0, "23": 0}, "top_type": "NO_HELMET", "top_zone": "Workbench-1", "peak_hour": "11:00-12:00", "repeat_violators": []}}
```

The `by_hour` object always includes keys `"00"` through `"23"`. A blank
query returns HTTP 400. Missing or wrongly typed required request fields return
HTTP 422. If Ollama is unavailable, the endpoint returns HTTP 200 with
`status: "fallback"` and an `answer` containing the unavailable message.

## Violation Record Format

Each violation is a JSON object. Extra fields are ignored; missing fields are
shown as `"UNKNOWN"` in reports.

| Field            | Type   | Example                    | Notes                          |
|------------------|--------|----------------------------|--------------------------------|
| `camera_id`      | int    | `0`                        | Camera index                   |
| `zone`           | string | `"Workbench-1"`            | Zone name                      |
| `track_id`       | int    | `7`                        | Person tracking ID             |
| `violation_type` | string | `"NO_HELMET"`              | Type of PPE violation          |
| `timestamp`      | string | `"2026-10-01T11:42:10"`    | ISO 8601 datetime              |
| `confidence`     | float  | `0.87`                     | Detection confidence 0–1       |

## KPI Fields (`compute_kpis`)

The `compute_kpis(violations: list[dict]) -> dict` function aggregates violation records into structured metrics:

| Field              | Type                      | Description                                                  | Example |
|--------------------|---------------------------|--------------------------------------------------------------|---------|
| `total`            | `int`                     | Total number of violations                                   | `12` |
| `by_type`          | `dict[str, int]`          | Breakdown of counts by violation type                        | `{"NO_HELMET": 7, "NO_VEST": 5}` |
| `by_zone`          | `dict[str, int]`          | Breakdown of counts by lab zone                              | `{"Workbench-1": 8, "Storage": 4}` |
| `by_hour`          | `dict[str, int]`          | 24-hour distribution (keys `"00"` to `"23"`)                 | `{"00": 0, ..., "11": 8, ...}` |
| `top_type`         | `str` or `null`           | Most common violation type (alphabetical tie-breaker)        | `"NO_HELMET"` |
| `top_zone`         | `str` or `null`           | Most violated zone (alphabetical tie-breaker)                | `"Workbench-1"` |
| `peak_hour`        | `str` or `null`           | Hour interval with most violations                           | `"11:00-12:00"` |
| `repeat_violators` | `list[dict]`              | Track IDs with >1 violation: `[{"track_id": 7, "count": 3}]` | `[{"track_id": 7, "count": 3}]` |

Missing fields in violation items are safely recorded under `"UNKNOWN"`. If `violations` is empty, `total` is `0`, `top_type`, `top_zone`, and `peak_hour` are `null`, and `repeat_violators` is `[]`.

## Configuration

| Variable                 | Default                  | Description                               |
|--------------------------|--------------------------|-------------------------------------------|
| Environment variable     | Default                  | Description                               |
|--------------------------|--------------------------|-------------------------------------------|
| `OLLAMA_URL`             | `http://localhost:11434` | Ollama server base URL                    |
| `OLLAMA_MODEL`           | `llama3.2`               | Model name for inference                  |
| `OLLAMA_TIMEOUT_SECONDS` | `120`                    | HTTP request timeout in seconds           |
| `OLLAMA_TEMPERATURE`     | `0.3`                    | Sampling temperature for deterministic output |

## Client & Error Handling (`client.py`)

The service talks to Ollama over HTTP via `chat_with_ollama(messages: list[dict]) -> str`:
- **Endpoint:** `POST http://localhost:11434/api/chat`
- **Payload:** `{"model": "llama3.2", "messages": [...], "stream": false, "options": {"temperature": 0.3}}`
- **Error Handling:** Raises a custom `OllamaError` (subclass of `RuntimeError`) on:
  - Connection failure (e.g. Ollama daemon not running)
  - Request timeout
  - Non-200 HTTP response
  - Invalid / unparseable JSON
  - Empty model response

## Prompt Builders (`prompts.py`)

All prompt templates are strictly defined in `prompts.py` and return `list[dict]` message structures for chat completion:
- `build_daily_report_prompt(kpis: dict) -> list[dict]`: System prompt instructs the model to act as a safety analyst and write a 5–7 line summary (total, top zone, top type, peak hour, repeat violators, 1 recommendation) using only provided KPIs.
- `build_query_prompt(query: str, kpis: dict) -> list[dict]`: System prompt grounds answers on KPI metrics, explicitly directing the model to answer *"I don't have that information in the provided safety data."* when facts are missing.

## What Other Modules Need to Send / Expect

- **To use the LLM Service**, send HTTP requests to `http://localhost:8001`.
- `GET /ping` requires no body; returns `{"status": "ok", "service": "llm_service"}`.
- `POST /generate_report` takes `{"violations": [...]}` and returns `status`, `report`, and computed `kpis`.
- `POST /answer_query` takes `{"query": "...", "data": {"violations": [...]}}`; `data` can also be a plain list. It returns `status`, `answer`, and computed `kpis`.
- Send one JSON violation object per event using the record fields documented below. Extra fields are ignored. Missing `zone` and `violation_type` values are grouped under `UNKNOWN`; missing or invalid timestamps are excluded from the hourly counts; records without `track_id` are excluded from repeat-violator counts.
- Both POST routes make a synchronous local Ollama request for non-empty data/questions. Their outage response uses `status: "fallback"`; empty reports skip Ollama. Blank questions return HTTP 400.

---

## Changelog

| Date       | Change | Breaking? |
|------------|--------|-----------|
| 2026-10-01 | Step 1: Initial skeleton with `GET /ping` endpoint | No |
| 2026-10-01 | Step 2: Implemented `client.py` (`chat_with_ollama`, `OllamaError`, timeouts, low temperature) | No |
| 2026-10-01 | Step 3: Implemented `analytics.py` (`compute_kpis`, `extract_violations`, 24h distribution, repeat violators, resilient parsing) | No |
| 2026-10-01 | Step 4: Implemented `tests/test_analytics.py` (9 unit tests for normal data, empty list, repeat violators, missing fields, timestamp formats, ties, and bad inputs) | No |
| 2026-10-01 | Step 5: Implemented `prompts.py` (`build_daily_report_prompt`, `build_query_prompt` with strict hallucination guardrails) | No |
| 2026-10-05 | Steps 6–8: Added validated report/query endpoints, endpoint and client tests, run scripts, and environment-based Ollama settings | No |
