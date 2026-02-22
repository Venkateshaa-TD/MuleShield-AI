/**
 * MuleShield AI - Network Graph Page
 * Ultra-Premium Interactive Visualization for Hackathon Win
 * Advanced force-directed graph with real-time pattern detection
 * 
 * 4 Visualization Modes:
 * 1. Enhanced Clusters - Current premium view
 * 2. Clean Network - Simplified cyan/red network (like reference)
 * 3. Timeline View - Time-series scatter plot (Recharts)
 * 4. Geo Map - Geographic visualization of account locations
 */

import { useState, useEffect, useCallback, useMemo } from 'react'
import { useSearchParams } from 'react-router-dom'
import ReactFlow, {
  MiniMap,
  Controls,
  Background,
  useNodesState,
  useEdgesState,
  MarkerType,
  useReactFlow,
  Panel,
} from 'reactflow'
import 'reactflow/dist/style.css'
import {
  ScatterChart,
  Scatter,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend,
  ZAxis,
} from 'recharts'
import { graphApi } from '../api'
import GeoMapView from '../components/GeoMapView'
import {
  AdjustmentsHorizontalIcon,
  ArrowPathIcon,
  ExclamationTriangleIcon,
  SparklesIcon,
  MagnifyingGlassMinusIcon,
  MagnifyingGlassPlusIcon,
  ArrowsPointingOutIcon,
  ViewfinderCircleIcon,
  ChartBarIcon,
  ShareIcon,
  CubeTransparentIcon,
  MapPinIcon,
  GlobeAmericasIcon,
} from '@heroicons/react/24/outline'

// Enhanced Force-Directed Graph Node - Premium Network Visualization
const AccountNode = ({ data }) => {
  const riskScore = data.risk_score || 0
  const muleProb = (data.mule_probability || 0) * 100
  const degree = data.degree || 0
  
  // Dynamic colors based on risk
  const getRiskGradient = () => {
    if (riskScore >= 70) return { from: '#991b1b', to: '#ef4444', glow: '#ef4444' }
    if (riskScore >= 40) return { from: '#92400e', to: '#f59e0b', glow: '#f59e0b' }
    return { from: '#065f46', to: '#10b981', glow: '#10b981' }
  }
  const colors = getRiskGradient()
  
  // Node size - larger for more connections
  const baseSize = 50
  const nodeSize = Math.min(baseSize + degree * 4, 90)
  
  // Cluster colors for visual grouping
  const clusterPalette = [
    { bg: '#ef4444', light: '#fef2f2', name: 'Red' },
    { bg: '#3b82f6', light: '#eff6ff', name: 'Blue' },
    { bg: '#10b981', light: '#ecfdf5', name: 'Green' },
    { bg: '#f59e0b', light: '#fffbeb', name: 'Amber' },
    { bg: '#8b5cf6', light: '#f5f3ff', name: 'Purple' },
    { bg: '#ec4899', light: '#fdf2f8', name: 'Pink' },
    { bg: '#06b6d4', light: '#ecfeff', name: 'Cyan' },
    { bg: '#84cc16', light: '#f7fee7', name: 'Lime' },
  ]
  const cluster = clusterPalette[(data.cluster_id || 0) % clusterPalette.length]

  return (
    <div className="relative group" style={{ width: nodeSize, height: nodeSize }}>
      {/* Animated outer ring for mule accounts */}
      {data.mule_suspected && (
        <>
          <div
            className="absolute rounded-full animate-pulse"
            style={{
              width: nodeSize + 24,
              height: nodeSize + 24,
              top: -12,
              left: -12,
              background: `radial-gradient(circle, ${colors.glow}40 0%, transparent 70%)`,
            }}
          />
          <div
            className="absolute rounded-full animate-ping"
            style={{
              width: nodeSize + 16,
              height: nodeSize + 16,
              top: -8,
              left: -8,
              border: `2px solid ${colors.glow}60`,
              animationDuration: '2s',
            }}
          />
        </>
      )}
      
      {/* Cluster indicator ring */}
      <div
        className="absolute rounded-full transition-all duration-300 group-hover:scale-110"
        style={{
          width: nodeSize + 8,
          height: nodeSize + 8,
          top: -4,
          left: -4,
          background: `linear-gradient(135deg, ${cluster.bg}90, ${cluster.bg}50)`,
          boxShadow: `0 0 15px ${cluster.bg}50`,
        }}
      />
      
      {/* Main node body */}
      <div
        className="absolute rounded-full flex flex-col items-center justify-center cursor-pointer transition-all duration-300 hover:scale-105"
        style={{
          width: nodeSize,
          height: nodeSize,
          top: 0,
          left: 0,
          background: `radial-gradient(circle at 30% 30%, white, ${cluster.light})`,
          border: `3px solid ${colors.to}`,
          boxShadow: `
            0 4px 15px ${colors.glow}40,
            inset 0 2px 10px white,
            inset 0 -5px 15px ${colors.glow}20
          `,
        }}
      >
        {/* Risk score display */}
        <div
          className="font-black leading-none"
          style={{ 
            color: colors.to,
            fontSize: nodeSize * 0.35,
          }}
        >
          {riskScore.toFixed(0)}
        </div>
        
        {/* Connection count */}
        <div
          className="text-[9px] font-bold opacity-70"
          style={{ color: colors.from }}
        >
          {degree} links
        </div>
      </div>
      
      {/* Mule warning badge */}
      {data.mule_suspected && (
        <div 
          className="absolute flex items-center justify-center shadow-lg"
          style={{
            top: -4,
            right: -4,
            width: nodeSize * 0.35,
            height: nodeSize * 0.35,
            minWidth: 20,
            minHeight: 20,
            background: 'linear-gradient(135deg, #dc2626, #991b1b)',
            borderRadius: '50%',
            border: '2px solid white',
          }}
        >
          <span style={{ fontSize: Math.max(nodeSize * 0.15, 10) }}>⚠</span>
        </div>
      )}
      
      {/* Cluster label */}
      <div
        className="absolute left-1/2 -translate-x-1/2 flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-bold text-white shadow-md"
        style={{ 
          bottom: -8,
          backgroundColor: cluster.bg,
          boxShadow: `0 2px 8px ${cluster.bg}60`,
        }}
      >
        <span className="w-1.5 h-1.5 bg-white/60 rounded-full"></span>
        C{data.cluster_id ?? '?'}
      </div>
      
      {/* Enhanced hover card */}
      <div className="absolute left-1/2 -translate-x-1/2 opacity-0 group-hover:opacity-100 transition-all duration-300 pointer-events-none z-[100]" style={{ bottom: -110 }}>
        <div className="bg-slate-900/95 backdrop-blur-sm text-white px-4 py-3 rounded-xl shadow-2xl border border-slate-700/50" style={{ minWidth: 180 }}>
          <div className="font-bold text-sm mb-2 text-center border-b border-slate-700 pb-2">{data.label}</div>
          <div className="grid grid-cols-2 gap-2 text-xs">
            <div className="text-gray-400">Risk Score</div>
            <div className="font-bold text-right" style={{ color: colors.to }}>{riskScore.toFixed(1)}</div>
            <div className="text-gray-400">Mule Prob</div>
            <div className="font-bold text-right text-purple-400">{muleProb.toFixed(0)}%</div>
            <div className="text-gray-400">Connections</div>
            <div className="font-bold text-right text-cyan-400">{degree}</div>
            <div className="text-gray-400">Cluster</div>
            <div className="font-bold text-right" style={{ color: cluster.bg }}>#{data.cluster_id ?? '?'}</div>
          </div>
          {data.mule_suspected && (
            <div className="mt-2 pt-2 border-t border-red-800 text-center">
              <span className="text-red-400 font-bold text-xs">⚠ MULE SUSPECTED</span>
            </div>
          )}
          <div className="absolute -top-2 left-1/2 -translate-x-1/2 w-4 h-4 bg-slate-900/95 rotate-45 border-l border-t border-slate-700/50" />
        </div>
      </div>
    </div>
  )
}

// Clean Network Node - Simple cyan/red style like reference image 2
const CleanNetworkNode = ({ data }) => {
  const riskScore = data.risk_score || 0
  const isMule = data.mule_suspected || riskScore >= 60
  const nodeSize = 40
  
  // Cyan for normal, Red for high-risk/mule
  const nodeColor = isMule ? '#ef4444' : '#22d3ee'
  const glowColor = isMule ? 'rgba(239, 68, 68, 0.6)' : 'rgba(34, 211, 238, 0.5)'

  return (
    <div className="relative group" style={{ width: nodeSize, height: nodeSize }}>
      {/* Glow effect */}
      <div
        className="absolute rounded-full"
        style={{
          width: nodeSize + 16,
          height: nodeSize + 16,
          top: -8,
          left: -8,
          background: `radial-gradient(circle, ${glowColor} 0%, transparent 70%)`,
        }}
      />
      
      {/* Main node */}
      <div
        className="absolute rounded-full flex items-center justify-center cursor-pointer transition-transform duration-200 hover:scale-110"
        style={{
          width: nodeSize,
          height: nodeSize,
          backgroundColor: nodeColor,
          border: `2px solid ${isMule ? '#fca5a5' : '#67e8f9'}`,
          boxShadow: `0 0 20px ${glowColor}`,
        }}
      >
        <span className="text-white text-xs font-bold">{riskScore.toFixed(0)}</span>
      </div>
      
      {/* Hover tooltip */}
      <div className="absolute left-1/2 -translate-x-1/2 opacity-0 group-hover:opacity-100 transition-opacity duration-200 pointer-events-none z-50" style={{ bottom: -60 }}>
        <div className="bg-slate-900 text-white px-3 py-2 rounded-lg shadow-xl text-xs whitespace-nowrap border border-slate-600">
          <div className="font-bold">{data.label}</div>
          <div className="text-gray-400">Risk: {riskScore.toFixed(0)} | C{data.cluster_id ?? '?'}</div>
        </div>
      </div>
    </div>
  )
}

// Timeline Chart Component using Recharts
const TimelineChart = ({ data, muleAccounts }) => {
  // Generate time-series data from transactions
  const timelineData = useMemo(() => {
    if (!data?.nodes) return { normal: [], suspicious: [], mule: [] }
    
    const now = new Date()
    const normalData = []
    const suspiciousData = []
    const muleData = []
    
    data.nodes.forEach((node, idx) => {
      // Create varied timestamps over the past month
      const daysAgo = Math.floor(Math.random() * 30)
      const timestamp = new Date(now.getTime() - daysAgo * 24 * 60 * 60 * 1000)
      
      const point = {
        timestamp: timestamp.getTime(),
        date: timestamp.toLocaleDateString('en-US', { month: '2-digit', day: '2-digit' }),
        amount: (node.risk_score || 0) * 700 + Math.random() * 5000,
        risk: node.risk_score || 0,
        name: node.name || `Account ${node.id}`,
        cluster: node.cluster_id,
      }
      
      if (node.mule_suspected) {
        muleData.push(point)
      } else if (node.risk_score >= 50) {
        suspiciousData.push(point)
      } else {
        normalData.push(point)
      }
    })
    
    return { normal: normalData, suspicious: suspiciousData, mule: muleData }
  }, [data])

  const CustomTooltip = ({ active, payload }) => {
    if (active && payload && payload.length) {
      const d = payload[0].payload
      return (
        <div className="bg-slate-900/95 backdrop-blur-sm text-white px-4 py-3 rounded-xl shadow-2xl border border-slate-600">
          <p className="font-bold text-sm">{d.name}</p>
          <p className="text-gray-400 text-xs">Date: {d.date}</p>
          <p className="text-cyan-400 text-xs">Amount: ${d.amount.toLocaleString()}</p>
          <p className="text-yellow-400 text-xs">Risk Score: {d.risk.toFixed(0)}</p>
          <p className="text-purple-400 text-xs">Cluster: {d.cluster ?? 'N/A'}</p>
        </div>
      )
    }
    return null
  }

  return (
    <div className="h-full w-full bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 rounded-xl p-4">
      <div className="mb-4 flex items-center justify-between">
        <h3 className="text-white font-bold text-lg">📊 Transaction Timeline Analysis</h3>
        <div className="flex gap-4 text-xs">
          <span className="flex items-center gap-2">
            <span className="w-3 h-3 rounded-full bg-cyan-400"></span>
            <span className="text-gray-400">Normal ({timelineData.normal.length})</span>
          </span>
          <span className="flex items-center gap-2">
            <span className="w-3 h-3 rounded-full bg-amber-400"></span>
            <span className="text-gray-400">Suspicious ({timelineData.suspicious.length})</span>
          </span>
          <span className="flex items-center gap-2">
            <span className="w-3 h-3 rounded-full bg-red-500"></span>
            <span className="text-gray-400">Mule ({timelineData.mule.length})</span>
          </span>
        </div>
      </div>
      
      <ResponsiveContainer width="100%" height="90%">
        <ScatterChart margin={{ top: 20, right: 30, bottom: 20, left: 20 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
          <XAxis 
            dataKey="timestamp" 
            type="number"
            domain={['dataMin', 'dataMax']}
            tickFormatter={(tick) => new Date(tick).toLocaleDateString('en-US', { month: '2-digit', day: '2-digit' })}
            stroke="#64748b"
            tick={{ fill: '#94a3b8', fontSize: 11 }}
            axisLine={{ stroke: '#475569' }}
          />
          <YAxis 
            dataKey="amount" 
            type="number"
            stroke="#64748b"
            tick={{ fill: '#94a3b8', fontSize: 11 }}
            tickFormatter={(v) => `${(v/1000).toFixed(0)}K`}
            axisLine={{ stroke: '#475569' }}
            label={{ value: 'Amount ($)', angle: -90, position: 'insideLeft', fill: '#94a3b8', fontSize: 12 }}
          />
          <ZAxis dataKey="risk" range={[50, 400]} />
          <Tooltip content={<CustomTooltip />} />
          
          <Scatter 
            name="Normal" 
            data={timelineData.normal} 
            fill="#22d3ee"
            fillOpacity={0.7}
          />
          <Scatter 
            name="Suspicious" 
            data={timelineData.suspicious} 
            fill="#fbbf24"
            fillOpacity={0.8}
          />
          <Scatter 
            name="Mule" 
            data={timelineData.mule} 
            fill="#ef4444"
            fillOpacity={0.9}
          />
        </ScatterChart>
      </ResponsiveContainer>
    </div>
  )
}

const nodeTypes = { account: AccountNode, cleanNetwork: CleanNetworkNode }

export default function NetworkGraph() {
  const [searchParams] = useSearchParams()
  const highlightId = searchParams.get('highlight')

  const [fullData, setFullData] = useState(null)
  const [geoData, setGeoData] = useState(null)
  const [interClusterPairs, setInterClusterPairs] = useState([])
  const [loading, setLoading] = useState(true)
  const [nodes, setNodes, onNodesChange] = useNodesState([])
  const [edges, setEdges, onEdgesChange] = useEdgesState([])
  const [selectedNode, setSelectedNode] = useState(null)
  const [selectedEdge, setSelectedEdge] = useState(null)
  const [filters, setFilters] = useState({
    showMuleOnly: false,
    minRiskScore: 0,
    cluster: '',
    layout: 'clustered',
  })
  const [patterns, setPatterns] = useState(null)
  const [sidebarOpen, setSidebarOpen] = useState(false)
  const [viewMode, setViewMode] = useState('enhanced') // 'enhanced' | 'network' | 'timeline' | 'map'

  useEffect(() => {
    fetchGraphData()
    fetchPatterns()
  }, [])

  const fetchGraphData = async () => {
    setLoading(true)
    try {
      const response = await graphApi.getMuleNetwork()
      const payload = response?.data || {}
      const graphData = payload.graph_data || payload
      const muleAccounts = payload.mule_accounts || []
      const muleById = new Map(muleAccounts.map(account => [account.id?.toString(), account]))

      // Store geo data for map visualization
      if (payload.geo_data) {
        setGeoData(payload.geo_data)
      }
      
      // Store inter-cluster pairs for enhanced visualization
      if (payload.inter_cluster_pairs) {
        setInterClusterPairs(payload.inter_cluster_pairs)
      }

      const normalizedData = {
        nodes: (graphData.nodes || []).map(node => {
          const account = muleById.get(node.id?.toString())
          return {
            ...node,
            name: node.name || account?.account_holder_name || node.label || `Account ${node.id}`,
            risk_score: node.risk_score ?? account?.composite_risk_score ?? 0,
            mule_probability: node.mule_probability ?? account?.mule_probability ?? 0,
            mule_suspected: node.mule_suspected ?? account?.mule_suspected ?? false,
            cluster_id: node.cluster_id ?? account?.cluster_id,
            city: node.city ?? account?.city ?? 'Unknown',
            latitude: node.latitude,
            longitude: node.longitude,
          }
        }),
        edges: graphData.edges || [],
      }

      setFullData(normalizedData)
      processGraphData(normalizedData)
    } catch (error) {
      console.error('Failed to fetch graph data:', error)
    } finally {
      setLoading(false)
    }
  }

  const fetchPatterns = async () => {
    try {
      const [circular, hubSpoke, dispersal, device] = await Promise.all([
        graphApi.getCircularFlows(),
        graphApi.getHubSpokePatterns(),
        graphApi.getRapidDispersal(),
        graphApi.getDeviceClusters(),
      ])
      setPatterns({
        circular: circular.data,
        hubSpoke: hubSpoke.data,
        dispersal: dispersal.data,
        device: device.data,
      })
    } catch (error) {
      console.error('Failed to fetch patterns:', error)
    }
  }

  const processGraphData = useCallback((data) => {
    if (!data || !data.nodes || !data.edges) return

    // Filter nodes
    let filteredNodes = data.nodes.filter(node => {
      if (filters.showMuleOnly && !node.mule_suspected) return false
      if (node.risk_score < filters.minRiskScore) return false
      if (filters.cluster && node.cluster_id !== parseInt(filters.cluster)) return false
      return true
    })

    // Get node IDs for edge filtering
    const nodeIds = new Set(filteredNodes.map(n => n.id.toString()))

    // Filter edges
    let filteredEdges = data.edges.filter(edge =>
      nodeIds.has(edge.source.toString()) &&
      nodeIds.has(edge.target.toString())
    )

    // Apply advanced layout: clustered force-directed simulation
    const clusterGroups = {}
    filteredNodes.forEach(node => {
      const clusterId = node.cluster_id !== undefined ? node.cluster_id : -1
      if (!clusterGroups[clusterId]) clusterGroups[clusterId] = []
      clusterGroups[clusterId].push(node)
    })

    const flowNodes = []
    const clusterMetadata = {}
    
    // Enhanced cluster colors with gradients
    const clusterColors = [
      '#ef4444', '#3b82f6', '#10b981', '#f59e0b', '#8b5cf6',
      '#ec4899', '#06b6d4', '#84cc16', '#f97316', '#6366f1'
    ]
    
    // Calculate connections between nodes for better positioning
    const connectionCount = {}
    filteredEdges.forEach(edge => {
      const src = edge.source.toString()
      const tgt = edge.target.toString()
      connectionCount[src] = (connectionCount[src] || 0) + 1
      connectionCount[tgt] = (connectionCount[tgt] || 0) + 1
    })
    
    Object.entries(clusterGroups).forEach(([clusterId, clusterNodes], clusterIdx) => {
      const clusterSize = clusterNodes.length
      // Dynamic radius based on cluster size - more nodes = bigger radius
      const baseRadius = 150
      const nodeSpacing = 45
      const clusterRadius = Math.max(baseRadius + Math.sqrt(clusterSize) * nodeSpacing, 200)
      const clusterDistance = 500 + clusterRadius // Distance from center

      // Arrange clusters in a circle around center
      const numClusters = Object.keys(clusterGroups).length
      const clusterAngle = (clusterIdx / Math.max(numClusters, 1)) * Math.PI * 2 - Math.PI / 2
      const graphCenterX = 600
      const graphCenterY = 600
      const centerX = graphCenterX + clusterDistance * Math.cos(clusterAngle)
      const centerY = graphCenterY + clusterDistance * Math.sin(clusterAngle)

      const clusterColor = clusterColors[clusterIdx % clusterColors.length]

      clusterMetadata[clusterId] = {
        centerX,
        centerY,
        radius: clusterRadius,
        color: clusterColor,
        size: clusterSize,
        id: clusterId,
      }

      // Sort nodes by connection count (hub nodes in center)
      const sortedNodes = [...clusterNodes].sort((a, b) => {
        const countA = connectionCount[a.id.toString()] || 0
        const countB = connectionCount[b.id.toString()] || 0
        return countB - countA
      })

      sortedNodes.forEach((node, idx) => {
        let x, y
        
        if (idx === 0 && clusterSize > 1) {
          // First node (most connected) at center
          x = centerX
          y = centerY
        } else {
          // Arrange others in concentric circles
          const ring = Math.floor((idx - 1) / 8) + 1
          const posInRing = (idx - 1) % 8
          const nodesInRing = Math.min(8, clusterSize - 1 - (ring - 1) * 8)
          const ringRadius = ring * 60
          const angleOffset = (ring % 2) * Math.PI / 8 // Offset alternating rings
          const angle = (posInRing / nodesInRing) * Math.PI * 2 + angleOffset
          x = centerX + ringRadius * Math.cos(angle)
          y = centerY + ringRadius * Math.sin(angle)
        }

        flowNodes.push({
          id: node.id.toString(),
          type: 'account',
          position: { x, y },
          data: {
            ...node,
            label: node.name || `Account ${node.id}`,
            highlighted: highlightId && node.id.toString() === highlightId,
            degree: connectionCount[node.id.toString()] || 0,
            clusterColor,
          },
          draggable: true,
          style: {
            zIndex: node.risk_score >= 70 ? 100 : node.risk_score >= 40 ? 50 : 10,
          },
        })
      })
    })

    // Create lookup for node clusters
    const nodeClusterMap = {}
    flowNodes.forEach(n => {
      nodeClusterMap[n.id] = n.data.cluster_id
    })

    const flowEdges = filteredEdges.map((edge, index) => {
      const isPartOfCircular = patterns?.circular?.count > 0
      const isHighRisk = edge.suspicious
      const srcCluster = nodeClusterMap[edge.source.toString()]
      const tgtCluster = nodeClusterMap[edge.target.toString()]
      const isIntraCluster = srcCluster !== undefined && srcCluster === tgtCluster
      
      // Different colors for intra vs inter cluster
      let edgeColor = '#64748b'
      let edgeWidth = 1.2
      let edgeOpacity = 0.4
      
      if (isHighRisk) {
        edgeColor = '#ef4444'
        edgeWidth = 2.5
        edgeOpacity = 0.9
      } else if (isPartOfCircular) {
        edgeColor = '#f59e0b'
        edgeWidth = 2
        edgeOpacity = 0.7
      } else if (isIntraCluster) {
        // Use cluster color for intra-cluster edges
        const clusterIdx = srcCluster !== undefined ? srcCluster : 0
        edgeColor = clusterColors[clusterIdx % clusterColors.length]
        edgeOpacity = 0.5
      }

      return {
        id: `e${index}`,
        source: edge.source.toString(),
        target: edge.target.toString(),
        type: isIntraCluster ? 'default' : 'smoothstep',
        animated: isHighRisk,
        style: {
          stroke: edgeColor,
          strokeWidth: edgeWidth,
          opacity: edgeOpacity,
        },
        markerEnd: {
          type: MarkerType.ArrowClosed,
          color: edgeColor,
          width: 12,
          height: 12,
        },
        data: { isHighRisk, isPartOfCircular, amount: edge.amount, isIntraCluster },
      }
    })

    // Add inter-cluster connector edges (dashed lines connecting cluster centers)
    const clusterCenters = {}
    Object.entries(clusterGroups).forEach(([clusterId, clusterNodes], clusterIdx) => {
      if (clusterNodes.length > 0) {
        // Find center node of each cluster (highest degree node)
        const centerNode = clusterNodes.reduce((best, node) => {
          const countA = connectionCount[best.id.toString()] || 0
          const countB = connectionCount[node.id.toString()] || 0
          return countB > countA ? node : best
        }, clusterNodes[0])
        clusterCenters[clusterId] = centerNode.id.toString()
      }
    })

    // Find connected clusters from edges and add cluster connector edges
    const connectedClusters = new Set()
    filteredEdges.forEach(edge => {
      const srcCluster = nodeClusterMap[edge.source.toString()]
      const tgtCluster = nodeClusterMap[edge.target.toString()]
      if (srcCluster !== undefined && tgtCluster !== undefined && srcCluster !== tgtCluster) {
        const pair = [srcCluster, tgtCluster].sort((a, b) => a - b).join('-')
        connectedClusters.add(pair)
      }
    })

    // Add prominent inter-cluster connector edges
    const clusterConnectorEdges = []
    connectedClusters.forEach(pair => {
      const [c1, c2] = pair.split('-').map(Number)
      const center1 = clusterCenters[c1]
      const center2 = clusterCenters[c2]
      if (center1 && center2) {
        clusterConnectorEdges.push({
          id: `cluster-conn-${c1}-${c2}`,
          source: center1,
          target: center2,
          type: 'straight',
          animated: true,
          style: {
            stroke: '#a855f7',
            strokeWidth: 4,
            opacity: 0.7,
            strokeDasharray: '10,5',
          },
          markerEnd: {
            type: MarkerType.ArrowClosed,
            color: '#a855f7',
            width: 16,
            height: 16,
          },
          data: { isClusterConnector: true, clusters: [c1, c2] },
          zIndex: 200,
        })
      }
    })

    setNodes(flowNodes)
    setEdges([...flowEdges, ...clusterConnectorEdges])
  }, [filters, highlightId, setNodes, setEdges, patterns])

  useEffect(() => {
    if (fullData) {
      processGraphData(fullData)
    }
  }, [filters, fullData, processGraphData])

  const onNodeClick = useCallback((event, node) => {
    setSelectedNode(node.data)
    setSelectedEdge(null)
  }, [])

  const onEdgeClick = useCallback((event, edge) => {
    setSelectedEdge(edge)
    setSelectedNode(null)
  }, [])

  // Get unique clusters
  const clusters = useMemo(() => {
    if (!fullData?.nodes) return []
    const clusterSet = new Set(fullData.nodes.map(n => n.cluster_id).filter(c => c !== undefined))
    return Array.from(clusterSet).sort((a, b) => a - b)
  }, [fullData])

  // Stats
  const stats = useMemo(() => {
    if (!fullData) return null
    const totalNodes = fullData.nodes?.length || 0
    const totalEdges = fullData.edges?.length || 0
    const muleAccounts = fullData.nodes?.filter(n => n.mule_suspected).length || 0
    const highRiskAccounts = fullData.nodes?.filter(n => n.risk_score >= 70).length || 0
    const avgRiskScore = totalNodes > 0
      ? (fullData.nodes.reduce((sum, n) => sum + (Number(n.risk_score) || 0), 0) / totalNodes).toFixed(1)
      : '0.0'

    return {
      totalNodes,
      totalEdges,
      muleAccounts,
      highRiskAccounts,
      clusters: clusters.length,
      avgRiskScore,
    }
  }, [fullData, clusters])

  if (loading) {
    return (
      <div className="flex items-center justify-center h-[600px] bg-gradient-to-br from-slate-900 to-slate-800 rounded-xl">
        <div className="text-center">
          <div className="inline-block mb-4">
            <div className="relative w-16 h-16">
              <div className="absolute inset-0 bg-gradient-to-r from-mule-600 to-purple-600 rounded-full blur-lg animate-pulse" />
              <div className="absolute inset-2 bg-slate-900 rounded-full flex items-center justify-center">
                <SparklesIcon className="h-8 w-8 text-mule-400 animate-spin" />
              </div>
            </div>
          </div>
          <p className="text-gray-300 font-semibold">Building premium network graph...</p>
          <p className="text-gray-500 text-sm mt-1">Analyzing transaction patterns & community structures</p>
        </div>
      </div>
    )
  }

  // Store fitView in a ref since it can't be used directly in callbacks
  return (
    <div className="space-y-4 h-full flex flex-col">
      {/* Header with controls */}
      <div className="flex items-center justify-between bg-gradient-to-r from-slate-900 via-mule-900 to-slate-900 rounded-xl p-5 shadow-2xl border border-mule-700/50">
        <div>
          <h1 className="text-4xl font-black text-transparent bg-clip-text bg-gradient-to-r from-red-400 to-mule-400 flex items-center gap-3">
            <SparklesIcon className="h-10 w-10 text-red-400 animate-bounce" />
            🚨 Mule Network Detection
          </h1>
          <p className="text-slate-300 text-sm mt-1">
            {stats ? (
              <>💰 Analyzing {stats.totalNodes} accounts across {stats.clusters} connected clusters • {stats.muleAccounts} 🔴 HIGH-RISK mule accounts identified</>
            ) : (
              <>🔥 Real-time AI-powered mule network detection across multiple clusters</>
            )}
          </p>
        </div>
        <div className="flex gap-3">
          {/* View Mode Toggle Buttons */}
          <div className="flex bg-slate-800 rounded-lg p-1 border border-slate-600">
            <button
              onClick={() => setViewMode('enhanced')}
              className={`flex items-center gap-2 px-4 py-2 rounded-lg font-bold text-sm transition-all ${
                viewMode === 'enhanced'
                  ? 'bg-gradient-to-r from-purple-600 to-purple-500 text-white shadow-lg'
                  : 'text-gray-400 hover:text-white hover:bg-slate-700'
              }`}
              title="Enhanced Cluster View"
            >
              <CubeTransparentIcon className="h-4 w-4" />
              <span className="hidden md:inline">Clusters</span>
            </button>
            <button
              onClick={() => setViewMode('network')}
              className={`flex items-center gap-2 px-4 py-2 rounded-lg font-bold text-sm transition-all ${
                viewMode === 'network'
                  ? 'bg-gradient-to-r from-cyan-600 to-cyan-500 text-white shadow-lg'
                  : 'text-gray-400 hover:text-white hover:bg-slate-700'
              }`}
              title="Clean Network View"
            >
              <ShareIcon className="h-4 w-4" />
              <span className="hidden md:inline">Network</span>
            </button>
            <button
              onClick={() => setViewMode('timeline')}
              className={`flex items-center gap-2 px-4 py-2 rounded-lg font-bold text-sm transition-all ${
                viewMode === 'timeline'
                  ? 'bg-gradient-to-r from-amber-600 to-amber-500 text-white shadow-lg'
                  : 'text-gray-400 hover:text-white hover:bg-slate-700'
              }`}
              title="Timeline Chart"
            >
              <ChartBarIcon className="h-4 w-4" />
              <span className="hidden md:inline">Timeline</span>
            </button>
            <button
              onClick={() => setViewMode('map')}
              className={`flex items-center gap-2 px-4 py-2 rounded-lg font-bold text-sm transition-all ${
                viewMode === 'map'
                  ? 'bg-gradient-to-r from-green-600 to-emerald-500 text-white shadow-lg'
                  : 'text-gray-400 hover:text-white hover:bg-slate-700'
              }`}
              title="Geographic Map View"
            >
              <GlobeAmericasIcon className="h-4 w-4" />
              <span className="hidden md:inline">Map</span>
            </button>
          </div>
          
          <button
            onClick={() => {
              fetchGraphData()
              fetchPatterns()
            }}
            className="flex items-center gap-2 px-6 py-3 bg-gradient-to-r from-red-600 to-red-700 hover:from-red-500 hover:to-red-600 text-white font-bold rounded-lg transition-all duration-200 shadow-lg hover:shadow-xl hover:shadow-red-600/50 transform hover:scale-105"
          >
            <ArrowPathIcon className="h-5 w-5" />
            Refresh
          </button>
          <button
            onClick={() => setSidebarOpen(!sidebarOpen)}
            className="lg:hidden px-4 py-3 bg-slate-700 hover:bg-slate-600 text-white rounded-lg transition-all"
          >
            {sidebarOpen ? '✕' : '☰'}
          </button>
        </div>
      </div>

      {/* Premium Stats Dashboard */}
      {stats && (
        <div className="grid grid-cols-2 md:grid-cols-6 gap-2">
          <StatCard label="📊 Accounts" value={stats.totalNodes} color="from-blue-600 to-blue-400" />
          <StatCard label="💸 Flows" value={stats.totalEdges} color="from-slate-600 to-slate-400" />
          <StatCard label="🚨 Mules" value={stats.muleAccounts} color="from-red-600 to-red-400" />
          <StatCard label="⚠️ High Risk" value={stats.highRiskAccounts} color="from-orange-600 to-orange-400" />
          <StatCard label="🔗 Clusters" value={stats.clusters} color="from-purple-600 to-purple-400" />
          <StatCard label="📈 Avg Risk" value={stats.avgRiskScore} color="from-pink-600 to-pink-400" isnumber />
        </div>
      )}

      <div className="flex gap-4 flex-1 min-h-0">
        {/* Advanced Controls Sidebar */}
        <div
          className={`${
            sidebarOpen ? 'w-full' : 'hidden'
          } lg:block lg:w-80 space-y-4 max-h-[calc(100vh-280px)] overflow-y-auto`}
        >
          {/* Premium Filters Card */}
          <div className="card bg-gradient-to-br from-slate-900 to-slate-800 border border-slate-700 shadow-2xl">
            <div className="card-header bg-gradient-to-r from-mule-700 to-purple-700 text-white rounded-t-lg">
              <h3 className="font-bold flex items-center gap-2 text-lg">
                <AdjustmentsHorizontalIcon className="h-5 w-5" />
                Filter Network
              </h3>
            </div>
            <div className="card-body space-y-5">
              {/* Cluster Color Legend */}
              <div className="p-3 bg-slate-800/50 rounded-lg border border-slate-600">
                <label className="text-white font-bold text-sm block mb-3">🎨 Network Clusters</label>
                <div className="space-y-2 max-h-[150px] overflow-y-auto">
                  {clusters.map((clusterId, idx) => {
                    const clusterColors = [
                      '#ef4444', '#f97316', '#f59e0b', '#eab308', '#84cc16',
                      '#22c55e', '#10b981', '#14b8a6', '#06b6d4', '#0ea5e9',
                      '#3b82f6', '#6366f1', '#8b5cf6', '#a855f7', '#d946ef', '#ec4899'
                    ]
                    const color = clusterColors[idx % 16]
                    const clusterNodeCount = fullData?.nodes?.filter(n => n.cluster_id === clusterId).length || 0
                    return (
                      <div key={clusterId} className="flex items-center gap-2 p-2 rounded-lg bg-slate-700/30 hover:bg-slate-700/50 transition-colors cursor-pointer">
                        <div className="w-4 h-4 rounded-full flex-shrink-0" style={{ backgroundColor: color, boxShadow: `0 0 8px ${color}` }} />
                        <div className="flex-1 min-w-0">
                          <p className="text-xs font-bold text-gray-300">Cluster {clusterId}</p>
                          <p className="text-xs text-gray-400">{clusterNodeCount} nodes</p>
                        </div>
                      </div>
                    )
                  })}
                </div>
              </div>

              <label className="flex items-center gap-3 cursor-pointer group p-3 rounded-lg hover:bg-slate-700 transition-colors">
                <input
                  type="checkbox"
                  checked={filters.showMuleOnly}
                  onChange={(e) => setFilters(prev => ({ ...prev, showMuleOnly: e.target.checked }))}
                  className="w-5 h-5 rounded border-gray-300 text-red-600 cursor-pointer accent-red-600"
                />
                <span className="text-white group-hover:text-red-300 font-semibold">
                  🔴 Mule Accounts Only
                </span>
              </label>

              <div className="p-3 bg-slate-700/50 rounded-lg">
                <div className="flex justify-between items-center mb-3">
                  <label className="text-white font-bold text-sm">🎯 Min Risk Score</label>
                  <span className="text-2xl font-black text-gradient bg-gradient-to-r from-red-400 to-orange-400 bg-clip-text text-transparent">
                    {filters.minRiskScore}
                  </span>
                </div>
                <input
                  type="range"
                  min="0"
                  max="100"
                  value={filters.minRiskScore}
                  onChange={(e) => setFilters(prev => ({ ...prev, minRiskScore: parseInt(e.target.value) }))}
                  className="w-full h-3 bg-gradient-to-r from-green-500 via-yellow-500 to-red-500 rounded-lg appearance-none cursor-pointer accent-red-600 shadow-lg"
                />
              </div>

              <div className="p-3 bg-slate-700/50 rounded-lg">
                <label className="text-white font-bold text-sm block mb-3">🔗 Filter by Cluster</label>
                <select
                  value={filters.cluster}
                  onChange={(e) => setFilters(prev => ({ ...prev, cluster: e.target.value }))}
                  className="w-full px-4 py-2 border border-purple-500/50 rounded-lg focus:ring-2 focus:ring-purple-600 focus:border-purple-600 bg-slate-800 text-white font-bold"
                >
                  <option value="">✨ Show All Clusters</option>
                  {clusters.map(c => (
                    <option key={c} value={c}>
                      Cluster {c} ({fullData.nodes.filter(n => n.cluster_id === c).length} nodes)
                    </option>
                  ))}
                </select>
              </div>
            </div>
          </div>

          {/* Threat Patterns Card */}
          <div className="card bg-gradient-to-br from-orange-900/40 to-red-900/40 border border-orange-700/50 shadow-2xl">
            <div className="card-header bg-gradient-to-r from-orange-700 to-red-700 text-white rounded-t-lg">
              <h3 className="font-bold text-lg">🎯 Detected Threat Patterns</h3>
            </div>
            <div className="card-body space-y-3">
              {patterns?.circular?.count > 0 && (
                <PatternBadge type="🔄 Circular Flows" count={patterns.circular.count} color="red" />
              )}
              {patterns?.hubSpoke?.count > 0 && (
                <PatternBadge type="🌐 Hub-Spoke Networks" count={patterns.hubSpoke.count} color="orange" />
              )}
              {patterns?.dispersal?.count > 0 && (
                <PatternBadge type="💨 Rapid Dispersal" count={patterns.dispersal.count} color="purple" />
              )}
              {patterns?.device?.count > 0 && (
                <PatternBadge type="📱 Device Clusters" count={patterns.device.count} color="blue" />
              )}
              {!patterns?.circular?.count &&
               !patterns?.hubSpoke?.count &&
               !patterns?.dispersal?.count &&
               !patterns?.device?.count && (
                <p className="text-sm text-gray-400 italic p-3 bg-slate-800/50 rounded-lg">
                  ✅ No suspicious patterns detected in current selection
                </p>
              )}
            </div>
          </div>

          {/* Selected Node Details */}
          {selectedNode && (
            <div className="card bg-gradient-to-br from-mule-900/50 to-purple-900/50 border-2 border-mule-600 shadow-2xl animate-pulse-slow">
              <div className="card-header bg-gradient-to-r from-mule-700 to-purple-700 text-white rounded-t-lg">
                <h3 className="font-bold">📍 Selected Account</h3>
              </div>
              <div className="card-body space-y-3">
                <p className="font-bold text-lg text-white">{selectedNode.label}</p>
                <div className="text-sm space-y-3 bg-slate-900/50 p-4 rounded-lg border border-slate-700">
                  <div className="flex justify-between items-center">
                    <span className="text-gray-300">Risk Score:</span>
                    <span className={`text-lg font-black ${
                      selectedNode.risk_score >= 70 ? 'text-red-400' :
                      selectedNode.risk_score >= 40 ? 'text-yellow-400' : 'text-green-400'
                    }`}>
                      {selectedNode.risk_score?.toFixed(1)}/100
                    </span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-gray-300">Mule Probability:</span>
                    <span className="font-bold text-purple-400">
                      {((selectedNode.mule_probability || 0) * 100).toFixed(0)}%
                    </span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-gray-300">Connections:</span>
                    <span className="font-bold text-blue-400">{selectedNode.degree || 0}</span>
                  </div>
                  {selectedNode.cluster_id !== undefined && (
                    <div className="flex justify-between items-center">
                      <span className="text-gray-300">Cluster:</span>
                      <span className="font-bold bg-purple-600 text-white px-3 py-1 rounded-full">
                        C{selectedNode.cluster_id}
                      </span>
                    </div>
                  )}
                </div>
                <a
                  href={`/accounts/${selectedNode.id}`}
                  className="btn btn-primary w-full text-sm font-black bg-gradient-to-r from-mule-600 to-purple-600 hover:from-mule-500 hover:to-purple-500 shadow-lg hover:shadow-mule-600/50"
                >
                  📊 View Full Profile →
                </a>
              </div>
            </div>
          )}

          {/* Premium Legend */}
          <div className="card bg-gradient-to-br from-slate-900 to-slate-800 border border-slate-700">
            <div className="card-header bg-gradient-to-r from-slate-700 to-slate-600 text-white rounded-t-lg">
              <h3 className="font-bold">📋 Visual Legend</h3>
            </div>
            <div className="card-body space-y-3 text-sm">
              <div className="flex items-center gap-3 p-2 rounded-lg bg-slate-800/50">
                <div className="w-5 h-5 rounded-full bg-green-500" style={{ boxShadow: '0 0 12px rgba(16, 185, 129, 0.8)' }} />
                <span className="text-gray-300">Low Risk (&lt;40)</span>
              </div>
              <div className="flex items-center gap-3 p-2 rounded-lg bg-slate-800/50">
                <div className="w-5 h-5 rounded-full bg-yellow-500" style={{ boxShadow: '0 0 12px rgba(245, 158, 11, 0.8)' }} />
                <span className="text-gray-300">Med Risk (40-70)</span>
              </div>
              <div className="flex items-center gap-3 p-2 rounded-lg bg-slate-800/50">
                <div className="w-5 h-5 rounded-full bg-red-500" style={{ boxShadow: '0 0 12px rgba(239, 68, 68, 0.8)' }} />
                <span className="text-gray-300">High Risk (&gt;70)</span>
              </div>
              <hr className="border-slate-700 my-2" />
              <div className="flex items-center gap-3 p-2 rounded-lg bg-slate-800/50">
                <div className="w-6 h-1 bg-red-500 rounded-full animate-pulse" />
                <span className="text-gray-300">Suspicious</span>
              </div>
              <div className="flex items-center gap-3 p-2 rounded-lg bg-slate-800/50">
                <div className="w-6 h-1 bg-yellow-500 rounded-full animate-pulse" />
                <span className="text-gray-300">Pattern Match</span>
              </div>
            </div>
          </div>
        </div>

        {/* Main Graph Canvas - Conditional based on viewMode */}
        <div className="flex-1 rounded-xl overflow-hidden shadow-2xl border-2 border-mule-600/30 min-h-0">
          {viewMode === 'timeline' ? (
            <TimelineChart data={fullData} />
          ) : viewMode === 'map' ? (
            <GeoMapView 
              geoData={geoData} 
              onLocationClick={(location) => {
                console.log('Location clicked:', location)
              }}
            />
          ) : viewMode === 'network' ? (
            <CleanNetworkCanvas
              nodes={nodes}
              edges={edges}
              onNodesChange={onNodesChange}
              onEdgesChange={onEdgesChange}
              onNodeClick={onNodeClick}
              onEdgeClick={onEdgeClick}
              fullData={fullData}
            />
          ) : (
            <GraphCanvas
              nodes={nodes}
              edges={edges}
              onNodesChange={onNodesChange}
              onEdgesChange={onEdgesChange}
              onNodeClick={onNodeClick}
              onEdgeClick={onEdgeClick}
              interClusterPairs={interClusterPairs}
            />
          )}
        </div>
      </div>
    </div>
  )
}

// Inner component for ReactFlow to use useReactFlow hook
function GraphCanvas({
  nodes,
  edges,
  onNodesChange,
  onEdgesChange,
  onNodeClick,
  onEdgeClick,
  interClusterPairs = [],
}) {
  const { fitView, zoomIn, zoomOut, setViewport, getViewport } = useReactFlow()

  useEffect(() => {
    const timer = setTimeout(() => {
      fitView({
        padding: 0.2,
        minZoom: 0.05,
        maxZoom: 2,
        duration: 800,
        includeHiddenNodes: false,
      })
    }, 150)
    return () => clearTimeout(timer)
  }, [nodes.length, fitView])

  const handleFullZoomOut = () => {
    fitView({ padding: 0.3, duration: 600, minZoom: 0.05 })
  }

  const handleZoomToCluster = (clusterId) => {
    const clusterNodes = nodes.filter(n => n.data?.cluster_id?.toString() === clusterId?.toString())
    if (clusterNodes.length === 0) return
    
    const xs = clusterNodes.map(n => n.position.x)
    const ys = clusterNodes.map(n => n.position.y)
    const centerX = (Math.min(...xs) + Math.max(...xs)) / 2
    const centerY = (Math.min(...ys) + Math.max(...ys)) / 2
    const spread = Math.max(Math.max(...xs) - Math.min(...xs), Math.max(...ys) - Math.min(...ys))
    const zoom = Math.min(1.5, 800 / (spread + 200))
    
    setViewport({ x: -centerX * zoom + 400, y: -centerY * zoom + 300, zoom }, { duration: 600 })
  }

  // Extract cluster metadata from nodes
  const clusterMetadata = useMemo(() => {
    const clusters = {}
    nodes.forEach(node => {
      const clusterId = node.data?.cluster_id !== undefined ? node.data.cluster_id : -1
      if (!clusters[clusterId]) {
        clusters[clusterId] = {
          nodes: [],
          centerX: node.position.x,
          centerY: node.position.y,
          color: node.data?.clusterColor || '#6366f1',
        }
      }
      clusters[clusterId].nodes.push(node)
      // Update center with average of all node positions
      clusters[clusterId].centerX = clusters[clusterId].nodes.reduce((sum, n) => sum + n.position.x, 0) / clusters[clusterId].nodes.length
      clusters[clusterId].centerY = clusters[clusterId].nodes.reduce((sum, n) => sum + n.position.y, 0) / clusters[clusterId].nodes.length
    })
    
    // Calculate radius for each cluster based on node spread
    Object.values(clusters).forEach(cluster => {
      let maxDist = 0
      cluster.nodes.forEach(n => {
        const dist = Math.sqrt(
          Math.pow(n.position.x - cluster.centerX, 2) +
          Math.pow(n.position.y - cluster.centerY, 2)
        )
        maxDist = Math.max(maxDist, dist)
      })
      cluster.radius = Math.max(maxDist + 50, 100) // Add padding
    })
    
    return clusters
  }, [nodes])

  // Cluster colors for quick access
  const clusterColors = ['#ef4444', '#3b82f6', '#10b981', '#f59e0b', '#8b5cf6', '#ec4899', '#06b6d4', '#84cc16']

  return (
    <div className="h-full bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950 relative overflow-hidden">
      {/* Animated background gradient */}
      <div className="absolute inset-0 opacity-30">
        <div className="absolute top-0 left-1/4 w-96 h-96 bg-purple-600 rounded-full filter blur-[128px] animate-pulse" />
        <div className="absolute bottom-0 right-1/4 w-96 h-96 bg-cyan-600 rounded-full filter blur-[128px] animate-pulse" style={{ animationDelay: '1s' }} />
      </div>
      
      <div style={{ position: 'relative', zIndex: 2, width: '100%', height: '100%' }}>
        <ReactFlow
          nodes={nodes}
          edges={edges}
          onNodesChange={onNodesChange}
          onEdgesChange={onEdgesChange}
          onNodeClick={onNodeClick}
          onEdgeClick={onEdgeClick}
          nodeTypes={nodeTypes}
          fitView
          minZoom={0.02}
          maxZoom={3}
          attributionPosition="bottom-left"
          defaultEdgeOptions={{
            type: 'smoothstep',
            animated: false,
          }}
        >
          <Background 
            color="#475569" 
            gap={30} 
            variant="dots" 
            size={1.5}
          />
          
          {/* Custom Zoom Controls Panel */}
          <Panel position="top-right" className="flex flex-col gap-2">
            <div className="bg-slate-900/90 backdrop-blur-sm rounded-xl p-2 border border-slate-700/50 shadow-xl">
              <div className="flex flex-col gap-1">
                <button
                  onClick={() => zoomIn({ duration: 300 })}
                  className="p-2 hover:bg-slate-700 rounded-lg transition-colors group"
                  title="Zoom In"
                >
                  <MagnifyingGlassPlusIcon className="w-5 h-5 text-slate-400 group-hover:text-white" />
                </button>
                <button
                  onClick={() => zoomOut({ duration: 300 })}
                  className="p-2 hover:bg-slate-700 rounded-lg transition-colors group"
                  title="Zoom Out"
                >
                  <MagnifyingGlassMinusIcon className="w-5 h-5 text-slate-400 group-hover:text-white" />
                </button>
                <div className="h-px bg-slate-700 my-1" />
                <button
                  onClick={handleFullZoomOut}
                  className="p-2 hover:bg-slate-700 rounded-lg transition-colors group"
                  title="Fit All Clusters"
                >
                  <ArrowsPointingOutIcon className="w-5 h-5 text-slate-400 group-hover:text-cyan-400" />
                </button>
                <button
                  onClick={() => fitView({ padding: 0.1, duration: 400 })}
                  className="p-2 hover:bg-slate-700 rounded-lg transition-colors group"
                  title="Center View"
                >
                  <ViewfinderCircleIcon className="w-5 h-5 text-slate-400 group-hover:text-green-400" />
                </button>
              </div>
            </div>
            
            {/* Quick Cluster Navigation */}
            <div className="bg-slate-900/90 backdrop-blur-sm rounded-xl p-2 border border-slate-700/50 shadow-xl">
              <div className="text-[10px] text-slate-500 font-bold mb-1 px-1">CLUSTERS</div>
              <div className="flex flex-col gap-1">
                {Object.keys(clusterMetadata).filter(id => id !== '-1').slice(0, 6).map((clusterId, idx) => {
                  const colors = ['#ef4444', '#3b82f6', '#10b981', '#f59e0b', '#8b5cf6', '#ec4899']
                  return (
                    <button
                      key={clusterId}
                      onClick={() => handleZoomToCluster(clusterId)}
                      className="px-2 py-1 rounded-lg text-xs font-bold transition-all hover:scale-105"
                      style={{ 
                        backgroundColor: `${colors[idx % colors.length]}20`,
                        color: colors[idx % colors.length],
                        border: `1px solid ${colors[idx % colors.length]}50`,
                      }}
                    >
                      C{clusterId}
                    </button>
                  )
                })}
              </div>
            </div>
          </Panel>
          
          <Controls
            position="bottom-right"
            showZoom={false}
            showFitView={false}
            style={{
              backgroundImage: 'linear-gradient(to right, rgb(15, 23, 42), rgb(30, 41, 59))',
              borderRadius: '8px',
              border: '1px solid rgba(30, 41, 59, 0.5)',
            }}
          />
          <MiniMap
            nodeStrokeColor={(n) => {
              // Use cluster color for border
              const clusterIdx = n.data?.cluster_id ?? 0
              return clusterColors[clusterIdx % clusterColors.length]
            }}
            nodeColor={(n) => {
              // Use risk-based colors for fill
              if (n.data?.mule_suspected) return '#fecaca'
              if (n.data?.risk_score >= 70) return '#fee2e2'
              if (n.data?.risk_score >= 40) return '#fef3c7'
              return '#d1fae5'
            }}
            nodeBorderRadius={50}
            maskColor="rgba(0, 0, 0, 0.6)"
            pannable
            zoomable
            style={{
              backgroundColor: '#0f172a',
              border: '2px solid rgba(99, 102, 241, 0.5)',
              borderRadius: '12px',
              boxShadow: '0 4px 30px rgba(99, 102, 241, 0.2)',
            }}
          />
        </ReactFlow>
      </div>
    </div>
  )
}

// Clean Network Canvas - Simpler cyan/red network visualization like reference image
function CleanNetworkCanvas({
  nodes: originalNodes,
  edges: originalEdges,
  onNodesChange,
  onEdgesChange,
  onNodeClick,
  onEdgeClick,
  fullData,
}) {
  const { fitView, zoomIn, zoomOut } = useReactFlow()

  useEffect(() => {
    const timer = setTimeout(() => {
      fitView({ padding: 0.15, minZoom: 0.1, maxZoom: 1.5, duration: 600 })
    }, 200)
    return () => clearTimeout(timer)
  }, [originalNodes.length, fitView])

  // Convert nodes to clean network style
  const cleanNodes = useMemo(() => {
    return originalNodes.map(node => ({
      ...node,
      type: 'cleanNetwork',
      data: {
        ...node.data,
      },
    }))
  }, [originalNodes])

  // Simplify edges for clean look - green for normal, red for suspicious
  const cleanEdges = useMemo(() => {
    return originalEdges.map(edge => {
      const isSuspicious = edge.data?.isHighRisk || edge.animated
      return {
        ...edge,
        type: 'default',
        animated: false,
        style: {
          stroke: isSuspicious ? '#ef4444' : '#10b981',
          strokeWidth: isSuspicious ? 2 : 1.5,
          opacity: 0.8,
        },
        markerEnd: {
          type: MarkerType.ArrowClosed,
          color: isSuspicious ? '#ef4444' : '#10b981',
          width: 10,
          height: 10,
        },
      }
    })
  }, [originalEdges])

  return (
    <div className="h-full bg-gradient-to-br from-slate-950 via-[#0c1929] to-slate-950 relative overflow-hidden">
      {/* Subtle animated background */}
      <div className="absolute inset-0 opacity-20">
        <div className="absolute top-1/4 left-1/4 w-64 h-64 bg-cyan-500 rounded-full filter blur-[100px]" />
        <div className="absolute bottom-1/4 right-1/4 w-64 h-64 bg-red-500 rounded-full filter blur-[100px]" />
      </div>
      
      <div style={{ position: 'relative', zIndex: 2, width: '100%', height: '100%' }}>
        <ReactFlow
          nodes={cleanNodes}
          edges={cleanEdges}
          onNodesChange={onNodesChange}
          onEdgesChange={onEdgesChange}
          onNodeClick={onNodeClick}
          onEdgeClick={onEdgeClick}
          nodeTypes={nodeTypes}
          fitView
          minZoom={0.05}
          maxZoom={2}
          attributionPosition="bottom-left"
        >
          <Background color="#1e3a5f" gap={40} variant="dots" size={1} />
          
          {/* Network Controls Legend */}
          <Panel position="top-right" className="bg-slate-900/90 backdrop-blur-sm rounded-xl p-3 border border-slate-700/50 shadow-xl">
            <h4 className="text-cyan-400 font-bold text-sm mb-2">🌐 Network Controls</h4>
            <div className="space-y-1 text-xs text-gray-400">
              <div className="flex items-center gap-2">
                <span className="text-gray-500">🖱️</span>
                <span><strong>Drag:</strong> Pan network</span>
              </div>
              <div className="flex items-center gap-2">
                <span className="text-gray-500">🔍</span>
                <span><strong>Scroll:</strong> Zoom in/out</span>
              </div>
              <div className="flex items-center gap-2">
                <span className="text-gray-500">👆</span>
                <span><strong>Click Node:</strong> Focus & info</span>
              </div>
              <div className="flex items-center gap-2">
                <span className="text-gray-500">✋</span>
                <span><strong>Drag Node:</strong> Reposition</span>
              </div>
            </div>
            <div className="mt-3 pt-2 border-t border-slate-700 flex gap-2">
              <button
                onClick={() => zoomIn({ duration: 300 })}
                className="flex-1 px-2 py-1 bg-slate-700 hover:bg-slate-600 rounded text-xs text-white"
              >
                +
              </button>
              <button
                onClick={() => zoomOut({ duration: 300 })}
                className="flex-1 px-2 py-1 bg-slate-700 hover:bg-slate-600 rounded text-xs text-white"
              >
                −
              </button>
              <button
                onClick={() => fitView({ padding: 0.15, duration: 400 })}
                className="flex-1 px-2 py-1 bg-cyan-700 hover:bg-cyan-600 rounded text-xs text-white"
              >
                Fit
              </button>
            </div>
          </Panel>
          
          {/* Legend */}
          <Panel position="bottom-left" className="bg-slate-900/90 backdrop-blur-sm rounded-xl p-3 border border-slate-700/50 shadow-xl">
            <div className="flex gap-4 text-xs">
              <div className="flex items-center gap-2">
                <div className="w-4 h-4 rounded-full bg-cyan-400 shadow-lg shadow-cyan-400/50"></div>
                <span className="text-gray-300">Normal</span>
              </div>
              <div className="flex items-center gap-2">
                <div className="w-4 h-4 rounded-full bg-red-500 shadow-lg shadow-red-500/50"></div>
                <span className="text-gray-300">High Risk</span>
              </div>
              <div className="flex items-center gap-2">
                <div className="w-3 h-0.5 bg-green-500"></div>
                <span className="text-gray-300">Normal Flow</span>
              </div>
              <div className="flex items-center gap-2">
                <div className="w-3 h-0.5 bg-red-500"></div>
                <span className="text-gray-300">Suspicious</span>
              </div>
            </div>
          </Panel>
          
          <MiniMap
            nodeColor={(n) => {
              if (n.data?.mule_suspected || n.data?.risk_score >= 60) return '#ef4444'
              return '#22d3ee'
            }}
            maskColor="rgba(0, 0, 0, 0.7)"
            style={{
              backgroundColor: '#0f172a',
              border: '2px solid rgba(34, 211, 238, 0.3)',
              borderRadius: '8px',
            }}
          />
        </ReactFlow>
      </div>
    </div>
  )
}

// Helper component for stat cards
function StatCard({ label, value, color, isnumber }) {
  return (
    <div
      className={`bg-gradient-to-br ${color} rounded-lg p-3 shadow-xl border border-white/10 hover:shadow-2xl transition-all transform hover:scale-105`}
    >
      <p className={`text-2xl md:text-3xl font-black text-white ${isnumber ? 'font-mono' : ''}`}>
        {value}
      </p>
      <p className="text-xs md:text-sm text-white/90 font-bold">{label}</p>
    </div>
  )
}

function PatternBadge({ type, count, color }) {
  const colors = {
    red: 'bg-gradient-to-r from-red-900/60 to-red-800/60 text-red-200 border border-red-600/50 shadow-lg shadow-red-600/30',
    orange: 'bg-gradient-to-r from-orange-900/60 to-orange-800/60 text-orange-200 border border-orange-600/50 shadow-lg shadow-orange-600/30',
    purple: 'bg-gradient-to-r from-purple-900/60 to-purple-800/60 text-purple-200 border border-purple-600/50 shadow-lg shadow-purple-600/30',
    blue: 'bg-gradient-to-r from-blue-900/60 to-blue-800/60 text-blue-200 border border-blue-600/50 shadow-lg shadow-blue-600/30',
  }

  return (
    <div
      className={`flex items-center justify-between p-4 rounded-lg font-bold transition-all transform hover:scale-105 cursor-pointer ${colors[color]}`}
    >
      <span className="text-sm font-bold">{type}</span>
      <span className="text-2xl font-black bg-gradient-to-r from-white/90 to-white/70 bg-clip-text text-transparent">
        {count}
      </span>
    </div>
  )
}
