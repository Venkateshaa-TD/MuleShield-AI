"""
MuleShield AI - Stream Processor
Real-time AML detection pipeline consuming from message broker

Processing Stages:
1. Transaction enrichment (add account context)
2. Risk scoring (ML-based scoring)
3. Pattern detection (rule-based checks)  
4. Alert generation (create alerts for high-risk)
5. Network analysis (detect mule clusters)
"""

import asyncio
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Callable, Any, Set
from collections import defaultdict
from dataclasses import dataclass, field
import logging

from .message_broker import MessageBroker, Consumer, Producer, Message, get_broker

logger = logging.getLogger("StreamProcessor")


# ============================================
# CONFIGURATION
# ============================================

@dataclass
class ProcessorConfig:
    """Stream processor configuration"""
    # Risk thresholds
    alert_threshold: float = 70.0
    sar_threshold: float = 80.0
    
    # Velocity windows
    velocity_window_minutes: int = 30
    velocity_threshold: int = 10  # Max transactions in window
    
    # Amount thresholds
    ctr_threshold: float = 10000.0  # Currency Transaction Report
    structuring_floor: float = 7500.0  # Potential structuring if multiple near this
    
    # Pattern detection
    enable_pattern_detection: bool = True
    enable_network_analysis: bool = True


# ============================================
# DETECTION RULES
# ============================================

class DetectionRule:
    """Base class for detection rules"""
    
    def __init__(self, name: str, severity: str = "medium"):
        self.name = name
        self.severity = severity
    
    def evaluate(self, transaction: Dict, context: Dict) -> Optional[Dict]:
        """Evaluate rule against transaction. Return alert if triggered."""
        raise NotImplementedError


class StructuringRule(DetectionRule):
    """Detect structuring (transactions just under CTR threshold)"""
    
    def __init__(self):
        super().__init__("Structuring Detection", "high")
        self.ctr_threshold = 10000.0
        self.min_amount = 8000.0
    
    def evaluate(self, transaction: Dict, context: Dict) -> Optional[Dict]:
        amount = transaction.get("amount", 0)
        
        if self.min_amount <= amount < self.ctr_threshold:
            # Check for multiple near-threshold transactions
            recent_txns = context.get("recent_transactions", [])
            near_threshold_count = sum(
                1 for t in recent_txns 
                if self.min_amount <= t.get("amount", 0) < self.ctr_threshold
            )
            
            if near_threshold_count >= 2:
                return {
                    "rule": self.name,
                    "severity": self.severity,
                    "description": f"Multiple transactions near CTR threshold detected. Amount: ${amount:,.2f}",
                    "indicators": [
                        f"Transaction amount ${amount:,.2f} just under $10,000 threshold",
                        f"{near_threshold_count} similar transactions in recent history"
                    ]
                }
        return None


class VelocityRule(DetectionRule):
    """Detect unusual transaction velocity"""
    
    def __init__(self, threshold: int = 10, window_minutes: int = 30):
        super().__init__("Velocity Anomaly", "medium")
        self.threshold = threshold
        self.window_minutes = window_minutes
    
    def evaluate(self, transaction: Dict, context: Dict) -> Optional[Dict]:
        recent_txns = context.get("recent_transactions", [])
        
        if len(recent_txns) >= self.threshold:
            return {
                "rule": self.name,
                "severity": self.severity,
                "description": f"Unusual transaction velocity: {len(recent_txns)} transactions in {self.window_minutes} minutes",
                "indicators": [
                    f"{len(recent_txns)} transactions detected in short window",
                    "Velocity exceeds normal account behavior"
                ]
            }
        return None


class HighRiskJurisdictionRule(DetectionRule):
    """Detect transactions to high-risk jurisdictions"""
    
    HIGH_RISK_COUNTRIES = {"RU", "BZ", "CY", "PA", "KP", "IR", "SY", "VE"}
    
    def __init__(self):
        super().__init__("High Risk Jurisdiction", "high")
    
    def evaluate(self, transaction: Dict, context: Dict) -> Optional[Dict]:
        dest_country = transaction.get("destination_country", "")
        
        if dest_country in self.HIGH_RISK_COUNTRIES:
            return {
                "rule": self.name,
                "severity": self.severity,
                "description": f"Transfer to high-risk jurisdiction: {transaction.get('destination_country_name', dest_country)}",
                "indicators": [
                    f"Destination country {dest_country} on high-risk list",
                    f"Amount: ${transaction.get('amount', 0):,.2f}"
                ]
            }
        return None


class RapidMovementRule(DetectionRule):
    """Detect rapid fund movement (layering)"""
    
    def __init__(self):
        super().__init__("Rapid Fund Movement", "high")
    
    def evaluate(self, transaction: Dict, context: Dict) -> Optional[Dict]:
        # Check if funds moved quickly (received and sent within short window)
        recent_txns = context.get("recent_transactions", [])
        
        incoming = [t for t in recent_txns if t.get("direction") == "incoming"]
        outgoing = [t for t in recent_txns if t.get("direction") == "outgoing"]
        
        if incoming and outgoing:
            incoming_amount = sum(t.get("amount", 0) for t in incoming)
            outgoing_amount = sum(t.get("amount", 0) for t in outgoing)
            
            # Check if similar amounts moved in/out quickly
            if 0.8 <= outgoing_amount / max(1, incoming_amount) <= 1.2:
                if outgoing_amount > 5000:
                    return {
                        "rule": self.name,
                        "severity": self.severity,
                        "description": f"Rapid fund movement detected. In: ${incoming_amount:,.2f}, Out: ${outgoing_amount:,.2f}",
                        "indicators": [
                            "Funds received and dispersed within short timeframe",
                            "Characteristic of layering activity"
                        ]
                    }
        return None


class RoundAmountRule(DetectionRule):
    """Detect suspicious round amount patterns"""
    
    def __init__(self):
        super().__init__("Round Amount Pattern", "low")
    
    def evaluate(self, transaction: Dict, context: Dict) -> Optional[Dict]:
        amount = transaction.get("amount", 0)
        
        # Check for round amounts
        if amount >= 1000 and amount % 1000 == 0:
            recent_txns = context.get("recent_transactions", [])
            round_count = sum(1 for t in recent_txns if t.get("amount", 0) % 1000 == 0)
            
            if round_count >= 3:
                return {
                    "rule": self.name,
                    "severity": self.severity,
                    "description": f"Multiple round amount transactions detected. Amount: ${amount:,.2f}",
                    "indicators": [
                        f"Transaction amount is round number: ${amount:,.2f}",
                        f"{round_count} round amount transactions in history"
                    ]
                }
        return None


# ============================================
# STREAM PROCESSOR
# ============================================

class StreamProcessor:
    """
    Real-time stream processor for AML detection
    Consumes from transaction topics and produces alerts
    """
    
    def __init__(
        self,
        broker: MessageBroker = None,
        config: ProcessorConfig = None,
        accounts: List[Dict] = None
    ):
        self.broker = broker or get_broker()
        self.config = config or ProcessorConfig()
        
        # Account context
        self.accounts: Dict[str, Dict] = {}
        if accounts:
            for acc in accounts:
                self.accounts[acc["id"]] = acc
        
        # Transaction history per account (for pattern detection)
        self.transaction_history: Dict[str, List[Dict]] = defaultdict(list)
        
        # Detection rules
        self.rules: List[DetectionRule] = [
            StructuringRule(),
            VelocityRule(
                threshold=self.config.velocity_threshold,
                window_minutes=self.config.velocity_window_minutes
            ),
            HighRiskJurisdictionRule(),
            RapidMovementRule(),
            RoundAmountRule(),
        ]
        
        # Processing state
        self.consumer: Optional[Consumer] = None
        self.producer: Optional[Producer] = None
        self.running = False
        
        # Statistics
        self.processed_count = 0
        self.alerts_generated = 0
        self.start_time: Optional[datetime] = None
        
        # Callbacks
        self.on_alert_callbacks: List[Callable] = []
        self.on_processed_callbacks: List[Callable] = []
    
    def set_accounts(self, accounts: List[Dict]):
        """Update account context"""
        for acc in accounts:
            self.accounts[acc["id"]] = acc
    
    async def start(self):
        """Start the stream processor"""
        self.consumer = self.broker.create_consumer(
            group_id="aml-processor",
            topics=["transactions.raw"]
        )
        await self.consumer.subscribe(["transactions.raw"])
        
        self.producer = self.broker.create_producer("aml-processor")
        
        # Register message handler
        self.consumer.on_message("transactions.raw", self._process_transaction)
        
        self.running = True
        self.start_time = datetime.now()
        
        logger.info("Stream processor started")
        
        # Start processing loop
        await self._processing_loop()
    
    async def stop(self):
        """Stop the stream processor"""
        self.running = False
        if self.consumer:
            await self.consumer.stop()
        logger.info(f"Stream processor stopped. Processed {self.processed_count} transactions")
    
    async def _processing_loop(self):
        """Main processing loop"""
        while self.running:
            try:
                messages = await self.consumer.poll(timeout_ms=100)
                await asyncio.sleep(0.01)
            except Exception as e:
                logger.error(f"Processing error: {e}")
                await asyncio.sleep(1)
    
    async def _process_transaction(self, message: Message):
        """Process a single transaction"""
        try:
            transaction = message.value
            account_id = transaction.get("account_id")
            
            # Stage 1: Enrich with account context
            transaction = self._enrich_transaction(transaction)
            
            # Stage 2: Update transaction history
            self._update_history(account_id, transaction)
            
            # Stage 3: Build context for rule evaluation
            context = self._build_context(account_id)
            
            # Stage 4: Run detection rules
            if self.config.enable_pattern_detection:
                alerts = self._run_detection_rules(transaction, context)
                
                # Stage 5: Generate alerts
                for alert_data in alerts:
                    alert = self._create_alert(transaction, alert_data)
                    await self._publish_alert(alert)
            
            # Stage 6: Publish enriched transaction
            await self.producer.send(
                topic="transactions.enriched",
                value=transaction,
                key=transaction["id"]
            )
            
            self.processed_count += 1
            
            # Execute callbacks
            for callback in self.on_processed_callbacks:
                try:
                    if asyncio.iscoroutinefunction(callback):
                        await callback(transaction)
                    else:
                        callback(transaction)
                except Exception as e:
                    logger.error(f"Processed callback error: {e}")
                    
        except Exception as e:
            logger.error(f"Transaction processing error: {e}")
    
    def _enrich_transaction(self, transaction: Dict) -> Dict:
        """Enrich transaction with account context"""
        account_id = transaction.get("account_id")
        
        if account_id and account_id in self.accounts:
            account = self.accounts[account_id]
            transaction["account_context"] = {
                "name": account.get("name"),
                "risk_score": account.get("risk_score", 0),
                "account_type": account.get("account_type", "checking"),
                "is_mule_suspect": account.get("mule_network_id") is not None,
                "mule_network_id": account.get("mule_network_id"),
                "cluster_id": account.get("cluster_id")
            }
        
        transaction["processed_at"] = datetime.now().isoformat()
        return transaction
    
    def _update_history(self, account_id: str, transaction: Dict):
        """Update transaction history for account"""
        if not account_id:
            return
        
        self.transaction_history[account_id].append(transaction)
        
        # Keep only recent history (within velocity window)
        cutoff = datetime.now() - timedelta(minutes=self.config.velocity_window_minutes)
        self.transaction_history[account_id] = [
            t for t in self.transaction_history[account_id]
            if datetime.fromisoformat(t.get("timestamp", datetime.now().isoformat())) > cutoff
        ]
    
    def _build_context(self, account_id: str) -> Dict:
        """Build context for rule evaluation"""
        return {
            "account_id": account_id,
            "account": self.accounts.get(account_id, {}),
            "recent_transactions": self.transaction_history.get(account_id, []),
            "transaction_count": len(self.transaction_history.get(account_id, [])),
        }
    
    def _run_detection_rules(self, transaction: Dict, context: Dict) -> List[Dict]:
        """Run all detection rules"""
        alerts = []
        
        for rule in self.rules:
            try:
                result = rule.evaluate(transaction, context)
                if result:
                    alerts.append(result)
            except Exception as e:
                logger.error(f"Rule {rule.name} error: {e}")
        
        return alerts
    
    def _create_alert(self, transaction: Dict, alert_data: Dict) -> Dict:
        """Create alert from detection result"""
        import uuid
        
        alert = {
            "id": str(uuid.uuid4()),
            "transaction_id": transaction["id"],
            "account_id": transaction.get("account_id"),
            "rule_name": alert_data["rule"],
            "severity": alert_data["severity"],
            "description": alert_data["description"],
            "risk_indicators": alert_data.get("indicators", []),
            "amount": transaction.get("amount"),
            "created_at": datetime.now().isoformat(),
            "status": "new",
            "aml_score": transaction.get("aml_score", 50) + 20,  # Boost score due to alert
            "requires_review": alert_data["severity"] in ["high", "critical"],
            "transaction_details": {
                "type": transaction.get("type"),
                "amount": transaction.get("amount"),
                "timestamp": transaction.get("timestamp"),
                "location": transaction.get("location"),
            }
        }
        
        return alert
    
    async def _publish_alert(self, alert: Dict):
        """Publish alert to broker"""
        topic = "alerts.high-priority" if alert["severity"] == "high" else "alerts"
        
        await self.producer.send(
            topic=topic,
            value=alert,
            key=alert["id"]
        )
        
        self.alerts_generated += 1
        
        # Also publish to AML detections topic
        await self.producer.send(
            topic="aml-detections",
            value=alert,
            key=alert["transaction_id"]
        )
        
        # Execute callbacks
        for callback in self.on_alert_callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(alert)
                else:
                    callback(alert)
            except Exception as e:
                logger.error(f"Alert callback error: {e}")
    
    def on_alert(self, callback: Callable):
        """Register callback for alerts"""
        self.on_alert_callbacks.append(callback)
    
    def on_processed(self, callback: Callable):
        """Register callback for processed transactions"""
        self.on_processed_callbacks.append(callback)
    
    def get_stats(self) -> Dict:
        """Get processor statistics"""
        uptime = (datetime.now() - self.start_time).total_seconds() if self.start_time else 0
        return {
            "running": self.running,
            "processed_count": self.processed_count,
            "alerts_generated": self.alerts_generated,
            "alert_rate": self.alerts_generated / max(1, self.processed_count),
            "uptime_seconds": uptime,
            "tps": self.processed_count / max(1, uptime),
            "accounts_tracked": len(self.accounts),
            "active_histories": len(self.transaction_history),
        }


# Factory function
def create_stream_processor(
    broker: MessageBroker = None,
    config: ProcessorConfig = None,
    accounts: List[Dict] = None
) -> StreamProcessor:
    """Create a new stream processor"""
    return StreamProcessor(broker, config, accounts)
