# 🛡️ MuleShield AI

## Banking-Grade AML and Mule Account Detection System

MuleShield AI is an advanced Anti-Money Laundering (AML) platform that combines graph intelligence, behavioral profiling, and dynamic risk scoring to detect mule accounts and suspicious transaction networks in real-time.

![MuleShield AI](https://img.shields.io/badge/MuleShield-AI-blueviolet?style=for-the-badge)
![Python](https://img.shields.io/badge/Python-3.9+-blue?style=flat-square)
![React](https://img.shields.io/badge/React-18-61DAFB?style=flat-square)
![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-009688?style=flat-square)

---

## 🎯 Key Features

### 🔍 Graph-Based Network Analysis
- **Transaction Network Visualization** - Interactive graph showing money flow patterns
- **Circular Flow Detection** - Identifies round-tripping and layering schemes
- **Hub-Spoke Pattern Recognition** - Detects central collector/distributor accounts
- **Rapid Dispersal Alerts** - Flags quick distribution of received funds
- **Device Cluster Analysis** - Links accounts sharing devices/fingerprints

### 📊 Dynamic Risk Scoring
Six-component weighted risk assessment:
1. **Transaction Velocity Score** - Unusual transaction frequency
2. **Beneficiary Diversity Score** - Too many unique counterparties
3. **Account Age Score** - New accounts with high activity
4. **Device Reuse Score** - Shared device fingerprints
5. **Graph Centrality Score** - Network position importance
6. **Behavior Deviation Score** - Anomalies from baseline patterns

### 🤖 Explainable AI
- **AI-Generated Risk Reasoning** - Natural language explanations for each alert
- **Risk Factor Breakdown** - Detailed component-level scoring
- **Adaptive Learning** - System improves from investigator feedback

### 📋 Investigation Workflow
- **Alert Management** - Prioritized queue with status tracking
- **Case Management** - Group related alerts into investigation cases
- **SAR Generation** - FinCEN-compliant Suspicious Activity Reports
- **Audit Trail** - Complete history of all actions

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    MuleShield AI                           │
├─────────────────────────────────────────────────────────────┤
│  Frontend (React + Vite)                                    │
│  ├── Dashboard - Real-time metrics & alerts                │
│  ├── Accounts - Risk profiles & transaction history        │
│  ├── Network Graph - Interactive ReactFlow visualization   │
│  ├── Alerts - Investigation queue management               │
│  ├── Cases - Multi-alert investigation tracking            │
│  └── Reports - SAR generation & download                   │
├─────────────────────────────────────────────────────────────┤
│  Backend (FastAPI + Python)                                 │
│  ├── Graph Engine - NetworkX-powered network analysis      │
│  ├── Risk Engine - ML-based composite scoring              │
│  ├── Behavioral Profiler - Anomaly detection               │
│  └── SAR Generator - Automated reporting                   │
├─────────────────────────────────────────────────────────────┤
│  Data Layer (SQLite + Mock Generator)                       │
│  └── 100 accounts, 200+ transactions, 2 mule clusters      │
└─────────────────────────────────────────────────────────────┘
```

---

## 🚀 Quick Start

### Prerequisites
- Python 3.9+
- Node.js 18+
- npm or yarn

### Backend Setup

```bash
# Navigate to backend
cd backend

# Create virtual environment
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/Mac

# Install dependencies
pip install -r requirements.txt

# Start the server
uvicorn main:app --reload --port 8000
```

The backend will:
- Initialize SQLite database
- Generate mock data (100 accounts, 200+ transactions)
- Create 2 mule network clusters for demo
- Start API server at http://localhost:8000

### Frontend Setup

```bash
# Navigate to frontend
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

Access the dashboard at http://localhost:5173

---

## 📡 API Endpoints

### Dashboard
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/dashboard/stats` | System statistics |
| GET | `/api/dashboard/risk-distribution` | Risk score distribution |
| GET | `/api/dashboard/recent-activity` | Recent alerts & transactions |

### Accounts
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/accounts` | List all accounts |
| GET | `/api/accounts/{id}` | Get account details |
| GET | `/api/accounts/{id}/transactions` | Account transactions |
| GET | `/api/accounts/{id}/risk-analysis` | Full risk breakdown |

### Alerts
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/alerts` | List alerts with filters |
| GET | `/api/alerts/{id}` | Get alert details |
| PUT | `/api/alerts/{id}/status` | Update alert status |

### Network Graph
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/graph/network` | Full network data |
| GET | `/api/graph/circular-flows` | Detected circular patterns |
| GET | `/api/graph/hub-spoke` | Hub-spoke patterns |
| GET | `/api/graph/device-clusters` | Device-linked accounts |

### Cases & Reports
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/cases` | List investigation cases |
| POST | `/api/cases` | Create new case |
| POST | `/api/reports/sar/{account_id}` | Generate SAR report |

### Adaptive Learning
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/learning/feedback` | Submit investigator feedback |
| GET | `/api/learning/weights` | Current scoring weights |

---

## 🎨 Technology Stack

### Backend
- **FastAPI** - High-performance async API framework
- **NetworkX** - Graph analysis & visualization
- **Scikit-learn** - Random Forest for mule probability
- **SQLAlchemy** - ORM for database operations
- **Pandas/NumPy** - Data manipulation

### Frontend
- **React 18** - UI framework with hooks
- **Vite 5** - Fast build tool
- **ReactFlow** - Interactive network graphs
- **Recharts** - Dashboard charts
- **Tailwind CSS** - Utility-first styling
- **Heroicons** - Beautiful SVG icons

---

## 🔬 Risk Scoring Algorithm

```python
composite_score = (
    transaction_velocity_score * 0.20 +
    beneficiary_diversity_score * 0.15 +
    account_age_score * 0.15 +
    device_reuse_score * 0.15 +
    graph_centrality_score * 0.20 +
    behavior_deviation_score * 0.15
)

# Weights adapt based on investigator feedback!
```

### Risk Categories
- **Low Risk**: Score 0-39 (🟢 Green)
- **Medium Risk**: Score 40-69 (🟡 Yellow)
- **High Risk**: Score 70-100 (🔴 Red)

---

## 🕵️ Detection Patterns

### 1. Circular Flow Detection
Identifies money round-tripping: A→B→C→A
```
Account A ──$5000──> Account B
    ↑                    │
    │                    ▼
   $4900 <──$4950── Account C
```

### 2. Hub-Spoke Pattern
Central account receiving from/sending to many:
```
        Account B
            │
   Account A ← HUB → Account C
            │
        Account D
```

### 3. Rapid Dispersal
Quick distribution of received funds:
```
Large Deposit → Account → Multiple Outbound
($10,000)        │         (within 24 hours)
                 ├──> $2,000
                 ├──> $2,500
                 └──> $3,000
```

---

## 📊 Mock Data Overview

The system generates realistic demo data:
- **100 Accounts** with varied risk profiles
- **200+ Transactions** with suspicious patterns
- **2 Mule Clusters** demonstrating detection
- **Shared Devices** between linked accounts
- **Alerts** auto-generated for high-risk activities

---

## 🛠️ Configuration

### Backend (`backend/main.py`)
```python
# Risk scoring weights (adaptive)
DEFAULT_WEIGHTS = {
    "transaction_velocity": 0.20,
    "beneficiary_diversity": 0.15,
    "account_age": 0.15,
    "device_reuse": 0.15,
    "graph_centrality": 0.20,
    "behavior_deviation": 0.15
}
```

### Frontend (`frontend/vite.config.js`)
```javascript
// API proxy configuration
proxy: {
  '/api': {
    target: 'http://localhost:8000',
    changeOrigin: true
  }
}
```

---

## 📁 Project Structure

```
MuleShield-AI/
├── backend/
│   ├── main.py                 # FastAPI application
│   ├── requirements.txt        # Python dependencies
│   ├── models/
│   │   ├── database.py        # SQLite configuration
│   │   └── schemas.py         # SQLAlchemy models
│   ├── graph_engine/
│   │   └── network_analyzer.py # NetworkX analysis
│   ├── risk_engine/
│   │   └── scoring_engine.py  # Risk scoring logic
│   └── services/
│       ├── mock_data_generator.py
│       ├── behavioral_profiler.py
│       └── sar_generator.py
├── frontend/
│   ├── package.json
│   ├── vite.config.js
│   ├── tailwind.config.js
│   └── src/
│       ├── main.jsx
│       ├── App.jsx
│       ├── api/
│       │   └── index.js       # API service layer
│       ├── components/
│       │   └── Layout.jsx
│       └── pages/
│           ├── Dashboard.jsx
│           ├── Accounts.jsx
│           ├── AccountDetail.jsx
│           ├── Alerts.jsx
│           ├── AlertDetail.jsx
│           ├── NetworkGraph.jsx
│           ├── Cases.jsx
│           └── Reports.jsx
└── README.md
```

---

## 🏆 Hackathon Highlights

### Innovation Points
1. **Graph Intelligence** - Network analysis beyond traditional rule-based systems
2. **Explainable AI** - Every alert includes human-readable reasoning
3. **Adaptive Learning** - System improves from investigator decisions
4. **Real-time Visualization** - Interactive ReactFlow network explorer
5. **FinCEN-Ready** - Automated SAR generation in regulatory format

### Demo Scenario
1. Open Dashboard → View high-risk alerts
2. Click "Network Graph" → Explore detected clusters
3. Select suspicious account → Review AI reasoning
4. Mark as True Positive → System learns
5. Generate SAR → Download regulatory report

---

## 📜 License

MIT License - See LICENSE file for details

---

## 👥 Team

**MuleShield AI** - Built for the future of financial crime prevention

---

<p align="center">
  <strong>🛡️ Protecting the financial system, one mule account at a time.</strong>
</p>
