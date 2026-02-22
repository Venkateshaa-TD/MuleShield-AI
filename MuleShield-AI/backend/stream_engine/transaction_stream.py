"""
MuleShield AI - Transaction Stream Generator
Generates realistic real-time bank transactions simulating actual bank servers

Transaction Types:
- Wire transfers (domestic/international)
- ACH transfers
- Card transactions (debit/credit)
- P2P payments
- Bill payments
- Cash deposits/withdrawals

Includes suspicious pattern injection for AML testing:
- Structuring (smurfing)
- Round-tripping
- Layering
- Rapid movement
"""

import asyncio
import random
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Callable, Any
from dataclasses import dataclass, field
import logging

from .message_broker import MessageBroker, Producer, get_broker

logger = logging.getLogger("TransactionStream")


# ============================================
# CONFIGURATION
# ============================================

@dataclass
class StreamConfig:
    """Configuration for transaction stream"""
    transactions_per_second: float = 5.0  # TPS rate
    suspicious_rate: float = 0.15  # 15% suspicious transactions
    batch_size: int = 10
    include_account_events: bool = True
    include_risk_events: bool = True
    working_hours_boost: float = 2.0  # 2x during business hours


# ============================================
# DATA POOLS FOR REALISTIC GENERATION
# ============================================

MERCHANT_CATEGORIES = {
    "retail": ["Walmart", "Target", "Amazon", "Costco", "Best Buy", "Home Depot"],
    "food": ["McDonald's", "Starbucks", "Chipotle", "Subway", "Pizza Hut", "Dominos"],
    "gas": ["Shell", "Chevron", "BP", "ExxonMobil", "Valero", "Speedway"],
    "travel": ["United Airlines", "Delta", "Marriott", "Hilton", "Expedia", "Uber"],
    "utilities": ["AT&T", "Verizon", "Comcast", "Duke Energy", "PG&E", "Water Utility"],
    "financial": ["Chase Bank", "Wells Fargo", "Bank of America", "Citibank", "Capital One"],
    "healthcare": ["CVS", "Walgreens", "Kaiser", "UnitedHealth", "Anthem", "Blue Cross"],
    "entertainment": ["Netflix", "Spotify", "Apple Music", "Disney+", "AMC Theaters"],
}

CITIES = {
    "New York": {"state": "NY", "lat": 40.7128, "lng": -74.0060, "timezone": "EST"},
    "Los Angeles": {"state": "CA", "lat": 34.0522, "lng": -118.2437, "timezone": "PST"},
    "Chicago": {"state": "IL", "lat": 41.8781, "lng": -87.6298, "timezone": "CST"},
    "Houston": {"state": "TX", "lat": 29.7604, "lng": -95.3698, "timezone": "CST"},
    "Phoenix": {"state": "AZ", "lat": 33.4484, "lng": -112.0740, "timezone": "MST"},
    "Miami": {"state": "FL", "lat": 25.7617, "lng": -80.1918, "timezone": "EST"},
    "Seattle": {"state": "WA", "lat": 47.6062, "lng": -122.3321, "timezone": "PST"},
    "Denver": {"state": "CO", "lat": 39.7392, "lng": -104.9903, "timezone": "MST"},
    "Boston": {"state": "MA", "lat": 42.3601, "lng": -71.0589, "timezone": "EST"},
    "Atlanta": {"state": "GA", "lat": 33.7490, "lng": -84.3880, "timezone": "EST"},
    "Dallas": {"state": "TX", "lat": 32.7767, "lng": -96.7970, "timezone": "CST"},
    "San Francisco": {"state": "CA", "lat": 37.7749, "lng": -122.4194, "timezone": "PST"},
    "Las Vegas": {"state": "NV", "lat": 36.1699, "lng": -115.1398, "timezone": "PST"},
    "Detroit": {"state": "MI", "lat": 42.3314, "lng": -83.0458, "timezone": "EST"},
    "Philadelphia": {"state": "PA", "lat": 39.9526, "lng": -75.1652, "timezone": "EST"},
}

INTERNATIONAL_COUNTRIES = [
    {"code": "UK", "name": "United Kingdom", "currency": "GBP", "risk": "low"},
    {"code": "DE", "name": "Germany", "currency": "EUR", "risk": "low"},
    {"code": "FR", "name": "France", "currency": "EUR", "risk": "low"},
    {"code": "JP", "name": "Japan", "currency": "JPY", "risk": "low"},
    {"code": "CN", "name": "China", "currency": "CNY", "risk": "medium"},
    {"code": "RU", "name": "Russia", "currency": "RUB", "risk": "high"},
    {"code": "MX", "name": "Mexico", "currency": "MXN", "risk": "medium"},
    {"code": "BZ", "name": "Belize", "currency": "BZD", "risk": "high"},
    {"code": "CY", "name": "Cyprus", "currency": "EUR", "risk": "high"},
    {"code": "PA", "name": "Panama", "currency": "USD", "risk": "high"},
]

FIRST_NAMES = [
    "James", "Mary", "John", "Patricia", "Robert", "Jennifer", "Michael", "Linda",
    "William", "Elizabeth", "David", "Barbara", "Richard", "Susan", "Joseph", "Jessica",
]

LAST_NAMES = [
    "Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis",
    "Rodriguez", "Martinez", "Hernandez", "Lopez", "Gonzalez", "Wilson", "Anderson",
]


# ============================================
# TRANSACTION MODELS
# ============================================

class TransactionType:
    """Transaction type definitions"""
    WIRE_DOMESTIC = "wire_domestic"
    WIRE_INTERNATIONAL = "wire_international"
    ACH_CREDIT = "ach_credit"
    ACH_DEBIT = "ach_debit"
    CARD_PURCHASE = "card_purchase"
    CARD_ATM = "card_atm"
    P2P_TRANSFER = "p2p_transfer"
    CASH_DEPOSIT = "cash_deposit"
    CASH_WITHDRAWAL = "cash_withdrawal"
    BILL_PAYMENT = "bill_payment"
    CHECK_DEPOSIT = "check_deposit"
    
    @classmethod
    def all_types(cls) -> List[str]:
        return [
            cls.WIRE_DOMESTIC, cls.WIRE_INTERNATIONAL,
            cls.ACH_CREDIT, cls.ACH_DEBIT,
            cls.CARD_PURCHASE, cls.CARD_ATM,
            cls.P2P_TRANSFER, cls.CASH_DEPOSIT,
            cls.CASH_WITHDRAWAL, cls.BILL_PAYMENT,
            cls.CHECK_DEPOSIT
        ]


class SuspiciousPattern:
    """AML red flag patterns"""
    STRUCTURING = "structuring"  # Multiple transactions just under $10K
    SMURFING = "smurfing"  # Multiple deposits from different sources
    LAYERING = "layering"  # Rapid fund movements
    ROUND_TRIPPING = "round_tripping"  # Funds return to source
    VELOCITY_ANOMALY = "velocity_anomaly"  # Unusual transaction frequency
    HIGH_RISK_JURISDICTION = "high_risk_jurisdiction"  # Transfers to risky countries
    UNUSUAL_AMOUNT = "unusual_amount"  # Amounts ending in suspicious patterns


# ============================================
# TRANSACTION GENERATOR
# ============================================

class TransactionStreamGenerator:
    """
    Real-time transaction stream generator
    Simulates actual bank transaction flow
    """
    
    def __init__(
        self,
        broker: MessageBroker = None,
        config: StreamConfig = None,
        accounts: List[Dict] = None
    ):
        self.broker = broker or get_broker()
        self.config = config or StreamConfig()
        self.accounts = accounts or []
        self.producer: Optional[Producer] = None
        
        # Stream state
        self.running = False
        self.generated_count = 0
        self.suspicious_count = 0
        self.start_time: Optional[datetime] = None
        
        # Mule network simulation
        self.mule_accounts: List[str] = []
        self.mule_networks: Dict[str, List[str]] = {}
        
        # Callbacks
        self.on_transaction_callbacks: List[Callable] = []
        self.on_alert_callbacks: List[Callable] = []
        
    def set_accounts(self, accounts: List[Dict]):
        """Set the account pool for transactions"""
        self.accounts = accounts
        
        # Identify mule accounts
        self.mule_accounts = [
            acc["id"] for acc in accounts
            if acc.get("mule_network_id") or acc.get("risk_score", 0) > 75
        ]
        
        # Group by mule network
        for acc in accounts:
            network_id = acc.get("mule_network_id")
            if network_id:
                if network_id not in self.mule_networks:
                    self.mule_networks[network_id] = []
                self.mule_networks[network_id].append(acc["id"])
        
        logger.info(f"Loaded {len(accounts)} accounts, {len(self.mule_accounts)} mule accounts")
    
    async def start(self):
        """Start the transaction stream"""
        if not self.accounts:
            logger.warning("No accounts loaded - generating sample accounts")
            self._generate_sample_accounts()
        
        self.producer = self.broker.create_producer("transaction-generator")
        self.running = True
        self.start_time = datetime.now()
        
        logger.info(f"Transaction stream started at {self.config.transactions_per_second} TPS")
        
        # Start generation loop
        await self._generation_loop()
    
    async def stop(self):
        """Stop the transaction stream"""
        self.running = False
        logger.info(f"Transaction stream stopped. Generated {self.generated_count} transactions")
    
    async def _generation_loop(self):
        """Main generation loop"""
        interval = 1.0 / self.config.transactions_per_second
        
        while self.running:
            try:
                # Apply working hours boost
                current_hour = datetime.now().hour
                if 9 <= current_hour <= 17:  # Business hours
                    actual_interval = interval / self.config.working_hours_boost
                else:
                    actual_interval = interval * 1.5  # Slower at night
                
                # Generate transaction
                transaction = await self._generate_transaction()
                
                # Publish to broker
                await self.producer.send(
                    topic="transactions.raw",
                    value=transaction,
                    key=transaction["account_id"]
                )
                
                # Also publish to main transactions topic
                await self.producer.send(
                    topic="transactions",
                    value=transaction,
                    key=transaction["id"]
                )
                
                self.generated_count += 1
                
                # Execute callbacks
                for callback in self.on_transaction_callbacks:
                    try:
                        if asyncio.iscoroutinefunction(callback):
                            await callback(transaction)
                        else:
                            callback(transaction)
                    except Exception as e:
                        logger.error(f"Transaction callback error: {e}")
                
                # Random delay for natural variation
                jitter = random.uniform(0.8, 1.2)
                await asyncio.sleep(actual_interval * jitter)
                
            except Exception as e:
                logger.error(f"Generation error: {e}")
                await asyncio.sleep(1)
    
    async def _generate_transaction(self) -> Dict:
        """Generate a single transaction"""
        # Determine if suspicious
        is_suspicious = random.random() < self.config.suspicious_rate
        
        if is_suspicious:
            return await self._generate_suspicious_transaction()
        else:
            return await self._generate_normal_transaction()
    
    async def _generate_normal_transaction(self) -> Dict:
        """Generate a normal/legitimate transaction"""
        account = random.choice(self.accounts)
        txn_type = random.choice(TransactionType.all_types())
        
        # Generate amount based on transaction type
        amount = self._generate_amount(txn_type)
        
        # Generate location
        city_name, city_data = random.choice(list(CITIES.items()))
        
        # Base transaction
        transaction = {
            "id": str(uuid.uuid4()),
            "account_id": account["id"],
            "account_number": account.get("account_number", self._generate_account_number()),
            "account_name": account.get("name", f"{random.choice(FIRST_NAMES)} {random.choice(LAST_NAMES)}"),
            "type": txn_type,
            "amount": amount,
            "currency": "USD",
            "timestamp": datetime.now().isoformat(),
            "status": "completed",
            "direction": "outgoing" if "debit" in txn_type or "withdrawal" in txn_type or "purchase" in txn_type else "incoming",
            "channel": self._get_channel(txn_type),
            "location": {
                "city": city_name,
                "state": city_data["state"],
                "country": "US",
                "lat": city_data["lat"],
                "lng": city_data["lng"],
            },
            "device": self._generate_device_info(),
            "risk_indicators": [],
            "is_suspicious": False,
            "aml_score": random.randint(0, 30),
        }
        
        # Add type-specific fields
        transaction = self._enrich_transaction(transaction, txn_type)
        
        return transaction
    
    async def _generate_suspicious_transaction(self) -> Dict:
        """Generate a suspicious transaction with AML red flags"""
        self.suspicious_count += 1
        
        # Choose a suspicious pattern
        pattern = random.choice([
            SuspiciousPattern.STRUCTURING,
            SuspiciousPattern.LAYERING,
            SuspiciousPattern.HIGH_RISK_JURISDICTION,
            SuspiciousPattern.VELOCITY_ANOMALY,
            SuspiciousPattern.UNUSUAL_AMOUNT,
        ])
        
        # Use mule account if available
        if self.mule_accounts and random.random() > 0.3:
            account_id = random.choice(self.mule_accounts)
            account = next((a for a in self.accounts if a["id"] == account_id), None)
        else:
            account = random.choice(self.accounts)
        
        if not account:
            account = random.choice(self.accounts)
        
        transaction = await self._generate_normal_transaction()
        transaction["account_id"] = account["id"]
        transaction["is_suspicious"] = True
        transaction["suspicious_pattern"] = pattern
        transaction["aml_score"] = random.randint(60, 95)
        
        # Apply pattern-specific modifications
        if pattern == SuspiciousPattern.STRUCTURING:
            # Just under $10,000 CTR threshold
            transaction["amount"] = round(random.uniform(9000, 9999), 2)
            transaction["type"] = TransactionType.CASH_DEPOSIT
            transaction["risk_indicators"].append("Amount just under CTR threshold ($10,000)")
            
        elif pattern == SuspiciousPattern.LAYERING:
            # Rapid movement between accounts
            transaction["type"] = TransactionType.WIRE_DOMESTIC
            transaction["amount"] = round(random.uniform(15000, 75000), 2)
            transaction["risk_indicators"].append("Rapid fund movement detected")
            
            # Add counterparty from same mule network
            network_id = account.get("mule_network_id")
            if network_id and network_id in self.mule_networks:
                counterparty_id = random.choice(self.mule_networks[network_id])
                if counterparty_id != account["id"]:
                    transaction["counterparty_account_id"] = counterparty_id
                    transaction["risk_indicators"].append("Connected to mule network cluster")
                    
        elif pattern == SuspiciousPattern.HIGH_RISK_JURISDICTION:
            transaction["type"] = TransactionType.WIRE_INTERNATIONAL
            country = random.choice([c for c in INTERNATIONAL_COUNTRIES if c["risk"] == "high"])
            transaction["destination_country"] = country["code"]
            transaction["destination_country_name"] = country["name"]
            transaction["amount"] = round(random.uniform(25000, 150000), 2)
            transaction["risk_indicators"].append(f"Transfer to high-risk jurisdiction: {country['name']}")
            
        elif pattern == SuspiciousPattern.VELOCITY_ANOMALY:
            transaction["risk_indicators"].append("Unusual transaction frequency")
            transaction["velocity_score"] = random.uniform(0.7, 1.0)
            
        elif pattern == SuspiciousPattern.UNUSUAL_AMOUNT:
            # Round numbers or repeated patterns
            base = random.choice([5000, 10000, 25000, 50000])
            transaction["amount"] = base
            transaction["risk_indicators"].append("Suspicious round amount pattern")
        
        # Publish alert for high-risk transactions
        if transaction["aml_score"] >= 75:
            alert = self._create_alert(transaction)
            await self.producer.send(
                topic="alerts",
                value=alert,
                key=alert["id"]
            )
            
            # Execute alert callbacks
            for callback in self.on_alert_callbacks:
                try:
                    if asyncio.iscoroutinefunction(callback):
                        await callback(alert)
                    else:
                        callback(alert)
                except Exception as e:
                    logger.error(f"Alert callback error: {e}")
        
        return transaction
    
    def _generate_amount(self, txn_type: str) -> float:
        """Generate realistic amount based on transaction type"""
        ranges = {
            TransactionType.WIRE_DOMESTIC: (1000, 50000),
            TransactionType.WIRE_INTERNATIONAL: (5000, 100000),
            TransactionType.ACH_CREDIT: (500, 15000),
            TransactionType.ACH_DEBIT: (100, 5000),
            TransactionType.CARD_PURCHASE: (10, 500),
            TransactionType.CARD_ATM: (20, 500),
            TransactionType.P2P_TRANSFER: (10, 2500),
            TransactionType.CASH_DEPOSIT: (100, 8000),
            TransactionType.CASH_WITHDRAWAL: (20, 1000),
            TransactionType.BILL_PAYMENT: (50, 500),
            TransactionType.CHECK_DEPOSIT: (100, 5000),
        }
        
        min_amt, max_amt = ranges.get(txn_type, (10, 1000))
        return round(random.uniform(min_amt, max_amt), 2)
    
    def _get_channel(self, txn_type: str) -> str:
        """Get transaction channel"""
        channels = {
            TransactionType.WIRE_DOMESTIC: "branch",
            TransactionType.WIRE_INTERNATIONAL: "branch",
            TransactionType.ACH_CREDIT: "online",
            TransactionType.ACH_DEBIT: "online",
            TransactionType.CARD_PURCHASE: "pos",
            TransactionType.CARD_ATM: "atm",
            TransactionType.P2P_TRANSFER: "mobile",
            TransactionType.CASH_DEPOSIT: random.choice(["atm", "branch"]),
            TransactionType.CASH_WITHDRAWAL: random.choice(["atm", "branch"]),
            TransactionType.BILL_PAYMENT: "online",
            TransactionType.CHECK_DEPOSIT: random.choice(["mobile", "branch"]),
        }
        return channels.get(txn_type, "online")
    
    def _generate_device_info(self) -> Dict:
        """Generate device information"""
        return {
            "device_id": f"DEV-{uuid.uuid4().hex[:12].upper()}",
            "device_type": random.choice(["mobile", "desktop", "tablet"]),
            "os": random.choice(["iOS", "Android", "Windows", "macOS"]),
            "browser": random.choice(["Chrome", "Safari", "Firefox", "Edge"]),
            "ip_address": f"{random.randint(1,255)}.{random.randint(0,255)}.{random.randint(0,255)}.{random.randint(1,254)}"
        }
    
    def _enrich_transaction(self, transaction: Dict, txn_type: str) -> Dict:
        """Add type-specific fields"""
        if txn_type == TransactionType.CARD_PURCHASE:
            category = random.choice(list(MERCHANT_CATEGORIES.keys()))
            merchant = random.choice(MERCHANT_CATEGORIES[category])
            transaction["merchant"] = {
                "name": merchant,
                "category": category,
                "mcc": str(random.randint(1000, 9999))
            }
            
        elif txn_type in [TransactionType.WIRE_DOMESTIC, TransactionType.ACH_CREDIT, TransactionType.ACH_DEBIT]:
            transaction["counterparty"] = {
                "name": f"{random.choice(FIRST_NAMES)} {random.choice(LAST_NAMES)}",
                "account_number": self._generate_account_number(),
                "bank": random.choice(["Chase", "Wells Fargo", "Bank of America", "Citibank"])
            }
            
        elif txn_type == TransactionType.WIRE_INTERNATIONAL:
            country = random.choice(INTERNATIONAL_COUNTRIES)
            transaction["destination_country"] = country["code"]
            transaction["destination_country_name"] = country["name"]
            transaction["destination_currency"] = country["currency"]
            transaction["swift_code"] = f"{random.choice(['CHAS', 'WELLS', 'CITI', 'HSBC'])}{country['code']}XX"
            
        elif txn_type == TransactionType.P2P_TRANSFER:
            transaction["p2p_service"] = random.choice(["Zelle", "Venmo", "PayPal", "CashApp"])
            transaction["recipient"] = f"{random.choice(FIRST_NAMES)} {random.choice(LAST_NAMES)}"
            
        return transaction
    
    def _create_alert(self, transaction: Dict) -> Dict:
        """Create an AML alert from suspicious transaction"""
        return {
            "id": str(uuid.uuid4()),
            "transaction_id": transaction["id"],
            "account_id": transaction["account_id"],
            "alert_type": transaction.get("suspicious_pattern", "suspicious_activity"),
            "severity": "high" if transaction["aml_score"] >= 85 else "medium",
            "aml_score": transaction["aml_score"],
            "description": f"Suspicious transaction detected: {', '.join(transaction['risk_indicators'])}",
            "risk_indicators": transaction["risk_indicators"],
            "amount": transaction["amount"],
            "created_at": datetime.now().isoformat(),
            "status": "new",
            "requires_sar": transaction["aml_score"] >= 80
        }
    
    def _generate_account_number(self) -> str:
        """Generate random account number"""
        return ''.join([str(random.randint(0, 9)) for _ in range(12)])
    
    def _generate_sample_accounts(self):
        """Generate sample accounts if none provided"""
        self.accounts = []
        for i in range(50):
            self.accounts.append({
                "id": str(uuid.uuid4()),
                "name": f"{random.choice(FIRST_NAMES)} {random.choice(LAST_NAMES)}",
                "account_number": self._generate_account_number(),
                "risk_score": random.randint(0, 100),
                "mule_network_id": f"network_{i % 5}" if i < 15 else None
            })
    
    def on_transaction(self, callback: Callable):
        """Register callback for new transactions"""
        self.on_transaction_callbacks.append(callback)
    
    def on_alert(self, callback: Callable):
        """Register callback for new alerts"""
        self.on_alert_callbacks.append(callback)
    
    def get_stats(self) -> Dict:
        """Get generator statistics"""
        uptime = (datetime.now() - self.start_time).total_seconds() if self.start_time else 0
        return {
            "running": self.running,
            "generated_count": self.generated_count,
            "suspicious_count": self.suspicious_count,
            "suspicious_rate": self.suspicious_count / max(1, self.generated_count),
            "uptime_seconds": uptime,
            "tps_actual": self.generated_count / max(1, uptime),
            "tps_configured": self.config.transactions_per_second,
            "accounts_loaded": len(self.accounts),
            "mule_accounts": len(self.mule_accounts)
        }


# Factory function
def create_transaction_stream(
    broker: MessageBroker = None,
    config: StreamConfig = None,
    accounts: List[Dict] = None
) -> TransactionStreamGenerator:
    """Create a new transaction stream generator"""
    return TransactionStreamGenerator(broker, config, accounts)
