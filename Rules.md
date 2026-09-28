## What to Use

### 1) General Coding Standards

- **Language:**  
  - Python **3.10+** only.  
  - No mixing of Python 2 syntax.

- **Naming Conventions:**  
  - **Files & folders:**  
    - `snake_case` only: `camera_manager.py`, `llm_service`, `endpoints_events.py`.  
    - No spaces, no CamelCase in filenames.  
  - **Modules & packages:**  
    - Lowercase, underscores for multi-word: `cv_engine`, `llm_service`.  
  - **Classes:**  
    - `PascalCase`: `CameraManager`, `ViolationEvent`, `Detector`.  
  - **Functions & variables:**  
    - `snake_case`: `detect_objects`, `violation_frames`, `get_stats`.  
  - **Constants:**  
    - `UPPER_SNAKE_CASE`: `DEFAULT_CONF_THRESHOLD`, `OLLAMA_URL`.  
  - **Private helpers:**  
    - Prefix with underscore: `_point_in_polygon`, `_build_prompt`.

- **Project Layout Rules:**  
  - Keep each service in its own top-level package: `cv_engine`, `api`, `ui`, `llm_service`.  
  - Do **not** put CV logic inside `api` or UI code inside `cv_engine`.  
  - Each package must have an `__init__.py` (even if empty).

- **Docstrings & Comments:**  
  - Every public function and class must have a **short docstring** (1–3 lines) describing:
    - What it does  
    - Inputs  
    - Outputs  
  - Use **type hints** for all function signatures:
    ```python
    def detect(frame: np.ndarray) -> list[Detection]:
        ...
    ```
  - Comments should explain **why**, not **what** (code should show what).

- **Error Handling:**  
  - Use explicit exceptions, not bare `except:`.  
  - For expected failures (DB locked, camera missing), log and degrade gracefully instead of crashing the whole process.  
  - Use custom exception classes sparingly; simple `RuntimeError` with clear messages is fine.

***

### 2) CV Engine (M1)

**Must Use:**

- **Ultralytics YOLOv8** for all detection/tracking:
  - Detection: `YOLO("yolov8n.pt")` or `yolov8s.pt`.  
  - Tracking: `model.track(..., tracker="bytetrack.yaml")`.  
- **OpenCV** for:
  - Camera I/O (`cv2.VideoCapture`).  
  - Drawing boxes, zones, text (`cv2.rectangle`, `cv2.putText`).  
- **NumPy** for:
  - Array slicing, coordinate math, zone checks.  
- **Config-driven behavior:**
  - Zones, cameras, PPE rules loaded from `configs/cameras.yaml` and `configs/ppe_rules.yaml`.  
  - No hardcoded zone coordinates or PPE requirements in logic.

**Patterns to Follow:**

- **Single responsibility per module:**
  - `camera_manager.py` → only camera handling.  
  - `detector.py` → only YOLO wrapper.  
  - `rules.py` → only PPE/zone logic.  
- **Pure functions for geometry & rules:**
  - `point_in_polygon(x, y, polygon) -> bool`  
  - `check_ppe_violations(detections, zones, ...) -> list[ViolationEvent]`  
  - These should be **deterministic** and easy to unit-test.

***

### 3) Backend API (M2)

**Must Use:**

- **FastAPI** for all HTTP APIs.  
- **Uvicorn** as the ASGI server.  
- **SQLAlchemy** (or **SQLModel**) as ORM.  
- **Pydantic** for:
  - Request bodies (`EventCreate`, `QueryRequest`).  
  - Response schemas (`ViolationResponse`, `StatsResponse`).  
- **SQLite** as default DB:
  - File: `safety.db` in project root or `data/` folder.  
- **Dependency injection** for DB sessions in FastAPI:
  ```python
  def get_db():
      db = SessionLocal()
      try:
          yield db
      finally:
          db.close()
  ```

**Patterns to Follow:**

- **One endpoint per resource:**
  - `/events` → create events.  
  - `/violations` → list violations.  
  - `/stats` → get stats.  
  - `/report/daily` → daily aggregated data.  
- **Keep endpoints thin:**
  - Delegate business logic to service modules (e.g., `analytics.py`), not inside endpoint functions.  
- **Use async only if you truly need it:**
  - For hackathon, sync FastAPI endpoints are fine and simpler.

***

### 4) Frontend / UI (M3)

**Must Use:**

- **Streamlit** as the only frontend framework for the hackathon.  
- **Plotly** (or **Altair**) for all charts.  
- **Pandas DataFrames** for:
  - Preparing data for tables and charts.  
- **Centralized API client:**
  - All calls to backend/LLM go through `ui/utils.py` functions:
    - `fetch_stats()`  
    - `fetch_violations()`  
    - `generate_report(data)`  
    - `answer_query(query, data)`  

**Patterns to Follow:**

- **One file per UI component:**
  - `camera_grid.py` → camera grid rendering.  
  - `violation_table.py` → violations table.  
  - `charts.py` → chart components.  
- **No business logic in UI:**
  - UI only:
    - Fetches data via `utils.py`.  
    - Displays it.  
    - Sends user actions to backend/LLM.  
  - All aggregation, KPI computation, and prompt building live in `api` or `llm_service`.

***

### 5) LLM Service (M4)

**Must Use:**

- **Ollama** as the only local LLM runtime.  
- **One model family** for the hackathon:
  - e.g., `llama3.2` (or `mistral`), but **not multiple different models**.  
- **FastAPI** for LLM service endpoints:
  - `/generate_report`  
  - `/answer_query`.  
- **HTTP (requests/httpx)** to call Ollama:
  - No direct Python bindings that require custom builds; stick to HTTP API.

**Patterns to Follow:**

- **Prompt templates in `prompts.py` only:**
  - No inline prompt strings scattered across code.  
  - Each template is a function:
    - `build_daily_report_prompt(data) -> list[dict]`  
    - `build_query_prompt(query, data) -> list[dict]`.  
- **Analytics separated from prompts:**
  - `analytics.py` computes KPIs.  
  - Prompt functions receive already-aggregated data.

***

### 6) Testing & Quality

**Must Use:**

- **pytest** for all tests.  
- **Test file naming:**
  - `test_<module>.py`: `test_zones.py`, `test_rules.py`, `test_analytics.py`.  
- **Arrange–Act–Assert** pattern in tests:
  ```python
  def test_point_in_polygon_inside():
      # Arrange
      polygon = [(0,0), (10,0), (10,10), (0,10)]
      # Act
      result = point_in_polygon(5, 5, polygon)
      # Assert
      assert result is True
  ```
- **black** for formatting:
  - Run `black .` before committing.  
- **ruff** for linting:
  - Run `ruff check .` before committing.

***

## What to Avoid

### 1) General Anti-Patterns

- **Do NOT mix concerns:**
  - No CV logic in `api` or `ui`.  
  - No DB queries inside `cv_engine`.  
  - No prompt building inside `ui`.  
- **Do NOT use global mutable state** for core logic:
  - No global `violations_list = []` that services append to.  
  - Use DB or explicit in-memory structures with clear ownership.  
- **Do NOT hardcode values that belong in config:**
  - No hardcoded zone coordinates, PPE requirements, thresholds in logic.  
  - All such values must come from `configs/*.yaml` or `.env`.

- **Do NOT use multiple competing patterns for the same thing:**
  - Don’t sometimes call Ollama via `requests` and other times via some other client.  
  - Don’t sometimes use SQLAlchemy and other times raw SQL for core operations.

***

### 2) CV Engine – What to Avoid

- **Do NOT train your own detection model from scratch** for the hackathon.  
  - Use pre-trained YOLOv8 models only.  
- **Do NOT implement your own tracker** (SORT, ByteTrack) from scratch.  
  - Use Ultralytics’ built-in tracking (`tracker="bytetrack.yaml"`).  
- **Do NOT process every single frame with heavy logic if it kills FPS:**
  - If needed, skip frames for detection and rely on tracking for intermediate frames.  
- **Do NOT block the main loop with slow I/O:**
  - Saving snapshots and sending events should not freeze the video loop.  
  - If needed, use a simple queue + background thread for event emission.

***

### 3) Backend – What to Avoid

- **Do NOT use multiple ORMs:**
  - No mixing of SQLAlchemy and raw `sqlite3` for core logic.  
- **Do NOT put business logic in endpoints:**
  - Endpoints should call service functions, not implement KPI computation directly.  
- **Do NOT use external cloud DBs or hosted services** for the hackathon:
  - No Supabase, Firebase, Neon, etc.  
  - Everything must run locally.  
- **Do NOT over-engineen auth:**
  - No OAuth, no external identity providers for v1.  
  - If you add login, keep it hardcoded/simple in Streamlit.

***

### 4) Frontend – What to Avoid

- **Do NOT use React/Next.js/Angular for this hackathon:**
  - Stick to Streamlit only.  
- **Do NOT embed complex state management in UI:**
  - No Redux-like patterns, no custom state stores.  
  - Streamlit’s rerun model is enough.  
- **Do NOT call Ollama or external APIs directly from UI:**
  - All LLM calls go through `llm_service` FastAPI, then UI calls that.  
- **Do NOT build custom charting from scratch:**
  - Use Plotly/Altair; no manual Canvas/D3 implementations.

***

### 5) LLM Service – What to Avoid

- **Do NOT call cloud LLM APIs** (OpenAI, Anthropic, etc.) for the core demo:
  - Use only local Ollama models.  
- **Do NOT send raw DB rows directly to LLM:**
  - Always aggregate into concise KPIs first (`analytics.py`).  
- **Do NOT build long, unstructured prompts:**
  - Prompts must be:
    - Short  
    - Structured (system + user)  
    - Built via functions in `prompts.py`.  
- **Do NOT stream responses in the UI for this version:**
  - Use simple request/response (non-streaming) for stability.

***

### 6) Testing & Ops – What to Avoid

- **Do NOT write tests without assertions:**
  - Every test must assert something meaningful.  
- **Do NOT test only happy paths:**
  - Include at least one failure case per critical function (e.g., invalid polygon, empty violations list).  
- **Do NOT commit without running:**
  - `black .`  
  - `ruff check .`  
  - `pytest` (at least core tests).  
- **Do NOT add Docker unless you can keep it simple:**
  - If `docker-compose.yml` becomes too complex, drop it for the hackathon and run services directly.

***

### 7) Design & UX – What to Avoid

- **Do NOT create more than 3–4 main sections on the dashboard:**
  - KPIs, Live Cameras, Charts, Violations, AI Report/Q&A.  
  - No endless scrolling pages of features.  
- **Do NOT use dark, low-contrast color schemes:**
  - Use clear, high-contrast colors for boxes, zones, and text.  
- **Do NOT overload the judge with configuration options during demo:**
  - Config is for you, not for live demo.  
  - Show a pre-configured lab with 2–3 zones and a few cameras.

