"""
MuleShield AI - Mock Data Generator
Generates realistic AML test data with synthetic mule network clusters

This generator creates:
- 100 accounts with varying risk profiles
- Legitimate transaction patterns
- Mule network clusters with suspicious patterns
- Device fingerprint data with shared device scenarios
- Circular fund flows and hub-spoke patterns

Mule Network Patterns Simulated:
1. Hub-Spoke: One central account receiving/distributing funds
2. Circular Flow: A→B→C→D→A money flow
3. Rapid Dispersal: Quick in-and-out transactions
4. Device Cluster: Multiple accounts sharing devices
5. Velocity Anomaly: Abnormally high transaction frequency
"""

import uuid
import random
from datetime import datetime, timedelta
from typing import List, Dict, Tuple
import json

# Seed for reproducibility
random.seed(42)

# ============================================
# NAME POOLS FOR REALISTIC DATA
# ============================================

FIRST_NAMES = [
    "James", "Mary", "John", "Patricia", "Robert", "Jennifer", "Michael", "Linda",
    "William", "Elizabeth", "David", "Barbara", "Richard", "Susan", "Joseph", "Jessica",
    "Thomas", "Sarah", "Charles", "Karen", "Christopher", "Nancy", "Daniel", "Lisa",
    "Matthew", "Betty", "Anthony", "Margaret", "Mark", "Sandra", "Donald", "Ashley",
    "Steven", "Kimberly", "Paul", "Emily", "Andrew", "Donna", "Joshua", "Michelle",
    "Kenneth", "Dorothy", "Kevin", "Carol", "Brian", "Amanda", "George", "Melissa",
    "Timothy", "Deborah", "Ronald", "Stephanie", "Edward", "Rebecca", "Jason", "Sharon"
]

LAST_NAMES = [
    "Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis",
    "Rodriguez", "Martinez", "Hernandez", "Lopez", "Gonzalez", "Wilson", "Anderson",
    "Thomas", "Taylor", "Moore", "Jackson", "Martin", "Lee", "Perez", "Thompson",
    "White", "Harris", "Sanchez", "Clark", "Ramirez", "Lewis", "Robinson", "Walker",
    "Young", "Allen", "King", "Wright", "Scott", "Torres", "Nguyen", "Hill", "Flores"
]

CITIES = [
    ("New York", "US"), ("Los Angeles", "US"), ("Chicago", "US"), ("Houston", "US"),
    ("Phoenix", "US"), ("Philadelphia", "US"), ("San Antonio", "US"), ("San Diego", "US"),
    ("Dallas", "US"), ("San Jose", "US"), ("Miami", "US"), ("Atlanta", "US"),
    ("Boston", "US"), ("Seattle", "US"), ("Denver", "US"), ("Portland", "US"),
    ("Las Vegas", "US"), ("Detroit", "US"), ("Austin", "US"), ("Newark", "US")
]

DEVICE_TYPES = ["mobile", "desktop", "tablet"]
OS_OPTIONS = ["iOS", "Android", "Windows", "macOS", "Linux"]
BROWSERS = ["Chrome", "Safari", "Firefox", "Edge", "Opera"]


def generate_uuid() -> str:
    """Generate a unique identifier"""
    return str(uuid.uuid4())


def generate_account_number() -> str:
    """Generate a realistic 12-digit account number"""
    return ''.join([str(random.randint(0, 9)) for _ in range(12)])


def generate_email(first_name: str, last_name: str) -> str:
    """Generate a realistic email address"""
    domains = ["gmail.com", "yahoo.com", "outlook.com", "hotmail.com", "email.com"]
    suffix = random.randint(1, 999) if random.random() > 0.5 else ""
    return f"{first_name.lower()}.{last_name.lower()}{suffix}@{random.choice(domains)}"


def generate_phone() -> str:
    """Generate a US phone number"""
    return f"+1-{random.randint(200, 999)}-{random.randint(200, 999)}-{random.randint(1000, 9999)}"


def generate_ip() -> str:
    """Generate a random IP address"""
    return f"{random.randint(1, 255)}.{random.randint(0, 255)}.{random.randint(0, 255)}.{random.randint(1, 254)}"


def generate_device_id() -> str:
    """Generate a device fingerprint ID"""
    return f"DEV-{uuid.uuid4().hex[:16].upper()}"


def generate_transaction_ref() -> str:
    """Generate a transaction reference number"""
    return f"TXN{datetime.now().strftime('%Y%m%d')}{random.randint(100000, 999999)}"


# ============================================
# ACCOUNT GENERATION
# ============================================

def generate_accounts(count: int = 100) -> List[Dict]:
    """
    Generate a mix of legitimate and suspicious accounts.
    
    Distribution:
    - 60% Legitimate accounts (low risk)
    - 25% Medium risk accounts (some suspicious patterns)
    - 15% High risk / Mule accounts
    """
    accounts = []
    
    for i in range(count):
        first_name = random.choice(FIRST_NAMES)
        last_name = random.choice(LAST_NAMES)
        city, country = random.choice(CITIES)
        
        # Determine account risk profile
        risk_roll = random.random()
        if risk_roll < 0.60:
            risk_category = "low"
            account_age_days = random.randint(180, 1825)  # 6 months to 5 years
            kyc_status = "verified"
        elif risk_roll < 0.85:
            risk_category = "medium"
            account_age_days = random.randint(30, 365)  # 1 month to 1 year
            kyc_status = random.choice(["verified", "pending"])
        else:
            risk_category = "high"
            account_age_days = random.randint(7, 90)  # Very new accounts (mule indicator)
            kyc_status = random.choice(["verified", "pending", "failed"])
        
        created_at = datetime.now() - timedelta(days=account_age_days)
        
        account = {
            "id": generate_uuid(),
            "account_number": generate_account_number(),
            "account_holder_name": f"{first_name} {last_name}",
            "email": generate_email(first_name, last_name),
            "phone": generate_phone(),
            "account_type": random.choice(["savings", "checking", "business"]),
            "created_at": created_at.isoformat(),
            "kyc_status": kyc_status,
            "kyc_verified_at": (created_at + timedelta(days=random.randint(1, 7))).isoformat() if kyc_status == "verified" else None,
            "is_flagged": risk_category == "high",
            "flag_reason": "Suspected mule account - under investigation" if risk_category == "high" else None,
            "risk_category": risk_category,
            "mule_probability": random.uniform(70, 95) if risk_category == "high" else (random.uniform(30, 60) if risk_category == "medium" else random.uniform(0, 20)),
            "status": "active",
            "country": country,
            "city": city
        }
        accounts.append(account)
    
    return accounts


# ============================================
# MULE NETWORK GENERATION
# ============================================

def create_mule_network_cluster(accounts: List[Dict], cluster_size: int = 8) -> Tuple[List[Dict], List[str]]:
    """
    Create a mule network cluster with specific patterns:
    - Hub account (central coordinator)
    - Spoke accounts (receive and distribute)
    - Circular flow pattern
    
    Returns transactions and list of account IDs in the network
    """
    # Select accounts for the mule network (prefer high-risk ones)
    high_risk = [a for a in accounts if a["risk_category"] == "high"]
    medium_risk = [a for a in accounts if a["risk_category"] == "medium"]
    
    network_accounts = random.sample(high_risk, min(cluster_size // 2, len(high_risk)))
    network_accounts += random.sample(medium_risk, min(cluster_size - len(network_accounts), len(medium_risk)))
    
    if len(network_accounts) < cluster_size:
        remaining = [a for a in accounts if a not in network_accounts]
        network_accounts += random.sample(remaining, cluster_size - len(network_accounts))
    
    network_ids = [a["id"] for a in network_accounts]
    hub_account = network_accounts[0]
    spoke_accounts = network_accounts[1:]
    
    transactions = []
    base_time = datetime.now() - timedelta(days=30)
    
    # Pattern 1: Hub receives from external sources (simulated)
    for i in range(5):
        txn_time = base_time + timedelta(hours=random.randint(1, 48))
        transactions.append({
            "id": generate_uuid(),
            "transaction_reference": generate_transaction_ref(),
            "sender_id": random.choice([a["id"] for a in accounts if a not in network_accounts]),
            "receiver_id": hub_account["id"],
            "amount": random.uniform(5000, 25000),
            "currency": "USD",
            "transaction_type": "transfer",
            "timestamp": txn_time.isoformat(),
            "device_id": generate_device_id(),
            "ip_address": generate_ip(),
            "geo_location": f"{hub_account['city']}, {hub_account['country']}",
            "status": "completed",
            "risk_score": random.uniform(40, 70),
            "is_suspicious": True,
            "suspicious_reason": "Large incoming transfer to hub account",
            "description": "Incoming funds"
        })
        base_time = txn_time
    
    # Pattern 2: Hub distributes to spokes (rapid dispersal)
    shared_device_id = generate_device_id()  # Shared device for mule cluster
    shared_ip = generate_ip()
    
    for spoke in spoke_accounts:
        # Hub to spoke
        txn_time = base_time + timedelta(minutes=random.randint(5, 60))
        transactions.append({
            "id": generate_uuid(),
            "transaction_reference": generate_transaction_ref(),
            "sender_id": hub_account["id"],
            "receiver_id": spoke["id"],
            "amount": random.uniform(1000, 5000),
            "currency": "USD",
            "transaction_type": "transfer",
            "timestamp": txn_time.isoformat(),
            "device_id": shared_device_id if random.random() > 0.3 else generate_device_id(),
            "ip_address": shared_ip if random.random() > 0.5 else generate_ip(),
            "geo_location": f"{spoke['city']}, {spoke['country']}",
            "status": "completed",
            "risk_score": random.uniform(50, 80),
            "is_suspicious": True,
            "suspicious_reason": "Rapid fund dispersal from hub",
            "description": "Fund distribution"
        })
        base_time = txn_time
    
    # Pattern 3: Circular flow (A→B→C→D→A)
    circular_amount = random.uniform(3000, 8000)
    for i in range(len(spoke_accounts)):
        sender = spoke_accounts[i]
        receiver = spoke_accounts[(i + 1) % len(spoke_accounts)]
        txn_time = base_time + timedelta(hours=random.randint(2, 12))
        
        transactions.append({
            "id": generate_uuid(),
            "transaction_reference": generate_transaction_ref(),
            "sender_id": sender["id"],
            "receiver_id": receiver["id"],
            "amount": circular_amount + random.uniform(-100, 100),  # Slight variation
            "currency": "USD",
            "transaction_type": "transfer",
            "timestamp": txn_time.isoformat(),
            "device_id": shared_device_id if random.random() > 0.5 else generate_device_id(),
            "ip_address": generate_ip(),
            "geo_location": f"{sender['city']}, {sender['country']}",
            "status": "completed",
            "risk_score": random.uniform(60, 90),
            "is_suspicious": True,
            "suspicious_reason": "Circular transaction pattern detected",
            "description": "Transfer to associated account"
        })
        base_time = txn_time
    
    # Pattern 4: Back to hub (closing the circle)
    transactions.append({
        "id": generate_uuid(),
        "transaction_reference": generate_transaction_ref(),
        "sender_id": spoke_accounts[-1]["id"],
        "receiver_id": hub_account["id"],
        "amount": circular_amount * 0.9,  # Slight reduction (layering)
        "currency": "USD",
        "transaction_type": "transfer",
        "timestamp": (base_time + timedelta(hours=5)).isoformat(),
        "device_id": shared_device_id,
        "ip_address": shared_ip,
        "geo_location": f"{hub_account['city']}, {hub_account['country']}",
        "status": "completed",
        "risk_score": 85,
        "is_suspicious": True,
        "suspicious_reason": "Circular flow completion - funds returning to origin",
        "description": "Return transfer"
    })
    
    return transactions, network_ids


def generate_legitimate_transactions(accounts: List[Dict], count: int = 200) -> List[Dict]:
    """
    Generate legitimate transaction patterns for non-mule accounts.
    
    Characteristics:
    - Moderate amounts
    - Regular intervals
    - Consistent beneficiaries
    - Normal working hours
    """
    low_risk_accounts = [a for a in accounts if a["risk_category"] == "low"]
    transactions = []
    
    for _ in range(count):
        sender = random.choice(low_risk_accounts)
        # Usually transact with same few beneficiaries
        receiver = random.choice(accounts)
        while receiver["id"] == sender["id"]:
            receiver = random.choice(accounts)
        
        # Transaction during business hours
        days_ago = random.randint(1, 90)
        hour = random.randint(9, 17)  # Business hours
        txn_time = datetime.now() - timedelta(days=days_ago, hours=random.randint(0, 12))
        txn_time = txn_time.replace(hour=hour)
        
        # Moderate, realistic amounts
        amount = random.choice([
            random.uniform(50, 500),      # Small daily transactions
            random.uniform(500, 2000),    # Medium transactions
            random.uniform(100, 300),     # Subscriptions/bills
        ])
        
        transactions.append({
            "id": generate_uuid(),
            "transaction_reference": generate_transaction_ref(),
            "sender_id": sender["id"],
            "receiver_id": receiver["id"],
            "amount": round(amount, 2),
            "currency": "USD",
            "transaction_type": random.choice(["transfer", "payment"]),
            "timestamp": txn_time.isoformat(),
            "device_id": generate_device_id(),
            "ip_address": generate_ip(),
            "geo_location": f"{sender['city']}, {sender['country']}",
            "status": "completed",
            "risk_score": random.uniform(0, 20),
            "is_suspicious": False,
            "suspicious_reason": None,
            "description": random.choice([
                "Monthly payment", "Bill payment", "Personal transfer",
                "Subscription", "Utility payment", "Rent payment",
                "Friend payment", "Family support", "Business expense"
            ])
        })
    
    return transactions


# ============================================
# DEVICE FINGERPRINT GENERATION
# ============================================

def generate_device_fingerprints(accounts: List[Dict], transactions: List[Dict]) -> List[Dict]:
    """
    Generate device fingerprint data with shared device scenarios.
    
    Mule Pattern:
    - Multiple accounts using same device = high mule probability
    - VPN/proxy usage from high-risk accounts
    """
    fingerprints = []
    device_to_accounts = {}  # Track device sharing
    
    # Extract unique devices from transactions
    for txn in transactions:
        device_id = txn.get("device_id")
        if not device_id:
            continue
            
        sender_id = txn["sender_id"]
        
        if device_id not in device_to_accounts:
            device_to_accounts[device_id] = set()
        device_to_accounts[device_id].add(sender_id)
    
    # Create fingerprint records
    for device_id, account_ids in device_to_accounts.items():
        for account_id in account_ids:
            account = next((a for a in accounts if a["id"] == account_id), None)
            if not account:
                continue
                
            is_shared = len(account_ids) > 1
            is_mule = account["risk_category"] == "high"
            
            fingerprint = {
                "id": generate_uuid(),
                "account_id": account_id,
                "device_id": device_id,
                "device_type": random.choice(DEVICE_TYPES),
                "os": random.choice(OS_OPTIONS),
                "browser": random.choice(BROWSERS),
                "ip_address": generate_ip(),
                "ip_country": account["country"],
                "ip_city": account["city"],
                "is_vpn": is_mule and random.random() > 0.5,
                "is_proxy": is_mule and random.random() > 0.7,
                "first_seen": (datetime.now() - timedelta(days=random.randint(1, 90))).isoformat(),
                "last_seen": datetime.now().isoformat(),
                "usage_count": random.randint(1, 50),
                "risk_score": random.uniform(60, 95) if is_shared else random.uniform(0, 30),
                "is_shared": is_shared,
                "shared_with_accounts": list(account_ids - {account_id}) if is_shared else None
            }
            fingerprints.append(fingerprint)
    
    return fingerprints


# ============================================
# ALERT GENERATION
# ============================================

def generate_alerts(accounts: List[Dict], mule_network_ids: List[str]) -> List[Dict]:
    """
    Generate risk alerts for suspicious accounts.
    
    Alert Types:
    - mule_network: Part of detected mule network
    - velocity: High transaction velocity
    - circular_flow: Circular money flow pattern
    - device_reuse: Shared device cluster
    """
    alerts = []
    
    # Alerts for mule network members
    for account_id in mule_network_ids:
        account = next((a for a in accounts if a["id"] == account_id), None)
        if not account:
            continue
        
        alert = {
            "id": generate_uuid(),
            "account_id": account_id,
            "alert_type": "mule_network",
            "severity": "high" if random.random() > 0.3 else "critical",
            "risk_score": random.uniform(75, 98),
            "confidence_score": random.uniform(80, 95),
            "mule_probability": account.get("mule_probability", random.uniform(70, 95)),
            "reasons": [
                "Connected to 4 high-risk accounts in transaction network",
                "High betweenness centrality (network connector)",
                "Involved in circular transaction pattern",
                "Shared device with confirmed mule accounts",
                "Rapid fund dispersal pattern detected"
            ][:random.randint(2, 5)],
            "status": random.choice(["open", "investigating"]),
            "resolution": None,
            "created_at": (datetime.now() - timedelta(days=random.randint(1, 7))).isoformat(),
            "updated_at": datetime.now().isoformat(),
            "resolved_at": None,
            "analyst_notes": None,
            "assigned_to": random.choice(["analyst_1", "analyst_2", None])
        }
        alerts.append(alert)
    
    # Alerts for other suspicious patterns
    medium_risk = [a for a in accounts if a["risk_category"] == "medium" and a["id"] not in mule_network_ids]
    for account in random.sample(medium_risk, min(5, len(medium_risk))):
        alert_type = random.choice(["velocity", "device_reuse", "behavior_deviation"])
        
        reasons_map = {
            "velocity": [
                "Transaction velocity 300% above baseline",
                "15 transactions in 24-hour period",
                "Unusual transaction timing (late night activity)"
            ],
            "device_reuse": [
                "Device shared with 3 other accounts",
                "VPN/proxy usage detected",
                "IP address associated with fraud reports"
            ],
            "behavior_deviation": [
                "Transaction amounts significantly higher than baseline",
                "New beneficiary pattern - 5 new recipients in 48 hours",
                "Geographic anomaly - transactions from unfamiliar location"
            ]
        }
        
        alert = {
            "id": generate_uuid(),
            "account_id": account["id"],
            "alert_type": alert_type,
            "severity": "medium",
            "risk_score": random.uniform(40, 70),
            "confidence_score": random.uniform(60, 80),
            "mule_probability": account.get("mule_probability", random.uniform(30, 60)),
            "reasons": reasons_map[alert_type],
            "status": "open",
            "resolution": None,
            "created_at": (datetime.now() - timedelta(days=random.randint(1, 14))).isoformat(),
            "updated_at": datetime.now().isoformat(),
            "resolved_at": None,
            "analyst_notes": None,
            "assigned_to": None
        }
        alerts.append(alert)
    
    return alerts


# ============================================
# MAIN DATA GENERATION
# ============================================

def generate_all_mock_data() -> Dict:
    """
    Generate complete mock dataset for MuleShield AI.
    
    Returns a dictionary containing:
    - accounts: 100 accounts with risk distribution
    - transactions: Mix of legitimate and suspicious
    - device_fingerprints: Device intelligence data
    - alerts: Risk alerts for investigation
    - mule_network_ids: IDs of accounts in mule network
    """
    print("🔄 Generating mock accounts...")
    accounts = generate_accounts(100)
    
    print("🔄 Creating mule network cluster...")
    mule_transactions, mule_network_ids = create_mule_network_cluster(accounts, cluster_size=8)
    
    # Add second smaller mule network
    mule_transactions_2, mule_network_ids_2 = create_mule_network_cluster(
        [a for a in accounts if a["id"] not in mule_network_ids], 
        cluster_size=5
    )
    mule_transactions.extend(mule_transactions_2)
    mule_network_ids.extend(mule_network_ids_2)
    
    print("🔄 Generating legitimate transactions...")
    legitimate_transactions = generate_legitimate_transactions(accounts, count=200)
    
    all_transactions = mule_transactions + legitimate_transactions
    random.shuffle(all_transactions)
    
    print("🔄 Generating device fingerprints...")
    device_fingerprints = generate_device_fingerprints(accounts, all_transactions)
    
    print("🔄 Generating alerts...")
    alerts = generate_alerts(accounts, mule_network_ids)
    
    print(f"✅ Generated {len(accounts)} accounts")
    print(f"✅ Generated {len(all_transactions)} transactions")
    print(f"✅ Generated {len(device_fingerprints)} device fingerprints")
    print(f"✅ Generated {len(alerts)} alerts")
    print(f"✅ Mule network contains {len(mule_network_ids)} accounts")
    
    return {
        "accounts": accounts,
        "transactions": all_transactions,
        "device_fingerprints": device_fingerprints,
        "alerts": alerts,
        "mule_network_ids": mule_network_ids
    }


def save_mock_data_to_json(output_path: str = "mock_data.json"):
    """Save generated mock data to JSON file"""
    data = generate_all_mock_data()
    with open(output_path, 'w') as f:
        json.dump(data, f, indent=2, default=str)
    print(f"✅ Mock data saved to {output_path}")
    return data


if __name__ == "__main__":
    save_mock_data_to_json()
