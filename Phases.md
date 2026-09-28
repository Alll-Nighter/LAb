## Phase 0 – Project Skeleton & Local Dev Setup  
**Goal:** Everyone can run their piece locally; repo structure is fixed.

**Duration:** 0.5–1 day  

**Scope:**
- Create repo with the agreed folder structure:
  - `cv_engine/`, `api/`, `ui/`, `llm_service/`, `configs/`, `scripts/`, `tests/`.  
- Add:
  - `requirements.txt` (with pinned versions).  
  - `.env.example`.  
  - Basic `README.md` with:
    - How to install deps  
    - How to run each service (even if they just print “Hello”).  
- Each member creates their “hello world” module:
  - M1: `cv_engine/main_loop.py` that prints “CV engine running” and exits.  
  - M2: `api/main.py` with a `/health` endpoint returning `{"status":"ok"}`.  
  - M3: `ui/app.py` with a simple “Hello, Smart Lab Safety” page.  
  - M4: `llm_service/main.py` with a `/ping` endpoint.

**Definition of Done:**
- All 4 services run locally without errors.  
- Everyone can pull repo, `pip install -r requirements.txt`, and run their service.  
- No CV, no DB, no LLM yet—just skeleton.

***

## Phase 1 – Single-Camera PPE Detection (Core CV)  
**Goal:** Detect people + PPE on **one camera** and print violations to console.

**Duration:** 2 days  

**Owner:** M1 (with others reviewing).

**Scope:**
- Implement:
  - `camera_manager.py` for a single webcam.  
  - `detector.py` with YOLOv8 (`yolov8n.pt`).  
  - Basic class mapping: person, helmet, vest.  
  - `rules.py` with simple logic:
    - If person detected and no helmet/vest in frame → print “VIOLATION: NO_HELMET”.  
- No zones, no tracking, no DB, no API yet.  
- Show a local OpenCV window with:
  - Bounding boxes  
  - Class labels  
  - Simple text when violation detected.

**Definition of Done:**
- Running `python -m cv_engine.main_loop`:
  - Opens webcam.  
  - Shows real-time detection at decent FPS.  
  - Prints violation messages to console when PPE is missing.  
- M2/M3/M4 can see a live demo of this and understand the output format.

***

## Phase 2 – Backend API + DB for Violations  
**Goal:** Persist violations from CV engine into a local DB via a simple API.

**Duration:** 1.5–2 days  

**Owner:** M2 (with M1 integrating).

**Scope:**
- M2:
  - Implement `api/main.py` with:
    - `POST /events` – accepts a JSON violation event.  
    - `GET /violations` – returns last N violations.  
  - Set up SQLite + SQLAlchemy models (`Violation` table).  
  - Basic `schemas.py` for request/response.  
- M1:
  - Extend `event_emitter.py`:
    - When a violation is detected, send `POST /events` with:
      - camera_id, track_id (can be dummy for now), violation_type, timestamp, confidence.  
  - Ensure CV engine doesn’t crash if API is down (log and skip).  
- No zones, no stats, no UI yet.

**Definition of Done:**
- Start API: `uvicorn api.main:app --reload`.  
- Start CV engine.  
- Trigger some violations (wave hands, remove helmet prop, etc.).  
- Call `GET /violations` (via browser or `curl`) and see stored violations.  
- DB file (`safety.db`) exists and contains data.

***

## Phase 3 – Zones & Multi-Camera (Core CV v2)  
**Goal:** Support 2 cameras and zone-based violations.

**Duration:** 2 days  

**Owner:** M1 (M2 helps with config/DB for zones).

**Scope:**
- M1:
  - Extend `camera_manager.py` to handle 2 cameras (loop over sources).  
  - Implement `zones.py`:
    - Load zone definitions from `configs/cameras.yaml`.  
    - `point_in_polygon` and `check_zones_for_point`.  
  - Update `rules.py`:
    - For each tracked person:
      - Compute centroid.  
      - Find which zone they’re in.  
      - Check required PPE for that zone.  
      - Emit violation only if missing PPE for N frames.  
- M2:
  - Add `Zone` and `Camera` tables.  
  - Add `zone` field to `Violation` model & schema.  
  - Create `seed_db.py` to insert 2 cameras and 2–3 zones.  

**Definition of Done:**
- Config file defines 2 cameras, each with 1–2 zones.  
- CV engine:
  - Opens 2 camera windows.  
  - Logs zone-specific violations (e.g., “NO_HELMET in Workbench-1”).  
- API stores zone name with each violation.  
- You can query `/violations` and see zone info.

***

## Phase 4 – Basic Dashboard (Live Stats + Violations Table)  
**Goal:** A working UI that shows real data from the API.

**Duration:** 1.5–2 days  

**Owner:** M3 (M2 supports API endpoints).

**Scope:**
- M2:
  - Add `GET /stats`:
    - Total violations today  
    - Violations per zone  
    - Violations per type.  
- M3:
  - Build `ui/app.py` with:
    - KPI cards (total violations today, top zone, top type).  
    - Violations table (calling `/violations`).  
    - Simple charts (using Plotly/Altair) for:
      - Violations per zone  
      - Violations per type.  
  - Implement `ui/utils.py` to call API endpoints.  
- No live video in UI yet, just stats & table.

**Definition of Done:**
- Run API + CV engine + UI.  
- Generate some violations.  
- Open Streamlit app:
  - See KPIs update after refresh.  
  - See violations table with real data.  
  - See charts rendered correctly.  

***

## Phase 5 – Tracking & Stable Violation Logic  
**Goal:** Add tracking IDs and more robust violation detection.

**Duration:** 1–1.5 days  

**Owner:** M1 (M4 starts analytics prep).

**Scope:**
- M1:
  - Switch to YOLO tracking:
    - `model.track(..., tracker="bytetrack.yaml")`.  
  - Parse `track_id` from results.  
  - Maintain `TrackState` (violation frame count per track).  
  - Emit violation only when:
    - Person in zone without required PPE for ≥ N frames.  
- M2:
  - Add `track_id` column to `Violation` table & schema.  
- M4:
  - Start `llm_service/analytics.py`:
    - Functions to compute:
      - Violations per zone/type/hour  
      - Repeat violators (track_id with multiple violations).  

**Definition of Done:**
- Violations now include `track_id`.  
- Same person isn’t counted as multiple unique violators within a short window.  
- You can query: “Show me violations for track_id X” (via API or DB).  

***

## Phase 6 – AI Incident Report & Q&A (LLM Integration)  
**Goal:** Generate daily reports and answer queries over safety data.

**Duration:** 1.5–2 days  

**Owner:** M4 (M2/M3 integrate).

**Scope:**
- M4:
  - Set up Ollama locally, pull `llama3.2` (or chosen model).  
  - Implement:
    - `llm_service/client.py` (HTTP to Ollama).  
    - `prompts.py` with:
      - `build_daily_report_prompt(data)`  
      - `build_query_prompt(query, data)`.  
    - `main.py` with:
      - `POST /generate_report`  
      - `POST /answer_query`.  
- M2:
  - Enhance `/report/daily`:
    - Return aggregated data (by zone, type, hour, repeat violators).  
- M3:
  - Add to UI:
    - “Generate Daily Report” button → calls `/report/daily` → `/generate_report` → shows text.  
    - “Ask Your Safety Data” box → calls `/answer_query` → shows answer.  

**Definition of Done:**
- Click “Generate Daily Report” → see a coherent 5–7 line summary.  
- Ask a question like “Which zone had most violations today?” → get a sensible answer.  
- All LLM calls are local (Ollama), no cloud APIs.

***

## Phase 7 – Live Camera View in UI (Demo Polish)  
**Goal:** Show live camera feeds with overlays in the dashboard.

**Duration:** 1–1.5 days  

**Owner:** M3 (M1 helps with frame streaming or snapshots).

**Scope:**
- Decide approach:
  - Option A (simpler):  
    - Keep OpenCV windows for live video.  
    - UI shows stats, charts, reports, and recent snapshots.  
  - Option B (more impressive):  
    - Stream frames from CV engine or API to UI:
      - Endpoint `/stream/<cam_id>` returns latest frame as JPEG.  
      - Streamlit displays via `st.image`.  
- M1:
  - If Option B: add endpoint or shared mechanism to expose latest frame per camera.  
- M3:
  - Add camera grid section to `app.py`.  
  - Ensure overlays (boxes, zones, IDs) are visible (either drawn in CV engine or in UI).

**Definition of Done:**
- Demo machine shows:
  - Live camera feeds (either in separate windows or embedded).  
  - Overlays with detections and zones.  
  - KPIs, charts, violations table, report, Q&A all working together.  

***

## Phase 8 – Hardening, Backup, and Demo Rehearsal  
**Goal:** Make the system stable and demo-proof.

**Duration:** 1–1.5 days  

**All Members.**

**Scope:**
- M1:
  - Optimize FPS (model size, resolution).  
  - Add fallback to pre-recorded video if webcams fail.  
- M2:
  - Add basic error handling:
    - DB locked → retry or in-memory buffer.  
    - API downtime → CV engine still runs, queues events.  
- M3:
  - Prepare:
    - Pre-seeded DB with sample violations (so charts aren’t empty at demo start).  
    - Pre-recorded demo video (screen capture of full flow).  
    - Pitch deck (problem, solution, architecture, impact).  
- M4:
  - Test LLM prompts with different data scenarios.  
  - Ensure LLM service degrades gracefully (e.g., shows “Report unavailable” instead of crashing).

**Definition of Done:**
- Full end-to-end rehearsal:
  - Start all services.  
  - Simulate violations.  
  - Show live dashboard, generate report, ask questions.  
  - Then simulate a failure (e.g., kill CV engine) and show backup video.  
- Everyone knows their demo role and talking points.

***

## Why This Phased Approach Matters

- Each phase is **small enough to fully test** before moving on.  
- You catch integration issues early (e.g., CV ↔ API, API ↔ UI, UI ↔ LLM).  
- You always have **something working** at the end of each phase, not a half-built monolith.  
- If time runs short, you can stop at Phase 6 or 7 and still have a **complete, demoable product**, not a broken “almost everything”.

***
