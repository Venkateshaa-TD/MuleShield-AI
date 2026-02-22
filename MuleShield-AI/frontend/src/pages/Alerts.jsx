/**
 * MuleShield AI - Alerts Page
 * View and manage AML alerts with prioritization
 */

import { useState, useEffect } from 'react'
import { Link, useSearchParams } from 'react-router-dom'
import { alertsApi } from '../api'
import {
  ExclamationTriangleIcon,
  CheckCircleIcon,
  XCircleIcon,
  ClockIcon,
  FunnelIcon,
  MagnifyingGlassIcon,
} from '@heroicons/react/24/outline'

export default function Alerts() {
  const [searchParams] = useSearchParams()
  const [alerts, setAlerts] = useState([])
  const [loading, setLoading] = useState(true)
  const [filters, setFilters] = useState({
    status: searchParams.get('status') || '',
    severity: '',
    alert_type: '',
  })
  const [selectedAlerts, setSelectedAlerts] = useState([])

  useEffect(() => {
    fetchAlerts()
  }, [filters])

  const fetchAlerts = async () => {
    setLoading(true)
    try {
      const response = await alertsApi.getList(filters)
      setAlerts(response.data)
    } catch (error) {
      console.error('Failed to fetch alerts:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleStatusUpdate = async (alertId, newStatus) => {
    try {
      await alertsApi.updateStatus(alertId, {
        status: newStatus,
        investigator_notes: `Status updated to ${newStatus}`,
      })
      fetchAlerts()
    } catch (error) {
      console.error('Failed to update alert status:', error)
    }
  }

  const handleBulkStatusUpdate = async (newStatus) => {
    try {
      await Promise.all(
        selectedAlerts.map(id =>
          alertsApi.updateStatus(id, {
            status: newStatus,
            investigator_notes: `Bulk status update to ${newStatus}`,
          })
        )
      )
      setSelectedAlerts([])
      fetchAlerts()
    } catch (error) {
      console.error('Failed to bulk update alerts:', error)
    }
  }

  const toggleSelectAll = () => {
    if (selectedAlerts.length === alerts.length) {
      setSelectedAlerts([])
    } else {
      setSelectedAlerts(alerts.map(a => a.id))
    }
  }

  const toggleSelectAlert = (id) => {
    setSelectedAlerts(prev =>
      prev.includes(id) ? prev.filter(a => a !== id) : [...prev, id]
    )
  }

  const getSeverityIcon = (severity) => {
    switch (severity) {
      case 'critical':
        return <XCircleIcon className="h-5 w-5 text-red-600" />
      case 'high':
        return <ExclamationTriangleIcon className="h-5 w-5 text-red-500" />
      case 'medium':
        return <ExclamationTriangleIcon className="h-5 w-5 text-yellow-500" />
      default:
        return <ClockIcon className="h-5 w-5 text-green-500" />
    }
  }

  const getStatusBadge = (status) => {
    const styles = {
      open: 'bg-red-100 text-red-800',
      investigating: 'bg-yellow-100 text-yellow-800',
      resolved: 'bg-green-100 text-green-800',
      escalated: 'bg-purple-100 text-purple-800',
      false_positive: 'bg-gray-100 text-gray-800',
    }
    return (
      <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${styles[status] || styles.open}`}>
        {status?.replace('_', ' ')}
      </span>
    )
  }

  // Summary stats
  const openCount = alerts.filter(a => a.status === 'open').length
  const criticalCount = alerts.filter(a => a.severity === 'critical' || a.severity === 'high').length
  const investigatingCount = alerts.filter(a => a.status === 'investigating').length

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Alerts</h1>
          <p className="text-gray-600">Monitor and investigate AML alerts</p>
        </div>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="bg-red-50 rounded-lg p-4">
          <div className="flex items-center gap-3">
            <ExclamationTriangleIcon className="h-8 w-8 text-red-600" />
            <div>
              <p className="text-2xl font-bold text-red-900">{openCount}</p>
              <p className="text-sm text-red-600">Open Alerts</p>
            </div>
          </div>
        </div>
        <div className="bg-yellow-50 rounded-lg p-4">
          <div className="flex items-center gap-3">
            <ClockIcon className="h-8 w-8 text-yellow-600" />
            <div>
              <p className="text-2xl font-bold text-yellow-900">{investigatingCount}</p>
              <p className="text-sm text-yellow-600">Under Investigation</p>
            </div>
          </div>
        </div>
        <div className="bg-purple-50 rounded-lg p-4">
          <div className="flex items-center gap-3">
            <XCircleIcon className="h-8 w-8 text-purple-600" />
            <div>
              <p className="text-2xl font-bold text-purple-900">{criticalCount}</p>
              <p className="text-sm text-purple-600">Critical/High Risk</p>
            </div>
          </div>
        </div>
      </div>

      {/* Filters & Bulk Actions */}
      <div className="card">
        <div className="card-body">
          <div className="flex flex-wrap items-center justify-between gap-4">
            <div className="flex flex-wrap items-center gap-4">
              <div className="flex items-center gap-2">
                <FunnelIcon className="h-5 w-5 text-gray-500" />
                <span className="font-medium text-gray-700">Filters:</span>
              </div>

              <select
                value={filters.status}
                onChange={(e) => setFilters(prev => ({ ...prev, status: e.target.value }))}
                className="px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-mule-500"
              >
                <option value="">All Status</option>
                <option value="open">Open</option>
                <option value="investigating">Investigating</option>
                <option value="resolved">Resolved</option>
                <option value="escalated">Escalated</option>
                <option value="false_positive">False Positive</option>
              </select>

              <select
                value={filters.severity}
                onChange={(e) => setFilters(prev => ({ ...prev, severity: e.target.value }))}
                className="px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-mule-500"
              >
                <option value="">All Severity</option>
                <option value="critical">Critical</option>
                <option value="high">High</option>
                <option value="medium">Medium</option>
                <option value="low">Low</option>
              </select>

              <select
                value={filters.alert_type}
                onChange={(e) => setFilters(prev => ({ ...prev, alert_type: e.target.value }))}
                className="px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-mule-500"
              >
                <option value="">All Types</option>
                <option value="mule_suspicion">Mule Suspicion</option>
                <option value="circular_flow">Circular Flow</option>
                <option value="hub_spoke">Hub-Spoke Pattern</option>
                <option value="rapid_dispersal">Rapid Dispersal</option>
                <option value="device_cluster">Device Cluster</option>
                <option value="behavioral_anomaly">Behavioral Anomaly</option>
              </select>
            </div>

            {/* Bulk Actions */}
            {selectedAlerts.length > 0 && (
              <div className="flex items-center gap-2">
                <span className="text-sm text-gray-600">{selectedAlerts.length} selected</span>
                <button
                  onClick={() => handleBulkStatusUpdate('investigating')}
                  className="btn btn-secondary text-sm"
                >
                  Mark Investigating
                </button>
                <button
                  onClick={() => handleBulkStatusUpdate('resolved')}
                  className="btn btn-primary text-sm"
                >
                  Mark Resolved
                </button>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Alerts Table */}
      <div className="card overflow-hidden">
        {loading ? (
          <div className="flex items-center justify-center h-64">
            <div className="spinner" />
            <span className="ml-3 text-gray-600">Loading alerts...</span>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="data-table">
              <thead>
                <tr>
                  <th className="w-8">
                    <input
                      type="checkbox"
                      checked={selectedAlerts.length === alerts.length && alerts.length > 0}
                      onChange={toggleSelectAll}
                      className="rounded border-gray-300 text-mule-600 focus:ring-mule-500"
                    />
                  </th>
                  <th>Severity</th>
                  <th>Alert Type</th>
                  <th>Account</th>
                  <th>Risk Score</th>
                  <th>Description</th>
                  <th>Status</th>
                  <th>Created</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {alerts.map((alert) => (
                  <tr
                    key={alert.id}
                    className={`hover:bg-gray-50 ${
                      alert.severity === 'critical' || alert.severity === 'high'
                        ? 'bg-red-50/50'
                        : ''
                    }`}
                  >
                    <td>
                      <input
                        type="checkbox"
                        checked={selectedAlerts.includes(alert.id)}
                        onChange={() => toggleSelectAlert(alert.id)}
                        className="rounded border-gray-300 text-mule-600 focus:ring-mule-500"
                      />
                    </td>
                    <td>
                      <div className="flex items-center gap-2">
                        {getSeverityIcon(alert.severity)}
                        <span className="capitalize font-medium">{alert.severity}</span>
                      </div>
                    </td>
                    <td>
                      <span className="text-sm">{alert.alert_type?.replace(/_/g, ' ')}</span>
                    </td>
                    <td>
                      <Link
                        to={`/accounts/${alert.account_id}`}
                        className="text-mule-600 hover:text-mule-700 font-medium"
                      >
                        {alert.account_name || `Account #${alert.account_id}`}
                      </Link>
                    </td>
                    <td>
                      <span className={`font-bold ${
                        alert.risk_score >= 70 ? 'text-red-600' :
                        alert.risk_score >= 40 ? 'text-yellow-600' : 'text-green-600'
                      }`}>
                        {alert.risk_score?.toFixed(1)}
                      </span>
                    </td>
                    <td className="max-w-xs truncate text-sm text-gray-600">
                      {alert.description}
                    </td>
                    <td>{getStatusBadge(alert.status)}</td>
                    <td className="text-sm text-gray-500">
                      {new Date(alert.created_at).toLocaleDateString()}
                    </td>
                    <td>
                      <div className="flex items-center gap-2">
                        <Link
                          to={`/alerts/${alert.id}`}
                          className="btn btn-secondary text-sm"
                        >
                          View
                        </Link>
                        {alert.status === 'open' && (
                          <button
                            onClick={() => handleStatusUpdate(alert.id, 'investigating')}
                            className="btn btn-primary text-sm"
                          >
                            Investigate
                          </button>
                        )}
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        {!loading && alerts.length === 0 && (
          <div className="text-center py-12">
            <CheckCircleIcon className="h-12 w-12 text-green-500 mx-auto mb-4" />
            <h3 className="text-lg font-medium text-gray-900">No alerts found</h3>
            <p className="text-gray-600">All clear! No alerts match your current filters.</p>
          </div>
        )}
      </div>
    </div>
  )
}
