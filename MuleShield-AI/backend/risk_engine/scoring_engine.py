"""
MuleShield AI - Dynamic Risk Scoring Engine
Composite risk scoring for mule account detection

This engine calculates multi-factor risk scores using:
1. Transaction velocity score
2. Beneficiary diversity score
3. Account age vs transaction size
4. Device reuse score
5. Graph centrality score
6. Behavior deviation score

Output:
- Composite Risk Score (0-100)
- Mule Probability (%)
- Risk Category (Low/Medium/High)
- Confidence Score
- Explainable AI reasons
"""

from typing import List, Dict, Optional, Tuple
from datetime import datetime, timedelta
from collections import defaultdict
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler
import pickle
import os


class RiskScoringEngine:
    """
    Dynamic risk scoring engine for mule account detection.
    
    Uses weighted component scores combined with ML model
    for comprehensive risk assessment.
    """
    
    # Component weights (can be adjusted via adaptive learning)
    DEFAULT_WEIGHTS = {
        "transaction_velocity": 0.18,
        "beneficiary_diversity": 0.15,
        "account_age": 0.12,
        "device_reuse": 0.20,
        "graph_centrality": 0.20,
        "behavior_deviation": 0.15
    }
    
    # Thresholds for risk categorization
    RISK_THRESHOLDS = {
        "high": 70,
        "medium": 40,
        "low": 0
    }
    
    def __init__(self, weights: Dict[str, float] = None):
        """
        Initialize risk scoring engine.
        
        Args:
            weights: Optional custom weights for component scores
        """
        self.weights = weights or self.DEFAULT_WEIGHTS.copy()
        self.ml_model: Optional[RandomForestClassifier] = None
        self.scaler = StandardScaler()
        self._weight_history: List[Dict] = []
    
    # ============================================
    # COMPONENT SCORE CALCULATIONS
    # ============================================
    
    def calculate_transaction_velocity_score(
        self, 
        account_id: str,
        transactions: List[Dict],
        time_window_days: int = 7
    ) -> Dict:
        """
        Calculate transaction velocity score.
        
        Mule Indicator:
        - High number of transactions in short time
        - Unusual transaction timing (late night, weekends)
        - Sudden spike in activity
        
        Score: 0-100 (higher = more suspicious)
        """
        cutoff = datetime.now() - timedelta(days=time_window_days)
        
        # Filter account transactions
        account_txns = [
            t for t in transactions
            if (t.get("sender_id") == account_id or t.get("receiver_id") == account_id)
            and datetime.fromisoformat(t.get("timestamp", datetime.now().isoformat()).replace("Z", "")) > cutoff
        ]
        
        if not account_txns:
            return {
                "score": 0,
                "transaction_count": 0,
                "daily_average": 0,
                "risk_factors": [],
                "explanation": "No recent transactions"
            }
        
        # Calculate metrics
        txn_count = len(account_txns)
        daily_average = txn_count / time_window_days
        
        # Analyze timing patterns
        late_night_count = 0
        weekend_count = 0
        
        for txn in account_txns:
            try:
                ts = datetime.fromisoformat(txn.get("timestamp", "").replace("Z", ""))
                if ts.hour >= 23 or ts.hour <= 5:
                    late_night_count += 1
                if ts.weekday() >= 5:
                    weekend_count += 1
            except (ValueError, TypeError):
                pass
        
        # Calculate score components
        velocity_score = min(daily_average * 10, 50)  # Cap at 50
        timing_score = (late_night_count / txn_count * 25 + weekend_count / txn_count * 25) if txn_count > 0 else 0
        
        total_score = min(velocity_score + timing_score, 100)
        
        risk_factors = []
        if daily_average > 5:
            risk_factors.append(f"High transaction velocity: {daily_average:.1f} transactions/day")
        if late_night_count > txn_count * 0.3:
            risk_factors.append(f"Unusual timing: {late_night_count} late night transactions")
        if weekend_count > txn_count * 0.5:
            risk_factors.append(f"High weekend activity: {weekend_count} weekend transactions")
        
        return {
            "score": round(total_score, 2),
            "transaction_count": txn_count,
            "daily_average": round(daily_average, 2),
            "late_night_count": late_night_count,
            "weekend_count": weekend_count,
            "risk_factors": risk_factors,
            "explanation": f"Transaction velocity score based on {txn_count} transactions in {time_window_days} days"
        }
    
    def calculate_beneficiary_diversity_score(
        self,
        account_id: str,
        transactions: List[Dict],
        time_window_days: int = 30
    ) -> Dict:
        """
        Calculate beneficiary diversity score.
        
        Mule Indicator:
        - Many unique beneficiaries in short time
        - Low recurring beneficiary ratio
        - New beneficiaries appearing frequently
        
        Score: 0-100 (higher = more suspicious)
        """
        cutoff = datetime.now() - timedelta(days=time_window_days)
        
        # Filter outgoing transactions
        outgoing = [
            t for t in transactions
            if t.get("sender_id") == account_id
            and datetime.fromisoformat(t.get("timestamp", datetime.now().isoformat()).replace("Z", "")) > cutoff
        ]
        
        if not outgoing:
            return {
                "score": 0,
                "unique_beneficiaries": 0,
                "recurring_ratio": 0,
                "risk_factors": [],
                "explanation": "No outgoing transactions"
            }
        
        # Count beneficiaries
        beneficiary_counts = defaultdict(int)
        for txn in outgoing:
            beneficiary_counts[txn.get("receiver_id")] += 1
        
        unique_beneficiaries = len(beneficiary_counts)
        recurring = sum(1 for count in beneficiary_counts.values() if count > 1)
        recurring_ratio = recurring / unique_beneficiaries if unique_beneficiaries > 0 else 0
        
        # Calculate score
        # High unique beneficiaries + low recurring = suspicious
        diversity_score = min(unique_beneficiaries * 5, 60)  # Cap at 60
        recurring_penalty = (1 - recurring_ratio) * 40  # Up to 40 points for low recurring
        
        total_score = min(diversity_score + recurring_penalty, 100)
        
        risk_factors = []
        if unique_beneficiaries > 10:
            risk_factors.append(f"High beneficiary diversity: {unique_beneficiaries} unique recipients")
        if recurring_ratio < 0.2:
            risk_factors.append(f"Low recurring beneficiary ratio: {recurring_ratio:.1%}")
        
        return {
            "score": round(total_score, 2),
            "unique_beneficiaries": unique_beneficiaries,
            "recurring_ratio": round(recurring_ratio, 2),
            "total_outgoing": len(outgoing),
            "risk_factors": risk_factors,
            "explanation": f"Beneficiary diversity based on {unique_beneficiaries} unique recipients"
        }
    
    def calculate_account_age_score(
        self,
        account: Dict,
        transactions: List[Dict]
    ) -> Dict:
        """
        Calculate account age vs transaction activity score.
        
        Mule Indicator:
        - New account with high transaction volume
        - Transaction amounts disproportionate to account age
        - Rapid activity buildup after dormancy
        
        Score: 0-100 (higher = more suspicious)
        """
        created_at = datetime.fromisoformat(account.get("created_at", datetime.now().isoformat()).replace("Z", ""))
        account_age_days = (datetime.now() - created_at).days
        
        # Get account transactions
        account_id = account.get("id")
        account_txns = [
            t for t in transactions
            if t.get("sender_id") == account_id or t.get("receiver_id") == account_id
        ]
        
        if not account_txns:
            return {
                "score": 0 if account_age_days > 90 else 20,
                "account_age_days": account_age_days,
                "transaction_count": 0,
                "risk_factors": [],
                "explanation": "No transaction history"
            }
        
        txn_count = len(account_txns)
        total_volume = sum(t.get("amount", 0) for t in account_txns)
        
        # Calculate expected activity based on age
        # New accounts should have lower activity
        if account_age_days <= 30:
            expected_txns = 10
            expected_volume = 5000
        elif account_age_days <= 90:
            expected_txns = 30
            expected_volume = 15000
        else:
            expected_txns = 100
            expected_volume = 50000
        
        txn_ratio = txn_count / expected_txns
        volume_ratio = total_volume / expected_volume
        
        # Score based on deviation from expected
        age_score = 0
        if account_age_days <= 30 and (txn_ratio > 2 or volume_ratio > 2):
            age_score = min((txn_ratio + volume_ratio) * 25, 100)
        elif account_age_days <= 90 and (txn_ratio > 1.5 or volume_ratio > 1.5):
            age_score = min((txn_ratio + volume_ratio) * 20, 80)
        elif txn_ratio > 1 or volume_ratio > 1:
            age_score = min((txn_ratio + volume_ratio) * 10, 50)
        
        risk_factors = []
        if account_age_days <= 30 and txn_count > 10:
            risk_factors.append(f"New account ({account_age_days} days) with {txn_count} transactions")
        if account_age_days <= 30 and total_volume > 10000:
            risk_factors.append(f"High volume (${total_volume:,.2f}) for new account")
        
        return {
            "score": round(age_score, 2),
            "account_age_days": account_age_days,
            "transaction_count": txn_count,
            "total_volume": round(total_volume, 2),
            "txn_ratio": round(txn_ratio, 2),
            "volume_ratio": round(volume_ratio, 2),
            "risk_factors": risk_factors,
            "explanation": f"Account age score based on {account_age_days} day old account with ${total_volume:,.2f} volume"
        }
    
    def calculate_device_reuse_score(
        self,
        account_id: str,
        device_fingerprints: List[Dict]
    ) -> Dict:
        """
        Calculate device reuse risk score.
        
        Mule Indicator:
        - Shared device with other accounts
        - VPN/proxy usage
        - Multiple IPs from different regions
        
        Score: 0-100 (higher = more suspicious)
        """
        # Get account's device fingerprints
        account_devices = [
            d for d in device_fingerprints
            if d.get("account_id") == account_id
        ]
        
        if not account_devices:
            return {
                "score": 0,
                "device_count": 0,
                "shared_devices": 0,
                "vpn_usage": False,
                "risk_factors": [],
                "explanation": "No device fingerprint data"
            }
        
        # Analyze device patterns
        shared_count = 0
        vpn_count = 0
        unique_ips = set()
        shared_accounts = set()
        
        for device in account_devices:
            if device.get("is_shared"):
                shared_count += 1
                shared_with = device.get("shared_with_accounts", [])
                shared_accounts.update(shared_with if shared_with else [])
            if device.get("is_vpn") or device.get("is_proxy"):
                vpn_count += 1
            unique_ips.add(device.get("ip_address"))
        
        # Calculate score
        device_count = len(account_devices)
        shared_score = min(shared_count * 30, 60)  # Up to 60 for shared devices
        vpn_score = min(vpn_count * 20, 30)  # Up to 30 for VPN usage
        ip_diversity_score = min((len(unique_ips) - 1) * 5, 10)  # Slight penalty for many IPs
        
        total_score = min(shared_score + vpn_score + ip_diversity_score, 100)
        
        risk_factors = []
        if shared_count > 0:
            risk_factors.append(f"Shared device with {len(shared_accounts)} other account(s)")
        if vpn_count > 0:
            risk_factors.append(f"VPN/Proxy usage detected on {vpn_count} device(s)")
        
        return {
            "score": round(total_score, 2),
            "device_count": device_count,
            "shared_devices": shared_count,
            "shared_with_count": len(shared_accounts),
            "vpn_usage": vpn_count > 0,
            "unique_ips": len(unique_ips),
            "risk_factors": risk_factors,
            "explanation": f"Device reuse score based on {device_count} device(s), {shared_count} shared"
        }
    
    def calculate_graph_centrality_score(
        self,
        account_id: str,
        centrality_data: Dict
    ) -> Dict:
        """
        Calculate graph centrality risk score.
        
        Mule Indicator:
        - High betweenness centrality (network bridge)
        - High degree centrality (many connections)
        - High PageRank (important in flow network)
        
        Score: 0-100 (higher = more suspicious)
        """
        if not centrality_data:
            return {
                "score": 0,
                "betweenness": 0,
                "degree": 0,
                "pagerank": 0,
                "risk_factors": [],
                "explanation": "No network data available"
            }
        
        betweenness = centrality_data.get("betweenness", 0)
        degree = centrality_data.get("degree", 0)
        pagerank = centrality_data.get("pagerank", 0)
        
        # Normalize and score
        # Betweenness: values > 0.1 are significant
        betweenness_score = min(betweenness * 300, 40)
        
        # Degree: values > 0.2 are significant
        degree_score = min(degree * 150, 35)
        
        # PageRank: values > 0.05 are significant
        pagerank_score = min(pagerank * 500, 25)
        
        total_score = min(betweenness_score + degree_score + pagerank_score, 100)
        
        risk_factors = []
        if betweenness > 0.05:
            risk_factors.append(f"High betweenness centrality ({betweenness:.3f}) - network bridge")
        if degree > 0.1:
            risk_factors.append(f"High degree centrality ({degree:.3f}) - many connections")
        if pagerank > 0.02:
            risk_factors.append(f"High PageRank ({pagerank:.3f}) - important in fund flows")
        
        return {
            "score": round(total_score, 2),
            "betweenness": round(betweenness, 4),
            "degree": round(degree, 4),
            "pagerank": round(pagerank, 4),
            "risk_factors": risk_factors,
            "explanation": f"Graph centrality score based on network position analysis"
        }
    
    def calculate_behavior_deviation_score(
        self,
        account_id: str,
        transactions: List[Dict],
        behavioral_profile: Optional[Dict] = None
    ) -> Dict:
        """
        Calculate behavior deviation score.
        
        Compares recent activity against baseline profile.
        
        Mule Indicator:
        - Sudden change in transaction patterns
        - Deviation from typical amounts
        - Change in beneficiary patterns
        
        Score: 0-100 (higher = more suspicious)
        """
        # Get recent transactions
        recent_cutoff = datetime.now() - timedelta(days=7)
        recent_txns = [
            t for t in transactions
            if (t.get("sender_id") == account_id or t.get("receiver_id") == account_id)
            and datetime.fromisoformat(t.get("timestamp", datetime.now().isoformat()).replace("Z", "")) > recent_cutoff
        ]
        
        if not recent_txns:
            return {
                "score": 0,
                "deviation_factors": [],
                "risk_factors": [],
                "explanation": "Insufficient recent activity for comparison"
            }
        
        # If no profile, create baseline from older transactions
        if not behavioral_profile:
            historical_cutoff = datetime.now() - timedelta(days=90)
            historical_txns = [
                t for t in transactions
                if (t.get("sender_id") == account_id or t.get("receiver_id") == account_id)
                and datetime.fromisoformat(t.get("timestamp", datetime.now().isoformat()).replace("Z", "")) < recent_cutoff
                and datetime.fromisoformat(t.get("timestamp", datetime.now().isoformat()).replace("Z", "")) > historical_cutoff
            ]
            
            if len(historical_txns) < 5:
                return {
                    "score": 30,  # Moderate risk for new accounts
                    "deviation_factors": ["Insufficient history for baseline"],
                    "risk_factors": ["New account with limited transaction history"],
                    "explanation": "Limited historical data for comparison"
                }
            
            # Build simple baseline
            historical_amounts = [t.get("amount", 0) for t in historical_txns]
            behavioral_profile = {
                "avg_transaction_amount": np.mean(historical_amounts),
                "max_transaction_amount": np.max(historical_amounts),
                "avg_daily_transactions": len(historical_txns) / 83  # 90-7 days
            }
        
        # Calculate deviations
        recent_amounts = [t.get("amount", 0) for t in recent_txns]
        recent_avg = np.mean(recent_amounts) if recent_amounts else 0
        recent_max = np.max(recent_amounts) if recent_amounts else 0
        recent_daily = len(recent_txns) / 7
        
        baseline_avg = behavioral_profile.get("avg_transaction_amount", recent_avg)
        baseline_max = behavioral_profile.get("max_transaction_amount", recent_max)
        baseline_daily = behavioral_profile.get("avg_daily_transactions", recent_daily)
        
        # Calculate deviation scores
        amount_deviation = abs(recent_avg - baseline_avg) / baseline_avg if baseline_avg > 0 else 0
        max_deviation = abs(recent_max - baseline_max) / baseline_max if baseline_max > 0 else 0
        velocity_deviation = abs(recent_daily - baseline_daily) / baseline_daily if baseline_daily > 0 else 0
        
        amount_score = min(amount_deviation * 40, 40)
        max_score = min(max_deviation * 30, 30)
        velocity_score = min(velocity_deviation * 30, 30)
        
        total_score = min(amount_score + max_score + velocity_score, 100)
        
        deviation_factors = []
        risk_factors = []
        
        if amount_deviation > 0.5:
            deviation_factors.append(f"Amount: {amount_deviation:.1%} above baseline")
            risk_factors.append(f"Transaction amounts {amount_deviation:.0%} higher than typical")
        if max_deviation > 0.5:
            deviation_factors.append(f"Max amount: {max_deviation:.1%} above baseline")
        if velocity_deviation > 0.5:
            deviation_factors.append(f"Velocity: {velocity_deviation:.1%} above baseline")
            risk_factors.append(f"Transaction frequency {velocity_deviation:.0%} higher than typical")
        
        return {
            "score": round(total_score, 2),
            "recent_avg_amount": round(recent_avg, 2),
            "baseline_avg_amount": round(baseline_avg, 2),
            "amount_deviation": round(amount_deviation, 2),
            "velocity_deviation": round(velocity_deviation, 2),
            "deviation_factors": deviation_factors,
            "risk_factors": risk_factors,
            "explanation": f"Behavior deviation based on comparison to baseline profile"
        }
    
    # ============================================
    # COMPOSITE SCORE CALCULATION
    # ============================================
    
    def calculate_composite_score(
        self,
        account: Dict,
        transactions: List[Dict],
        device_fingerprints: List[Dict],
        centrality_data: Dict,
        behavioral_profile: Optional[Dict] = None
    ) -> Dict:
        """
        Calculate composite risk score from all components.
        
        Returns comprehensive risk assessment with:
        - Composite score (0-100)
        - Risk category (low/medium/high)
        - Mule probability estimate
        - All component scores
        - Explainable AI reasons
        """
        account_id = account.get("id")
        
        # Calculate all component scores
        velocity = self.calculate_transaction_velocity_score(account_id, transactions)
        beneficiary = self.calculate_beneficiary_diversity_score(account_id, transactions)
        age = self.calculate_account_age_score(account, transactions)
        device = self.calculate_device_reuse_score(account_id, device_fingerprints)
        graph = self.calculate_graph_centrality_score(account_id, centrality_data)
        behavior = self.calculate_behavior_deviation_score(account_id, transactions, behavioral_profile)
        
        # Calculate weighted composite
        composite_score = (
            velocity["score"] * self.weights["transaction_velocity"] +
            beneficiary["score"] * self.weights["beneficiary_diversity"] +
            age["score"] * self.weights["account_age"] +
            device["score"] * self.weights["device_reuse"] +
            graph["score"] * self.weights["graph_centrality"] +
            behavior["score"] * self.weights["behavior_deviation"]
        )
        
        # Determine risk category
        if composite_score >= self.RISK_THRESHOLDS["high"]:
            risk_category = "high"
        elif composite_score >= self.RISK_THRESHOLDS["medium"]:
            risk_category = "medium"
        else:
            risk_category = "low"
        
        # Estimate mule probability (simplified ML-like calculation)
        mule_probability = self._estimate_mule_probability(
            velocity["score"], beneficiary["score"], age["score"],
            device["score"], graph["score"], behavior["score"]
        )
        
        # Calculate confidence based on data availability
        confidence_score = self._calculate_confidence(
            len(transactions), len(device_fingerprints), bool(centrality_data)
        )
        
        # Collect all risk factors for explainability
        all_risk_factors = (
            velocity["risk_factors"] +
            beneficiary["risk_factors"] +
            age["risk_factors"] +
            device["risk_factors"] +
            graph["risk_factors"] +
            behavior["risk_factors"]
        )
        
        # Sort by importance (based on component scores)
        component_scores = [
            (velocity["score"], velocity["risk_factors"]),
            (beneficiary["score"], beneficiary["risk_factors"]),
            (age["score"], age["risk_factors"]),
            (device["score"], device["risk_factors"]),
            (graph["score"], graph["risk_factors"]),
            (behavior["score"], behavior["risk_factors"])
        ]
        component_scores.sort(key=lambda x: x[0], reverse=True)
        
        top_risk_factors = []
        for score, factors in component_scores[:3]:
            if score > 30:  # Only include significant factors
                top_risk_factors.extend(factors[:2])  # Top 2 from each
        
        return {
            "account_id": account_id,
            "composite_score": round(composite_score, 2),
            "risk_category": risk_category,
            "mule_probability": round(mule_probability, 2),
            "confidence_score": round(confidence_score, 2),
            "component_scores": {
                "transaction_velocity": velocity,
                "beneficiary_diversity": beneficiary,
                "account_age": age,
                "device_reuse": device,
                "graph_centrality": graph,
                "behavior_deviation": behavior
            },
            "weights_used": self.weights,
            "top_risk_factors": top_risk_factors[:5],
            "all_risk_factors": all_risk_factors,
            "calculated_at": datetime.now().isoformat()
        }
    
    def _estimate_mule_probability(
        self,
        velocity: float,
        beneficiary: float,
        age: float,
        device: float,
        graph: float,
        behavior: float
    ) -> float:
        """
        Estimate mule probability based on component scores.
        
        Uses sigmoid-like function for probability estimation.
        """
        # Weighted average with emphasis on most indicative factors
        weighted_avg = (
            velocity * 0.15 +
            beneficiary * 0.15 +
            age * 0.10 +
            device * 0.25 +  # Device sharing is strong indicator
            graph * 0.25 +   # Network position is strong indicator
            behavior * 0.10
        )
        
        # Apply sigmoid transformation for probability
        # Scores 0-30 → 0-20% probability
        # Scores 30-60 → 20-60% probability
        # Scores 60-100 → 60-95% probability
        if weighted_avg < 30:
            probability = weighted_avg * 0.67  # 0-20%
        elif weighted_avg < 60:
            probability = 20 + (weighted_avg - 30) * 1.33  # 20-60%
        else:
            probability = 60 + (weighted_avg - 60) * 0.875  # 60-95%
        
        return min(probability, 95)  # Cap at 95%
    
    def _calculate_confidence(
        self,
        transaction_count: int,
        device_count: int,
        has_network_data: bool
    ) -> float:
        """Calculate confidence in risk assessment."""
        confidence = 50  # Base confidence
        
        if transaction_count >= 20:
            confidence += 20
        elif transaction_count >= 10:
            confidence += 10
        
        if device_count >= 3:
            confidence += 15
        elif device_count >= 1:
            confidence += 10
        
        if has_network_data:
            confidence += 15
        
        return min(confidence, 95)
    
    # ============================================
    # ADAPTIVE LEARNING
    # ============================================
    
    def update_weights(
        self,
        feedback_type: str,  # "true_mule" or "false_positive"
        component_scores: Dict[str, float]
    ):
        """
        Update weights based on investigator feedback.
        
        Adaptive Learning:
        - True Mule: Increase weights of high-scoring components
        - False Positive: Decrease weights of high-scoring components
        
        This simulates online learning from investigator decisions.
        """
        adjustment_rate = 0.05
        
        if feedback_type == "true_mule":
            # Increase weights for components that scored high
            multiplier = 1 + adjustment_rate
        else:  # false_positive
            # Decrease weights for components that scored high
            multiplier = 1 - adjustment_rate
        
        # Find top scoring components
        sorted_components = sorted(
            component_scores.items(),
            key=lambda x: x[1],
            reverse=True
        )
        
        # Adjust top 3 component weights
        for component_name, score in sorted_components[:3]:
            if score > 50:  # Only adjust if score was significant
                current_weight = self.weights.get(component_name, 0.15)
                new_weight = current_weight * multiplier
                
                # Keep weights bounded
                new_weight = max(0.05, min(0.35, new_weight))
                self.weights[component_name] = new_weight
        
        # Normalize weights to sum to 1
        total = sum(self.weights.values())
        self.weights = {k: v / total for k, v in self.weights.items()}
        
        # Record adjustment
        self._weight_history.append({
            "timestamp": datetime.now().isoformat(),
            "feedback_type": feedback_type,
            "new_weights": self.weights.copy()
        })
        
        return self.weights
    
    def get_weight_history(self) -> List[Dict]:
        """Get history of weight adjustments."""
        return self._weight_history
    
    # ============================================
    # ML MODEL (OPTIONAL)
    # ============================================
    
    def train_ml_model(self, training_data: List[Dict]):
        """
        Train ML model on labeled data.
        
        Training data format:
        [{features: {score1: x, score2: y, ...}, label: 0|1}, ...]
        """
        if len(training_data) < 10:
            print("Insufficient training data")
            return
        
        X = []
        y = []
        
        for sample in training_data:
            features = sample.get("features", {})
            label = sample.get("label", 0)
            
            feature_vector = [
                features.get("transaction_velocity", 0),
                features.get("beneficiary_diversity", 0),
                features.get("account_age", 0),
                features.get("device_reuse", 0),
                features.get("graph_centrality", 0),
                features.get("behavior_deviation", 0)
            ]
            X.append(feature_vector)
            y.append(label)
        
        X = np.array(X)
        y = np.array(y)
        
        # Fit scaler
        X_scaled = self.scaler.fit_transform(X)
        
        # Train model
        self.ml_model = RandomForestClassifier(
            n_estimators=100,
            max_depth=5,
            random_state=42
        )
        self.ml_model.fit(X_scaled, y)
        
        print(f"✅ ML model trained on {len(training_data)} samples")
    
    def predict_with_ml(self, component_scores: Dict) -> Dict:
        """
        Get ML model prediction for account.
        """
        if self.ml_model is None:
            return {"error": "ML model not trained"}
        
        feature_vector = np.array([[
            component_scores.get("transaction_velocity", {}).get("score", 0),
            component_scores.get("beneficiary_diversity", {}).get("score", 0),
            component_scores.get("account_age", {}).get("score", 0),
            component_scores.get("device_reuse", {}).get("score", 0),
            component_scores.get("graph_centrality", {}).get("score", 0),
            component_scores.get("behavior_deviation", {}).get("score", 0)
        ]])
        
        X_scaled = self.scaler.transform(feature_vector)
        
        prediction = self.ml_model.predict(X_scaled)[0]
        probability = self.ml_model.predict_proba(X_scaled)[0]
        
        return {
            "prediction": "mule" if prediction == 1 else "legitimate",
            "mule_probability_ml": round(probability[1] * 100, 2),
            "confidence": round(max(probability) * 100, 2)
        }


# ============================================
# FACTORY FUNCTION
# ============================================

def create_risk_engine(custom_weights: Dict = None) -> RiskScoringEngine:
    """Create and initialize risk scoring engine."""
    return RiskScoringEngine(weights=custom_weights)
