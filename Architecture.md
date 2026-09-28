## App Flow & Architecture

### 1) High-Level Architecture (Where Everything Lives)

All components run **locally** on one or two laptops (your RTX 4050 machines). No cloud is required for the demo.

**Processes:**

1. **CV Engine Process** (`cv_engine/main_loop.py`)
   - Lives on: **Laptop 1** (or same machine as API).  
   - Reads from 2–3 cameras (webcams or video files).  
   - Runs YOLO detection + tracking.  
   - Applies PPE + zone rules.  
   - Emits violation events via HTTP to the Backend API.

2. **Backend API Process** (`api/main.py`)
   - Lives on: **Laptop 1** (same as CV engine for low latency).  
   - FastAPI server on `http://localhost:8000`.  
   - Receives violation events (`POST /events`).  
   - Stores data in local DB (`safety.db`).  
   - Exposes:
     - `/violations`  
     - `/stats`  
     - `/report/daily`.

3. **LLM Service Process** (`llm_service/main.py`)
   - Lives on: **Laptop 2** (or same machine if powerful enough).  
   - FastAPI server on `http://localhost:8001`.  
   - Runs local LLM via **Ollama** (`http://localhost:11434`).  
   - Exposes:
     - `/generate_report`  
     - `/answer_query`.

4. **UI Process** (`ui/app.py` – Streamlit)
   - Lives on: **Laptop 1 or 2** (wherever you’ll demo).  
   - Streamlit app on `http://localhost:8501`.  
   - Calls:
     - Backend API (`:8000`) for stats, violations, daily data.  
     - LLM Service (`:8001`) for reports and Q&A.  
   - Shows:
     - Live camera grid (via direct CV preview windows or streamed frames).  
     - Dashboards, tables, charts.  
     - Report & Q&A panels.

**Data flow:**

- **Cameras → CV Engine → Backend API → DB**  
- **UI ↔ Backend API** (stats, violations, daily data)  
- **UI ↔ LLM Service** (reports, Q&A)  
- **LLM Service ↔ Ollama** (local LLM inference)

***

### 2) User Flow (Screen by Screen)

Assume the user is a **lab in-charge** opening the dashboard on a monitor in the lab office.

#### Screen 1: Login (Optional / Nice-to-Have)

- **URL:** `/` (Streamlit app can simulate login with a simple password box).  
- **Elements:**
  - Text input: “Enter access code”  
  - Button: “Login”  
- **Action:**
  - On click:
    - If correct → show Dashboard.  
    - If wrong → show error message.

*(You can skip real auth for hackathon and just go straight to Dashboard.)*

***

#### Screen 2: Main Dashboard

- **URL:** `/dashboard` (in Streamlit, this is just the main page).  
- **Sections (top to bottom):**

1. **Header**
   - Title: “Smart Lab Safety & PPE Compliance”  
   - Subtitle: “Lab A – Main Building”  
   - “Last updated: <timestamp>”  

2. **KPI Cards (top row)**
   - Card 1: “Violations Today” → number (e.g., 27)  
   - Card 2: “Most Violated Zone” → zone name (e.g., “Workbench-1”)  
   - Card 3: “Most Common Violation” → type (e.g., “NO_HELMET”)  
   - Card 4: “Peak Hour” → hour (e.g., “11–12”)  

3. **Live Camera Grid**
   - 2–3 panels, each showing:
     - Live video feed with overlays:
       - Bounding boxes (person, helmet, vest) with IDs.  
       - Zone polygons (colored overlays).  
       - Red flash or border when a violation occurs.  
   - Below each camera:
     - Camera name (e.g., “Cam1 – Lab A Entrance”).  
     - Current violation count for that camera (today).

4. **Charts Section**
   - Chart 1: “Violations per Zone” (bar chart).  
   - Chart 2: “Violations per Type” (bar or pie chart).  
   - Chart 3: “Violations by Hour” (line chart).  

5. **Recent Violations Table**
   - Table columns:
     - Timestamp  
     - Camera  
     - Zone  
     - Track ID  
     - Violation Type  
     - Confidence  
     - Snapshot (thumbnail).  
   - Clicking a row:
     - Opens a modal or side panel with:
       - Larger snapshot  
       - Full details (timestamp, zone, required PPE, missing PPE).  

6. **Filters Panel (sidebar or top)**
   - Date range picker (from–to).  
   - Dropdowns:
     - Camera  
     - Zone  
     - Violation type.  
   - Button: “Apply Filters” → refreshes charts & table.

***

#### Screen 3: AI Incident Report

- **Access:** Section on the same Dashboard page (scroll down) or a separate tab.  
- **Elements:**
  - Header: “AI Incident Report”  
  - Dropdown: “Select date” (default: today).  
  - Button: “Generate Daily Report”.  
  - Text area: Displays LLM-generated report.  

- **Action:**
  - User selects date (or keeps today).  
  - Clicks “Generate Daily Report”.  
  - UI:
    - Calls `GET /report/daily` on Backend API → gets aggregated data.  
    - Calls `POST /generate_report` on LLM Service with that data.  
    - Displays returned report text in the text area.  

- **Next:**
  - User can:
    - Copy report text.  
    - Optionally export as TXT/PDF (nice-to-have).  

***

#### Screen 4: Ask Your Safety Data (Q&A)

- **Access:** Section on Dashboard or separate tab.  
- **Elements:**
  - Header: “Ask Your Safety Data”  
  - Text input: “Ask a question about today’s safety data”  
  - Button: “Ask”  
  - Response area: displays LLM answer.  

- **Action:**
  - User types a query, e.g.:
    - “Which zone had the most violations this morning?”  
    - “How many helmet violations today?”  
  - Clicks “Ask”.  
  - UI:
    - Calls `GET /report/daily` to fetch today’s data.  
    - Calls `POST /answer_query` on LLM Service with `{query, data}`.  
    - Displays answer text.  

- **Next:**
  - User can ask follow-up questions.  

***

#### Screen 5: Violation Details (Modal / Side Panel)

- **Trigger:** Clicking a row in the Recent Violations table.  
- **Elements:**
  - Large snapshot image.  
  - Details:
    - Timestamp  
    - Camera name  
    - Zone name  
    - Track ID  
    - Violation type  
    - Required PPE vs detected PPE  
    - Confidence score.  
  - Button: “Close”.  

- **Action:**
  - User reviews details, then closes modal.  

***

### 3) What Happens After Each Key Button Press

| Button / Action | Frontend (UI) | Backend API | LLM Service | DB | CV Engine |
|-----------------|---------------|-------------|-------------|----|-----------|
| **Apply Filters** | Sends request to `/violations` and `/stats` with filters | Queries DB with filters, returns filtered violations & stats | – | Read-only queries | – |
| **Generate Daily Report** | Calls `/report/daily` → gets data; then calls `/generate_report` with data | Aggregates today’s violations, returns JSON | Receives data, builds prompt, calls Ollama, returns report text | Read-only aggregation | – |
| **Ask (Q&A)** | Calls `/report/daily` + `/answer_query` with `{query, data}` | Returns daily data | Builds Q&A prompt, calls Ollama, returns answer | Read-only | – |
| **Violation occurs (in real time)** | UI periodically polls `/stats` and `/violations` (or uses WebSocket if you implement) | Receives `POST /events` from CV engine, inserts violation into DB | – | Inserts new violation row | Detects violation, emits `POST /events` |
| **Refresh Stats** | Calls `/stats` | Aggregates counts from DB, returns JSON | – | Read-only | – |

***

## File and Folder Structure

Use this exact structure so your AI tool and team stay consistent:

```text
smart-lab-safety/
├─ README.md
├─ requirements.txt
├─ .env.example
├─ docker-compose.yml          (optional but recommended)
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
│  ├─ run_api.sh
│  ├─ run_api.bat
│  ├─ run_cv_engine.sh
│  ├─ run_cv_engine.bat
│  ├─ run_ui.sh
│  ├─ run_ui.bat
│  ├─ run_llm.sh
│  ├─ run_llm.bat
│  └─ seed_db.py
│
└─ tests/
   ├─ __init__.py
   ├─ test_zones.py
   ├─ test_rules.py
   └─ test_analytics.py
```

**Ownership by role:**

- **M1 (CV Core):** `cv_engine/*`, `configs/*`, `tests/test_zones.py`, `tests/test_rules.py`.  
- **M2 (Backend & DB):** `api/*`, `db_migrations/*`, `scripts/seed_db.py`, `scripts/run_api.*`.  
- **M3 (Frontend & Demo):** `ui/*`, `scripts/run_ui.*`.  
- **M4 (LLM & Analytics):** `llm_service/*`, `tests/test_analytics.py`, `scripts/run_llm.*`.

***

## Tech Stack

### Core Languages & Runtimes

- **Python 3.10+** (all services: CV engine, API, UI, LLM service).  
- **Node.js** – not required unless you add a custom web frontend later.

### Computer Vision & Media

- **Ultralytics YOLOv8** – object detection & tracking (`yolov8n.pt` / `yolov8s.pt`).  
- **OpenCV (`opencv-python`)** – camera I/O, frame processing, drawing overlays.  
- **NumPy** – array operations, geometry helpers.  
- **Pillow** – image handling for snapshots/thumbnails.

### Backend & Database

- **FastAPI** – REST API for events, violations, stats, reports.  
- **Uvicorn** – ASGI server to run FastAPI.  
- **SQLAlchemy** (or **SQLModel**) – ORM for DB access.  
- **SQLite** (default) – local file-based DB (`safety.db`).  
  - Optionally **PostgreSQL** via Docker if you want to look more “prod-ready”.  
- **Pydantic** – request/response schemas (built into FastAPI).  

### Frontend / Dashboard

- **Streamlit** – main dashboard UI (live stats, tables, charts, report & Q&A panels).  
- **Plotly** (or **Altair**) – interactive charts (violations per zone/type/hour).  
- **Pandas** – convenient data manipulation for charts/tables.

### LLM & AI

- **Ollama** – local LLM server (runs on `http://localhost:11434`).  
- **Models via Ollama:**  
  - `llama3.2` (or `mistral`, `phi3`) – for report generation & Q&A.  
- **requests / httpx** – Python HTTP clients to call Ollama and internal APIs.

### DevOps & Quality

- **Git + GitHub** – version control, collaboration.  
- **pytest** – unit tests for zone logic, rules, analytics.  
- **black** / **ruff** – code formatting & linting.  
- **Docker** / **Docker Compose** (optional but strong):
  - Services: `api`, `db` (if Postgres), `llm` (Ollama), `ui` (Streamlit).  
  - One-command deploy for pilot installations.

### Auth (If You Implement)

- For hackathon: **simple hardcoded password** in Streamlit (no external provider).  
- If you extend later:  
  - **FastAPI + JWT** (e.g., `PyJWT` or `fastapi-users`) for real auth.  
  - No external auth provider needed for v1.

### Hosting & Deployment (For Hackathon)

- **All local**:
  - CV engine, API, DB, UI, Ollama all run on your laptops.  
- No external hosting required.  
- For future pilots:
  - Deploy on a local server in the lab (Ubuntu box with GPU).  
  - Use Docker Compose to manage services.

***
