/**
 * MuleShield AI - Cases Page
 * Case management for AML investigations
 */

import { useState, useEffect } from 'react'
import { Link, useSearchParams } from 'react-router-dom'
import { casesApi, alertsApi } from '../api'
import {
  PlusIcon,
  FunnelIcon,
  FolderIcon,
  ClockIcon,
  CheckCircleIcon,
  XCircleIcon,
  UserIcon,
} from '@heroicons/react/24/outline'

export default function Cases() {
  const [searchParams] = useSearchParams()
  const [cases, setCases] = useState([])
  const [loading, setLoading] = useState(true)
  const [showCreateModal, setShowCreateModal] = useState(searchParams.get('create') === 'true')
  const [filters, setFilters] = useState({
    status: '',
    priority: '',
  })

  // Create case form state
  const [newCase, setNewCase] = useState({
    title: '',
    description: '',
    priority: 'medium',
    assigned_to: '',
    related_alert_ids: searchParams.get('alert_id') ? [parseInt(searchParams.get('alert_id'))] : [],
    related_account_ids: searchParams.get('account_id') ? [parseInt(searchParams.get('account_id'))] : [],
  })
  const [creating, setCreating] = useState(false)

  useEffect(() => {
    fetchCases()
  }, [filters])

  const fetchCases = async () => {
    setLoading(true)
    try {
      const response = await casesApi.getList(filters)
      setCases(response.data)
    } catch (error) {
      console.error('Failed to fetch cases:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleCreateCase = async () => {
    if (!newCase.title) return

    setCreating(true)
    try {
      await casesApi.create(newCase)
      setShowCreateModal(false)
      setNewCase({
        title: '',
        description: '',
        priority: 'medium',
        assigned_to: '',
        related_alert_ids: [],
        related_account_ids: [],
      })
      fetchCases()
    } catch (error) {
      console.error('Failed to create case:', error)
    } finally {
      setCreating(false)
    }
  }

  const handleStatusUpdate = async (caseId, newStatus) => {
    try {
      await casesApi.update(caseId, { status: newStatus })
      fetchCases()
    } catch (error) {
      console.error('Failed to update case:', error)
    }
  }

  const getStatusBadge = (status) => {
    const styles = {
      open: 'bg-blue-100 text-blue-800',
      investigating: 'bg-yellow-100 text-yellow-800',
      pending_review: 'bg-purple-100 text-purple-800',
      closed_confirmed: 'bg-red-100 text-red-800',
      closed_false_positive: 'bg-green-100 text-green-800',
    }
    return (
      <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${styles[status] || styles.open}`}>
        {status?.replace(/_/g, ' ')}
      </span>
    )
  }

  const getPriorityBadge = (priority) => {
    const styles = {
      critical: 'bg-red-100 text-red-800 border border-red-200',
      high: 'bg-orange-100 text-orange-800 border border-orange-200',
      medium: 'bg-yellow-100 text-yellow-800 border border-yellow-200',
      low: 'bg-gray-100 text-gray-800 border border-gray-200',
    }
    return (
      <span className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium ${styles[priority] || styles.medium}`}>
        {priority}
      </span>
    )
  }

  // Stats
  const stats = {
    total: cases.length,
    open: cases.filter(c => c.status === 'open').length,
    investigating: cases.filter(c => c.status === 'investigating').length,
    closed: cases.filter(c => c.status?.startsWith('closed')).length,
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Cases</h1>
          <p className="text-gray-600">Manage AML investigation cases</p>
        </div>
        <button
          onClick={() => setShowCreateModal(true)}
          className="btn btn-primary flex items-center gap-2"
        >
          <PlusIcon className="h-5 w-5" />
          Create Case
        </button>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-4 gap-4">
        <StatCard
          icon={FolderIcon}
          label="Total Cases"
          value={stats.total}
          color="blue"
        />
        <StatCard
          icon={ClockIcon}
          label="Open"
          value={stats.open}
          color="yellow"
        />
        <StatCard
          icon={UserIcon}
          label="Investigating"
          value={stats.investigating}
          color="purple"
        />
        <StatCard
          icon={CheckCircleIcon}
          label="Closed"
          value={stats.closed}
          color="green"
        />
      </div>

      {/* Filters */}
      <div className="card">
        <div className="card-body">
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
              <option value="pending_review">Pending Review</option>
              <option value="closed_confirmed">Closed (Confirmed)</option>
              <option value="closed_false_positive">Closed (False Positive)</option>
            </select>

            <select
              value={filters.priority}
              onChange={(e) => setFilters(prev => ({ ...prev, priority: e.target.value }))}
              className="px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-mule-500"
            >
              <option value="">All Priorities</option>
              <option value="critical">Critical</option>
              <option value="high">High</option>
              <option value="medium">Medium</option>
              <option value="low">Low</option>
            </select>
          </div>
        </div>
      </div>

      {/* Cases List */}
      <div className="space-y-4">
        {loading ? (
          <div className="flex items-center justify-center h-64">
            <div className="spinner" />
            <span className="ml-3 text-gray-600">Loading cases...</span>
          </div>
        ) : cases.length === 0 ? (
          <div className="card">
            <div className="card-body text-center py-12">
              <FolderIcon className="h-12 w-12 text-gray-400 mx-auto mb-4" />
              <h3 className="text-lg font-medium text-gray-900">No cases found</h3>
              <p className="text-gray-600 mb-4">Create a new case to start tracking investigations</p>
              <button
                onClick={() => setShowCreateModal(true)}
                className="btn btn-primary"
              >
                Create Case
              </button>
            </div>
          </div>
        ) : (
          cases.map((caseItem) => (
            <div key={caseItem.id} className="card hover:shadow-md transition-shadow">
              <div className="card-body">
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <div className="flex items-center gap-3 mb-2">
                      <h3 className="text-lg font-semibold text-gray-900">
                        {caseItem.title}
                      </h3>
                      {getPriorityBadge(caseItem.priority)}
                      {getStatusBadge(caseItem.status)}
                    </div>
                    <p className="text-gray-600 mb-3 line-clamp-2">
                      {caseItem.description || 'No description provided'}
                    </p>
                    <div className="flex flex-wrap items-center gap-4 text-sm text-gray-500">
                      <span>Case #{caseItem.id}</span>
                      <span>Created: {new Date(caseItem.created_at).toLocaleDateString()}</span>
                      {caseItem.assigned_to && (
                        <span className="flex items-center gap-1">
                          <UserIcon className="h-4 w-4" />
                          {caseItem.assigned_to}
                        </span>
                      )}
                      {caseItem.related_alerts_count > 0 && (
                        <span>{caseItem.related_alerts_count} related alerts</span>
                      )}
                    </div>
                  </div>
                  <div className="flex items-center gap-2 ml-4">
                    <Link
                      to={`/cases/${caseItem.id}`}
                      className="btn btn-secondary text-sm"
                    >
                      View
                    </Link>
                    {caseItem.status === 'open' && (
                      <button
                        onClick={() => handleStatusUpdate(caseItem.id, 'investigating')}
                        className="btn btn-primary text-sm"
                      >
                        Start
                      </button>
                    )}
                  </div>
                </div>
              </div>
            </div>
          ))
        )}
      </div>

      {/* Create Case Modal */}
      {showCreateModal && (
        <div className="fixed inset-0 z-50 overflow-y-auto">
          <div className="flex items-center justify-center min-h-screen px-4">
            <div
              className="fixed inset-0 bg-black bg-opacity-50"
              onClick={() => setShowCreateModal(false)}
            />
            <div className="relative bg-white rounded-lg shadow-xl max-w-lg w-full p-6">
              <h2 className="text-xl font-bold text-gray-900 mb-4">Create New Case</h2>

              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Title *
                  </label>
                  <input
                    type="text"
                    value={newCase.title}
                    onChange={(e) => setNewCase(prev => ({ ...prev, title: e.target.value }))}
                    placeholder="Enter case title..."
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-mule-500"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Description
                  </label>
                  <textarea
                    value={newCase.description}
                    onChange={(e) => setNewCase(prev => ({ ...prev, description: e.target.value }))}
                    placeholder="Describe the case..."
                    rows={3}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-mule-500"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Priority
                  </label>
                  <select
                    value={newCase.priority}
                    onChange={(e) => setNewCase(prev => ({ ...prev, priority: e.target.value }))}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-mule-500"
                  >
                    <option value="low">Low</option>
                    <option value="medium">Medium</option>
                    <option value="high">High</option>
                    <option value="critical">Critical</option>
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Assigned To
                  </label>
                  <input
                    type="text"
                    value={newCase.assigned_to}
                    onChange={(e) => setNewCase(prev => ({ ...prev, assigned_to: e.target.value }))}
                    placeholder="Investigator name..."
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-mule-500"
                  />
                </div>
              </div>

              <div className="flex justify-end gap-3 mt-6">
                <button
                  onClick={() => setShowCreateModal(false)}
                  className="btn btn-secondary"
                >
                  Cancel
                </button>
                <button
                  onClick={handleCreateCase}
                  disabled={!newCase.title || creating}
                  className="btn btn-primary disabled:opacity-50"
                >
                  {creating ? 'Creating...' : 'Create Case'}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

function StatCard({ icon: Icon, label, value, color }) {
  const colors = {
    blue: 'bg-blue-50 text-blue-600',
    yellow: 'bg-yellow-50 text-yellow-600',
    purple: 'bg-purple-50 text-purple-600',
    green: 'bg-green-50 text-green-600',
  }

  return (
    <div className={`rounded-lg p-4 ${colors[color]}`}>
      <div className="flex items-center gap-3">
        <Icon className="h-8 w-8" />
        <div>
          <p className="text-2xl font-bold">{value}</p>
          <p className="text-sm">{label}</p>
        </div>
      </div>
    </div>
  )
}
