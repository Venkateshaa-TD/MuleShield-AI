"""
MuleShield AI - SAR Report Generator
Generates Suspicious Activity Report (SAR) style reports

This module creates regulatory-compliant report formats for:
- Suspicious account activity
- Mule network detection
- Transaction pattern analysis

Report includes:
- Account details
- Suspicious pattern summary
- Risk score breakdown
- AI reasoning explanation
- Transaction summary
- Network analysis
"""

from typing import List, Dict, Optional
from datetime import datetime
import uuid
import json


class SARReportGenerator:
    """
    Generates SAR-style reports for suspicious activity.
    
    Reports follow FinCEN-inspired format for regulatory compliance
    simulation.
    """
    
    def __init__(self):
        self.report_counter = 0
    
    def generate_report_number(self) -> str:
        """Generate unique SAR report number."""
        self.report_counter += 1
        return f"SAR-{datetime.now().strftime('%Y%m%d')}-{self.report_counter:05d}"
    
    def generate_sar_report(
        self,
        account: Dict,
        risk_score_data: Dict,
        transactions: List[Dict],
        network_analysis: Dict = None,
        alert: Dict = None,
        case_id: str = None
    ) -> Dict:
        """
        Generate comprehensive SAR report.
        
        Args:
            account: Account information
            risk_score_data: Risk scoring engine output
            transactions: Related transaction records
            network_analysis: Graph analysis results
            alert: Associated alert (if any)
            case_id: Associated case ID (if any)
            
        Returns:
            Complete SAR report dictionary
        """
        account_id = account.get("id")
        
        # Filter account transactions
        account_txns = [
            t for t in transactions
            if t.get("sender_id") == account_id or t.get("receiver_id") == account_id
        ]
        
        # Calculate transaction summary
        txn_summary = self._summarize_transactions(account_id, account_txns)
        
        # Build suspicious pattern summary
        patterns = self._identify_suspicious_patterns(
            risk_score_data, network_analysis
        )
        
        # Generate AI reasoning
        ai_reasoning = self._generate_ai_reasoning(
            risk_score_data, network_analysis, patterns
        )
        
        report = {
            "id": str(uuid.uuid4()),
            "report_number": self.generate_report_number(),
            "case_id": case_id,
            "generated_at": datetime.now().isoformat(),
            "generated_by": "MuleShield AI v1.0",
            "status": "draft",
            
            # Section 1: Subject Information
            "subject_information": {
                "account_id": account.get("id"),
                "account_number": account.get("account_number"),
                "account_holder_name": account.get("account_holder_name"),
                "email": account.get("email"),
                "phone": account.get("phone"),
                "account_type": account.get("account_type"),
                "account_opened": account.get("created_at"),
                "kyc_status": account.get("kyc_status"),
                "country": account.get("country"),
                "city": account.get("city"),
                "current_status": account.get("status")
            },
            
            # Section 2: Risk Assessment
            "risk_assessment": {
                "composite_risk_score": risk_score_data.get("composite_score", 0),
                "risk_category": risk_score_data.get("risk_category", "unknown"),
                "mule_probability": risk_score_data.get("mule_probability", 0),
                "confidence_score": risk_score_data.get("confidence_score", 0),
                "component_scores": {
                    "transaction_velocity": risk_score_data.get("component_scores", {}).get("transaction_velocity", {}).get("score", 0),
                    "beneficiary_diversity": risk_score_data.get("component_scores", {}).get("beneficiary_diversity", {}).get("score", 0),
                    "account_age": risk_score_data.get("component_scores", {}).get("account_age", {}).get("score", 0),
                    "device_reuse": risk_score_data.get("component_scores", {}).get("device_reuse", {}).get("score", 0),
                    "graph_centrality": risk_score_data.get("component_scores", {}).get("graph_centrality", {}).get("score", 0),
                    "behavior_deviation": risk_score_data.get("component_scores", {}).get("behavior_deviation", {}).get("score", 0)
                }
            },
            
            # Section 3: Suspicious Activity Description
            "suspicious_activity": {
                "summary": self._generate_activity_summary(patterns, risk_score_data),
                "identified_patterns": patterns,
                "ai_reasoning": ai_reasoning,
                "top_risk_factors": risk_score_data.get("top_risk_factors", [])
            },
            
            # Section 4: Transaction Analysis
            "transaction_analysis": txn_summary,
            
            # Section 5: Network Analysis
            "network_analysis": self._format_network_analysis(network_analysis) if network_analysis else None,
            
            # Section 6: Supporting Evidence
            "supporting_evidence": {
                "alert_id": alert.get("id") if alert else None,
                "alert_type": alert.get("alert_type") if alert else None,
                "alert_severity": alert.get("severity") if alert else None,
                "related_accounts": network_analysis.get("connected_accounts", [])[:10] if network_analysis else [],
                "device_indicators": self._get_device_indicators(risk_score_data)
            },
            
            # Section 7: Recommendation
            "recommendation": self._generate_recommendation(risk_score_data, patterns),
            
            # Metadata
            "metadata": {
                "report_version": "1.0",
                "model_version": risk_score_data.get("component_scores", {}).get("transaction_velocity", {}).get("model_version", "v1.0"),
                "analysis_timestamp": risk_score_data.get("calculated_at"),
                "total_transactions_analyzed": len(account_txns)
            }
        }
        
        return report
    
    def _summarize_transactions(
        self,
        account_id: str,
        transactions: List[Dict]
    ) -> Dict:
        """Generate transaction summary for report."""
        if not transactions:
            return {
                "transaction_count": 0,
                "total_incoming": 0,
                "total_outgoing": 0,
                "period_start": None,
                "period_end": None
            }
        
        incoming = [t for t in transactions if t.get("receiver_id") == account_id]
        outgoing = [t for t in transactions if t.get("sender_id") == account_id]
        
        incoming_total = sum(t.get("amount", 0) for t in incoming)
        outgoing_total = sum(t.get("amount", 0) for t in outgoing)
        
        # Get date range
        timestamps = []
        for t in transactions:
            try:
                ts = datetime.fromisoformat(t.get("timestamp", "").replace("Z", ""))
                timestamps.append(ts)
            except (ValueError, TypeError):
                pass
        
        return {
            "transaction_count": len(transactions),
            "incoming_count": len(incoming),
            "outgoing_count": len(outgoing),
            "total_incoming_amount": round(incoming_total, 2),
            "total_outgoing_amount": round(outgoing_total, 2),
            "net_flow": round(incoming_total - outgoing_total, 2),
            "average_transaction_amount": round(
                sum(t.get("amount", 0) for t in transactions) / len(transactions), 2
            ) if transactions else 0,
            "period_start": min(timestamps).isoformat() if timestamps else None,
            "period_end": max(timestamps).isoformat() if timestamps else None,
            "suspicious_transaction_count": sum(
                1 for t in transactions if t.get("is_suspicious")
            ),
            "unique_counterparties": len(set(
                t.get("receiver_id") for t in outgoing
            ) | set(
                t.get("sender_id") for t in incoming
            )),
            "sample_transactions": [
                {
                    "id": t.get("id"),
                    "amount": t.get("amount"),
                    "type": "incoming" if t.get("receiver_id") == account_id else "outgoing",
                    "timestamp": t.get("timestamp"),
                    "is_suspicious": t.get("is_suspicious"),
                    "suspicious_reason": t.get("suspicious_reason")
                }
                for t in sorted(
                    transactions,
                    key=lambda x: x.get("amount", 0),
                    reverse=True
                )[:5]
            ]
        }
    
    def _identify_suspicious_patterns(
        self,
        risk_score_data: Dict,
        network_analysis: Dict
    ) -> List[Dict]:
        """Identify and describe suspicious patterns."""
        patterns = []
        
        # Check component scores for pattern indicators
        components = risk_score_data.get("component_scores", {})
        
        # Transaction velocity pattern
        velocity = components.get("transaction_velocity", {})
        if velocity.get("score", 0) > 50:
            patterns.append({
                "pattern_type": "high_transaction_velocity",
                "severity": "high" if velocity.get("score", 0) > 70 else "medium",
                "description": "Abnormally high transaction frequency detected",
                "indicator_score": velocity.get("score", 0),
                "details": velocity.get("risk_factors", [])
            })
        
        # Beneficiary diversity pattern
        beneficiary = components.get("beneficiary_diversity", {})
        if beneficiary.get("score", 0) > 50:
            patterns.append({
                "pattern_type": "beneficiary_diversity",
                "severity": "high" if beneficiary.get("score", 0) > 70 else "medium",
                "description": "High number of unique beneficiaries with low recurring ratio",
                "indicator_score": beneficiary.get("score", 0),
                "details": beneficiary.get("risk_factors", [])
            })
        
        # Device sharing pattern
        device = components.get("device_reuse", {})
        if device.get("score", 0) > 50:
            patterns.append({
                "pattern_type": "device_sharing",
                "severity": "critical" if device.get("score", 0) > 70 else "high",
                "description": "Device shared with other potentially suspicious accounts",
                "indicator_score": device.get("score", 0),
                "details": device.get("risk_factors", [])
            })
        
        # Network position pattern
        graph = components.get("graph_centrality", {})
        if graph.get("score", 0) > 50:
            patterns.append({
                "pattern_type": "network_position",
                "severity": "high" if graph.get("score", 0) > 70 else "medium",
                "description": "Account occupies significant position in transaction network",
                "indicator_score": graph.get("score", 0),
                "details": graph.get("risk_factors", [])
            })
        
        # Network-specific patterns
        if network_analysis:
            if network_analysis.get("circular_flow_involvement"):
                patterns.append({
                    "pattern_type": "circular_fund_flow",
                    "severity": "critical",
                    "description": "Account involved in circular money flow pattern",
                    "indicator_score": 90,
                    "details": [
                        f"Part of {len(network_analysis['circular_flow_involvement'])} circular flow(s)"
                    ]
                })
            
            if network_analysis.get("is_hub_account"):
                patterns.append({
                    "pattern_type": "hub_account",
                    "severity": "critical",
                    "description": "Account identified as hub in money distribution network",
                    "indicator_score": 95,
                    "details": [
                        "Receives from multiple sources",
                        "Distributes to multiple destinations"
                    ]
                })
            
            if network_analysis.get("device_cluster"):
                patterns.append({
                    "pattern_type": "device_cluster",
                    "severity": "critical",
                    "description": "Account shares device with multiple other accounts",
                    "indicator_score": 85,
                    "details": [
                        f"Cluster contains {network_analysis['device_cluster'].get('account_count', 0)} accounts"
                    ]
                })
        
        return patterns
    
    def _generate_ai_reasoning(
        self,
        risk_score_data: Dict,
        network_analysis: Dict,
        patterns: List[Dict]
    ) -> List[str]:
        """Generate explainable AI reasoning statements."""
        reasoning = []
        
        # Risk score based reasoning
        risk_score = risk_score_data.get("composite_score", 0)
        mule_prob = risk_score_data.get("mule_probability", 0)
        
        if risk_score >= 70:
            reasoning.append(
                f"High composite risk score ({risk_score:.1f}/100) indicates significant suspicious activity"
            )
        
        if mule_prob >= 70:
            reasoning.append(
                f"Mule probability of {mule_prob:.1f}% based on multi-factor analysis"
            )
        
        # Pattern-based reasoning
        for pattern in patterns:
            if pattern["severity"] == "critical":
                reasoning.append(
                    f"CRITICAL: {pattern['description']} (confidence: {pattern['indicator_score']:.0f}%)"
                )
            elif pattern["severity"] == "high":
                reasoning.append(
                    f"HIGH RISK: {pattern['description']}"
                )
        
        # Network-based reasoning
        if network_analysis:
            conn_count = network_analysis.get("connection_count", 0)
            if conn_count > 5:
                reasoning.append(
                    f"Connected to {conn_count} accounts in transaction network"
                )
            
            centrality = network_analysis.get("centrality", {})
            if centrality.get("betweenness", 0) > 0.05:
                reasoning.append(
                    "High betweenness centrality indicates account acts as network bridge"
                )
        
        # Add risk factors from scoring
        for factor in risk_score_data.get("top_risk_factors", [])[:3]:
            reasoning.append(factor)
        
        return reasoning[:8]  # Limit to top 8 reasons
    
    def _generate_activity_summary(
        self,
        patterns: List[Dict],
        risk_score_data: Dict
    ) -> str:
        """Generate narrative summary of suspicious activity."""
        risk_category = risk_score_data.get("risk_category", "unknown")
        mule_prob = risk_score_data.get("mule_probability", 0)
        
        summary_parts = []
        
        # Opening statement
        if risk_category == "high":
            summary_parts.append(
                "This account has been flagged as HIGH RISK with strong indicators of mule activity."
            )
        elif risk_category == "medium":
            summary_parts.append(
                "This account shows MODERATE risk indicators requiring further investigation."
            )
        else:
            summary_parts.append(
                "This account shows some anomalous activity warranting review."
            )
        
        summary_parts.append(f"The estimated mule probability is {mule_prob:.1f}%.")
        
        # Pattern descriptions
        critical_patterns = [p for p in patterns if p["severity"] == "critical"]
        if critical_patterns:
            pattern_names = [p["pattern_type"].replace("_", " ") for p in critical_patterns]
            summary_parts.append(
                f"Critical patterns detected: {', '.join(pattern_names)}."
            )
        
        high_patterns = [p for p in patterns if p["severity"] == "high"]
        if high_patterns:
            summary_parts.append(
                f"{len(high_patterns)} additional high-severity patterns identified."
            )
        
        return " ".join(summary_parts)
    
    def _format_network_analysis(self, network_analysis: Dict) -> Dict:
        """Format network analysis for report."""
        return {
            "network_position": {
                "degree_centrality": network_analysis.get("centrality", {}).get("degree", 0),
                "betweenness_centrality": network_analysis.get("centrality", {}).get("betweenness", 0),
                "pagerank": network_analysis.get("centrality", {}).get("pagerank", 0)
            },
            "community_id": network_analysis.get("community_id"),
            "connected_accounts_count": network_analysis.get("connection_count", 0),
            "circular_flows_detected": len(network_analysis.get("circular_flow_involvement", [])),
            "is_hub_account": network_analysis.get("is_hub_account", False),
            "device_cluster_size": network_analysis.get("device_cluster", {}).get("account_count", 0) if network_analysis.get("device_cluster") else 0,
            "network_risk_indicators": network_analysis.get("network_risk_indicators", {})
        }
    
    def _get_device_indicators(self, risk_score_data: Dict) -> Dict:
        """Extract device-related risk indicators."""
        device_data = risk_score_data.get("component_scores", {}).get("device_reuse", {})
        return {
            "device_count": device_data.get("device_count", 0),
            "shared_devices": device_data.get("shared_devices", 0),
            "vpn_detected": device_data.get("vpn_usage", False),
            "shared_with_accounts": device_data.get("shared_with_count", 0)
        }
    
    def _generate_recommendation(
        self,
        risk_score_data: Dict,
        patterns: List[Dict]
    ) -> Dict:
        """Generate investigation recommendation."""
        risk_category = risk_score_data.get("risk_category", "low")
        mule_prob = risk_score_data.get("mule_probability", 0)
        critical_count = sum(1 for p in patterns if p["severity"] == "critical")
        
        if risk_category == "high" and mule_prob > 80:
            action = "IMMEDIATE_REVIEW"
            priority = "P1"
            description = "Immediate investigation recommended. Consider account suspension pending review."
        elif risk_category == "high" or mule_prob > 60:
            action = "URGENT_INVESTIGATION"
            priority = "P2"
            description = "Urgent investigation required. Enhanced monitoring recommended."
        elif risk_category == "medium" or critical_count > 0:
            action = "INVESTIGATION_REQUIRED"
            priority = "P3"
            description = "Investigation recommended within 48 hours. Continue monitoring."
        else:
            action = "MONITOR"
            priority = "P4"
            description = "Continue enhanced monitoring. Re-evaluate if activity persists."
        
        return {
            "recommended_action": action,
            "priority": priority,
            "description": description,
            "suggested_next_steps": [
                "Review full transaction history",
                "Examine network connections",
                "Verify device usage patterns",
                "Contact account holder if appropriate",
                "Consider SAR filing if confirmed"
            ][:3 if risk_category != "high" else 5]
        }
    
    def export_report_json(self, report: Dict, filepath: str = None) -> str:
        """Export report to JSON format."""
        output = json.dumps(report, indent=2, default=str)
        
        if filepath:
            with open(filepath, 'w') as f:
                f.write(output)
        
        return output


# ============================================
# FACTORY FUNCTION
# ============================================

def create_sar_generator() -> SARReportGenerator:
    """Create SAR report generator instance."""
    return SARReportGenerator()
