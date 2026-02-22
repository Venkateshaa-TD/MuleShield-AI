"""
MuleShield AI - Graph Analytics Engine
Network analysis for detecting mule account clusters

This engine uses NetworkX to:
1. Build transaction network graphs
2. Detect circular fund flows
3. Identify hub-spoke patterns
4. Calculate centrality metrics
5. Perform community detection
6. Find shared device clusters

Key AML Network Patterns:
- High degree centrality: Account involved in many transactions
- High betweenness centrality: Account acting as network bridge
- Circular flows: Money returning to origin through intermediaries
- Hub-spoke: One account coordinating many others
- Dense communities: Tight-knit groups of transacting accounts
"""

import networkx as nx
from typing import List, Dict, Tuple, Set, Optional
from collections import defaultdict
from datetime import datetime, timedelta
import numpy as np


class MuleNetworkAnalyzer:
    """
    Graph-based analyzer for detecting mule account networks.
    
    Uses transaction data to build directed graphs and identify
    suspicious patterns indicative of money mule activity.
    """
    
    def __init__(self):
        self.transaction_graph: nx.DiGraph = nx.DiGraph()
        self.device_graph: nx.Graph = nx.Graph()
        self._centrality_cache: Dict = {}
        self._community_cache: Dict = {}
    
    def build_transaction_graph(self, transactions: List[Dict]) -> nx.DiGraph:
        """
        Build a directed graph from transaction data.
        
        Nodes: Account IDs
        Edges: Transactions (directed from sender to receiver)
        Edge weights: Transaction amounts (aggregated)
        
        Args:
            transactions: List of transaction dictionaries
            
        Returns:
            NetworkX DiGraph with transaction network
        """
        self.transaction_graph = nx.DiGraph()
        
        # Aggregate transactions between same pairs
        edge_data = defaultdict(lambda: {"weight": 0, "count": 0, "transactions": []})
        
        for txn in transactions:
            sender = txn.get("sender_id")
            receiver = txn.get("receiver_id")
            amount = txn.get("amount", 0)
            
            if sender and receiver:
                key = (sender, receiver)
                edge_data[key]["weight"] += amount
                edge_data[key]["count"] += 1
                edge_data[key]["transactions"].append(txn.get("id"))
        
        # Add edges to graph
        for (sender, receiver), data in edge_data.items():
            self.transaction_graph.add_edge(
                sender, receiver,
                weight=data["weight"],
                count=data["count"],
                transaction_ids=data["transactions"]
            )
        
        # Clear caches when graph changes
        self._centrality_cache = {}
        self._community_cache = {}
        
        return self.transaction_graph
    
    def build_device_graph(self, device_fingerprints: List[Dict]) -> nx.Graph:
        """
        Build undirected graph based on shared device relationships.
        
        Nodes: Account IDs
        Edges: Shared device connection
        
        Shared devices strongly indicate mule network coordination.
        """
        self.device_graph = nx.Graph()
        
        # Group accounts by device
        device_to_accounts = defaultdict(set)
        for fp in device_fingerprints:
            device_id = fp.get("device_id")
            account_id = fp.get("account_id")
            if device_id and account_id:
                device_to_accounts[device_id].add(account_id)
        
        # Create edges between accounts sharing devices
        for device_id, accounts in device_to_accounts.items():
            accounts_list = list(accounts)
            for i in range(len(accounts_list)):
                for j in range(i + 1, len(accounts_list)):
                    if self.device_graph.has_edge(accounts_list[i], accounts_list[j]):
                        # Increment shared device count
                        self.device_graph[accounts_list[i]][accounts_list[j]]["shared_devices"] += 1
                    else:
                        self.device_graph.add_edge(
                            accounts_list[i], accounts_list[j],
                            shared_devices=1,
                            device_ids=[device_id]
                        )
        
        return self.device_graph
    
    # ============================================
    # CENTRALITY CALCULATIONS
    # ============================================
    
    def calculate_degree_centrality(self) -> Dict[str, float]:
        """
        Calculate in-degree and out-degree centrality.
        
        AML Insight:
        - High in-degree: Account receiving from many sources
        - High out-degree: Account sending to many destinations
        - Both high: Potential hub account in mule network
        """
        if "degree" in self._centrality_cache:
            return self._centrality_cache["degree"]
        
        in_degree = nx.in_degree_centrality(self.transaction_graph)
        out_degree = nx.out_degree_centrality(self.transaction_graph)
        
        # Combine into single score
        combined = {}
        all_nodes = set(in_degree.keys()) | set(out_degree.keys())
        for node in all_nodes:
            combined[node] = {
                "in_degree": in_degree.get(node, 0),
                "out_degree": out_degree.get(node, 0),
                "total_degree": in_degree.get(node, 0) + out_degree.get(node, 0)
            }
        
        self._centrality_cache["degree"] = combined
        return combined
    
    def calculate_betweenness_centrality(self) -> Dict[str, float]:
        """
        Calculate betweenness centrality.
        
        AML Insight:
        - High betweenness: Account acts as bridge between groups
        - Mule networks use intermediaries to obscure fund flows
        - Bridge accounts are often key mule coordinators
        """
        if "betweenness" in self._centrality_cache:
            return self._centrality_cache["betweenness"]
        
        betweenness = nx.betweenness_centrality(self.transaction_graph, weight="weight")
        self._centrality_cache["betweenness"] = betweenness
        return betweenness
    
    def calculate_pagerank(self) -> Dict[str, float]:
        """
        Calculate PageRank for transaction flow importance.
        
        AML Insight:
        - High PageRank: Important node in fund flow network
        - Accounts receiving from multiple high-value sources
        - Useful for identifying collection points in mule networks
        """
        if "pagerank" in self._centrality_cache:
            return self._centrality_cache["pagerank"]
        
        try:
            pagerank = nx.pagerank(self.transaction_graph, weight="weight")
        except nx.PowerIterationFailedConvergence:
            pagerank = {node: 0 for node in self.transaction_graph.nodes()}
        
        self._centrality_cache["pagerank"] = pagerank
        return pagerank
    
    def get_centrality_scores(self, account_id: str) -> Dict[str, float]:
        """Get all centrality scores for a specific account."""
        degree = self.calculate_degree_centrality()
        betweenness = self.calculate_betweenness_centrality()
        pagerank = self.calculate_pagerank()
        
        return {
            "degree": degree.get(account_id, {"total_degree": 0})["total_degree"] if isinstance(degree.get(account_id), dict) else 0,
            "in_degree": degree.get(account_id, {"in_degree": 0})["in_degree"] if isinstance(degree.get(account_id), dict) else 0,
            "out_degree": degree.get(account_id, {"out_degree": 0})["out_degree"] if isinstance(degree.get(account_id), dict) else 0,
            "betweenness": betweenness.get(account_id, 0),
            "pagerank": pagerank.get(account_id, 0)
        }
    
    # ============================================
    # PATTERN DETECTION
    # ============================================
    
    def detect_circular_flows(self, max_cycle_length: int = 6) -> List[Dict]:
        """
        Detect circular fund flow patterns.
        
        AML Pattern:
        A → B → C → D → A
        
        This is a classic money laundering technique where funds
        pass through multiple accounts and return to origin,
        making tracing difficult.
        
        Returns list of detected cycles with account IDs.
        """
        cycles = []
        
        try:
            # Find simple cycles up to max length
            for cycle in nx.simple_cycles(self.transaction_graph):
                if 3 <= len(cycle) <= max_cycle_length:
                    # Calculate total flow through cycle
                    total_flow = 0
                    for i in range(len(cycle)):
                        sender = cycle[i]
                        receiver = cycle[(i + 1) % len(cycle)]
                        edge_data = self.transaction_graph.get_edge_data(sender, receiver, {})
                        total_flow += edge_data.get("weight", 0)
                    
                    cycles.append({
                        "accounts": cycle,
                        "length": len(cycle),
                        "total_flow": total_flow,
                        "risk_level": "high" if len(cycle) >= 4 else "medium",
                        "pattern_type": "circular_flow"
                    })
        except Exception:
            pass  # Graph may not have cycles
        
        # Sort by total flow (higher = more suspicious)
        cycles.sort(key=lambda x: x["total_flow"], reverse=True)
        return cycles[:20]  # Return top 20 cycles
    
    def detect_hub_spoke_patterns(self, min_spokes: int = 3) -> List[Dict]:
        """
        Detect hub-spoke transaction patterns.
        
        AML Pattern:
        - Hub account receives from multiple sources
        - Hub distributes to multiple destinations
        - Short time between receive and distribute (layering)
        
        Returns list of detected hub accounts with spoke details.
        """
        hubs = []
        
        for node in self.transaction_graph.nodes():
            in_degree = self.transaction_graph.in_degree(node)
            out_degree = self.transaction_graph.out_degree(node)
            
            # Hub receives from many AND sends to many
            if in_degree >= min_spokes and out_degree >= min_spokes:
                # Calculate flow statistics
                incoming = sum(
                    self.transaction_graph[pred][node].get("weight", 0)
                    for pred in self.transaction_graph.predecessors(node)
                )
                outgoing = sum(
                    self.transaction_graph[node][succ].get("weight", 0)
                    for succ in self.transaction_graph.successors(node)
                )
                
                hubs.append({
                    "hub_account": node,
                    "incoming_connections": in_degree,
                    "outgoing_connections": out_degree,
                    "total_incoming": incoming,
                    "total_outgoing": outgoing,
                    "flow_through_ratio": outgoing / incoming if incoming > 0 else 0,
                    "sources": list(self.transaction_graph.predecessors(node)),
                    "destinations": list(self.transaction_graph.successors(node)),
                    "risk_level": "critical" if in_degree >= 5 and out_degree >= 5 else "high",
                    "pattern_type": "hub_spoke"
                })
        
        # Sort by total connections
        hubs.sort(key=lambda x: x["incoming_connections"] + x["outgoing_connections"], reverse=True)
        return hubs
    
    def detect_rapid_dispersal(self, transactions: List[Dict], time_window_hours: int = 24) -> List[Dict]:
        """
        Detect rapid fund dispersal patterns.
        
        AML Pattern:
        - Large deposit followed by multiple withdrawals
        - All within short time window
        - Classic mule behavior: receive → split → distribute
        """
        patterns = []
        
        # Group transactions by account
        account_txns = defaultdict(list)
        for txn in transactions:
            account_txns[txn.get("receiver_id")].append(("in", txn))
            account_txns[txn.get("sender_id")].append(("out", txn))
        
        for account_id, txns in account_txns.items():
            # Sort by timestamp
            txns.sort(key=lambda x: x[1].get("timestamp", ""))
            
            # Look for large incoming followed by multiple outgoing
            for i, (direction, txn) in enumerate(txns):
                if direction == "in" and txn.get("amount", 0) > 3000:
                    # Check for dispersal within time window
                    incoming_time = datetime.fromisoformat(txn.get("timestamp", datetime.now().isoformat()).replace("Z", ""))
                    outgoing_total = 0
                    outgoing_count = 0
                    
                    for j in range(i + 1, len(txns)):
                        out_direction, out_txn = txns[j]
                        if out_direction == "out":
                            out_time = datetime.fromisoformat(out_txn.get("timestamp", datetime.now().isoformat()).replace("Z", ""))
                            if (out_time - incoming_time).total_seconds() <= time_window_hours * 3600:
                                outgoing_total += out_txn.get("amount", 0)
                                outgoing_count += 1
                    
                    if outgoing_count >= 2 and outgoing_total >= txn.get("amount", 0) * 0.7:
                        patterns.append({
                            "account": account_id,
                            "incoming_amount": txn.get("amount"),
                            "incoming_transaction": txn.get("id"),
                            "outgoing_count": outgoing_count,
                            "outgoing_total": outgoing_total,
                            "dispersal_ratio": outgoing_total / txn.get("amount", 1),
                            "time_window_hours": time_window_hours,
                            "risk_level": "high",
                            "pattern_type": "rapid_dispersal"
                        })
        
        return patterns
    
    # ============================================
    # COMMUNITY DETECTION
    # ============================================
    
    def detect_communities(self) -> Dict[str, int]:
        """
        Detect communities/clusters in transaction network.
        
        AML Insight:
        - Mule networks often form tight communities
        - Accounts in same community transact frequently
        - Cross-community transactions may indicate network expansion
        
        Uses Louvain-style community detection.
        """
        if "communities" in self._community_cache:
            return self._community_cache["communities"]
        
        # Convert to undirected for community detection
        undirected = self.transaction_graph.to_undirected()
        
        if len(undirected.nodes()) == 0:
            return {}
        
        # Use greedy modularity communities
        try:
            from networkx.algorithms.community import greedy_modularity_communities
            communities = greedy_modularity_communities(undirected)
            
            # Assign community IDs to accounts
            account_communities = {}
            for i, community in enumerate(communities):
                for account in community:
                    account_communities[account] = i
            
            self._community_cache["communities"] = account_communities
            return account_communities
        except Exception:
            return {}
    
    def get_community_risk_scores(self) -> Dict[int, Dict]:
        """
        Calculate risk score for each detected community.
        
        High-risk community indicators:
        - Dense internal connections
        - Few external connections
        - Multiple flagged accounts
        - Circular flows within community
        """
        communities = self.detect_communities()
        
        # Group accounts by community
        community_accounts = defaultdict(list)
        for account, community_id in communities.items():
            community_accounts[community_id].append(account)
        
        community_risks = {}
        for community_id, accounts in community_accounts.items():
            # Calculate internal vs external edges
            internal_edges = 0
            external_edges = 0
            
            for account in accounts:
                for neighbor in self.transaction_graph.successors(account):
                    if neighbor in accounts:
                        internal_edges += 1
                    else:
                        external_edges += 1
            
            total_edges = internal_edges + external_edges
            internal_ratio = internal_edges / total_edges if total_edges > 0 else 0
            
            community_risks[community_id] = {
                "account_count": len(accounts),
                "accounts": accounts,
                "internal_edges": internal_edges,
                "external_edges": external_edges,
                "internal_ratio": internal_ratio,
                "risk_score": internal_ratio * 100 if len(accounts) >= 3 else 0,
                "risk_level": "high" if internal_ratio > 0.7 and len(accounts) >= 3 else "medium" if internal_ratio > 0.5 else "low"
            }
        
        return community_risks
    
    # ============================================
    # DEVICE CLUSTER ANALYSIS
    # ============================================
    
    def detect_device_clusters(self) -> List[Dict]:
        """
        Detect clusters of accounts sharing devices.
        
        AML Insight:
        - Multiple accounts on same device = likely mule operation
        - Device clusters often correspond to mule networks
        - Legitimate users rarely share banking devices
        """
        if len(self.device_graph.nodes()) == 0:
            return []
        
        # Find connected components (device clusters)
        clusters = []
        for i, component in enumerate(nx.connected_components(self.device_graph)):
            if len(component) >= 2:  # Only multi-account clusters
                accounts = list(component)
                
                # Calculate cluster metrics
                subgraph = self.device_graph.subgraph(accounts)
                density = nx.density(subgraph)
                
                # Count shared devices
                shared_device_count = sum(
                    self.device_graph[u][v].get("shared_devices", 0)
                    for u, v in subgraph.edges()
                )
                
                clusters.append({
                    "cluster_id": i,
                    "accounts": accounts,
                    "account_count": len(accounts),
                    "density": density,
                    "shared_device_count": shared_device_count,
                    "risk_level": "critical" if len(accounts) >= 4 else "high" if len(accounts) >= 2 else "medium",
                    "pattern_type": "device_cluster"
                })
        
        clusters.sort(key=lambda x: x["account_count"], reverse=True)
        return clusters
    
    # ============================================
    # NETWORK VISUALIZATION DATA
    # ============================================
    
    def get_network_visualization_data(self, account_ids: Optional[List[str]] = None) -> Dict:
        """
        Generate data for frontend network visualization.
        
        Returns nodes and edges formatted for React Flow / D3.
        """
        if account_ids:
            # Subgraph for specific accounts
            nodes_to_include = set(account_ids)
            # Include neighbors
            for account in account_ids:
                nodes_to_include.update(self.transaction_graph.predecessors(account))
                nodes_to_include.update(self.transaction_graph.successors(account))
            subgraph = self.transaction_graph.subgraph(nodes_to_include)
        else:
            subgraph = self.transaction_graph
        
        communities = self.detect_communities()
        centrality = self.calculate_betweenness_centrality()
        
        nodes = []
        for node in subgraph.nodes():
            nodes.append({
                "id": node,
                "community": communities.get(node, 0),
                "centrality": centrality.get(node, 0),
                "in_degree": subgraph.in_degree(node),
                "out_degree": subgraph.out_degree(node),
            })
        
        edges = []
        for source, target, data in subgraph.edges(data=True):
            edges.append({
                "id": f"{source}-{target}",
                "source": source,
                "target": target,
                "weight": data.get("weight", 0),
                "count": data.get("count", 0)
            })
        
        return {
            "nodes": nodes,
            "edges": edges,
            "node_count": len(nodes),
            "edge_count": len(edges)
        }
    
    # ============================================
    # COMPREHENSIVE ANALYSIS
    # ============================================
    
    def analyze_account_network(self, account_id: str) -> Dict:
        """
        Comprehensive network analysis for a specific account.
        
        Returns all relevant network metrics and detected patterns.
        """
        centrality_scores = self.get_centrality_scores(account_id)
        communities = self.detect_communities()
        
        # Find connected accounts
        connected_accounts = set()
        connected_accounts.update(self.transaction_graph.predecessors(account_id))
        connected_accounts.update(self.transaction_graph.successors(account_id))
        
        # Check if part of any detected patterns
        circular_flows = self.detect_circular_flows()
        hub_spokes = self.detect_hub_spoke_patterns()
        
        in_circular = [c for c in circular_flows if account_id in c["accounts"]]
        is_hub = [h for h in hub_spokes if h["hub_account"] == account_id]
        
        # Device cluster check
        device_clusters = self.detect_device_clusters()
        in_device_cluster = [c for c in device_clusters if account_id in c["accounts"]]
        
        return {
            "account_id": account_id,
            "centrality": centrality_scores,
            "community_id": communities.get(account_id),
            "connected_accounts": list(connected_accounts),
            "connection_count": len(connected_accounts),
            "circular_flow_involvement": in_circular,
            "is_hub_account": len(is_hub) > 0,
            "hub_details": is_hub[0] if is_hub else None,
            "device_cluster": in_device_cluster[0] if in_device_cluster else None,
            "network_risk_indicators": self._calculate_network_risk_indicators(
                account_id, centrality_scores, in_circular, is_hub, in_device_cluster
            )
        }
    
    def _calculate_network_risk_indicators(
        self, 
        account_id: str,
        centrality: Dict,
        circular_flows: List,
        hub_patterns: List,
        device_clusters: List
    ) -> Dict:
        """Calculate network-based risk indicators."""
        risk_score = 0
        reasons = []
        
        # High centrality
        if centrality.get("betweenness", 0) > 0.1:
            risk_score += 25
            reasons.append(f"High betweenness centrality ({centrality['betweenness']:.3f})")
        
        if centrality.get("degree", 0) > 0.2:
            risk_score += 20
            reasons.append(f"High degree centrality - connected to many accounts")
        
        # Circular flow involvement
        if circular_flows:
            risk_score += 30
            reasons.append(f"Involved in {len(circular_flows)} circular transaction flow(s)")
        
        # Hub account
        if hub_patterns:
            risk_score += 25
            reasons.append(f"Identified as hub account with {hub_patterns[0]['incoming_connections']} sources and {hub_patterns[0]['outgoing_connections']} destinations")
        
        # Device cluster
        if device_clusters:
            risk_score += 20
            reasons.append(f"Part of device cluster with {device_clusters[0]['account_count']} accounts sharing devices")
        
        return {
            "network_risk_score": min(risk_score, 100),
            "risk_factors": reasons,
            "risk_level": "high" if risk_score >= 60 else "medium" if risk_score >= 30 else "low"
        }


# ============================================
# FACTORY FUNCTION
# ============================================

def create_analyzer(transactions: List[Dict], device_fingerprints: List[Dict] = None) -> MuleNetworkAnalyzer:
    """
    Factory function to create and initialize analyzer.
    
    Args:
        transactions: List of transaction records
        device_fingerprints: Optional device fingerprint data
        
    Returns:
        Initialized MuleNetworkAnalyzer
    """
    analyzer = MuleNetworkAnalyzer()
    analyzer.build_transaction_graph(transactions)
    
    if device_fingerprints:
        analyzer.build_device_graph(device_fingerprints)
    
    return analyzer
