# Project Memory – Smart Lab Safety & PPE Compliance

**Last updated:** 2026-09-28  
**Hackathon:** HackNex 2026 (Computer Vision track)  
**Team:** 4 members (M1: CV Core, M2: Backend/DB, M3: Frontend/Demo, M4: LLM/Analytics)

***

## 1) Project Vision (One Paragraph)

A **multi-camera smart lab safety system** that automatically monitors engineering/college labs in real time, detects whether people are wearing required PPE (helmet, vest, goggles), checks if they enter designated safety zones without proper gear, and logs every violation with snapshots and timestamps. The system runs locally (no cloud), shows live camera feeds with overlays on a dashboard, provides analytics (violations per zone/hour/type), and uses a local LLM to generate daily safety reports and answer natural-language queries like “Which zone had the most violations today?” It is designed for lab in-charges and safety officers to reduce accidents, enforce compliance, and get data-driven insights without manual monitoring.

***

## 2) Target Users

- **Primary:**  
  - Lab in-charges / lab supervisors in engineering colleges and polytechnics (age ~25–55).  
  - Safety officers / HSE executives in small/medium manufacturing units and training centers.  
- **Skill level:** Basic computer literacy; no ML/CV expertise required.  
- **Problem:**  
  - PPE non-compliance in labs/workshops leads to accidents.  
  - Manual monitoring is inconsistent and time-consuming.  
  - No structured data on violations (when, where, what type).  
  - Need an always-on, automated, local system for detection, logging, and reporting.

***

## 3) Core Feature Set

### Must-Have

1. Multi-camera live monitoring (2–3 cameras) with overlays (boxes, IDs, zones).  
2. PPE detection (person, helmet, vest, optionally goggles).  
3. Zone-based violation logic (per-zone required PPE, temporal smoothing).  
4. Violation logging with snapshots, timestamps, track IDs.  
5. Backend API (FastAPI) + SQLite DB for events, violations, stats.  
6. Dashboard UI (Streamlit):
   - KPIs (violations today, top zone, top type, peak hour).  
   - Violations table with filters.  
   - Charts (per zone/type/hour).  
7. AI incident reporting (local LLM via Ollama):
   - Daily report generation.  
   - Natural-language Q&A over safety data.  
8. Local-first, offline operation (no cloud APIs during demo).  
9. Config-driven behavior (cameras, zones, PPE rules in YAML).

### Nice-to-Have (if time permits)

- Basic user roles (admin/viewer).  
- Export violations to CSV / simple PDF report.  
- On-screen alerts for violations.  
- Advanced analytics (repeat violators, zone risk scores).  
- Dockerized deployment.  

***

## 4) Architecture Overview

**Processes (all local):**

1. **CV Engine** (`cv_engine/main_loop.py`)  
   - Reads 2–3 cameras.  
   - YOLOv8 detection + tracking.  
   - PPE + zone rules → violation events.  
   - Emits `POST /events` to Backend API.

2. **Backend API** (`api/main.py`, port 8000)  
   - `POST /events` – ingest violations.  
   - `GET /violations` – list violations.  
   - `GET /stats` – KPIs.  
   - `GET /report/daily` – aggregated daily data.  
   - SQLite DB (`safety.db`).

3. **LLM Service** (`llm_service/main.py`, port 8001)  
   - Ollama (local LLM) on `:11434`.  
   - `POST /generate_report` – daily incident report.  
   - `POST /answer_query` – Q&A over safety data.

4. **UI** (`ui/app.py`, Streamlit, port 8501)  
   - Calls Backend API for stats, violations, daily data.  
   - Calls LLM Service for reports & Q&A.  
   - Shows KPIs, charts, violations table, report & Q&A panels.  
   - Live camera view (OpenCV windows or streamed frames).

**Data flow:**

Cameras → CV Engine → Backend API → DB  
UI ↔ Backend API (stats, violations, daily)  
UI ↔ LLM Service (reports, Q&A)  
LLM Service ↔ Ollama

***

## 5) File & Folder Structure

```text
smart-lab-safety/
├─ README.md
├─ requirements.txt
├─ .env.example
├─ docker-compose.yml          (optional)
│
├─ configs/
│  ├─ cameras.yaml
│  └─ ppe_rules.yaml
│
├─ cv_engine/
│  ├─ __init__.py
│  ├─ camera_manager.py
│  ├─ detector.py
│  ├─ tracker.py
│  ├─ zones.py
│  ├─ rules.py
│  ├─ event_emitter.py
│  └─ main_loop.py
│
├─ api/
│  ├─ __init__.py
│  ├─ main.py
│  ├─ config.py
│  ├─ db.py
│  ├─ models.py
│  ├─ schemas.py
│  ├─ endpoints_events.py
│  ├─ endpoints_violations.py
│  ├─ endpoints_stats.py
│  └─ endpoints_report.py
│
├─ db_migrations/
│  └─ init_db.sql
│
├─ ui/
│  ├─ __init__.py
│  ├─ app.py
│  ├─ components/
│  │  ├─ __init__.py
│  │  ├─ camera_grid.py
│  │  ├─ violation_table.py
│  │  └─ charts.py
│  └─ utils.py
│
├─ llm_service/
│  ├─ __init__.py
│  ├─ client.py
│  ├─ prompts.py
│  ├─ analytics.py
│  └─ main.py
│
├─ scripts/
│  ├─ run_api.sh / .bat
│  ├─ run_cv_engine.sh / .bat
│  ├─ run_ui.sh / .bat
│  ├─ run_llm.sh / .bat
│  └─ seed_db.py
│
└─ tests/
   ├─ __init__.py
   ├─ test_zones.py
   ├─ test_rules.py
   └─ test_analytics.py
```

***

## 6) Tech Stack (Fixed)

- **Language:** Python 3.10+  
- **CV:** Ultralytics YOLOv8, OpenCV, NumPy  
- **Backend:** FastAPI, Uvicorn, SQLAlchemy, SQLite  
- **Frontend:** Streamlit, Plotly, Pandas  
- **LLM:** Ollama + Llama 3.2 (or Mistral)  
- **DevOps:** Git/GitHub, pytest, black, ruff  
- **Optional:** Docker/Docker Compose

***

## 7) Design System (Colors, Fonts, Theme)

- **Theme:** Light mode only (for hackathon).  
- **Background:** `#F5F7FA`  
- **Surface:** `#FFFFFF`  
- **Border:** `#E3E8EF`  
- **Primary Blue:** `#2563EB` (hover `#1D4ED8`)  
- **Text:** Primary `#0F172A`, Secondary `#475569`, Muted `#94A3B8`  
- **Status Colors:**  
  - Safe: `#16A34A`  
  - Warning: `#F59E0B`  
  - Violation: `#DC2626`  
- **Font:** `Inter, system-ui, -apple-system, Segoe UI, Roboto, Arial, sans-serif`  
- **Type scale:**  
  - h1: 28–32px, bold  
  - h2: 22–24px, bold  
  - h3: 18–20px, semi-bold  
  - Body: 15–16px  
  - Metrics: 28–32px, bold  

Reference vibe: **Grafana-style ops dashboard + enterprise HSE tool** (data-dense, high-contrast, serious).

***

## 8) Development Principles (What to Use / Avoid)

### What to Use

- `snake_case` for files/functions, `PascalCase` for classes.  
- Type hints + docstrings on all public functions/classes.  
- Config-driven behavior (no hardcoded zones/PPE in logic).  
- FastAPI endpoints thin; business logic in service modules.  
- Streamlit-only frontend; Plotly for charts.  
- Ollama-only local LLM; prompts in `prompts.py`.  
- pytest for tests; black + ruff for format/lint.

### What to Avoid

- No cloud APIs (LLM, DB, auth) for hackathon.  
- No custom model training; use pre-trained YOLOv8.  
- No React/Next.js; Streamlit only.  
- No mixed ORMs; SQLAlchemy only.  
- No business logic in UI; no DB queries in CV engine.  
- No over-engineered auth; simple or none for v1.  
- No dark mode during hackathon.

***

## 9) Phased Build Plan (Summary)

1. **Phase 0 – Skeleton & Dev Setup**  
   - Repo structure, requirements, hello-world services.  

2. **Phase 1 – Single-Camera PPE Detection**  
   - One webcam, YOLO detection, console violations, OpenCV preview.  

3. **Phase 2 – Backend API + DB**  
   - FastAPI `/events`, `/violations`; SQLite; CV engine posts events.  

4. **Phase 3 – Zones & Multi-Camera**  
   - 2 cameras, zone config, zone-based violations, seed DB.  

5. **Phase 4 – Basic Dashboard**  
   - KPIs, violations table, charts (no live video yet).  

6. **Phase 5 – Tracking & Stable Logic**  
   - YOLO tracking, track IDs, temporal smoothing, repeat violator logic.  

7. **Phase 6 – AI Report & Q&A**  
   - Ollama setup, `/generate_report`, `/answer_query`, UI integration.  

8. **Phase 7 – Live Camera View in UI**  
   - Camera grid with overlays (OpenCV windows or streamed frames).  

9. **Phase 8 – Hardening & Demo Rehearsal**  
   - FPS optimization, backup video, pre-seeded data, pitch rehearsal.

***

## 10) Current State (Update This Every Session)

**As of 2026-09-28 (end of planning, before heavy implementation):**

- **Decisions made:**
  - Topic: Multi-camera PPE + zone violations + local LLM reports.  
  - Stack: YOLOv8, FastAPI, SQLite, Streamlit, Ollama.  
  - Design: Light mode, Inter font, Grafana/HSE vibe, specific color palette.  
  - Phases: 0–8 defined, with clear owners and “done” criteria.  

- **What’s built so far:**
  - Repo structure defined.  
  - This memory document created.  
  - No substantial code yet (starting from next session).

- **Open questions / risks:**
  - Whether to implement live video in Streamlit or keep OpenCV windows separate.  
  - Exact YOLO class mapping for PPE (may need to rely on person + heuristic if no PPE classes).  

*(Update this section after every major work session.)*

***

## 11) Change Log (Append New Entries Each Session)

**2026-09-28 – Initial planning session**
- Defined project vision, target users, and feature set.  
- Fixed architecture: CV engine → API → DB, UI ↔ API ↔ LLM.  
- Finalized folder structure and tech stack.  
- Agreed on design system (colors, fonts, theme).  
- Defined phased build plan (Phases 0–8).  
- Created this `PROJECT_MEMORY.md`.

*(After each future session, add a new entry like:)*  
**YYYY-MM-DD – Session summary**
- What was implemented (e.g., “Phase 1 complete: single-camera detection working”).  
- What changed (e.g., “Switched tracker from ByteTrack to BoT-SORT due to X”).  
- Why (e.g., “Better FPS on RTX 4050”, “Simpler integration”).  
- New open questions or risks.

***

## 12) How to Use This Document

- **At the start of every session:**
  - Open `PROJECT_MEMORY.md`.  
  - Read Sections 1–9 to re-ground yourself (or paste into AI tool).  
- **At the end of every session:**
  - Update:
    - Section 10: **Current State** (what’s working now).  
    - Section 11: **Change Log** (what changed and why).  
- **When using an AI coding assistant:**
  - Paste this entire file (or latest version) at the start of the chat.  
  - Then ask for help with the next phase/task.

***
