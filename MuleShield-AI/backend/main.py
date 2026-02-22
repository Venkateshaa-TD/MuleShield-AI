"""
MuleShield AI - FastAPI Backend Application
Banking-Grade AML and Mule Account Detection System

This is the main API server providing endpoints for:
- Account management and risk analysis
- Transaction monitoring and network analysis
- Alert management and case workflow
- SAR report generation
- Dashboard data

Author: MuleShield AI Team
Version: 1.0.0
"""

from fastapi import FastAPI, HTTPException, Query, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Dict, Optional
from datetime import datetime
import uvicorn

# Import MuleShield components
from services.mock_data_generator import generate_all_mock_data
from graph_engine.network_analyzer import MuleNetworkAnalyzer, create_analyzer
from risk_engine.scoring_engine import RiskScoringEngine, create_risk_engine
from services.behavioral_profiler import BehavioralProfiler, create_profiler
from services.sar_generator import SARReportGenerator, create_sar_generator

# ============================================
# APPLICATION SETUP
# ============================================

app = FastAPI(
    title="MuleShield AI",
    description="Banking-Grade AML and Mule Account Detection System",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS configuration for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000", "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================
# IN-MEMORY DATA STORE (Demo purposes)
# ============================================

class DataStore:
    """In-memory data store for demo purposes."""
    def __init__(self):
        self.accounts: List[Dict] = []
        self.transactions: List[Dict] = []
        self.device_fingerprints: List[Dict] = []
        self.alerts: List[Dict] = []
        self.cases: List[Dict] = []
        self.mule_network_ids: List[str] = []
        self.is_initialized: bool = False
        
        # Analytics engines
        self.graph_analyzer: Optional[MuleNetworkAnalyzer] = None
        self.risk_engine: Optional[RiskScoringEngine] = None
        self.profiler: Optional[BehavioralProfiler] = None
        self.sar_generator: Optional[SARReportGenerator] = None

data_store = DataStore()

# ============================================
# PYDANTIC MODELS
# ============================================

class AlertUpdate(BaseModel):
    status: Optional[str] = None
    resolution: Optional[str] = None
    analyst_notes: Optional[str] = None
    assigned_to: Optional[str] = None

class CaseCreate(BaseModel):
    alert_id: str
    title: str
    description: str
    priority: str = "medium"
    assigned_analyst: Optional[str] = None

class CaseUpdate(BaseModel):
    status: Optional[str] = None
    outcome: Optional[str] = None
    investigation_notes: Optional[str] = None
    assigned_analyst: Optional[str] = None

class FeedbackRequest(BaseModel):
    account_id: str
    feedback_type: str  # "true_mule" or "false_positive"

# ============================================
# INITIALIZATION ENDPOINT
# ============================================

@app.on_event("startup")
async def startup_event():
    """Initialize data on startup."""
    initialize_data()

@app.post("/api/initialize", tags=["System"])
async def initialize_system():
    """Re-initialize the system with fresh mock data."""
    initialize_data()
    return {
        "status": "success",
        "message": "System initialized with mock data",
        "stats": {
            "accounts": len(data_store.accounts),
            "transactions": len(data_store.transactions),
            "alerts": len(data_store.alerts),
            "mule_network_size": len(data_store.mule_network_ids)
        }
    }

def initialize_data():
    """Generate and load mock data."""
    print("🔄 Initializing MuleShield AI...")
    
    # Generate mock data
    mock_data = generate_all_mock_data()
    
    data_store.accounts = mock_data["accounts"]
    data_store.transactions = mock_data["transactions"]
    data_store.device_fingerprints = mock_data["device_fingerprints"]
    data_store.alerts = mock_data["alerts"]
    data_store.mule_network_ids = mock_data["mule_network_ids"]
    data_store.cases = []
    
    # Initialize analytics engines
    data_store.graph_analyzer = create_analyzer(
        data_store.transactions,
        data_store.device_fingerprints
    )
    data_store.risk_engine = create_risk_engine()
    data_store.profiler = create_profiler()
    data_store.sar_generator = create_sar_generator()
    
    data_store.is_initialized = True
    print("✅ MuleShield AI initialized successfully")

# ============================================
# DASHBOARD ENDPOINTS
# ============================================

@app.get("/api/dashboard/stats", tags=["Dashboard"])
async def get_dashboard_stats():
    """Get overview statistics for dashboard."""
    if not data_store.is_initialized:
        raise HTTPException(status_code=503, detail="System not initialized")
    
    # Calculate stats
    high_risk = sum(1 for a in data_store.accounts if a.get("risk_category") == "high")
    medium_risk = sum(1 for a in data_store.accounts if a.get("risk_category") == "medium")
    low_risk = sum(1 for a in data_store.accounts if a.get("risk_category") == "low")
    
    open_alerts = sum(1 for a in data_store.alerts if a.get("status") == "open")
    investigating_alerts = sum(1 for a in data_store.alerts if a.get("status") == "investigating")
    
    suspicious_txns = sum(1 for t in data_store.transactions if t.get("is_suspicious"))
    total_volume = sum(t.get("amount", 0) for t in data_store.transactions)
    
    return {
        "accounts": {
            "total": len(data_store.accounts),
            "high_risk": high_risk,
            "medium_risk": medium_risk,
            "low_risk": low_risk,
            "flagged": sum(1 for a in data_store.accounts if a.get("is_flagged"))
        },
        "alerts": {
            "total": len(data_store.alerts),
            "open": open_alerts,
            "investigating": investigating_alerts,
            "closed": len(data_store.alerts) - open_alerts - investigating_alerts
        },
        "transactions": {
            "total": len(data_store.transactions),
            "suspicious": suspicious_txns,
            "total_volume": round(total_volume, 2)
        },
        "mule_network": {
            "detected_accounts": len(data_store.mule_network_ids),
            "clusters_identified": 2  # We created 2 clusters in mock data
        },
        "cases": {
            "total": len(data_store.cases),
            "open": sum(1 for c in data_store.cases if c.get("status") == "open")
        }
    }

@app.get("/api/dashboard/risk-distribution", tags=["Dashboard"])
async def get_risk_distribution():
    """Get risk score distribution for charts."""
    if not data_store.is_initialized:
        raise HTTPException(status_code=503, detail="System not initialized")
    
    # Bin risk scores
    bins = {"0-20": 0, "21-40": 0, "41-60": 0, "61-80": 0, "81-100": 0}
    
    for account in data_store.accounts:
        prob = account.get("mule_probability", 0)
        if prob <= 20:
            bins["0-20"] += 1
        elif prob <= 40:
            bins["21-40"] += 1
        elif prob <= 60:
            bins["41-60"] += 1
        elif prob <= 80:
            bins["61-80"] += 1
        else:
            bins["81-100"] += 1
    
    return {
        "distribution": bins,
        "categories": {
            "low": sum(1 for a in data_store.accounts if a.get("risk_category") == "low"),
            "medium": sum(1 for a in data_store.accounts if a.get("risk_category") == "medium"),
            "high": sum(1 for a in data_store.accounts if a.get("risk_category") == "high")
        }
    }

@app.get("/api/dashboard/recent-activity", tags=["Dashboard"])
async def get_recent_activity():
    """Get recent suspicious activity for dashboard."""
    if not data_store.is_initialized:
        raise HTTPException(status_code=503, detail="System not initialized")
    
    # Get recent alerts
    recent_alerts = sorted(
        data_store.alerts,
        key=lambda x: x.get("created_at", ""),
        reverse=True
    )[:10]
    
    # Get recent suspicious transactions
    suspicious_txns = [t for t in data_store.transactions if t.get("is_suspicious")]
    recent_txns = sorted(
        suspicious_txns,
        key=lambda x: x.get("timestamp", ""),
        reverse=True
    )[:10]
    
    return {
        "recent_alerts": recent_alerts,
        "recent_suspicious_transactions": recent_txns
    }

# ============================================
# ACCOUNT ENDPOINTS
# ============================================

@app.get("/api/accounts", tags=["Accounts"])
async def get_accounts(
    risk_category: Optional[str] = Query(None, description="Filter by risk category"),
    is_flagged: Optional[bool] = Query(None, description="Filter by flagged status"),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0)
):
    """Get list of accounts with optional filters."""
    if not data_store.is_initialized:
        raise HTTPException(status_code=503, detail="System not initialized")
    
    accounts = data_store.accounts
    
    # Apply filters
    if risk_category:
        accounts = [a for a in accounts if a.get("risk_category") == risk_category]
    if is_flagged is not None:
        accounts = [a for a in accounts if a.get("is_flagged") == is_flagged]
    
    # Sort by risk
    accounts = sorted(accounts, key=lambda x: x.get("mule_probability", 0), reverse=True)
    
    return {
        "total": len(accounts),
        "accounts": accounts[offset:offset + limit]
    }

@app.get("/api/accounts/{account_id}", tags=["Accounts"])
async def get_account(account_id: str):
    """Get detailed account information."""
    if not data_store.is_initialized:
        raise HTTPException(status_code=503, detail="System not initialized")
    
    account = next((a for a in data_store.accounts if a.get("id") == account_id), None)
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")
    
    return account

@app.get("/api/accounts/{account_id}/risk-analysis", tags=["Accounts"])
async def get_account_risk_analysis(account_id: str):
    """Get comprehensive risk analysis for an account."""
    if not data_store.is_initialized:
        raise HTTPException(status_code=503, detail="System not initialized")
    
    account = next((a for a in data_store.accounts if a.get("id") == account_id), None)
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")
    
    # Get centrality data from graph analysis
    centrality_data = data_store.graph_analyzer.get_centrality_scores(account_id)
    
    # Calculate composite risk score
    risk_analysis = data_store.risk_engine.calculate_composite_score(
        account=account,
        transactions=data_store.transactions,
        device_fingerprints=data_store.device_fingerprints,
        centrality_data=centrality_data
    )
    
    return risk_analysis

@app.get("/api/accounts/{account_id}/network", tags=["Accounts"])
async def get_account_network(account_id: str):
    """Get network analysis for an account."""
    if not data_store.is_initialized:
        raise HTTPException(status_code=503, detail="System not initialized")
    
    account = next((a for a in data_store.accounts if a.get("id") == account_id), None)
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")
    
    # Get comprehensive network analysis
    network_analysis = data_store.graph_analyzer.analyze_account_network(account_id)
    
    return network_analysis

@app.get("/api/accounts/{account_id}/transactions", tags=["Accounts"])
async def get_account_transactions(
    account_id: str,
    limit: int = Query(50, ge=1, le=200)
):
    """Get transactions for an account."""
    if not data_store.is_initialized:
        raise HTTPException(status_code=503, detail="System not initialized")
    
    # Filter transactions
    txns = [
        t for t in data_store.transactions
        if t.get("sender_id") == account_id or t.get("receiver_id") == account_id
    ]
    
    # Sort by timestamp
    txns = sorted(txns, key=lambda x: x.get("timestamp", ""), reverse=True)
    
    return {
        "total": len(txns),
        "transactions": txns[:limit]
    }

@app.get("/api/accounts/{account_id}/behavioral-profile", tags=["Accounts"])
async def get_account_behavioral_profile(account_id: str):
    """Get behavioral profile for an account."""
    if not data_store.is_initialized:
        raise HTTPException(status_code=503, detail="System not initialized")
    
    # Build profile
    profile = data_store.profiler.build_profile(account_id, data_store.transactions)
    
    # Detect anomalies
    recent_txns = [
        t for t in data_store.transactions
        if t.get("sender_id") == account_id or t.get("receiver_id") == account_id
    ]
    anomalies = data_store.profiler.detect_anomalies(account_id, recent_txns, profile)
    
    return {
        "profile": profile,
        "anomaly_detection": anomalies
    }

# ============================================
# TRANSACTION ENDPOINTS
# ============================================

@app.get("/api/transactions", tags=["Transactions"])
async def get_transactions(
    is_suspicious: Optional[bool] = Query(None),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0)
):
    """Get list of transactions."""
    if not data_store.is_initialized:
        raise HTTPException(status_code=503, detail="System not initialized")
    
    txns = data_store.transactions
    
    if is_suspicious is not None:
        txns = [t for t in txns if t.get("is_suspicious") == is_suspicious]
    
    # Sort by timestamp
    txns = sorted(txns, key=lambda x: x.get("timestamp", ""), reverse=True)
    
    return {
        "total": len(txns),
        "transactions": txns[offset:offset + limit]
    }

@app.get("/api/transactions/{transaction_id}", tags=["Transactions"])
async def get_transaction(transaction_id: str):
    """Get transaction details."""
    if not data_store.is_initialized:
        raise HTTPException(status_code=503, detail="System not initialized")
    
    txn = next((t for t in data_store.transactions if t.get("id") == transaction_id), None)
    if not txn:
        raise HTTPException(status_code=404, detail="Transaction not found")
    
    return txn

# ============================================
# ALERT ENDPOINTS
# ============================================

@app.get("/api/alerts", tags=["Alerts"])
async def get_alerts(
    status: Optional[str] = Query(None),
    severity: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0)
):
    """Get list of alerts."""
    if not data_store.is_initialized:
        raise HTTPException(status_code=503, detail="System not initialized")
    
    alerts = data_store.alerts
    
    if status:
        alerts = [a for a in alerts if a.get("status") == status]
    if severity:
        alerts = [a for a in alerts if a.get("severity") == severity]
    
    # Sort by risk score
    alerts = sorted(alerts, key=lambda x: x.get("risk_score", 0), reverse=True)
    
    # Enrich with account info
    enriched_alerts = []
    for alert in alerts[offset:offset + limit]:
        account = next(
            (a for a in data_store.accounts if a.get("id") == alert.get("account_id")),
            {}
        )
        enriched_alerts.append({
            **alert,
            "account_name": account.get("account_holder_name"),
            "account_number": account.get("account_number")
        })
    
    return {
        "total": len(alerts),
        "alerts": enriched_alerts
    }

@app.get("/api/alerts/{alert_id}", tags=["Alerts"])
async def get_alert(alert_id: str):
    """Get alert details."""
    if not data_store.is_initialized:
        raise HTTPException(status_code=503, detail="System not initialized")
    
    alert = next((a for a in data_store.alerts if a.get("id") == alert_id), None)
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    
    # Get account info
    account = next(
        (a for a in data_store.accounts if a.get("id") == alert.get("account_id")),
        {}
    )
    
    return {
        **alert,
        "account": account
    }

@app.put("/api/alerts/{alert_id}", tags=["Alerts"])
async def update_alert(alert_id: str, update: AlertUpdate):
    """Update alert status or details."""
    if not data_store.is_initialized:
        raise HTTPException(status_code=503, detail="System not initialized")
    
    alert_idx = next(
        (i for i, a in enumerate(data_store.alerts) if a.get("id") == alert_id),
        None
    )
    if alert_idx is None:
        raise HTTPException(status_code=404, detail="Alert not found")
    
    # Update fields
    if update.status:
        data_store.alerts[alert_idx]["status"] = update.status
    if update.resolution:
        data_store.alerts[alert_idx]["resolution"] = update.resolution
        data_store.alerts[alert_idx]["resolved_at"] = datetime.now().isoformat()
    if update.analyst_notes:
        data_store.alerts[alert_idx]["analyst_notes"] = update.analyst_notes
    if update.assigned_to:
        data_store.alerts[alert_idx]["assigned_to"] = update.assigned_to
    
    data_store.alerts[alert_idx]["updated_at"] = datetime.now().isoformat()
    
    return data_store.alerts[alert_idx]

# ============================================
# CASE MANAGEMENT ENDPOINTS
# ============================================

@app.post("/api/cases", tags=["Cases"])
async def create_case(case_data: CaseCreate):
    """Create a new investigation case."""
    if not data_store.is_initialized:
        raise HTTPException(status_code=503, detail="System not initialized")
    
    import uuid
    
    case = {
        "id": str(uuid.uuid4()),
        "case_number": f"CASE-{datetime.now().strftime('%Y%m%d')}-{len(data_store.cases) + 1:04d}",
        "alert_id": case_data.alert_id,
        "title": case_data.title,
        "description": case_data.description,
        "priority": case_data.priority,
        "status": "open",
        "outcome": None,
        "assigned_analyst": case_data.assigned_analyst,
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat(),
        "closed_at": None,
        "evidence": [],
        "investigation_notes": None,
        "sar_filed": False,
        "sar_reference": None
    }
    
    data_store.cases.append(case)
    
    return case

@app.get("/api/cases", tags=["Cases"])
async def get_cases(
    status: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=100)
):
    """Get list of cases."""
    if not data_store.is_initialized:
        raise HTTPException(status_code=503, detail="System not initialized")
    
    cases = data_store.cases
    
    if status:
        cases = [c for c in cases if c.get("status") == status]
    
    return {
        "total": len(cases),
        "cases": cases[:limit]
    }

@app.get("/api/cases/{case_id}", tags=["Cases"])
async def get_case(case_id: str):
    """Get case details."""
    if not data_store.is_initialized:
        raise HTTPException(status_code=503, detail="System not initialized")
    
    case = next((c for c in data_store.cases if c.get("id") == case_id), None)
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
    
    return case

@app.put("/api/cases/{case_id}", tags=["Cases"])
async def update_case(case_id: str, update: CaseUpdate):
    """Update case."""
    if not data_store.is_initialized:
        raise HTTPException(status_code=503, detail="System not initialized")
    
    case_idx = next(
        (i for i, c in enumerate(data_store.cases) if c.get("id") == case_id),
        None
    )
    if case_idx is None:
        raise HTTPException(status_code=404, detail="Case not found")
    
    if update.status:
        data_store.cases[case_idx]["status"] = update.status
        if update.status == "closed":
            data_store.cases[case_idx]["closed_at"] = datetime.now().isoformat()
    if update.outcome:
        data_store.cases[case_idx]["outcome"] = update.outcome
    if update.investigation_notes:
        data_store.cases[case_idx]["investigation_notes"] = update.investigation_notes
    if update.assigned_analyst:
        data_store.cases[case_idx]["assigned_analyst"] = update.assigned_analyst
    
    data_store.cases[case_idx]["updated_at"] = datetime.now().isoformat()
    
    return data_store.cases[case_idx]

# ============================================
# NETWORK GRAPH ENDPOINTS
# ============================================

@app.get("/api/graph/visualization", tags=["Network Analysis"])
async def get_graph_visualization(
    account_ids: Optional[str] = Query(None, description="Comma-separated account IDs")
):
    """Get network graph data for visualization."""
    if not data_store.is_initialized:
        raise HTTPException(status_code=503, detail="System not initialized")
    
    account_list = account_ids.split(",") if account_ids else None
    
    graph_data = data_store.graph_analyzer.get_network_visualization_data(account_list)
    
    # Enrich nodes with account info
    for node in graph_data["nodes"]:
        account = next(
            (a for a in data_store.accounts if a.get("id") == node["id"]),
            {}
        )
        node["account_name"] = account.get("account_holder_name", "Unknown")
        node["risk_category"] = account.get("risk_category", "unknown")
        node["mule_probability"] = account.get("mule_probability", 0)
        node["is_mule_network"] = node["id"] in data_store.mule_network_ids
    
    return graph_data

@app.get("/api/graph/patterns", tags=["Network Analysis"])
async def get_detected_patterns():
    """Get all detected suspicious patterns."""
    if not data_store.is_initialized:
        raise HTTPException(status_code=503, detail="System not initialized")
    
    circular_flows = data_store.graph_analyzer.detect_circular_flows()
    hub_spokes = data_store.graph_analyzer.detect_hub_spoke_patterns()
    rapid_dispersal = data_store.graph_analyzer.detect_rapid_dispersal(data_store.transactions)
    device_clusters = data_store.graph_analyzer.detect_device_clusters()
    communities = data_store.graph_analyzer.get_community_risk_scores()
    
    return {
        "circular_flows": circular_flows,
        "hub_spoke_patterns": hub_spokes,
        "rapid_dispersal_patterns": rapid_dispersal,
        "device_clusters": device_clusters,
        "communities": communities
    }

@app.get("/api/graph/mule-network", tags=["Network Analysis"])
async def get_mule_network():
    """Get identified mule network details."""
    if not data_store.is_initialized:
        raise HTTPException(status_code=503, detail="System not initialized")
    
    mule_accounts = [
        a for a in data_store.accounts
        if a.get("id") in data_store.mule_network_ids
    ]
    
    # Get graph data for mule network
    graph_data = data_store.graph_analyzer.get_network_visualization_data(
        data_store.mule_network_ids
    )
    
    return {
        "mule_accounts": mule_accounts,
        "network_size": len(mule_accounts),
        "graph_data": graph_data
    }

# ============================================
# SAR REPORT ENDPOINTS
# ============================================

@app.post("/api/reports/sar/{account_id}", tags=["Reports"])
async def generate_sar_report(account_id: str):
    """Generate SAR report for an account."""
    if not data_store.is_initialized:
        raise HTTPException(status_code=503, detail="System not initialized")
    
    account = next((a for a in data_store.accounts if a.get("id") == account_id), None)
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")
    
    # Get risk analysis
    centrality_data = data_store.graph_analyzer.get_centrality_scores(account_id)
    risk_analysis = data_store.risk_engine.calculate_composite_score(
        account=account,
        transactions=data_store.transactions,
        device_fingerprints=data_store.device_fingerprints,
        centrality_data=centrality_data
    )
    
    # Get network analysis
    network_analysis = data_store.graph_analyzer.analyze_account_network(account_id)
    
    # Get alert if exists
    alert = next(
        (a for a in data_store.alerts if a.get("account_id") == account_id),
        None
    )
    
    # Generate report
    report = data_store.sar_generator.generate_sar_report(
        account=account,
        risk_score_data=risk_analysis,
        transactions=data_store.transactions,
        network_analysis=network_analysis,
        alert=alert
    )
    
    return report

# ============================================
# ADAPTIVE LEARNING ENDPOINTS
# ============================================

@app.post("/api/feedback", tags=["Adaptive Learning"])
async def submit_feedback(feedback: FeedbackRequest):
    """Submit investigator feedback for adaptive learning."""
    if not data_store.is_initialized:
        raise HTTPException(status_code=503, detail="System not initialized")
    
    account = next(
        (a for a in data_store.accounts if a.get("id") == feedback.account_id),
        None
    )
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")
    
    # Get current risk analysis
    centrality_data = data_store.graph_analyzer.get_centrality_scores(feedback.account_id)
    risk_analysis = data_store.risk_engine.calculate_composite_score(
        account=account,
        transactions=data_store.transactions,
        device_fingerprints=data_store.device_fingerprints,
        centrality_data=centrality_data
    )
    
    # Extract component scores for weight adjustment
    component_scores = {
        "transaction_velocity": risk_analysis["component_scores"]["transaction_velocity"]["score"],
        "beneficiary_diversity": risk_analysis["component_scores"]["beneficiary_diversity"]["score"],
        "account_age": risk_analysis["component_scores"]["account_age"]["score"],
        "device_reuse": risk_analysis["component_scores"]["device_reuse"]["score"],
        "graph_centrality": risk_analysis["component_scores"]["graph_centrality"]["score"],
        "behavior_deviation": risk_analysis["component_scores"]["behavior_deviation"]["score"]
    }
    
    # Update weights
    new_weights = data_store.risk_engine.update_weights(
        feedback.feedback_type,
        component_scores
    )
    
    return {
        "status": "success",
        "message": f"Weights updated based on {feedback.feedback_type} feedback",
        "new_weights": new_weights
    }

@app.get("/api/weights", tags=["Adaptive Learning"])
async def get_current_weights():
    """Get current risk scoring weights."""
    if not data_store.is_initialized:
        raise HTTPException(status_code=503, detail="System not initialized")
    
    return {
        "current_weights": data_store.risk_engine.weights,
        "weight_history": data_store.risk_engine.get_weight_history()
    }

# ============================================
# HEALTH CHECK
# ============================================

@app.get("/api/health", tags=["System"])
async def health_check():
    """System health check."""
    return {
        "status": "healthy",
        "initialized": data_store.is_initialized,
        "timestamp": datetime.now().isoformat()
    }

# ============================================
# MAIN ENTRY POINT
# ============================================

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
