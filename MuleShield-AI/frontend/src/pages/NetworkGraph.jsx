/**
 * MuleShield AI - Network Graph Page
 * Interactive visualization of transaction networks using ReactFlow
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
} from 'reactflow'
import 'reactflow/dist/style.css'
import { graphApi } from '../api'
import {
  AdjustmentsHorizontalIcon,
  MagnifyingGlassIcon,
  ArrowPathIcon,
  ExclamationTriangleIcon,
} from '@heroicons/react/24/outline'

// Custom node component
const AccountNode = ({ data }) => {
  const riskColor = data.risk_score >= 70 ? '#ef4444' :
                    data.risk_score >= 40 ? '#f59e0b' : '#22c55e'
  const borderColor = data.highlighted ? '#0ea5e9' : riskColor

  return (
    <div
      className={`px-4 py-3 rounded-lg bg-white shadow-lg border-2 min-w-[150px] ${
        data.mule_suspected ? 'ring-2 ring-red-500 ring-offset-2' : ''
      }`}
      style={{ borderColor }}
    >
      <div className="flex items-center gap-2 mb-2">
        {data.mule_suspected && (
          <ExclamationTriangleIcon className="h-4 w-4 text-red-500" />
        )}
        <span className="font-semibold text-gray-900 text-sm truncate">
          {data.label}
        </span>
      </div>
      <div className="space-y-1 text-xs">
        <div className="flex justify-between">
          <span className="text-gray-500">Risk:</span>
          <span className="font-medium" style={{ color: riskColor }}>
            {data.risk_score?.toFixed(0) || 0}
          </span>
        </div>
        <div className="flex justify-between">
          <span className="text-gray-500">Mule Prob:</span>
          <span className="font-medium">
            {((data.mule_probability || 0) * 100).toFixed(0)}%
          </span>
        </div>
        {data.cluster_id !== undefined && (
          <div className="flex justify-between">
            <span className="text-gray-500">Cluster:</span>
            <span className="font-medium">{data.cluster_id}</span>
          </div>
        )}
      </div>
    </div>
  )
}

const nodeTypes = { account: AccountNode }

export default function NetworkGraph() {
  const [searchParams] = useSearchParams()
  const highlightId = searchParams.get('highlight')

  const [fullData, setFullData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [nodes, setNodes, onNodesChange] = useNodesState([])
  const [edges, setEdges, onEdgesChange] = useEdgesState([])
  const [selectedNode, setSelectedNode] = useState(null)
  const [filters, setFilters] = useState({
    showMuleOnly: false,
    minRiskScore: 0,
    cluster: '',
  })
  const [patterns, setPatterns] = useState(null)

  useEffect(() => {
    fetchGraphData()
    fetchPatterns()
  }, [])

  const fetchGraphData = async () => {
    setLoading(true)
    try {
      const response = await graphApi.getFullNetwork()
      setFullData(response.data)
      processGraphData(response.data)
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

    // Convert to ReactFlow format
    const flowNodes = data.nodes
      .filter(node => {
        if (filters.showMuleOnly && !node.mule_suspected) return false
        if (node.risk_score < filters.minRiskScore) return false
        if (filters.cluster && node.cluster_id !== parseInt(filters.cluster)) return false
        return true
      })
      .map((node, index) => ({
        id: node.id.toString(),
        type: 'account',
        position: {
          x: (index % 8) * 220 + Math.random() * 50,
          y: Math.floor(index / 8) * 180 + Math.random() * 50,
        },
        data: {
          ...node,
          label: node.name || `Account ${node.id}`,
          highlighted: highlightId && node.id.toString() === highlightId,
        },
      }))

    const nodeIds = new Set(flowNodes.map(n => n.id))
    const flowEdges = data.edges
      .filter(edge =>
        nodeIds.has(edge.source.toString()) &&
        nodeIds.has(edge.target.toString())
      )
      .map((edge, index) => ({
        id: `e${index}`,
        source: edge.source.toString(),
        target: edge.target.toString(),
        animated: edge.suspicious,
        style: {
          stroke: edge.suspicious ? '#ef4444' : '#94a3b8',
          strokeWidth: Math.min(edge.weight || 1, 4),
        },
        markerEnd: {
          type: MarkerType.ArrowClosed,
          color: edge.suspicious ? '#ef4444' : '#94a3b8',
        },
        label: edge.amount ? `$${edge.amount.toLocaleString()}` : undefined,
        labelStyle: { fontSize: 10 },
      }))

    setNodes(flowNodes)
    setEdges(flowEdges)
  }, [filters, highlightId, setNodes, setEdges])

  useEffect(() => {
    if (fullData) {
      processGraphData(fullData)
    }
  }, [filters, fullData, processGraphData])

  const onNodeClick = useCallback((event, node) => {
    setSelectedNode(node.data)
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
    return {
      totalNodes: fullData.nodes?.length || 0,
      totalEdges: fullData.edges?.length || 0,
      muleAccounts: fullData.nodes?.filter(n => n.mule_suspected).length || 0,
      highRiskAccounts: fullData.nodes?.filter(n => n.risk_score >= 70).length || 0,
      clusters: clusters.length,
    }
  }, [fullData, clusters])

  if (loading) {
    return (
      <div className="flex items-center justify-center h-[600px]">
        <div className="spinner" />
        <span className="ml-3 text-gray-600">Loading network graph...</span>
      </div>
    )
  }

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Network Graph</h1>
          <p className="text-gray-600">Interactive visualization of transaction networks</p>
        </div>
        <button
          onClick={fetchGraphData}
          className="btn btn-secondary flex items-center gap-2"
        >
          <ArrowPathIcon className="h-5 w-5" />
          Refresh
        </button>
      </div>

      {/* Stats Bar */}
      {stats && (
        <div className="grid grid-cols-5 gap-4">
          <div className="bg-blue-50 rounded-lg p-3 text-center">
            <p className="text-2xl font-bold text-blue-600">{stats.totalNodes}</p>
            <p className="text-sm text-blue-700">Total Accounts</p>
          </div>
          <div className="bg-gray-50 rounded-lg p-3 text-center">
            <p className="text-2xl font-bold text-gray-600">{stats.totalEdges}</p>
            <p className="text-sm text-gray-700">Connections</p>
          </div>
          <div className="bg-red-50 rounded-lg p-3 text-center">
            <p className="text-2xl font-bold text-red-600">{stats.muleAccounts}</p>
            <p className="text-sm text-red-700">Suspected Mules</p>
          </div>
          <div className="bg-yellow-50 rounded-lg p-3 text-center">
            <p className="text-2xl font-bold text-yellow-600">{stats.highRiskAccounts}</p>
            <p className="text-sm text-yellow-700">High Risk</p>
          </div>
          <div className="bg-purple-50 rounded-lg p-3 text-center">
            <p className="text-2xl font-bold text-purple-600">{stats.clusters}</p>
            <p className="text-sm text-purple-700">Clusters</p>
          </div>
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-4 gap-4">
        {/* Filters Sidebar */}
        <div className="lg:col-span-1 space-y-4">
          {/* Filters */}
          <div className="card">
            <div className="card-header">
              <h3 className="font-medium flex items-center gap-2">
                <AdjustmentsHorizontalIcon className="h-5 w-5" />
                Filters
              </h3>
            </div>
            <div className="card-body space-y-4">
              <label className="flex items-center gap-2">
                <input
                  type="checkbox"
                  checked={filters.showMuleOnly}
                  onChange={(e) => setFilters(prev => ({ ...prev, showMuleOnly: e.target.checked }))}
                  className="rounded border-gray-300 text-mule-600 focus:ring-mule-500"
                />
                <span className="text-sm text-gray-700">Show mule accounts only</span>
              </label>

              <div>
                <label className="text-sm text-gray-700 block mb-1">
                  Min Risk Score: {filters.minRiskScore}
                </label>
                <input
                  type="range"
                  min="0"
                  max="100"
                  value={filters.minRiskScore}
                  onChange={(e) => setFilters(prev => ({ ...prev, minRiskScore: parseInt(e.target.value) }))}
                  className="w-full"
                />
              </div>

              <div>
                <label className="text-sm text-gray-700 block mb-1">Cluster</label>
                <select
                  value={filters.cluster}
                  onChange={(e) => setFilters(prev => ({ ...prev, cluster: e.target.value }))}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                >
                  <option value="">All Clusters</option>
                  {clusters.map(c => (
                    <option key={c} value={c}>Cluster {c}</option>
                  ))}
                </select>
              </div>
            </div>
          </div>

          {/* Detected Patterns */}
          <div className="card">
            <div className="card-header">
              <h3 className="font-medium">Detected Patterns</h3>
            </div>
            <div className="card-body space-y-3">
              {patterns?.circular?.patterns?.length > 0 && (
                <PatternBadge
                  type="Circular Flows"
                  count={patterns.circular.patterns.length}
                  color="red"
                />
              )}
              {patterns?.hubSpoke?.hubs?.length > 0 && (
                <PatternBadge
                  type="Hub-Spoke"
                  count={patterns.hubSpoke.hubs.length}
                  color="yellow"
                />
              )}
              {patterns?.dispersal?.dispersal_patterns?.length > 0 && (
                <PatternBadge
                  type="Rapid Dispersal"
                  count={patterns.dispersal.dispersal_patterns.length}
                  color="purple"
                />
              )}
              {patterns?.device?.clusters?.length > 0 && (
                <PatternBadge
                  type="Device Clusters"
                  count={patterns.device.clusters.length}
                  color="blue"
                />
              )}
              {!patterns?.circular?.patterns?.length &&
               !patterns?.hubSpoke?.hubs?.length &&
               !patterns?.dispersal?.dispersal_patterns?.length &&
               !patterns?.device?.clusters?.length && (
                <p className="text-sm text-gray-500">No suspicious patterns detected</p>
              )}
            </div>
          </div>

          {/* Selected Node Info */}
          {selectedNode && (
            <div className="card">
              <div className="card-header">
                <h3 className="font-medium">Selected Account</h3>
              </div>
              <div className="card-body space-y-2">
                <p className="font-medium text-gray-900">{selectedNode.label}</p>
                <div className="text-sm space-y-1">
                  <p className="flex justify-between">
                    <span className="text-gray-500">Risk Score:</span>
                    <span className={`font-medium ${
                      selectedNode.risk_score >= 70 ? 'text-red-600' :
                      selectedNode.risk_score >= 40 ? 'text-yellow-600' : 'text-green-600'
                    }`}>
                      {selectedNode.risk_score?.toFixed(1)}
                    </span>
                  </p>
                  <p className="flex justify-between">
                    <span className="text-gray-500">Mule Probability:</span>
                    <span className="font-medium">
                      {((selectedNode.mule_probability || 0) * 100).toFixed(0)}%
                    </span>
                  </p>
                  {selectedNode.cluster_id !== undefined && (
                    <p className="flex justify-between">
                      <span className="text-gray-500">Cluster:</span>
                      <span className="font-medium">{selectedNode.cluster_id}</span>
                    </p>
                  )}
                </div>
                <a
                  href={`/accounts/${selectedNode.id}`}
                  className="btn btn-primary w-full mt-3 text-sm"
                >
                  View Full Profile
                </a>
              </div>
            </div>
          )}

          {/* Legend */}
          <div className="card">
            <div className="card-header">
              <h3 className="font-medium">Legend</h3>
            </div>
            <div className="card-body space-y-2 text-sm">
              <div className="flex items-center gap-2">
                <div className="w-4 h-4 rounded border-2 border-green-500" />
                <span>Low Risk (&lt;40)</span>
              </div>
              <div className="flex items-center gap-2">
                <div className="w-4 h-4 rounded border-2 border-yellow-500" />
                <span>Medium Risk (40-70)</span>
              </div>
              <div className="flex items-center gap-2">
                <div className="w-4 h-4 rounded border-2 border-red-500" />
                <span>High Risk (&gt;70)</span>
              </div>
              <div className="flex items-center gap-2">
                <div className="w-4 h-4 rounded border-2 border-sky-500 ring-2 ring-sky-500 ring-offset-1" />
                <span>Highlighted</span>
              </div>
              <div className="flex items-center gap-2">
                <div className="w-4 h-0.5 bg-red-500" />
                <span className="text-red-600">Suspicious Flow</span>
              </div>
            </div>
          </div>
        </div>

        {/* Graph */}
        <div className="lg:col-span-3 card h-[700px]">
          <ReactFlow
            nodes={nodes}
            edges={edges}
            onNodesChange={onNodesChange}
            onEdgesChange={onEdgesChange}
            onNodeClick={onNodeClick}
            nodeTypes={nodeTypes}
            fitView
            attributionPosition="bottom-left"
          >
            <Background color="#e2e8f0" gap={16} />
            <Controls />
            <MiniMap
              nodeStrokeColor={(n) => {
                if (n.data?.risk_score >= 70) return '#ef4444'
                if (n.data?.risk_score >= 40) return '#f59e0b'
                return '#22c55e'
              }}
              nodeColor={(n) => {
                if (n.data?.mule_suspected) return '#fecaca'
                return '#f1f5f9'
              }}
            />
          </ReactFlow>
        </div>
      </div>
    </div>
  )
}

function PatternBadge({ type, count, color }) {
  const colors = {
    red: 'bg-red-100 text-red-800',
    yellow: 'bg-yellow-100 text-yellow-800',
    purple: 'bg-purple-100 text-purple-800',
    blue: 'bg-blue-100 text-blue-800',
  }

  return (
    <div className={`flex items-center justify-between p-2 rounded-lg ${colors[color]}`}>
      <span className="text-sm font-medium">{type}</span>
      <span className="text-sm font-bold">{count}</span>
    </div>
  )
}
