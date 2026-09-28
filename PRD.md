## What to Build

Build a **multi-camera smart lab safety system** that automatically monitors engineering/college labs in real time, detects whether people are wearing required PPE (helmet, vest, goggles), checks if they enter designated safety zones without proper gear, and logs every violation with snapshots and timestamps. The system runs on local hardware (no cloud), shows live camera feeds with overlays on a dashboard, provides analytics (violations per zone/hour/type), and uses a local LLM to generate daily safety reports and answer natural-language queries like “Which zone had the most violations today?” It is designed for lab in-charges and safety officers to reduce accidents, enforce compliance, and get data-driven insights without manual monitoring.

***

## Target Users

- **Primary users:**  
  - **Lab in-charges / lab supervisors** in engineering colleges and polytechnics (age ~25–55).  
  - **Safety officers / HSE executives** in small/medium manufacturing units and training centers.  

- **Technical skill level:**  
  - Basic computer literacy (can use a browser, click buttons, read dashboards).  
  - No ML/CV expertise required; they just need to view dashboards, export reports, and configure simple settings (e.g., zone names, thresholds).

- **Problem they’re trying to solve:**  
  - Students/workers often skip PPE (helmets, vests, goggles) in labs/workshops, leading to accidents.  
  - Manual monitoring by staff is inconsistent and time-consuming.  
  - There is no structured data on violations (when, where, what type), making it hard to improve safety.  
  - They need an **always-on, automated system** that:
    - Detects PPE violations in real time  
    - Logs incidents with evidence (snapshots, timestamps)  
    - Summarizes daily/weekly safety status in plain language  
    - Helps them enforce rules and justify safety investments.

***

## Features of the App

### Must-Have Features (Core – Build These First)

1. **Multi-Camera Live Monitoring**
   - Support for **2–3 camera feeds** (webcams or IP cameras).  
   - Real-time display of each camera with:
     - Bounding boxes around **people**, **helmets**, **vests**, (optionally **goggles**).  
     - **Track IDs** assigned to each person.  
     - Visual overlays for **safety zones** (colored polygons/rectangles).  

2. **PPE Detection & Zone Violation Logic**
   - Detect whether each person in a zone is wearing required PPE based on config (e.g., Lab-A requires helmet + vest).  
   - Define **zones per camera** with:
     - Name (e.g., “Workbench-1”, “Entrance”)  
     - Polygon/rectangle coordinates  
     - Required PPE list.  
   - Emit a **violation event** only if:
     - Person is inside a zone, and  
     - Missing required PPE for at least **N consecutive frames** (to avoid flicker).  

3. **Violation Logging with Snapshots**
   - For each violation, store:
     - Camera ID, zone name, track ID  
     - Violation type (e.g., `NO_HELMET`, `NO_VEST`)  
     - Timestamp  
     - Confidence score  
     - Snapshot image path (or base64).  
   - Store all data in a local database (SQLite/PostgreSQL).  

4. **Backend API**
   - REST endpoints to:
     - Receive violation events from CV engine (`POST /events`).  
     - Query violations with filters (`GET /violations?from_date=...&to_date=...&zone=...`).  
     - Get stats/KPIs (`GET /stats`).  
     - Get daily aggregated data for reports (`GET /report/daily`).  

5. **Dashboard UI (Streamlit or similar)**
   - **Live camera grid**:
     - 2–3 camera feeds with overlays (boxes, IDs, zones).  
   - **KPIs at a glance**:
     - Total violations today  
     - Violations per zone  
     - Violations per PPE type  
     - Peak violation hour.  
   - **Recent violations table**:
     - Columns: timestamp, camera, zone, track ID, violation type, confidence, snapshot thumbnail.  
     - Ability to click a row and see a larger snapshot + details.  
   - **Filters**:
     - By date range, camera, zone, violation type.  

6. **AI Incident Reporting (Local LLM)**
   - **Daily report generation**:
     - Button: “Generate Daily Report”.  
     - System fetches today’s violations, aggregates by type/zone/hour.  
     - Calls local LLM (Ollama + Llama/Mistral) with a structured prompt.  
     - Displays a 5–7 line plain-language report highlighting:
       - Total violations  
       - Most problematic zone & PPE type  
       - Time patterns (e.g., “most violations during 11–12”)  
       - Simple recommendations.  
   - **Natural-language Q&A**:
     - Text box: “Ask your safety data”.  
     - Example queries:
       - “Which zone had the most violations this morning?”  
       - “How many helmet violations today?”  
     - Backend aggregates relevant stats, LLM formats an answer.  

7. **Local-First, Offline Operation**
   - Entire system (CV, API, DB, UI, LLM) runs **locally** on college/lab hardware.  
   - No dependency on external cloud APIs during demo or deployment.  
   - Emphasize **privacy**: video and violation data never leave the premises.

8. **Basic Configuration**
   - Config files (YAML/JSON) to define:
     - Cameras (ID, name).  
     - Zones per camera (name, polygon, required PPE).  
     - Violation thresholds (min frames, confidence thresholds).  
   - Simple mechanism to reload config without code changes.

***

### Nice-to-Have Features (Add If Time Permits)

1. **User Accounts & Roles (Basic)**
   - Simple login (even hardcoded or single admin user).  
   - Roles:
     - **Admin**: can view all cameras, export data, configure zones.  
     - **Viewer**: can only view dashboards and reports.  

2. **Export & Reporting**
   - Export violations to CSV/Excel (filtered by date/zone/type).  
   - Export daily/weekly PDF report (LLM-generated text + key charts).  

3. **Alerts & Notifications**
   - On-screen alert (popup / red flash) when a violation occurs.  
   - Optional: sound alert or simulated “notification” in UI.  
   - Future idea: integrate with email/SMS gateway (not required for hackathon).  

4. **Advanced Analytics**
   - Repeat violator detection (track IDs with multiple violations in a day/week).  
   - Zone risk score (combine violation count, severity, time-of-day).  
   - Trend charts (violations per day over a week).  

5. **Multi-Session / Multi-Lab Support**
   - Ability to switch between different labs/shifts in the UI.  
   - Separate stats per lab.  

6. **Simple Anomaly Detection**
   - Flag days/hours with unusually high violations (e.g., >2x average).  
   - Show these as “anomalies” in the dashboard.  

7. **Dockerized Deployment**
   - `docker-compose.yml` to run:
     - CV engine (as a service)  
     - API + DB  
     - UI  
     - Ollama  
   - One-command deploy for pilot installations.  

8. **Basic Camera Health Monitoring**
   - Detect if a camera feed is lost or frozen.  
   - Show a warning in the UI (“Camera 2 offline”).  

***
