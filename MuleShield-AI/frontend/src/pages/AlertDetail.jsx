/**
 * MuleShield AI - Alert Detail Page
 * Detailed view of a single alert with investigation tools
 */

import { useState, useEffect } from 'react'
import { useParams, useNavigate, Link } from 'react-router-dom'
import { alertsApi, learningApi } from '../api'
import {
  ArrowLeftIcon,
  ExclamationTriangleIcon,
  CheckCircleIcon,
  XCircleIcon,
  ClockIcon,
  UserCircleIcon,
  DocumentTextIcon,
} from '@heroicons/react/24/outline'

export default function AlertDetail() {
  const { id } = useParams()
  const navigate = useNavigate()
  const [alert, setAlert] = useState(null)
  const [loading, setLoading] = useState(true)
  const [notes, setNotes] = useState('')
  const [updating, setUpdating] = useState(false)

  useEffect(() => {
    fetchAlert()
  }, [id])

  const fetchAlert = async () => {
    try {
      const response = await alertsApi.getById(id)
      setAlert(response.data)
      setNotes(response.data.investigator_notes || '')
    } catch (error) {
      console.error('Failed to fetch alert:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleStatusUpdate = async (newStatus, isTruePositive = null) => {
    setUpdating(true)
    try {
      await alertsApi.updateStatus(id, {
        status: newStatus,
        investigator_notes: notes,
      })

      // If resolving, provide feedback for adaptive learning
      if (newStatus === 'resolved' && isTruePositive !== null) {
        await learningApi.submitFeedback({
          alert_id: parseInt(id),
          is_true_positive: isTruePositive,
          adjusted_risk_score: isTruePositive ? alert.risk_score : alert.risk_score * 0.5,
          investigator_notes: notes,
        })
      }

      fetchAlert()
    } catch (error) {
      console.error('Failed to update alert:', error)
    } finally {
      setUpdating(false)
    }
  }

  const handleCreateCase = async () => {
    try {
      // Navigate to cases with pre-filled alert
      navigate(`/cases?create=true&alert_id=${id}`)
    } catch (error) {
      console.error('Failed to create case:', error)
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="spinner" />
        <span className="ml-3 text-gray-600">Loading alert details...</span>
      </div>
    )
  }

  if (!alert) {
    return (
      <div className="text-center py-12">
        <h2 className="text-xl font-semibold text-gray-900">Alert not found</h2>
        <Link to="/alerts" className="text-mule-600 hover:text-mule-700 mt-4 inline-block">
          ← Back to alerts
        </Link>
      </div>
    )
  }

  const getSeverityColor = (severity) => {
    const colors = {
      critical: 'bg-red-100 text-red-800 border-red-200',
      high: 'bg-red-50 text-red-700 border-red-100',
      medium: 'bg-yellow-50 text-yellow-700 border-yellow-100',
      low: 'bg-green-50 text-green-700 border-green-100',
    }
    return colors[severity] || colors.medium
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center gap-4">
        <button
          onClick={() => navigate(-1)}
          className="p-2 rounded-lg hover:bg-gray-100 transition-colors"
        >
          <ArrowLeftIcon className="h-5 w-5 text-gray-600" />
        </button>
        <div className="flex-1">
          <div className="flex items-center gap-3">
            <h1 className="text-2xl font-bold text-gray-900">
              Alert #{id}
            </h1>
            <span className={`px-3 py-1 rounded-full text-sm font-medium border ${getSeverityColor(alert.severity)}`}>
              {alert.severity?.toUpperCase()}
            </span>
          </div>
          <p className="text-gray-600">{alert.alert_type?.replace(/_/g, ' ')}</p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Main Content */}
        <div className="lg:col-span-2 space-y-6">
          {/* Alert Details */}
          <div className="card">
            <div className="card-header">
              <h3 className="text-lg font-medium">Alert Details</h3>
            </div>
            <div className="card-body">
              <div className="space-y-4">
                <div>
                  <h4 className="text-sm font-medium text-gray-500 mb-1">Description</h4>
                  <p className="text-gray-900">{alert.description}</p>
                </div>

                {alert.ai_reasoning && (
                  <div className="bg-mule-50 rounded-lg p-4 border border-mule-200">
                    <h4 className="text-sm font-medium text-mule-800 mb-2">
                      AI Risk Assessment
                    </h4>
                    <p className="text-mule-700">{alert.ai_reasoning}</p>
                  </div>
                )}

                <div className="grid grid-cols-2 gap-4 pt-4 border-t">
                  <div>
                    <p className="text-sm text-gray-500">Risk Score</p>
                    <p className={`text-2xl font-bold ${
                      alert.risk_score >= 70 ? 'text-red-600' :
                      alert.risk_score >= 40 ? 'text-yellow-600' : 'text-green-600'
                    }`}>
                      {alert.risk_score?.toFixed(1)}
                    </p>
                  </div>
                  <div>
                    <p className="text-sm text-gray-500">Created</p>
                    <p className="text-lg font-medium">
                      {new Date(alert.created_at).toLocaleString()}
                    </p>
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Account Info */}
          <div className="card">
            <div className="card-header flex items-center justify-between">
              <h3 className="text-lg font-medium">Related Account</h3>
              <Link
                to={`/accounts/${alert.account_id}`}
                className="text-sm text-mule-600 hover:text-mule-700"
              >
                View full profile →
              </Link>
            </div>
            <div className="card-body">
              <div className="flex items-center gap-4">
                <div className="h-12 w-12 rounded-full bg-gray-100 flex items-center justify-center">
                  <UserCircleIcon className="h-8 w-8 text-gray-400" />
                </div>
                <div>
                  <p className="font-medium text-gray-900">
                    {alert.account_name || `Account #${alert.account_id}`}
                  </p>
                  <p className="text-sm text-gray-500">{alert.account_number}</p>
                </div>
              </div>
            </div>
          </div>

          {/* Investigation Notes */}
          <div className="card">
            <div className="card-header">
              <h3 className="text-lg font-medium">Investigation Notes</h3>
            </div>
            <div className="card-body">
              <textarea
                value={notes}
                onChange={(e) => setNotes(e.target.value)}
                placeholder="Add investigation notes..."
                rows={4}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-mule-500 focus:border-mule-500"
              />
              <button
                onClick={() => handleStatusUpdate(alert.status)}
                disabled={updating}
                className="mt-3 btn btn-secondary"
              >
                {updating ? 'Saving...' : 'Save Notes'}
              </button>
            </div>
          </div>
        </div>

        {/* Sidebar */}
        <div className="space-y-6">
          {/* Status Card */}
          <div className="card">
            <div className="card-header">
              <h3 className="text-lg font-medium">Status</h3>
            </div>
            <div className="card-body space-y-4">
              <div className={`p-4 rounded-lg ${
                alert.status === 'open' ? 'bg-red-50' :
                alert.status === 'investigating' ? 'bg-yellow-50' :
                alert.status === 'resolved' ? 'bg-green-50' :
                alert.status === 'escalated' ? 'bg-purple-50' : 'bg-gray-50'
              }`}>
                <p className={`text-lg font-semibold capitalize ${
                  alert.status === 'open' ? 'text-red-800' :
                  alert.status === 'investigating' ? 'text-yellow-800' :
                  alert.status === 'resolved' ? 'text-green-800' :
                  alert.status === 'escalated' ? 'text-purple-800' : 'text-gray-800'
                }`}>
                  {alert.status?.replace('_', ' ')}
                </p>
              </div>

              {/* Action Buttons */}
              <div className="space-y-2">
                {alert.status === 'open' && (
                  <button
                    onClick={() => handleStatusUpdate('investigating')}
                    disabled={updating}
                    className="w-full btn btn-primary"
                  >
                    <ClockIcon className="h-5 w-5 mr-2" />
                    Start Investigation
                  </button>
                )}

                {alert.status === 'investigating' && (
                  <>
                    <button
                      onClick={() => handleStatusUpdate('resolved', true)}
                      disabled={updating}
                      className="w-full btn btn-danger"
                    >
                      <CheckCircleIcon className="h-5 w-5 mr-2" />
                      Confirm as True Positive
                    </button>
                    <button
                      onClick={() => handleStatusUpdate('false_positive', false)}
                      disabled={updating}
                      className="w-full btn btn-secondary"
                    >
                      <XCircleIcon className="h-5 w-5 mr-2" />
                      Mark as False Positive
                    </button>
                    <button
                      onClick={() => handleStatusUpdate('escalated')}
                      disabled={updating}
                      className="w-full btn btn-warning"
                    >
                      <ExclamationTriangleIcon className="h-5 w-5 mr-2" />
                      Escalate
                    </button>
                  </>
                )}

                {(alert.status === 'open' || alert.status === 'investigating') && (
                  <button
                    onClick={handleCreateCase}
                    className="w-full btn btn-secondary mt-4"
                  >
                    <DocumentTextIcon className="h-5 w-5 mr-2" />
                    Create Case
                  </button>
                )}
              </div>
            </div>
          </div>

          {/* Timeline */}
          <div className="card">
            <div className="card-header">
              <h3 className="text-lg font-medium">Activity Timeline</h3>
            </div>
            <div className="card-body">
              <div className="space-y-4">
                <TimelineItem
                  icon={<ExclamationTriangleIcon className="h-4 w-4" />}
                  title="Alert Created"
                  time={alert.created_at}
                  color="red"
                />
                {alert.status !== 'open' && (
                  <TimelineItem
                    icon={<ClockIcon className="h-4 w-4" />}
                    title="Investigation Started"
                    time={alert.updated_at}
                    color="yellow"
                  />
                )}
                {alert.status === 'resolved' && (
                  <TimelineItem
                    icon={<CheckCircleIcon className="h-4 w-4" />}
                    title="Resolved"
                    time={alert.resolved_at || alert.updated_at}
                    color="green"
                  />
                )}
              </div>
            </div>
          </div>

          {/* Quick Links */}
          <div className="card">
            <div className="card-header">
              <h3 className="text-lg font-medium">Quick Links</h3>
            </div>
            <div className="card-body space-y-2">
              <Link
                to={`/accounts/${alert.account_id}`}
                className="block p-3 rounded-lg bg-gray-50 hover:bg-gray-100 transition-colors"
              >
                <p className="font-medium text-gray-900">View Account Profile</p>
                <p className="text-sm text-gray-500">Full account details & history</p>
              </Link>
              <Link
                to={`/network?highlight=${alert.account_id}`}
                className="block p-3 rounded-lg bg-gray-50 hover:bg-gray-100 transition-colors"
              >
                <p className="font-medium text-gray-900">Network Analysis</p>
                <p className="text-sm text-gray-500">View transaction network</p>
              </Link>
              <Link
                to={`/reports?account_id=${alert.account_id}`}
                className="block p-3 rounded-lg bg-gray-50 hover:bg-gray-100 transition-colors"
              >
                <p className="font-medium text-gray-900">Generate SAR</p>
                <p className="text-sm text-gray-500">Create suspicious activity report</p>
              </Link>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

function TimelineItem({ icon, title, time, color }) {
  const colorClasses = {
    red: 'bg-red-100 text-red-600',
    yellow: 'bg-yellow-100 text-yellow-600',
    green: 'bg-green-100 text-green-600',
    gray: 'bg-gray-100 text-gray-600',
  }

  return (
    <div className="flex items-start gap-3">
      <div className={`p-2 rounded-full ${colorClasses[color]}`}>
        {icon}
      </div>
      <div>
        <p className="font-medium text-gray-900">{title}</p>
        <p className="text-sm text-gray-500">
          {new Date(time).toLocaleString()}
        </p>
      </div>
    </div>
  )
}
