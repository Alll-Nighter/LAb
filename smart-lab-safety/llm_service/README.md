# LLM Service (`llm_service/`)

> **Last updated:** 2026-10-01

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

*(More endpoints will be added in subsequent steps.)*

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

## What Other Modules Need to Send / Expect

- **To use the LLM Service**, send HTTP requests to `http://localhost:8001`.
- `GET /ping` requires no body; returns `{"status": "ok", "service": "llm_service"}`.
- Further endpoint contracts will be documented as they are built.

---

## Changelog

| Date       | Change | Breaking? |
|------------|--------|-----------|
| 2026-10-01 | Step 1: Initial skeleton with `GET /ping` endpoint | No |
| 2026-10-01 | Step 2: Implemented `client.py` (`chat_with_ollama`, `OllamaError`, timeouts, low temperature) | No |
| 2026-10-01 | Step 3: Implemented `analytics.py` (`compute_kpis`, `extract_violations`, 24h distribution, repeat violators, resilient parsing) | No |
| 2026-10-01 | Step 4: Implemented `tests/test_analytics.py` (9 unit tests for normal data, empty list, repeat violators, missing fields, timestamp formats, ties, and bad inputs) | No |
