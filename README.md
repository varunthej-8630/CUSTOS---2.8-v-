# CUSTOS 2.8 — Autonomous Edge AI Threat Detection & People Intelligence Platform

[![Build Status](https://img.shields.io/badge/build-passing-brightgreen.svg)](https://github.com/)
[![Tests](https://img.shields.io/badge/tests-passing%20%28100%25%29-success.svg)](https://github.com/)
[![Python Version](https://img.shields.io/badge/python-3.8%20%7C%203.9%20%7C%203.10%20%7C%203.11-blue.svg)](https://python.org)
[![Framework](https://img.shields.io/badge/framework-Flask%20%7C%20Socket.IO%20%7C%20OpenCV%20%7C%20YOLOv8%20%7C%20YuNet%20%7C%20SFace-orange.svg)](https://github.com/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

**CUSTOS** is an enterprise-grade, edge-deployed autonomous Computer Vision & AI Security Platform. Designed for mission-critical physical perimeter defense, CUSTOS unifies real-time object tracking, multi-camera zone monitoring, 7-condition optical tamper protection, biometric face intelligence, and zero-spam incident lifecycle orchestration into a unified security command center.

---

## 📑 Table of Contents

1. [Key Platform Capabilities](#-key-platform-capabilities)
2. [High-Level Architecture](#-high-level-architecture)
3. [Deep-Dive Core Modules](#-deep-dive-core-modules)
   - [AI Perception & Multi-Object Tracking](#1-ai-perception--multi-object-tracking)
   - [Biometric Face Intelligence & Identity Layer](#2-biometric-face-intelligence--identity-layer)
   - [7-Condition Optical Tamper Engine & 15s Circular Pre-Roll](#3-7-condition-optical-tamper-engine--15s-circular-pre-roll)
   - [Zero-Spam Incident Lifecycle & State Machine](#4-zero-spam-incident-lifecycle--state-machine)
   - [Verifiable Evidence Capture Pipeline](#5-verifiable-evidence-capture-pipeline)
4. [Web Command Center & User Interface](#-web-command-center--user-interface)
5. [Project Structure](#-project-structure)
6. [Prerequisites & System Requirements](#-prerequisites--system-requirements)
7. [Installation & Setup Guide](#-installation--setup-guide)
8. [Running the Application](#-running-the-application)
9. [Default Authentication & RBAC](#-default-authentication--rbac)
10. [REST API Reference](#-rest-api-reference)
11. [Socket.IO Real-Time Event Protocol](#-socketio-real-time-event-protocol)
12. [Configuration Reference](#-configuration-reference)
13. [Testing & Verification Protocol](#-testing--verification-protocol)
14. [Production Deployment & Windows Service Setup](#-production-deployment--windows-service-setup)

---

## 🚀 Key Platform Capabilities

- **Real-Time Edge Perception**: YOLOv8-powered multi-class perception (persons, vehicles, backpacks, anomalous objects) with temporal track smoothing.
- **Biometric Face Intelligence (Stage 2.8)**: YuNet face detection, 5-point landmark alignment, and SFace 128-dimensional embedding matching ($\ge 0.40$ cosine threshold) with dynamic quality assessment.
- **Automated Face Clustering**: Agglomerative clustering of unrecognized individuals across camera feeds into persistent cluster profiles with single-click conversion to permanent identities.
- **Watchlist & Suspicious Identity Escalation**: Three-tier classification (`KNOWN`, `UNKNOWN`, `SUSPICIOUS`) with instant alert triggers and audio dispatch upon watchlist detection.
- **7-Condition Optical Tamper Detection**: Instant detection of lens covering, spray/defocusing, camera shift/displacement, disconnection, freezing, brightness flare, and darkness shock.
- **15-Second Circular In-Memory Pre-Roll**: Circular frame buffer preserving $15\,\text{seconds}$ of footage prior to incident trigger for forensic pre-roll evidence video generation.
- **Zero-Spam Incident State Machine**: Deterministic deduplication ensuring one continuous incident per breach/tamper event with exit grace tracking and live dwell timers.
- **Forensic Video & Snapshot Evidence**: Auto-generated trigger JPEGs and MP4 video recordings verified with on-disk integrity checks.
- **Role-Based Access Control (RBAC)**: Enterprise security model featuring `Admin`, `Operator`, and `Viewer` tiers.

---

## 🏛 High-Level Architecture

```
                               ┌────────────────────────┐
                               │  Camera VideoCapture   │
                               │  (RTSP / WebCam / File)│
                               └───────────┬────────────┘
                                           │ (Single Frame Pipeline)
                      ┌────────────────────┴────────────────────┐
                      ▼                                         ▼
          ┌───────────────────────┐                 ┌───────────────────────┐
          │ Rolling 15s Pre-Roll  │                 │ Temporal Tamper       │
          │ Circular Frame Buffer │                 │ Detection Engine      │
          └───────────┬───────────┘                 └───────────┬───────────┘
                      │                                         │
                      ▼                                         ▼
          ┌─────────────────────────────────────────────────────────────────┐
          │                      Perception Pipeline                        │
          │  ┌───────────────────────────┐   ┌───────────────────────────┐  │
          │  │ YOLOv8 Object Tracking    │   │ YuNet + SFace Biometrics  │  │
          │  │ (Persons, Bags, Vehicles) │   │ (Face Recog & Clustering) │  │
          │  └─────────────┬─────────────┘   └─────────────┬─────────────┘  │
          └────────────────┼───────────────────────────────┼────────────────┘
                           │                               │
                           └───────────────┬───────────────┘
                                           ▼
          ┌─────────────────────────────────────────────────────────────────┐
          │             Incident Lifecycle Manager & State Machine          │
          │  - Deterministic Key Deduplication ("zone:cam:subject:name")    │
          │  - Trigger Snapshot Capture & Verification                      │
          │  - Dynamic Risk Scoring & Dwell-Time Escalation                 │
          │  - Post-Grace MP4 Video Staged Assembly (Pre + Event + Post)    │
          └──────────────┬───────────────────────────────────┬──────────────┘
                         │                                   │
                         ▼                                   ▼
          ┌────────────────────────────┐       ┌────────────────────────────┐
          │ SQLite ORM Persistence     │       │ Flask-SocketIO Realtime    │
          │ (WAL Mode, Thread-Safe)    │       │ (Alerts, Threats, Live AI) │
          └──────────────┬─────────────┘       └─────────────┬──────────────┘
                         │                                   │
                         └─────────────────┬─────────────────┘
                                           ▼
                         ┌───────────────────────────────────┐
                         │  CUSTOS Command Center Frontend   │
                         │  (Vanilla JS, Dark Modern Glass)  │
                         └───────────────────────────────────┘
```

---

## 🔬 Deep-Dive Core Modules

### 1. AI Perception & Multi-Object Tracking
- **Detection Model**: YOLOv8 neural network optimized for low latency on edge CPUs and CUDA GPUs.
- **Dynamic Dual-Zone Monitoring**:
  - **HIGH SECURITY Zone (Red)**: Instant perimeter breach alarm triggering immediate incident recording and operator dispatch.
  - **OBSERVATION / WATCH Zone (Orange/Green)**: Loitering and dwell-time monitoring with automated score escalation.
- **Track Smoothing**: Maintains persistent identity across brief line-of-sight occlusions.

### 2. Biometric Face Intelligence & Identity Layer
- **Detection & Landmarks**: OpenCV YuNet neural network detecting faces with sub-millisecond inference and extracting 5 facial landmarks (eyes, nose tip, mouth corners).
- **Quality Filtering**: Laplacian variance blur scoring, minimum face box size ($40\times40\,\text{px}$), and yaw/pitch orientation checks filter out degraded face crops.
- **Feature Extraction**: OpenCV SFace generates 128-dimensional L2-normalized embeddings.
- **Cosine Similarity Matching**: Computes cosine distance against enrolled active profiles; matches above threshold ($\ge 0.40$) resolve identity instantly.
- **Unknown Clustering**: Automatically aggregates unrecognized faces into `PersonCluster` nodes via agglomerative similarity clustering without manual labeling.

### 3. 7-Condition Optical Tamper Engine & 15s Circular Pre-Roll
CUSTOS detects 7 distinct physical and signal tampering anomalies:
1. **Lens Obstruction / Blur**: Drop in Laplacian variance below dynamic baseline.
2. **Lens Covering / Blackout**: Sudden drop in mean pixel luminance ($< 15.0$).
3. **Camera Displacement / Shift**: Background subtraction structural difference ($> 65\%$).
4. **Video Signal Loss**: Feed disconnection, packet drops, or EOF conditions.
5. **Frame Freezing**: Zero frame difference across consecutive intervals.
6. **Optical Flare / Blinding**: Sudden extreme luminance spikes ($> 245.0$).
7. **Darkness Shock**: Sudden global illumination loss.

- **Temporal Confirmation**: Requires sustained anomaly duration ($0.8\,\text{s}$) to prevent momentary glitches from triggering false alarms.
- **15s Circular Pre-Roll**: Circular RAM buffer continuously stores the preceding 450 frames. When tampering occurs, the final forensic video contains 15 seconds of pre-tamper footage, the tamper event, and recovery.

### 4. Zero-Spam Incident Lifecycle & State Machine
- **Deterministic Deduplication Key**:
  - Intrusion: `("zone", camera_id, subject_id, zone_name, "ZONE_BREACH")`
  - Tamper: `("tamper", camera_id, "TAMPER")`
- **Single Canonical Alert**: An ongoing breach or camera covering maintains **ONE** canonical incident record. Dwell duration, risk scores, and event logs update in real time without creating duplicate alerts.
- **Exit Grace Period**: Configurable grace window ($3.0\text{--}5.0\,\text{s}$) prevents track flicker from fragmenting single events into multiple records.

### 5. Verifiable Evidence Capture Pipeline
- **Dual Media Assets**: Captures both a high-resolution trigger JPEG snapshot and an assembled MP4 video clip.
- **Integrity Validation**: Media is validated on disk (file existence, non-zero bytes, decode check) before state is set to `AVAILABLE`.
- **Smart Path Resolver**: Path resolution automatically handles relocated project directories, ensuring legacy database records load reliably.

---

## 🖥 Web Command Center & User Interface

The web interface is accessible via modern browsers at `http://localhost:5000`:

| View | Purpose & Key Features |
| :--- | :--- |
| **Live Monitor** | Interactive dual-zone canvas drawing, high-framerate MJPEG stream, real-time bounding boxes, live threat gauges, and situation briefings. |
| **Security Dashboard** | System overview, active situation briefings, threat curves, and 24-hour activity distribution. |
| **Alert Center** | Server-side filtered alerts (`CRITICAL`, `HIGH`, `MEDIUM`, `LOW`), search, explainable AI reasons, and single-click operator resolution with audit notes. |
| **Evidence Center** | Forensic video player, pre-roll playback, high-res snapshot inspector, chronological audit timelines, and single-click JSON evidence export. |
| **People Intelligence** | Face gallery, known profile manager, suspicious watchlist catalog, reference photo enrollment, cluster-to-profile conversion, and cross-camera appearance history. |
| **Security Analytics** | Risk trends, hourly incident density curves, and camera activity heatmaps. |

---

## 📁 Project Structure

```
custos-stage2.8/
├── config/
│   ├── __init__.py
│   └── settings.py               # Centralized configuration & environment loader
├── core/
│   ├── __init__.py
│   └── logging.py                # Colorized thread-safe logging framework
├── data/
│   ├── evidence/                 # Saved incident snapshots & MP4 videos
│   ├── people/                   # Enrolled face profiles & cluster snapshots
│   ├── recordings/               # Continuous recordings & pre-roll clips
│   ├── snapshots/                # Periodic & trigger snapshots
│   └── weights/                  # YOLOv8, YuNet, and SFace model weights
├── database/
│   ├── __init__.py
│   ├── database_manager.py       # Thread-safe SQLite SQLAlchemy ORM manager
│   └── models.py                 # Incident, Alert, PersonProfile, PersonFace, User models
├── engine/
│   ├── camera/
│   │   ├── frame_buffer.py       # Rolling 15s circular in-memory frame buffer
│   │   └── tamper_detector.py    # 7-condition optical tamper detection engine
│   ├── evidence/
│   │   ├── media_recorder.py     # Background MP4 video writer & trimmer
│   │   ├── media_resolver.py     # Smart media path resolver
│   │   └── media_validator.py    # On-disk file integrity validation
│   ├── face/
│   │   ├── face_engine.py        # YuNet detection + SFace recognition engine
│   │   ├── face_quality.py       # Laplacian blur & orientation quality evaluator
│   │   └── face_store.py         # Embedding cache & similarity search
│   ├── incident/
│   │   ├── incident_manager.py   # State machine, deduplication & lifecycle orchestrator
│   │   └── risk_engine.py        # Threat score & severity evaluator
│   ├── vision/
│   │   ├── ai_engine.py          # Unified AI perception pipeline coordinator
│   │   ├── detector.py           # YOLOv8 multi-class object perception
│   │   ├── tracker.py            # Temporal track maintenance & smoothing
│   │   └── zone_monitor.py       # Polygon containment & dwell calculation
│   └── zone_store.py             # Thread-safe zone configuration storage
├── frontend/
│   ├── index.html                # Unified dark-mode Command Center application
│   └── app.js                    # Core UI state & chart controller
├── tests/                        # Comprehensive Pytest test suite (100% passing)
├── web/
│   ├── __init__.py
│   └── server.py                 # Flask server, REST APIs, Socket.IO & Auth
├── DEPLOYMENT.md                 # Production deployment & service installation guide
├── requirements.txt              # Production Python dependencies
├── run_server.py                 # Main entrypoint: starts full perception & web server
└── run_debug.py                  # Headless debug mode for terminal testing
```

---

## ⚙ Prerequisites & System Requirements

### Hardware Requirements
- **CPU**: Intel Core i5 / AMD Ryzen 5 or higher (Edge/x86_64)
- **RAM**: Minimum 4 GB (8 GB recommended for 15s pre-roll buffer)
- **Camera**: Standard USB Webcam, Integrated Camera, or RTSP IP Camera stream
- **GPU (Optional)**: NVIDIA GPU with CUDA 11.8+ for hardware-accelerated YOLO & SFace inference

### Software Requirements
- **Operating System**: Windows 10/11, Ubuntu 20.04+, or macOS
- **Python**: `3.8`, `3.9`, `3.10`, or `3.11` (Python 3.10 recommended)
- **C++ Build Tools**: Required for OpenCV DNN modules

---

## 📦 Installation & Setup Guide

### 1. Clone Repository & Navigate
```bash
git clone https://github.com/your-org/custos.git
cd custos-stage2.8
```

### 2. Create and Activate Virtual Environment
```bash
# Windows
python -m venv venv
.\venv\Scripts\activate

# Linux / macOS
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Required Dependencies
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### 4. Verify AI Model Weights
Ensure the model weight files are located in `data/weights/`:
- `yolov8n.pt` — YOLOv8 Nano object perception
- `face_detection_yunet_2023mar.onnx` — YuNet face detection & landmarks
- `face_recognition_sface_2021dec.onnx` — SFace 128-dim face embeddings

---

## 🏃 Running the Application

### Production Web Server & Real-Time Engine (Recommended)
```bash
python run_server.py
```
*Starts the camera capture thread, perception engine, SQLite database, Flask REST API, and Socket.IO real-time server on `http://localhost:5000`.*

### Headless CLI Debug Mode (No Web Server)
```bash
python run_debug.py
```
*Runs perception and tamper detection directly inside an OpenCV window.*

---

## 🔐 Default Authentication & RBAC

CUSTOS enforces secure session authentication and Role-Based Access Control:

| Role | Default Username | Default Password | Permissions |
| :--- | :--- | :--- | :--- |
| **Administrator** | `admin` | `txt me i will tell` | Full access: user management, security config, face enrollment, incident resolution. |
| **Operator** | `operator` | `operator123` | Operational access: live monitoring, zone setup, alert resolution, evidence export. |
| **Viewer** | `viewer` | `viewer123` | Read-only access: live feed, read alerts, and view evidence. |

> [!TIP]
> Admin passwords can be customized anytime via `.env` using `CUSTOS_ADMIN_PASSWORD=YourPassword` or directly via the People & User settings.

---

## 📡 REST API Reference

All protected endpoints require an authenticated session or valid API token.

### Authentication & Sessions
| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `POST` | `/login` | Authenticate operator (`username`, `password`). |
| `GET` | `/logout` | Invalidate current session. |
| `GET` | `/api/auth/status` | Current authentication status and user details. |

### Alerts & Incident Management
| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/api/alerts` | Paginated alert records with status, severity, and camera filters. |
| `GET` | `/api/alerts/stats` | Real-time counts (`total`, `active`, `critical`, `today`, `resolved`). |
| `GET` | `/api/alerts/<id>` | Full alert detail with linked incident and event history. |
| `POST` | `/api/alerts/<id>/resolve` | Mark alert as resolved with operator notes. |

### People Intelligence & Biometrics
| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/api/people` | Retrieve enrolled profiles with optional `include_inactive=true` filter. |
| `GET` | `/api/people/stats` | Aggregate stats (`known_profiles`, `clusters`, `suspicious`, `appearances`). |
| `GET` | `/api/people/suspicious` | Watchlist profiles flagged as `SUSPICIOUS`. |
| `GET` | `/api/people/<person_id>` | Single person profile with reference photos & appearance history. |
| `POST` | `/api/people/enroll` | Multipart upload to enroll a person (`photo`, `name`, `classification`, `notes`). |
| `PATCH` | `/api/people/<person_id>` | Update name, classification (`KNOWN`, `UNKNOWN`, `SUSPICIOUS`), or status. |
| `DELETE`| `/api/people/<person_id>` | Deactivate or delete person profile. |
| `POST` | `/api/people/<person_id>/faces` | Add reference face photograph to existing profile. |
| `DELETE`| `/api/people/<person_id>/faces/<face_id>` | Remove reference photo. |
| `GET` | `/api/faces/clusters` | List detected unknown face clusters. |
| `POST` | `/api/faces/clusters/<cluster_id>/profile` | Convert unknown face cluster into a named profile. |

### Evidence Center
| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/api/evidence` | Paginated evidence records with search and type filters. |
| `GET` | `/api/evidence/stats` | Media asset metrics (`snapshots`, `clips`, `tamper_records`). |
| `GET` | `/api/evidence/<id>` | Complete evidence dossier with chronological audit events. |
| `GET` | `/api/evidence/<id>/media/<type>` | Stream verified JPEG snapshot or MP4 video. |
| `POST` | `/api/evidence/<id>/export` | Generate downloadable JSON evidence bundle. |

### Live Feeds & Zones
| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/video_feed` | High-framerate annotated MJPEG video stream. |
| `POST` | `/api/zones` | Save zone coordinates (`HIGH` / `WATCH` polygons). |
| `POST` | `/api/zones/clear` | Clear all configured zones. |
| `POST` | `/api/monitoring/toggle` | Enable / disable active AI perception engine. |

---

## ⚡ Socket.IO Real-Time Event Protocol

The server broadcasts low-latency WebSocket events to synchronize all connected operator consoles:

| Event Name | Direction | Description |
| :--- | :--- | :--- |
| `alert_created` | Server $\rightarrow$ Client | Emitted when a new security breach or tamper event creates an alert. |
| `alert_updated` | Server $\rightarrow$ Client | Real-time dwell duration and threat score updates. |
| `alert_resolved` | Server $\rightarrow$ Client | Broadcasts when an operator marks an alert as resolved. |
| `evidence_created` | Server $\rightarrow$ Client | Emitted upon trigger JPEG snapshot generation. |
| `evidence_updated` | Server $\rightarrow$ Client | Emitted when MP4 video recording is validated on disk. |
| `person_profile_created` | Server $\rightarrow$ Client | Emitted when a new person is enrolled or converted from a cluster. |
| `cluster_updated` | Server $\rightarrow$ Client | Emitted when a new face cluster is detected or updated. |
| `tamper_started` | Server $\rightarrow$ Client | Instant alert when optical tampering is confirmed. |
| `tamper_resolved` | Server $\rightarrow$ Client | Broadcasts when clear camera video view is restored. |

---

## 🛠 Configuration Reference

All settings can be customized in [`config/settings.py`](file:///c:/Users/VARUN%20THEJ/Downloads/custos-folder/custos-stage2.8/custos-stage2.8/config/settings.py) or overridden using a `.env` file in the project root:

```ini
# ================================================================
# CAMERA & INGESTION
# ================================================================
CUSTOS_CAMERA_SOURCE=0                 # 0 for default USB webcam, or "rtsp://..."
CUSTOS_CAMERA_TARGET_FPS=30            # Desired acquisition framerate
CUSTOS_CAMERA_WARMUP_FRAMES=10         # Frames to discard during camera sensor warmup

# ================================================================
# PRE-ROLL & TAMPER DETECTION
# ================================================================
CUSTOS_PRE_TAMPER_SECONDS=15.0         # Seconds of circular pre-roll footage
CUSTOS_TAMPER_CONFIRM_SECONDS=0.8      # Duration anomaly must persist before trigger
CUSTOS_TAMPER_RECOVERY_SECONDS=3.0     # Recovery duration before tamper resolves

# ================================================================
# FACE INTELLIGENCE & BIOMETRICS
# ================================================================
CUSTOS_FACE_MATCH_THRESHOLD=0.40       # SFace cosine similarity threshold
CUSTOS_FACE_MIN_SIZE=40                # Minimum face crop size (pixels)
CUSTOS_FACE_MIN_QUALITY=15.0           # Laplacian variance blur quality threshold

# ================================================================
# SECURITY & DATABASE
# ================================================================
CUSTOS_SECRET_KEY=custos_production_secret_key_2026
CUSTOS_ADMIN_PASSWORD= txt me i will tell
CUSTOS_DATABASE_URI=sqlite:///instance/custos.db
```

---

## 🧪 Testing & Verification Protocol

CUSTOS includes an automated test suite verifying all system components:

```bash
# Run all unit, integration, and lifecycle tests
pytest -v

# Run specific test suites
pytest tests/test_people_intelligence.py -v
pytest tests/test_tamper_lifecycle.py -v
pytest tests/test_incident_lifecycle.py -v
pytest tests/test_hardening_regression.py -v
```

---

## 🚢 Production Deployment & Windows Service Setup

### Running as a Windows Background Service
To configure CUSTOS to automatically start on system boot without user login, use NSSM (Non-Sucking Service Manager):

```cmd
# 1. Download NSSM and open Administrator Command Prompt
nssm install CustosSecurityEngine "C:\Users\VARUN THEJ\Downloads\custos-folder\custos-stage2.8\custos-stage2.8\venv\Scripts\python.exe"
nssm set CustosSecurityEngine AppParameters "run_server.py"
nssm set CustosSecurityEngine AppDirectory "C:\Users\VARUN THEJ\Downloads\custos-folder\custos-stage2.8\custos-stage2.8"
nssm set CustosSecurityEngine Start SERVICE_AUTO_START

# 2. Start Service
nssm start CustosSecurityEngine
```

---

## 📄 License

CUSTOS is licensed under the [MIT License](LICENSE). Built for security and enterprise automation.
