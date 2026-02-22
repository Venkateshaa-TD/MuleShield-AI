"""
MuleShield AI - FastAPI Backend Application
Banking-Grade AML and Mule Account Detection System

This is the main API server providing endpoints for:
- Account management and risk analysis
- Transaction monitoring and network analysis
- Alert management and case workflow
- SAR report generation
- Dashboard data
- Real-time transaction streaming (Kafka-style)

Author: MuleShield AI Team
Version: 2.0.0
"""

from fastapi import FastAPI, HTTPException, Query, Depends, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Set
from datetime import datetime
import uvicorn
import asyncio
import json

# Import MuleShield components
from services.mock_data_generator import generate_all_mock_data, CITIES_WITH_COORDS, get_city_coordinates
from graph_engine.network_analyzer import MuleNetworkAnalyzer, create_analyzer
from risk_engine.scoring_engine import RiskScoringEngine, create_risk_engine
from services.behavioral_profiler import BehavioralProfiler, create_profiler
from services.sar_generator import SARReportGenerator, create_sar_generator
from services.pdf_generator import SARPDFGenerator, create_pdf_generator
from services.email_service import EmailService, create_email_service

# Import Stream Engine components
from stream_engine.message_broker import MessageBroker, get_broker
from stream_engine.transaction_stream import TransactionStreamGenerator, StreamConfig, create_transaction_stream
from stream_engine.stream_processor import StreamProcessor, ProcessorConfig, create_stream_processor

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
        self.pdf_generator: Optional[SARPDFGenerator] = None
        self.email_service: Optional[EmailService] = None
        
        # Stream engine components
        self.message_broker: Optional[MessageBroker] = None
        self.transaction_stream: Optional[TransactionStreamGenerator] = None
        self.stream_processor: Optional[StreamProcessor] = None
        self.stream_running: bool = False

data_store = DataStore()


# ============================================
# WEBSOCKET CONNECTION MANAGER
# ============================================

class ConnectionManager:
    """Manages WebSocket connections for real-time streaming."""
    
    def __init__(self):
        self.active_connections: Dict[str, Set[WebSocket]] = {
            "transactions": set(),
            "alerts": set(),
            "stats": set(),
        }
    
    async def connect(self, websocket: WebSocket, channel: str):
        """Accept and track new connection."""
        await websocket.accept()
        if channel not in self.active_connections:
            self.active_connections[channel] = set()
        self.active_connections[channel].add(websocket)
    
    def disconnect(self, websocket: WebSocket, channel: str):
        """Remove connection on disconnect."""
        if channel in self.active_connections:
            self.active_connections[channel].discard(websocket)
    
    async def broadcast(self, channel: str, message: Dict):
        """Broadcast message to all connections on a channel."""
        if channel not in self.active_connections:
            return
        
        disconnected = set()
        for connection in self.active_connections[channel]:
            try:
                await connection.send_json(message)
            except Exception:
                disconnected.add(connection)
        
        # Clean up disconnected
        for conn in disconnected:
            self.active_connections[channel].discard(conn)
    
    async def send_personal(self, websocket: WebSocket, message: Dict):
        """Send message to specific connection."""
        try:
            await websocket.send_json(message)
        except Exception:
            pass
    
    def get_connection_count(self) -> Dict[str, int]:
        """Get count of active connections per channel."""
        return {
            channel: len(connections)
            for channel, connections in self.active_connections.items()
        }

ws_manager = ConnectionManager()

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

class EmailRequest(BaseModel):
    """Request model for sending SAR report via email."""
    recipient_emails: List[str] = Field(..., description="List of recipient email addresses")
    cc_emails: Optional[List[str]] = Field(None, description="List of CC email addresses")
    custom_message: Optional[str] = Field(None, description="Custom message to include in email")
    include_pdf: bool = Field(True, description="Whether to attach PDF report")

class EmailConfigRequest(BaseModel):
    """Request model for configuring email settings."""
    smtp_server: str = Field(..., description="SMTP server address (e.g., smtp.gmail.com)")
    smtp_port: int = Field(587, description="SMTP port (587 for TLS)")
    sender_email: str = Field(..., description="Sender email address")
    sender_password: str = Field(..., description="Sender email password/app password")

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
    data_store.pdf_generator = create_pdf_generator()
    data_store.email_service = create_email_service()
    
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
    account_type: Optional[str] = Query(None, description="Filter by account type"),
    mule_suspected: Optional[str] = Query(None, description="Filter by mule status"),
    is_flagged: Optional[bool] = Query(None, description="Filter by flagged status"),
    limit: int = Query(100, ge=1, le=100),
    offset: int = Query(0, ge=0),
    skip: int = Query(0, ge=0)
):
    """Get list of accounts with optional filters."""
    if not data_store.is_initialized:
        raise HTTPException(status_code=503, detail="System not initialized")
    
    accounts = data_store.accounts
    
    # Apply filters
    if risk_category:
        accounts = [a for a in accounts if a.get("risk_category") == risk_category]
    if account_type:
        accounts = [a for a in accounts if a.get("account_type") == account_type]
    if mule_suspected:
        mule_bool = mule_suspected.lower() == 'true'
        accounts = [a for a in accounts if a.get("mule_suspected") == mule_bool]
    if is_flagged is not None:
        accounts = [a for a in accounts if a.get("is_flagged") == is_flagged]
    
    # Sort by risk
    accounts = sorted(accounts, key=lambda x: x.get("composite_risk_score", 0), reverse=True)
    
    # Use skip if provided, otherwise use offset
    pagination_offset = skip if skip > 0 else offset
    return accounts[pagination_offset:pagination_offset + limit]

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
    alert_type: Optional[str] = Query(None),
    limit: int = Query(100, ge=1, le=100),
    offset: int = Query(0, ge=0),
    skip: int = Query(0, ge=0)
):
    """Get list of alerts."""
    if not data_store.is_initialized:
        raise HTTPException(status_code=503, detail="System not initialized")
    
    alerts = data_store.alerts
    
    if status:
        alerts = [a for a in alerts if a.get("status") == status]
    if severity:
        alerts = [a for a in alerts if a.get("severity") == severity]
    if alert_type:
        alerts = [a for a in alerts if a.get("alert_type") == alert_type]
    
    # Sort by risk score
    alerts = sorted(alerts, key=lambda x: x.get("risk_score", 0), reverse=True)
    
    # Enrich with account info
    enriched_alerts = []
    pagination_offset = skip if skip > 0 else offset
    for alert in alerts[pagination_offset:pagination_offset + limit]:
        account = next(
            (a for a in data_store.accounts if a.get("id") == alert.get("account_id")),
            {}
        )
        enriched_alerts.append({
            **alert,
            "account_name": account.get("account_holder_name"),
            "account_number": account.get("account_number")
        })
    
    return enriched_alerts

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
    priority: Optional[str] = Query(None),
    limit: int = Query(100, ge=1, le=100),
    offset: int = Query(0, ge=0),
    skip: int = Query(0, ge=0)
):
    """Get list of cases."""
    if not data_store.is_initialized:
        raise HTTPException(status_code=503, detail="System not initialized")
    
    cases = data_store.cases
    
    if status:
        cases = [c for c in cases if c.get("status") == status]
    if priority:
        cases = [c for c in cases if c.get("priority") == priority]
    
    # Sort by created date descending
    cases = sorted(cases, key=lambda x: x.get("created_at", ""), reverse=True)
    
    pagination_offset = skip if skip > 0 else offset
    return cases[pagination_offset:pagination_offset + limit]

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
    """Get identified mule network details with geo data."""
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
    
    # Enrich nodes with location data
    for node in graph_data.get("nodes", []):
        account = next(
            (a for a in data_store.accounts if a.get("id") == node["id"]),
            {}
        )
        city = account.get("city", "New York")
        coords = get_city_coordinates(city)
        node["city"] = city
        node["country"] = account.get("country", coords.get("country", "US"))
        node["latitude"] = coords.get("lat", 39.8283)
        node["longitude"] = coords.get("lng", -98.5795)
        node["name"] = account.get("account_holder_name", "Unknown")
        node["risk_score"] = account.get("composite_risk_score", 0)
        node["mule_probability"] = account.get("mule_probability", 0)
        node["mule_suspected"] = account.get("mule_suspected", False)
        node["cluster_id"] = account.get("cluster_id")
    
    # Add inter-cluster edges (connect clusters that have transactions between them)
    cluster_edges = []
    existing_edges = set((e["source"], e["target"]) for e in graph_data.get("edges", []))
    
    # Group nodes by cluster
    clusters = {}
    for node in graph_data.get("nodes", []):
        cid = node.get("cluster_id")
        if cid is not None:
            if cid not in clusters:
                clusters[cid] = []
            clusters[cid].append(node)
    
    # Find inter-cluster connections through existing edges
    inter_cluster_pairs = set()
    for edge in graph_data.get("edges", []):
        src_cluster = None
        tgt_cluster = None
        for node in graph_data.get("nodes", []):
            if node["id"] == edge["source"]:
                src_cluster = node.get("cluster_id")
            if node["id"] == edge["target"]:
                tgt_cluster = node.get("cluster_id")
        if src_cluster is not None and tgt_cluster is not None and src_cluster != tgt_cluster:
            pair = tuple(sorted([src_cluster, tgt_cluster]))
            inter_cluster_pairs.add(pair)
    
    # Create geo_data for map visualization
    geo_data = {
        "nodes": [],
        "connections": [],
        "cluster_centers": {}
    }
    
    # Aggregate by location for map
    location_aggregates = {}
    for node in graph_data.get("nodes", []):
        key = f"{node.get('latitude', 0)},{node.get('longitude', 0)}"
        if key not in location_aggregates:
            location_aggregates[key] = {
                "latitude": node.get("latitude", 0),
                "longitude": node.get("longitude", 0),
                "city": node.get("city", "Unknown"),
                "country": node.get("country", "US"),
                "accounts": [],
                "total_risk": 0,
                "mule_count": 0
            }
        location_aggregates[key]["accounts"].append(node["id"])
        location_aggregates[key]["total_risk"] += node.get("risk_score", 0)
        if node.get("mule_suspected"):
            location_aggregates[key]["mule_count"] += 1
    
    for loc_key, loc_data in location_aggregates.items():
        geo_data["nodes"].append({
            "latitude": loc_data["latitude"],
            "longitude": loc_data["longitude"],
            "city": loc_data["city"],
            "country": loc_data["country"],
            "account_count": len(loc_data["accounts"]),
            "avg_risk": loc_data["total_risk"] / len(loc_data["accounts"]) if loc_data["accounts"] else 0,
            "mule_count": loc_data["mule_count"],
            "accounts": loc_data["accounts"]
        })
    
    # Add connection lines for transactions between different locations
    for edge in graph_data.get("edges", []):
        src_node = next((n for n in graph_data["nodes"] if n["id"] == edge["source"]), None)
        tgt_node = next((n for n in graph_data["nodes"] if n["id"] == edge["target"]), None)
        if src_node and tgt_node:
            src_loc = (src_node.get("latitude"), src_node.get("longitude"))
            tgt_loc = (tgt_node.get("latitude"), tgt_node.get("longitude"))
            if src_loc != tgt_loc:
                geo_data["connections"].append({
                    "from": {"lat": src_loc[0], "lng": src_loc[1], "city": src_node.get("city")},
                    "to": {"lat": tgt_loc[0], "lng": tgt_loc[1], "city": tgt_node.get("city")},
                    "amount": edge.get("weight", 0),
                    "suspicious": edge.get("suspicious", False)
                })
    
    return {
        "mule_accounts": mule_accounts,
        "network_size": len(mule_accounts),
        "graph_data": graph_data,
        "geo_data": geo_data,
        "inter_cluster_pairs": list(inter_cluster_pairs)
    }

@app.get("/api/graph/network", tags=["Network Analysis"])
async def get_full_network():
    """Get full transaction network visualization data."""
    if not data_store.is_initialized:
        raise HTTPException(status_code=503, detail="System not initialized")
    
    graph_data = data_store.graph_analyzer.get_network_visualization_data()
    
    # Enrich nodes with account info
    for node in graph_data.get("nodes", []):
        account = next(
            (a for a in data_store.accounts if a.get("id") == node["id"]),
            {}
        )
        node["name"] = account.get("account_holder_name", "Unknown")
        node["risk_score"] = account.get("composite_risk_score", 0)
        node["mule_probability"] = account.get("mule_probability", 0)
        node["mule_suspected"] = account.get("mule_suspected", False)
        node["cluster_id"] = account.get("cluster_id")
    
    return graph_data

@app.get("/api/graph/account/{account_id}", tags=["Network Analysis"])
async def get_account_network(account_id: str):
    """Get network data for a specific account."""
    if not data_store.is_initialized:
        raise HTTPException(status_code=503, detail="System not initialized")
    
    account = next((a for a in data_store.accounts if a.get("id") == account_id), None)
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")
    
    # Get centrality scores
    centrality = data_store.graph_analyzer.get_centrality_scores(account_id)
    
    return {
        "id": account_id,
        "name": account.get("account_holder_name"),
        "risk_score": account.get("composite_risk_score"),
        "mule_probability": account.get("mule_probability"),
        "centrality_metrics": centrality,
        "cluster_id": account.get("cluster_id")
    }

@app.get("/api/graph/circular-flows", tags=["Network Analysis"])
async def get_circular_flows():
    """Get detected circular flow patterns."""
    if not data_store.is_initialized:
        raise HTTPException(status_code=503, detail="System not initialized")
    
    patterns = data_store.graph_analyzer.detect_circular_flows()
    return {
        "patterns": patterns,
        "count": len(patterns) if patterns else 0
    }

@app.get("/api/graph/hub-spoke", tags=["Network Analysis"])
async def get_hub_spoke_patterns():
    """Get detected hub-spoke patterns."""
    if not data_store.is_initialized:
        raise HTTPException(status_code=503, detail="System not initialized")
    
    hubs = data_store.graph_analyzer.detect_hub_spoke_patterns()
    return {
        "hubs": hubs,
        "count": len(hubs) if hubs else 0
    }

@app.get("/api/graph/rapid-dispersal", tags=["Network Analysis"])
async def get_rapid_dispersal():
    """Get detected rapid dispersal patterns."""
    if not data_store.is_initialized:
        raise HTTPException(status_code=503, detail="System not initialized")
    
    dispersal = data_store.graph_analyzer.detect_rapid_dispersal(data_store.transactions)
    return {
        "dispersal_patterns": dispersal,
        "count": len(dispersal) if dispersal else 0
    }

@app.get("/api/graph/device-clusters", tags=["Network Analysis"])
async def get_device_clusters():
    """Get device-linked account clusters."""
    if not data_store.is_initialized:
        raise HTTPException(status_code=503, detail="System not initialized")
    
    clusters = data_store.graph_analyzer.detect_device_clusters()
    return {
        "clusters": clusters,
        "count": len(clusters) if clusters else 0
    }

# ============================================
# SAR REPORT ENDPOINTS
# ============================================

@app.get("/api/reports", tags=["Reports"])
async def get_reports(
    status: Optional[str] = Query(None),
    limit: int = Query(100, ge=1, le=100),
    offset: int = Query(0, ge=0),
    skip: int = Query(0, ge=0)
):
    """Get list of generated SAR reports."""
    if not data_store.is_initialized:
        raise HTTPException(status_code=503, detail="System not initialized")
    
    # Get reports from alerts that have been marked as reported
    reports = []
    for alert in data_store.alerts:
        if alert.get("sar_generated"):
            account = next((a for a in data_store.accounts if a.get("id") == alert.get("account_id")), {})
            reports.append({
                "id": alert.get("id"),
                "report_reference": f"SAR-{alert.get('id')}",
                "account_id": alert.get("account_id"),
                "account_name": account.get("account_holder_name"),
                "report_type": "SAR",
                "status": alert.get("sar_status", "draft"),
                "created_at": alert.get("created_at"),
                "content": alert.get("sar_content")
            })
    
    if status:
        reports = [r for r in reports if r.get("status") == status]
    
    # Sort by created_at descending
    reports = sorted(reports, key=lambda x: x.get("created_at", ""), reverse=True)
    
    pagination_offset = skip if skip > 0 else offset
    return reports[pagination_offset:pagination_offset + limit]

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

@app.get("/api/reports/sar/{account_id}/pdf", tags=["Reports"])
async def download_sar_pdf(account_id: str):
    """
    Generate and download SAR report as PDF.
    
    Returns PDF file as downloadable response.
    """
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
    
    # Generate SAR report data
    report = data_store.sar_generator.generate_sar_report(
        account=account,
        risk_score_data=risk_analysis,
        transactions=data_store.transactions,
        network_analysis=network_analysis,
        alert=alert
    )
    
    # Generate PDF
    try:
        pdf_bytes = data_store.pdf_generator.generate_pdf(report)
    except ImportError as e:
        raise HTTPException(
            status_code=500,
            detail="PDF generation not available. Please install reportlab: pip install reportlab"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate PDF: {str(e)}"
        )
    
    # Return PDF as downloadable response
    filename = f"{report.get('report_number', 'SAR-Report')}.pdf"
    
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f"attachment; filename={filename}"
        }
    )

@app.post("/api/reports/sar/{account_id}/email", tags=["Reports"])
async def send_sar_email(account_id: str, email_request: EmailRequest):
    """
    Generate SAR report and send via email.
    
    Optionally attaches PDF report to email.
    """
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
    
    # Generate SAR report data
    report = data_store.sar_generator.generate_sar_report(
        account=account,
        risk_score_data=risk_analysis,
        transactions=data_store.transactions,
        network_analysis=network_analysis,
        alert=alert
    )
    
    # Generate PDF if requested
    pdf_bytes = None
    if email_request.include_pdf:
        try:
            pdf_bytes = data_store.pdf_generator.generate_pdf(report)
        except ImportError:
            # PDF generation not available, continue without attachment
            pass
        except Exception:
            # Failed to generate PDF, continue without attachment
            pass
    
    # Send email
    result = data_store.email_service.send_sar_report(
        recipient_emails=email_request.recipient_emails,
        report_data=report,
        pdf_attachment=pdf_bytes,
        cc_emails=email_request.cc_emails,
        custom_message=email_request.custom_message
    )
    
    if not result["success"]:
        raise HTTPException(
            status_code=500,
            detail=result.get("error", "Failed to send email")
        )
    
    return result

@app.post("/api/email/configure", tags=["Reports"])
async def configure_email(config: EmailConfigRequest):
    """
    Configure email settings for SAR report delivery.
    
    For Gmail, use App Passwords (not your regular password).
    """
    if not data_store.is_initialized:
        raise HTTPException(status_code=503, detail="System not initialized")
    
    data_store.email_service.configure(
        smtp_server=config.smtp_server,
        smtp_port=config.smtp_port,
        sender_email=config.sender_email,
        sender_password=config.sender_password
    )
    
    # Test connection
    test_result = data_store.email_service.test_connection()
    
    return {
        "status": "configured" if test_result["success"] else "configuration_failed",
        "message": test_result.get("message") or test_result.get("error"),
        "details": test_result.get("details")
    }

@app.get("/api/email/test", tags=["Reports"])
async def test_email_connection():
    """Test the configured email connection."""
    if not data_store.is_initialized:
        raise HTTPException(status_code=503, detail="System not initialized")
    
    return data_store.email_service.test_connection()

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
# STREAMING DATA - KAFKA-STYLE
# ============================================

@app.post("/api/stream/start", tags=["Stream"])
async def start_stream(
    tps: float = Query(default=3.0, description="Transactions per second"),
    suspicious_rate: float = Query(default=0.15, description="Rate of suspicious transactions")
):
    """
    Start the real-time transaction stream.
    Simulates bank server transaction flow with Kafka-style message broker.
    """
    if not data_store.is_initialized:
        raise HTTPException(status_code=503, detail="System not initialized")
    
    if data_store.stream_running:
        return {"status": "already_running", "message": "Stream is already running"}
    
    # Initialize message broker
    data_store.message_broker = get_broker()
    await data_store.message_broker.start()
    
    # Configure and create transaction stream
    config = StreamConfig(
        transactions_per_second=tps,
        suspicious_rate=suspicious_rate
    )
    data_store.transaction_stream = create_transaction_stream(
        broker=data_store.message_broker,
        config=config,
        accounts=data_store.accounts
    )
    
    # Configure and create stream processor
    processor_config = ProcessorConfig()
    data_store.stream_processor = create_stream_processor(
        broker=data_store.message_broker,
        config=processor_config,
        accounts=data_store.accounts
    )
    
    # Register callbacks for WebSocket broadcasting
    async def broadcast_transaction(txn: Dict):
        await ws_manager.broadcast("transactions", {
            "type": "transaction",
            "data": txn
        })
        # Also add to data store
        data_store.transactions.append(txn)
        if len(data_store.transactions) > 10000:  # Keep last 10000
            data_store.transactions = data_store.transactions[-10000:]
    
    async def broadcast_alert(alert: Dict):
        await ws_manager.broadcast("alerts", {
            "type": "alert",
            "data": alert
        })
        # Also add to data store
        data_store.alerts.append(alert)
    
    data_store.transaction_stream.on_transaction(broadcast_transaction)
    data_store.transaction_stream.on_alert(broadcast_alert)
    data_store.stream_processor.on_alert(broadcast_alert)
    
    # Start stream and processor in background tasks
    data_store.stream_running = True
    asyncio.create_task(data_store.transaction_stream.start())
    asyncio.create_task(data_store.stream_processor.start())
    
    return {
        "status": "started",
        "message": f"Transaction stream started at {tps} TPS",
        "config": {
            "tps": tps,
            "suspicious_rate": suspicious_rate,
            "accounts_loaded": len(data_store.accounts)
        }
    }


@app.post("/api/stream/stop", tags=["Stream"])
async def stop_stream():
    """Stop the real-time transaction stream."""
    if not data_store.stream_running:
        return {"status": "not_running", "message": "Stream is not running"}
    
    # Stop stream components
    if data_store.transaction_stream:
        await data_store.transaction_stream.stop()
    if data_store.stream_processor:
        await data_store.stream_processor.stop()
    if data_store.message_broker:
        await data_store.message_broker.stop()
    
    data_store.stream_running = False
    
    # Get final stats
    stats = {}
    if data_store.transaction_stream:
        stats["generator"] = data_store.transaction_stream.get_stats()
    if data_store.stream_processor:
        stats["processor"] = data_store.stream_processor.get_stats()
    
    return {
        "status": "stopped",
        "message": "Transaction stream stopped",
        "stats": stats
    }


@app.get("/api/stream/status", tags=["Stream"])
async def get_stream_status():
    """Get current stream status and statistics."""
    status = {
        "running": data_store.stream_running,
        "websocket_connections": ws_manager.get_connection_count()
    }
    
    if data_store.stream_running:
        if data_store.transaction_stream:
            status["generator"] = data_store.transaction_stream.get_stats()
        if data_store.stream_processor:
            status["processor"] = data_store.stream_processor.get_stats()
        if data_store.message_broker:
            status["broker"] = data_store.message_broker.get_stats()
    
    return status


@app.get("/api/stream/topics", tags=["Stream"])
async def get_stream_topics():
    """Get list of available stream topics."""
    if not data_store.message_broker:
        return {"topics": [], "message": "Stream not started"}
    
    broker_stats = data_store.message_broker.get_stats()
    return {
        "topics": data_store.message_broker.list_topics(),
        "topic_details": broker_stats.get("topic_details", {})
    }


# ============================================
# WEBSOCKET ENDPOINTS
# ============================================

@app.websocket("/ws/transactions")
async def websocket_transactions(websocket: WebSocket):
    """
    WebSocket endpoint for real-time transaction stream.
    Clients receive transactions as they are generated.
    """
    await ws_manager.connect(websocket, "transactions")
    try:
        # Send initial connection confirmation
        await ws_manager.send_personal(websocket, {
            "type": "connected",
            "channel": "transactions",
            "message": "Connected to transaction stream"
        })
        
        # Keep connection alive and handle client messages
        while True:
            try:
                data = await asyncio.wait_for(
                    websocket.receive_text(),
                    timeout=30.0
                )
                # Handle ping/pong or commands
                if data == "ping":
                    await ws_manager.send_personal(websocket, {"type": "pong"})
                elif data == "status":
                    await ws_manager.send_personal(websocket, {
                        "type": "status",
                        "stream_running": data_store.stream_running,
                        "connections": ws_manager.get_connection_count()
                    })
            except asyncio.TimeoutError:
                # Send heartbeat
                await ws_manager.send_personal(websocket, {"type": "heartbeat"})
                
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket, "transactions")


@app.websocket("/ws/alerts")
async def websocket_alerts(websocket: WebSocket):
    """
    WebSocket endpoint for real-time AML alerts.
    Clients receive alerts as suspicious activity is detected.
    """
    await ws_manager.connect(websocket, "alerts")
    try:
        await ws_manager.send_personal(websocket, {
            "type": "connected",
            "channel": "alerts",
            "message": "Connected to alert stream"
        })
        
        while True:
            try:
                data = await asyncio.wait_for(
                    websocket.receive_text(),
                    timeout=30.0
                )
                if data == "ping":
                    await ws_manager.send_personal(websocket, {"type": "pong"})
            except asyncio.TimeoutError:
                await ws_manager.send_personal(websocket, {"type": "heartbeat"})
                
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket, "alerts")


@app.websocket("/ws/stats")
async def websocket_stats(websocket: WebSocket):
    """
    WebSocket endpoint for real-time statistics.
    Sends periodic updates on stream performance.
    """
    await ws_manager.connect(websocket, "stats")
    try:
        await ws_manager.send_personal(websocket, {
            "type": "connected",
            "channel": "stats",
            "message": "Connected to stats stream"
        })
        
        while True:
            # Send stats every 2 seconds
            stats = {
                "type": "stats_update",
                "timestamp": datetime.now().isoformat(),
                "stream_running": data_store.stream_running,
                "connections": ws_manager.get_connection_count()
            }
            
            if data_store.stream_running and data_store.transaction_stream:
                stats["generator"] = data_store.transaction_stream.get_stats()
            if data_store.stream_running and data_store.stream_processor:
                stats["processor"] = data_store.stream_processor.get_stats()
            
            await ws_manager.send_personal(websocket, stats)
            await asyncio.sleep(2)
            
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket, "stats")


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
