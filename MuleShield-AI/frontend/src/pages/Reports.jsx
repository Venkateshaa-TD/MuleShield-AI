/**
 * MuleShield AI - Reports Page
 * Generate and manage SAR (Suspicious Activity Reports)
 */

import { useState, useEffect } from 'react'
import { useSearchParams } from 'react-router-dom'
import { reportsApi, accountsApi } from '../api'
import {
  DocumentTextIcon,
  ArrowDownTrayIcon,
  ClockIcon,
  CheckCircleIcon,
  EyeIcon,
  XMarkIcon,
  MagnifyingGlassIcon,
} from '@heroicons/react/24/outline'

export default function Reports() {
  const [searchParams] = useSearchParams()
  const [reports, setReports] = useState([])
  const [loading, setLoading] = useState(true)
  const [generating, setGenerating] = useState(false)
  const [selectedReport, setSelectedReport] = useState(null)
  const [accounts, setAccounts] = useState([])
  const [searchTerm, setSearchTerm] = useState('')
  const [showGenerateModal, setShowGenerateModal] = useState(false)
  const [selectedAccountId, setSelectedAccountId] = useState(
    searchParams.get('account_id') || ''
  )

  useEffect(() => {
    fetchReports()
    fetchAccounts()
  }, [])

  const fetchReports = async () => {
    setLoading(true)
    try {
      const response = await reportsApi.getList()
      setReports(response.data)
    } catch (error) {
      console.error('Failed to fetch reports:', error)
    } finally {
      setLoading(false)
    }
  }

  const fetchAccounts = async () => {
    try {
      // Only fetch high-risk accounts for SAR generation
      const response = await accountsApi.getList({ risk_category: 'high' })
      setAccounts(response.data)
    } catch (error) {
      console.error('Failed to fetch accounts:', error)
    }
  }

  const handleGenerateSAR = async () => {
    if (!selectedAccountId) return

    setGenerating(true)
    try {
      const response = await reportsApi.generate(parseInt(selectedAccountId))
      setShowGenerateModal(false)
      setSelectedAccountId('')
      fetchReports()
      // Show the generated report
      setSelectedReport(response.data)
    } catch (error) {
      console.error('Failed to generate SAR:', error)
    } finally {
      setGenerating(false)
    }
  }

  const handleDownload = async (reportId) => {
    try {
      const response = await reportsApi.download(reportId)
      // Create blob and download
      const blob = new Blob([JSON.stringify(response.data, null, 2)], {
        type: 'application/json'
      })
      const url = window.URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `SAR-Report-${reportId}.json`
      document.body.appendChild(a)
      a.click()
      document.body.removeChild(a)
      window.URL.revokeObjectURL(url)
    } catch (error) {
      console.error('Failed to download report:', error)
    }
  }

  const getStatusBadge = (status) => {
    const styles = {
      draft: 'bg-gray-100 text-gray-800',
      pending: 'bg-yellow-100 text-yellow-800',
      submitted: 'bg-blue-100 text-blue-800',
      filed: 'bg-green-100 text-green-800',
    }
    return (
      <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${styles[status] || styles.draft}`}>
        {status}
      </span>
    )
  }

  const filteredAccounts = accounts.filter(acc => {
    if (!searchTerm) return true
    const term = searchTerm.toLowerCase()
    return (
      acc.account_name?.toLowerCase().includes(term) ||
      acc.account_number?.toLowerCase().includes(term)
    )
  })

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Reports</h1>
          <p className="text-gray-600">Generate and manage Suspicious Activity Reports (SARs)</p>
        </div>
        <button
          onClick={() => setShowGenerateModal(true)}
          className="btn btn-primary flex items-center gap-2"
        >
          <DocumentTextIcon className="h-5 w-5" />
          Generate SAR
        </button>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-4 gap-4">
        <div className="bg-gray-50 rounded-lg p-4">
          <p className="text-2xl font-bold text-gray-900">{reports.length}</p>
          <p className="text-sm text-gray-600">Total Reports</p>
        </div>
        <div className="bg-yellow-50 rounded-lg p-4">
          <p className="text-2xl font-bold text-yellow-600">
            {reports.filter(r => r.status === 'draft').length}
          </p>
          <p className="text-sm text-yellow-700">Drafts</p>
        </div>
        <div className="bg-blue-50 rounded-lg p-4">
          <p className="text-2xl font-bold text-blue-600">
            {reports.filter(r => r.status === 'pending' || r.status === 'submitted').length}
          </p>
          <p className="text-sm text-blue-700">Pending/Submitted</p>
        </div>
        <div className="bg-green-50 rounded-lg p-4">
          <p className="text-2xl font-bold text-green-600">
            {reports.filter(r => r.status === 'filed').length}
          </p>
          <p className="text-sm text-green-700">Filed</p>
        </div>
      </div>

      {/* Reports Table */}
      <div className="card overflow-hidden">
        {loading ? (
          <div className="flex items-center justify-center h-64">
            <div className="spinner" />
            <span className="ml-3 text-gray-600">Loading reports...</span>
          </div>
        ) : reports.length === 0 ? (
          <div className="text-center py-12">
            <DocumentTextIcon className="h-12 w-12 text-gray-400 mx-auto mb-4" />
            <h3 className="text-lg font-medium text-gray-900">No reports yet</h3>
            <p className="text-gray-600 mb-4">
              Generate a SAR for suspicious accounts
            </p>
            <button
              onClick={() => setShowGenerateModal(true)}
              className="btn btn-primary"
            >
              Generate SAR
            </button>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Report ID</th>
                  <th>Account</th>
                  <th>Type</th>
                  <th>Status</th>
                  <th>Generated</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {reports.map((report) => (
                  <tr key={report.id} className="hover:bg-gray-50">
                    <td className="font-mono">{report.report_reference || `SAR-${report.id}`}</td>
                    <td className="font-medium">{report.account_name || `Account #${report.account_id}`}</td>
                    <td>{report.report_type || 'SAR'}</td>
                    <td>{getStatusBadge(report.status)}</td>
                    <td className="text-gray-500">
                      {new Date(report.created_at).toLocaleDateString()}
                    </td>
                    <td>
                      <div className="flex items-center gap-2">
                        <button
                          onClick={() => setSelectedReport(report)}
                          className="btn btn-secondary text-sm flex items-center gap-1"
                        >
                          <EyeIcon className="h-4 w-4" />
                          View
                        </button>
                        <button
                          onClick={() => handleDownload(report.id)}
                          className="btn btn-secondary text-sm flex items-center gap-1"
                        >
                          <ArrowDownTrayIcon className="h-4 w-4" />
                          Download
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Generate SAR Modal */}
      {showGenerateModal && (
        <div className="fixed inset-0 z-50 overflow-y-auto">
          <div className="flex items-center justify-center min-h-screen px-4">
            <div
              className="fixed inset-0 bg-black bg-opacity-50"
              onClick={() => setShowGenerateModal(false)}
            />
            <div className="relative bg-white rounded-lg shadow-xl max-w-lg w-full p-6">
              <h2 className="text-xl font-bold text-gray-900 mb-4">
                Generate Suspicious Activity Report
              </h2>

              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Select Account
                  </label>
                  <div className="relative mb-2">
                    <MagnifyingGlassIcon className="h-5 w-5 absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
                    <input
                      type="text"
                      placeholder="Search high-risk accounts..."
                      value={searchTerm}
                      onChange={(e) => setSearchTerm(e.target.value)}
                      className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg"
                    />
                  </div>
                  <div className="max-h-60 overflow-y-auto border border-gray-200 rounded-lg">
                    {filteredAccounts.length === 0 ? (
                      <p className="p-4 text-gray-500 text-center">
                        No high-risk accounts found
                      </p>
                    ) : (
                      filteredAccounts.map((account) => (
                        <button
                          key={account.id}
                          onClick={() => setSelectedAccountId(account.id.toString())}
                          className={`w-full text-left p-3 border-b border-gray-100 hover:bg-gray-50 transition-colors ${
                            selectedAccountId === account.id.toString()
                              ? 'bg-mule-50 border-l-4 border-l-mule-500'
                              : ''
                          }`}
                        >
                          <p className="font-medium text-gray-900">
                            {account.account_name}
                          </p>
                          <div className="flex items-center gap-4 text-sm text-gray-500">
                            <span>{account.account_number}</span>
                            <span className={`font-medium ${
                              account.composite_risk_score >= 70 ? 'text-red-600' : 'text-yellow-600'
                            }`}>
                              Risk: {account.composite_risk_score?.toFixed(0)}
                            </span>
                          </div>
                        </button>
                      ))
                    )}
                  </div>
                </div>

                {selectedAccountId && (
                  <div className="bg-mule-50 rounded-lg p-4">
                    <p className="text-sm text-mule-700">
                      A comprehensive SAR will be generated including:
                    </p>
                    <ul className="mt-2 text-sm text-mule-600 list-disc list-inside">
                      <li>Subject information</li>
                      <li>Suspicious activity summary</li>
                      <li>Transaction analysis</li>
                      <li>AI-generated narrative</li>
                      <li>Supporting evidence</li>
                    </ul>
                  </div>
                )}
              </div>

              <div className="flex justify-end gap-3 mt-6">
                <button
                  onClick={() => {
                    setShowGenerateModal(false)
                    setSelectedAccountId('')
                    setSearchTerm('')
                  }}
                  className="btn btn-secondary"
                >
                  Cancel
                </button>
                <button
                  onClick={handleGenerateSAR}
                  disabled={!selectedAccountId || generating}
                  className="btn btn-primary disabled:opacity-50"
                >
                  {generating ? 'Generating...' : 'Generate SAR'}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* View Report Modal */}
      {selectedReport && (
        <div className="fixed inset-0 z-50 overflow-y-auto">
          <div className="flex items-center justify-center min-h-screen px-4 py-8">
            <div
              className="fixed inset-0 bg-black bg-opacity-50"
              onClick={() => setSelectedReport(null)}
            />
            <div className="relative bg-white rounded-lg shadow-xl max-w-4xl w-full max-h-[90vh] overflow-y-auto">
              <div className="sticky top-0 bg-white border-b p-4 flex items-center justify-between">
                <h2 className="text-xl font-bold text-gray-900">
                  SAR Report - {selectedReport.report_reference || `#${selectedReport.id}`}
                </h2>
                <button
                  onClick={() => setSelectedReport(null)}
                  className="p-2 hover:bg-gray-100 rounded-lg"
                >
                  <XMarkIcon className="h-5 w-5" />
                </button>
              </div>

              <div className="p-6 space-y-6">
                {/* Report Header */}
                <div className="bg-gray-50 rounded-lg p-4">
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <p className="text-sm text-gray-500">Report Type</p>
                      <p className="font-medium">{selectedReport.report_type || 'SAR'}</p>
                    </div>
                    <div>
                      <p className="text-sm text-gray-500">Status</p>
                      <p>{getStatusBadge(selectedReport.status)}</p>
                    </div>
                    <div>
                      <p className="text-sm text-gray-500">Generated</p>
                      <p className="font-medium">
                        {new Date(selectedReport.created_at).toLocaleString()}
                      </p>
                    </div>
                    <div>
                      <p className="text-sm text-gray-500">Account</p>
                      <p className="font-medium">
                        {selectedReport.account_name || `Account #${selectedReport.account_id}`}
                      </p>
                    </div>
                  </div>
                </div>

                {/* Report Content */}
                {selectedReport.content && (
                  <>
                    {/* Filing Institution */}
                    {selectedReport.content.filing_institution && (
                      <ReportSection title="1. Filing Institution">
                        <KeyValue label="Name" value={selectedReport.content.filing_institution.name} />
                        <KeyValue label="ID Type" value={selectedReport.content.filing_institution.id_type} />
                        <KeyValue label="ID Number" value={selectedReport.content.filing_institution.id_number} />
                      </ReportSection>
                    )}

                    {/* Subject Information */}
                    {selectedReport.content.subject_information && (
                      <ReportSection title="2. Subject Information">
                        <KeyValue label="Name" value={selectedReport.content.subject_information.name} />
                        <KeyValue label="Account Number" value={selectedReport.content.subject_information.account_number} />
                        <KeyValue label="Account Type" value={selectedReport.content.subject_information.account_type} />
                        <KeyValue label="Email" value={selectedReport.content.subject_information.email} />
                        <KeyValue label="Phone" value={selectedReport.content.subject_information.phone} />
                      </ReportSection>
                    )}

                    {/* Suspicious Activity */}
                    {selectedReport.content.suspicious_activity && (
                      <ReportSection title="3. Suspicious Activity Information">
                        <KeyValue label="Date Range" value={selectedReport.content.suspicious_activity.date_range} />
                        <KeyValue
                          label="Total Amount"
                          value={`$${selectedReport.content.suspicious_activity.total_amount?.toLocaleString() || 0}`}
                        />
                        <div className="mt-3">
                          <p className="text-sm font-medium text-gray-700 mb-2">Activity Types:</p>
                          <div className="flex flex-wrap gap-2">
                            {selectedReport.content.suspicious_activity.activity_types?.map((type, idx) => (
                              <span
                                key={idx}
                                className="px-2 py-1 bg-red-100 text-red-800 rounded text-sm"
                              >
                                {type}
                              </span>
                            ))}
                          </div>
                        </div>
                      </ReportSection>
                    )}

                    {/* AI Narrative */}
                    {selectedReport.content.narrative && (
                      <ReportSection title="4. AI-Generated Narrative">
                        <div className="bg-mule-50 rounded-lg p-4 border border-mule-200">
                          <p className="text-mule-800 whitespace-pre-wrap">
                            {selectedReport.content.narrative}
                          </p>
                        </div>
                      </ReportSection>
                    )}

                    {/* Risk Factors */}
                    {selectedReport.content.risk_factors && (
                      <ReportSection title="5. Risk Factors Identified">
                        <ul className="space-y-2">
                          {selectedReport.content.risk_factors.map((factor, idx) => (
                            <li key={idx} className="flex items-start gap-2">
                              <span className="inline-block w-2 h-2 mt-2 rounded-full bg-red-500" />
                              <span>{factor}</span>
                            </li>
                          ))}
                        </ul>
                      </ReportSection>
                    )}
                  </>
                )}

                {/* Download Button */}
                <div className="flex justify-end pt-4 border-t">
                  <button
                    onClick={() => handleDownload(selectedReport.id)}
                    className="btn btn-primary flex items-center gap-2"
                  >
                    <ArrowDownTrayIcon className="h-5 w-5" />
                    Download Full Report
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

function ReportSection({ title, children }) {
  return (
    <div>
      <h3 className="text-lg font-semibold text-gray-900 mb-3">{title}</h3>
      <div className="space-y-2">{children}</div>
    </div>
  )
}

function KeyValue({ label, value }) {
  return (
    <div className="flex">
      <span className="w-40 text-gray-500 text-sm">{label}:</span>
      <span className="font-medium text-gray-900">{value || 'N/A'}</span>
    </div>
  )
}
