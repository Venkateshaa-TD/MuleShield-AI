"""
MuleShield AI - Behavioral Profiling Service
Builds and maintains account behavioral baselines for anomaly detection

This module:
1. Creates behavioral profiles from historical transactions
2. Detects deviations from baseline patterns
3. Tracks profile evolution over time
4. Generates anomaly alerts

Key Behavioral Metrics:
- Transaction frequency patterns
- Amount distributions
- Time-of-day usage
- Geographic patterns
- Beneficiary patterns
"""

from typing import List, Dict, Optional, Tuple
from datetime import datetime, timedelta
from collections import defaultdict
import numpy as np


class BehavioralProfiler:
    """
    Builds and analyzes behavioral profiles for accounts.
    
    Uses statistical methods to establish baselines and
    detect anomalous behavior indicative of mule activity.
    """
    
    def __init__(self, lookback_days: int = 90):
        """
        Initialize profiler.
        
        Args:
            lookback_days: Days of history to use for baseline
        """
        self.lookback_days = lookback_days
        self.profiles: Dict[str, Dict] = {}
    
    def build_profile(
        self,
        account_id: str,
        transactions: List[Dict]
    ) -> Dict:
        """
        Build comprehensive behavioral profile for an account.
        
        Analyzes historical transactions to establish:
        - Transaction frequency baseline
        - Amount pattern baseline
        - Time-of-day patterns
        - Geographic patterns
        - Beneficiary patterns
        """
        cutoff = datetime.now() - timedelta(days=self.lookback_days)
        
        # Filter account transactions
        account_txns = [
            t for t in transactions
            if (t.get("sender_id") == account_id or t.get("receiver_id") == account_id)
        ]
        
        # Parse and filter by date
        parsed_txns = []
        for txn in account_txns:
            try:
                ts = datetime.fromisoformat(txn.get("timestamp", "").replace("Z", ""))
                if ts > cutoff:
                    parsed_txns.append({**txn, "parsed_timestamp": ts})
            except (ValueError, TypeError):
                continue
        
        if len(parsed_txns) < 3:
            return self._create_empty_profile(account_id)
        
        # Calculate frequency metrics
        frequency_profile = self._calculate_frequency_profile(parsed_txns)
        
        # Calculate amount metrics
        amount_profile = self._calculate_amount_profile(parsed_txns)
        
        # Calculate time-of-day patterns
        time_profile = self._calculate_time_profile(parsed_txns)
        
        # Calculate geographic patterns
        geo_profile = self._calculate_geo_profile(parsed_txns)
        
        # Calculate beneficiary patterns
        beneficiary_profile = self._calculate_beneficiary_profile(account_id, parsed_txns)
        
        profile = {
            "account_id": account_id,
            "samples_count": len(parsed_txns),
            "lookback_days": self.lookback_days,
            "created_at": datetime.now().isoformat(),
            "profile_version": "v1.0",
            "frequency": frequency_profile,
            "amounts": amount_profile,
            "time_patterns": time_profile,
            "geo_patterns": geo_profile,
            "beneficiaries": beneficiary_profile
        }
        
        # Cache profile
        self.profiles[account_id] = profile
        
        return profile
    
    def _create_empty_profile(self, account_id: str) -> Dict:
        """Create empty profile for accounts with insufficient history."""
        return {
            "account_id": account_id,
            "samples_count": 0,
            "lookback_days": self.lookback_days,
            "created_at": datetime.now().isoformat(),
            "profile_version": "v1.0",
            "frequency": {
                "avg_daily_transactions": 0,
                "avg_weekly_transactions": 0,
                "avg_monthly_transactions": 0,
                "max_daily_transactions": 0
            },
            "amounts": {
                "mean": 0,
                "median": 0,
                "std": 0,
                "min": 0,
                "max": 0,
                "percentile_25": 0,
                "percentile_75": 0,
                "percentile_95": 0
            },
            "time_patterns": {
                "typical_hours": [],
                "peak_hour": None,
                "weekend_ratio": 0,
                "business_hours_ratio": 0
            },
            "geo_patterns": {
                "typical_locations": [],
                "unique_locations": 0,
                "primary_location": None
            },
            "beneficiaries": {
                "unique_count": 0,
                "recurring_count": 0,
                "recurring_ratio": 0,
                "top_beneficiaries": []
            },
            "is_empty": True
        }
    
    def _calculate_frequency_profile(self, transactions: List[Dict]) -> Dict:
        """Calculate transaction frequency metrics."""
        # Group by date
        daily_counts = defaultdict(int)
        for txn in transactions:
            date_key = txn["parsed_timestamp"].date()
            daily_counts[date_key] += 1
        
        counts = list(daily_counts.values()) if daily_counts else [0]
        
        return {
            "avg_daily_transactions": round(np.mean(counts), 2),
            "avg_weekly_transactions": round(np.mean(counts) * 7, 2),
            "avg_monthly_transactions": round(np.mean(counts) * 30, 2),
            "max_daily_transactions": max(counts),
            "std_daily_transactions": round(np.std(counts), 2),
            "total_active_days": len(daily_counts)
        }
    
    def _calculate_amount_profile(self, transactions: List[Dict]) -> Dict:
        """Calculate transaction amount statistics."""
        amounts = [t.get("amount", 0) for t in transactions]
        
        if not amounts:
            return {
                "mean": 0, "median": 0, "std": 0,
                "min": 0, "max": 0,
                "percentile_25": 0, "percentile_75": 0, "percentile_95": 0
            }
        
        return {
            "mean": round(np.mean(amounts), 2),
            "median": round(np.median(amounts), 2),
            "std": round(np.std(amounts), 2),
            "min": round(min(amounts), 2),
            "max": round(max(amounts), 2),
            "percentile_25": round(np.percentile(amounts, 25), 2),
            "percentile_75": round(np.percentile(amounts, 75), 2),
            "percentile_95": round(np.percentile(amounts, 95), 2),
            "total_volume": round(sum(amounts), 2)
        }
    
    def _calculate_time_profile(self, transactions: List[Dict]) -> Dict:
        """Calculate time-of-day patterns."""
        hour_counts = defaultdict(int)
        weekend_count = 0
        business_hours_count = 0
        
        for txn in transactions:
            ts = txn["parsed_timestamp"]
            hour_counts[ts.hour] += 1
            
            if ts.weekday() >= 5:
                weekend_count += 1
            
            if 9 <= ts.hour <= 17 and ts.weekday() < 5:
                business_hours_count += 1
        
        total = len(transactions)
        
        # Find typical hours (above average activity)
        avg_count = total / 24 if total > 0 else 0
        typical_hours = [h for h, c in hour_counts.items() if c > avg_count]
        peak_hour = max(hour_counts, key=hour_counts.get) if hour_counts else None
        
        return {
            "typical_hours": sorted(typical_hours),
            "peak_hour": peak_hour,
            "hour_distribution": dict(hour_counts),
            "weekend_ratio": round(weekend_count / total, 2) if total > 0 else 0,
            "business_hours_ratio": round(business_hours_count / total, 2) if total > 0 else 0,
            "late_night_ratio": round(
                sum(hour_counts.get(h, 0) for h in [23, 0, 1, 2, 3, 4, 5]) / total, 2
            ) if total > 0 else 0
        }
    
    def _calculate_geo_profile(self, transactions: List[Dict]) -> Dict:
        """Calculate geographic pattern metrics."""
        locations = defaultdict(int)
        
        for txn in transactions:
            geo = txn.get("geo_location")
            if geo:
                locations[geo] += 1
        
        if not locations:
            return {
                "typical_locations": [],
                "unique_locations": 0,
                "primary_location": None,
                "location_diversity_score": 0
            }
        
        total = sum(locations.values())
        sorted_locations = sorted(locations.items(), key=lambda x: x[1], reverse=True)
        primary_location = sorted_locations[0][0]
        primary_ratio = sorted_locations[0][1] / total
        
        return {
            "typical_locations": [loc for loc, count in sorted_locations[:5]],
            "unique_locations": len(locations),
            "primary_location": primary_location,
            "primary_location_ratio": round(primary_ratio, 2),
            "location_diversity_score": round((1 - primary_ratio) * 100, 2)
        }
    
    def _calculate_beneficiary_profile(
        self,
        account_id: str,
        transactions: List[Dict]
    ) -> Dict:
        """Calculate beneficiary pattern metrics."""
        beneficiary_counts = defaultdict(int)
        
        for txn in transactions:
            if txn.get("sender_id") == account_id:
                receiver = txn.get("receiver_id")
                if receiver:
                    beneficiary_counts[receiver] += 1
        
        if not beneficiary_counts:
            return {
                "unique_count": 0,
                "recurring_count": 0,
                "recurring_ratio": 0,
                "top_beneficiaries": []
            }
        
        unique_count = len(beneficiary_counts)
        recurring = [b for b, c in beneficiary_counts.items() if c >= 2]
        recurring_count = len(recurring)
        
        sorted_beneficiaries = sorted(
            beneficiary_counts.items(),
            key=lambda x: x[1],
            reverse=True
        )
        
        return {
            "unique_count": unique_count,
            "recurring_count": recurring_count,
            "recurring_ratio": round(recurring_count / unique_count, 2) if unique_count > 0 else 0,
            "top_beneficiaries": [
                {"id": b, "count": c}
                for b, c in sorted_beneficiaries[:5]
            ]
        }
    
    # ============================================
    # ANOMALY DETECTION
    # ============================================
    
    def detect_anomalies(
        self,
        account_id: str,
        recent_transactions: List[Dict],
        profile: Dict = None
    ) -> Dict:
        """
        Detect behavioral anomalies in recent activity.
        
        Compares recent transactions against baseline profile
        to identify deviations.
        """
        if profile is None:
            profile = self.profiles.get(account_id)
        
        if not profile or profile.get("is_empty"):
            return {
                "account_id": account_id,
                "has_anomalies": False,
                "message": "Insufficient profile data for anomaly detection"
            }
        
        anomalies = []
        deviation_scores = {}
        
        # Parse recent transactions
        parsed_recent = []
        for txn in recent_transactions:
            try:
                ts = datetime.fromisoformat(txn.get("timestamp", "").replace("Z", ""))
                if txn.get("sender_id") == account_id or txn.get("receiver_id") == account_id:
                    parsed_recent.append({**txn, "parsed_timestamp": ts})
            except (ValueError, TypeError):
                continue
        
        if not parsed_recent:
            return {
                "account_id": account_id,
                "has_anomalies": False,
                "message": "No recent transactions to analyze"
            }
        
        # Frequency anomaly
        freq_anomaly = self._detect_frequency_anomaly(parsed_recent, profile)
        if freq_anomaly["is_anomaly"]:
            anomalies.append(freq_anomaly)
        deviation_scores["frequency"] = freq_anomaly["deviation_score"]
        
        # Amount anomaly
        amount_anomaly = self._detect_amount_anomaly(parsed_recent, profile)
        if amount_anomaly["is_anomaly"]:
            anomalies.append(amount_anomaly)
        deviation_scores["amount"] = amount_anomaly["deviation_score"]
        
        # Time pattern anomaly
        time_anomaly = self._detect_time_anomaly(parsed_recent, profile)
        if time_anomaly["is_anomaly"]:
            anomalies.append(time_anomaly)
        deviation_scores["time_pattern"] = time_anomaly["deviation_score"]
        
        # Beneficiary anomaly
        beneficiary_anomaly = self._detect_beneficiary_anomaly(
            account_id, parsed_recent, profile
        )
        if beneficiary_anomaly["is_anomaly"]:
            anomalies.append(beneficiary_anomaly)
        deviation_scores["beneficiary"] = beneficiary_anomaly["deviation_score"]
        
        # Calculate overall deviation score
        overall_deviation = np.mean(list(deviation_scores.values()))
        
        return {
            "account_id": account_id,
            "has_anomalies": len(anomalies) > 0,
            "anomaly_count": len(anomalies),
            "anomalies": anomalies,
            "deviation_scores": deviation_scores,
            "overall_deviation_score": round(overall_deviation, 2),
            "risk_level": "high" if overall_deviation > 60 else "medium" if overall_deviation > 30 else "low",
            "analyzed_transactions": len(parsed_recent),
            "analysis_timestamp": datetime.now().isoformat()
        }
    
    def _detect_frequency_anomaly(
        self,
        recent_txns: List[Dict],
        profile: Dict
    ) -> Dict:
        """Detect transaction frequency anomalies."""
        # Group by date
        daily_counts = defaultdict(int)
        for txn in recent_txns:
            date_key = txn["parsed_timestamp"].date()
            daily_counts[date_key] += 1
        
        if not daily_counts:
            return {"type": "frequency", "is_anomaly": False, "deviation_score": 0}
        
        recent_avg = np.mean(list(daily_counts.values()))
        recent_max = max(daily_counts.values())
        
        baseline_avg = profile.get("frequency", {}).get("avg_daily_transactions", 0)
        baseline_max = profile.get("frequency", {}).get("max_daily_transactions", 0)
        
        # Calculate deviation
        if baseline_avg > 0:
            avg_deviation = (recent_avg - baseline_avg) / baseline_avg
        else:
            avg_deviation = recent_avg  # No baseline
        
        if baseline_max > 0:
            max_deviation = (recent_max - baseline_max) / baseline_max
        else:
            max_deviation = 0
        
        deviation_score = min(max(avg_deviation, max_deviation) * 50, 100)
        is_anomaly = deviation_score > 50
        
        return {
            "type": "frequency",
            "is_anomaly": is_anomaly,
            "deviation_score": round(deviation_score, 2),
            "recent_avg": round(recent_avg, 2),
            "baseline_avg": round(baseline_avg, 2),
            "recent_max": recent_max,
            "baseline_max": baseline_max,
            "explanation": f"Transaction frequency {avg_deviation:.0%} {'above' if avg_deviation > 0 else 'below'} baseline" if is_anomaly else None
        }
    
    def _detect_amount_anomaly(
        self,
        recent_txns: List[Dict],
        profile: Dict
    ) -> Dict:
        """Detect transaction amount anomalies."""
        amounts = [t.get("amount", 0) for t in recent_txns]
        
        if not amounts:
            return {"type": "amount", "is_anomaly": False, "deviation_score": 0}
        
        recent_mean = np.mean(amounts)
        recent_max = max(amounts)
        
        baseline = profile.get("amounts", {})
        baseline_mean = baseline.get("mean", 0)
        baseline_p95 = baseline.get("percentile_95", 0)
        baseline_std = baseline.get("std", 1)
        
        # Z-score based deviation
        if baseline_std > 0:
            z_score = (recent_mean - baseline_mean) / baseline_std
        else:
            z_score = 0
        
        # Check for amounts exceeding p95
        above_p95 = sum(1 for a in amounts if a > baseline_p95) if baseline_p95 > 0 else 0
        above_p95_ratio = above_p95 / len(amounts)
        
        deviation_score = min(abs(z_score) * 20 + above_p95_ratio * 50, 100)
        is_anomaly = deviation_score > 40
        
        return {
            "type": "amount",
            "is_anomaly": is_anomaly,
            "deviation_score": round(deviation_score, 2),
            "recent_mean": round(recent_mean, 2),
            "baseline_mean": round(baseline_mean, 2),
            "z_score": round(z_score, 2),
            "above_baseline_p95": above_p95,
            "explanation": f"Transaction amounts significantly {'higher' if z_score > 0 else 'lower'} than baseline (z-score: {z_score:.1f})" if is_anomaly else None
        }
    
    def _detect_time_anomaly(
        self,
        recent_txns: List[Dict],
        profile: Dict
    ) -> Dict:
        """Detect time-of-day pattern anomalies."""
        time_patterns = profile.get("time_patterns", {})
        typical_hours = set(time_patterns.get("typical_hours", []))
        baseline_late_night = time_patterns.get("late_night_ratio", 0)
        
        outside_typical = 0
        late_night = 0
        
        for txn in recent_txns:
            hour = txn["parsed_timestamp"].hour
            if typical_hours and hour not in typical_hours:
                outside_typical += 1
            if hour in [23, 0, 1, 2, 3, 4, 5]:
                late_night += 1
        
        total = len(recent_txns)
        outside_ratio = outside_typical / total if total > 0 else 0
        late_night_ratio = late_night / total if total > 0 else 0
        
        # Anomaly if significant increase in unusual timing
        late_night_deviation = late_night_ratio - baseline_late_night
        
        deviation_score = outside_ratio * 50 + max(late_night_deviation, 0) * 50
        is_anomaly = deviation_score > 40
        
        return {
            "type": "time_pattern",
            "is_anomaly": is_anomaly,
            "deviation_score": round(deviation_score, 2),
            "outside_typical_hours": outside_typical,
            "outside_ratio": round(outside_ratio, 2),
            "late_night_count": late_night,
            "late_night_ratio": round(late_night_ratio, 2),
            "baseline_late_night_ratio": round(baseline_late_night, 2),
            "explanation": f"Unusual transaction timing: {outside_ratio:.0%} outside typical hours" if is_anomaly else None
        }
    
    def _detect_beneficiary_anomaly(
        self,
        account_id: str,
        recent_txns: List[Dict],
        profile: Dict
    ) -> Dict:
        """Detect beneficiary pattern anomalies."""
        beneficiary_profile = profile.get("beneficiaries", {})
        
        # Get recent outgoing transactions
        outgoing = [t for t in recent_txns if t.get("sender_id") == account_id]
        
        if not outgoing:
            return {"type": "beneficiary", "is_anomaly": False, "deviation_score": 0}
        
        # Count new beneficiaries
        known_beneficiaries = set(
            b["id"] for b in beneficiary_profile.get("top_beneficiaries", [])
        )
        
        recent_beneficiaries = set()
        new_beneficiaries = set()
        
        for txn in outgoing:
            receiver = txn.get("receiver_id")
            if receiver:
                recent_beneficiaries.add(receiver)
                if receiver not in known_beneficiaries:
                    new_beneficiaries.add(receiver)
        
        # High ratio of new beneficiaries is suspicious
        new_ratio = len(new_beneficiaries) / len(recent_beneficiaries) if recent_beneficiaries else 0
        
        # Compare to baseline diversity
        baseline_recurring_ratio = beneficiary_profile.get("recurring_ratio", 0.5)
        
        deviation_score = new_ratio * 70 + (1 - baseline_recurring_ratio) * 30
        is_anomaly = deviation_score > 50
        
        return {
            "type": "beneficiary",
            "is_anomaly": is_anomaly,
            "deviation_score": round(deviation_score, 2),
            "new_beneficiary_count": len(new_beneficiaries),
            "new_ratio": round(new_ratio, 2),
            "total_recent_beneficiaries": len(recent_beneficiaries),
            "explanation": f"High new beneficiary ratio: {len(new_beneficiaries)} new recipients ({new_ratio:.0%})" if is_anomaly else None
        }
    
    # ============================================
    # UTILITY METHODS
    # ============================================
    
    def get_profile(self, account_id: str) -> Optional[Dict]:
        """Get cached profile for account."""
        return self.profiles.get(account_id)
    
    def get_all_profiles(self) -> Dict[str, Dict]:
        """Get all cached profiles."""
        return self.profiles
    
    def clear_profiles(self):
        """Clear profile cache."""
        self.profiles = {}


# ============================================
# FACTORY FUNCTION
# ============================================

def create_profiler(lookback_days: int = 90) -> BehavioralProfiler:
    """Create behavioral profiler instance."""
    return BehavioralProfiler(lookback_days=lookback_days)
