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
  EnvelopeIcon,
  PaperAirplaneIcon,
  Cog6ToothIcon,
  DocumentArrowDownIcon,
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
  
  // Email state
  const [showEmailModal, setShowEmailModal] = useState(false)
  const [emailAccountId, setEmailAccountId] = useState(null)
  const [emailForm, setEmailForm] = useState({
    recipients: '',
    cc: '',
    message: '',
    includePdf: true
  })
  const [sendingEmail, setSendingEmail] = useState(false)
  const [emailResult, setEmailResult] = useState(null)
  
  // Email config state
  const [showConfigModal, setShowConfigModal] = useState(false)
  const [emailConfig, setEmailConfig] = useState({
    smtp_server: 'smtp.gmail.com',
    smtp_port: 587,
    sender_email: '',
    sender_password: ''
  })
  const [configuring, setConfiguring] = useState(false)

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
      const response = await reportsApi.generate(selectedAccountId)
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

  const handleDownloadPdf = async (accountId) => {
    try {
      const response = await fetch(`http://localhost:8000/api/reports/sar/${accountId}/pdf`)
      if (!response.ok) {
        const error = await response.json()
        alert(error.detail || 'Failed to download PDF')
        return
      }
      const blob = await response.blob()
      const url = window.URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `SAR-Report-${accountId}.pdf`
      document.body.appendChild(a)
      a.click()
      document.body.removeChild(a)
      window.URL.revokeObjectURL(url)
    } catch (error) {
      console.error('Failed to download PDF:', error)
      alert('Failed to download PDF. Make sure the backend is running.')
    }
  }

  const openEmailModal = (accountId) => {
    setEmailAccountId(accountId)
    setEmailForm({ recipients: '', cc: '', message: '', includePdf: true })
    setEmailResult(null)
    setShowEmailModal(true)
  }

  const handleSendEmail = async () => {
    if (!emailForm.recipients.trim()) {
      alert('Please enter at least one recipient email')
      return
    }

    setSendingEmail(true)
    setEmailResult(null)

    try {
      const recipientEmails = emailForm.recipients.split(',').map(e => e.trim()).filter(Boolean)
      const ccEmails = emailForm.cc ? emailForm.cc.split(',').map(e => e.trim()).filter(Boolean) : []

      const response = await fetch(`http://localhost:8000/api/reports/sar/${emailAccountId}/email`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          recipient_emails: recipientEmails,
          cc_emails: ccEmails.length > 0 ? ccEmails : null,
          custom_message: emailForm.message || null,
          include_pdf: emailForm.includePdf
        })
      })

      const result = await response.json()
      
      if (response.ok) {
        setEmailResult({ success: true, message: result.message })
        setTimeout(() => {
          setShowEmailModal(false)
          setEmailResult(null)
        }, 2000)
      } else {
        setEmailResult({ success: false, message: result.detail || 'Failed to send email' })
      }
    } catch (error) {
      console.error('Failed to send email:', error)
      setEmailResult({ success: false, message: 'Network error. Please check if the backend is running.' })
    } finally {
      setSendingEmail(false)
    }
  }

  const handleConfigureEmail = async () => {
    if (!emailConfig.sender_email || !emailConfig.sender_password) {
      alert('Please fill in all required fields')
      return
    }

    setConfiguring(true)
    try {
      const response = await fetch('http://localhost:8000/api/email/configure', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(emailConfig)
      })

      const result = await response.json()
      
      if (result.status === 'configured') {
        alert('Email configured successfully!')
        setShowConfigModal(false)
      } else {
        alert(`Configuration failed: ${result.message}`)
      }
    } catch (error) {
      console.error('Failed to configure email:', error)
      alert('Failed to configure email. Please try again.')
    } finally {
      setConfiguring(false)
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
        <div className="flex gap-2">
          <button
            onClick={() => setShowConfigModal(true)}
            className="btn btn-secondary flex items-center gap-2"
          >
            <Cog6ToothIcon className="h-5 w-5" />
            Configure Email
          </button>
          <button
            onClick={() => setShowGenerateModal(true)}
            className="btn btn-primary flex items-center gap-2"
          >
            <DocumentTextIcon className="h-5 w-5" />
            Generate SAR
          </button>
        </div>
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
                          title="View Report"
                        >
                          <EyeIcon className="h-4 w-4" />
                        </button>
                        <button
                          onClick={() => handleDownloadPdf(report.account_id)}
                          className="btn btn-secondary text-sm flex items-center gap-1 text-red-600 hover:text-red-700"
                          title="Download PDF"
                        >
                          <DocumentArrowDownIcon className="h-4 w-4" />
                        </button>
                        <button
                          onClick={() => openEmailModal(report.account_id)}
                          className="btn btn-secondary text-sm flex items-center gap-1 text-blue-600 hover:text-blue-700"
                          title="Send via Email"
                        >
                          <EnvelopeIcon className="h-4 w-4" />
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
                <div className="flex justify-end gap-3 pt-4 border-t">
                  <button
                    onClick={() => handleDownloadPdf(selectedReport.account_id)}
                    className="btn btn-secondary flex items-center gap-2"
                  >
                    <DocumentArrowDownIcon className="h-5 w-5" />
                    Download PDF
                  </button>
                  <button
                    onClick={() => {
                      setSelectedReport(null)
                      openEmailModal(selectedReport.account_id)
                    }}
                    className="btn btn-primary flex items-center gap-2"
                  >
                    <EnvelopeIcon className="h-5 w-5" />
                    Send via Email
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Email Modal */}
      {showEmailModal && (
        <div className="fixed inset-0 z-50 overflow-y-auto">
          <div className="flex items-center justify-center min-h-screen px-4">
            <div
              className="fixed inset-0 bg-black bg-opacity-50"
              onClick={() => setShowEmailModal(false)}
            />
            <div className="relative bg-white rounded-lg shadow-xl max-w-lg w-full p-6">
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-xl font-bold text-gray-900 flex items-center gap-2">
                  <EnvelopeIcon className="h-6 w-6 text-blue-600" />
                  Send SAR Report via Email
                </h2>
                <button
                  onClick={() => setShowEmailModal(false)}
                  className="p-2 hover:bg-gray-100 rounded-lg"
                >
                  <XMarkIcon className="h-5 w-5" />
                </button>
              </div>

              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Recipients <span className="text-red-500">*</span>
                  </label>
                  <input
                    type="text"
                    placeholder="email@example.com, another@example.com"
                    value={emailForm.recipients}
                    onChange={(e) => setEmailForm({ ...emailForm, recipients: e.target.value })}
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  />
                  <p className="text-xs text-gray-500 mt-1">Separate multiple emails with commas</p>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    CC (Optional)
                  </label>
                  <input
                    type="text"
                    placeholder="cc@example.com"
                    value={emailForm.cc}
                    onChange={(e) => setEmailForm({ ...emailForm, cc: e.target.value })}
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Custom Message (Optional)
                  </label>
                  <textarea
                    placeholder="Add a personal note to the email..."
                    value={emailForm.message}
                    onChange={(e) => setEmailForm({ ...emailForm, message: e.target.value })}
                    rows={3}
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  />
                </div>

                <div className="flex items-center">
                  <input
                    type="checkbox"
                    id="includePdf"
                    checked={emailForm.includePdf}
                    onChange={(e) => setEmailForm({ ...emailForm, includePdf: e.target.checked })}
                    className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                  />
                  <label htmlFor="includePdf" className="ml-2 text-sm text-gray-700">
                    Attach PDF report
                  </label>
                </div>

                {emailResult && (
                  <div className={`p-4 rounded-lg ${emailResult.success ? 'bg-green-50 text-green-800' : 'bg-red-50 text-red-800'}`}>
                    <p className="font-medium">{emailResult.success ? '✓ Success!' : '✗ Error'}</p>
                    <p className="text-sm">{emailResult.message}</p>
                  </div>
                )}
              </div>

              <div className="flex justify-end gap-3 mt-6">
                <button
                  onClick={() => setShowEmailModal(false)}
                  className="btn btn-secondary"
                >
                  Cancel
                </button>
                <button
                  onClick={handleSendEmail}
                  disabled={sendingEmail || !emailForm.recipients.trim()}
                  className="btn btn-primary flex items-center gap-2 disabled:opacity-50"
                >
                  {sendingEmail ? (
                    <>
                      <div className="spinner h-4 w-4" />
                      Sending...
                    </>
                  ) : (
                    <>
                      <PaperAirplaneIcon className="h-5 w-5" />
                      Send Email
                    </>
                  )}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Email Configuration Modal */}
      {showConfigModal && (
        <div className="fixed inset-0 z-50 overflow-y-auto">
          <div className="flex items-center justify-center min-h-screen px-4">
            <div
              className="fixed inset-0 bg-black bg-opacity-50"
              onClick={() => setShowConfigModal(false)}
            />
            <div className="relative bg-white rounded-lg shadow-xl max-w-lg w-full p-6">
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-xl font-bold text-gray-900 flex items-center gap-2">
                  <Cog6ToothIcon className="h-6 w-6 text-gray-600" />
                  Configure Email Settings
                </h2>
                <button
                  onClick={() => setShowConfigModal(false)}
                  className="p-2 hover:bg-gray-100 rounded-lg"
                >
                  <XMarkIcon className="h-5 w-5" />
                </button>
              </div>

              <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-4">
                <p className="text-sm text-blue-800">
                  <strong>For Gmail:</strong> Use an App Password instead of your regular password.
                  Go to Google Account → Security → 2-Step Verification → App Passwords
                </p>
              </div>

              <div className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      SMTP Server
                    </label>
                    <input
                      type="text"
                      placeholder="smtp.gmail.com"
                      value={emailConfig.smtp_server}
                      onChange={(e) => setEmailConfig({ ...emailConfig, smtp_server: e.target.value })}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Port
                    </label>
                    <input
                      type="number"
                      placeholder="587"
                      value={emailConfig.smtp_port}
                      onChange={(e) => setEmailConfig({ ...emailConfig, smtp_port: parseInt(e.target.value) })}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                    />
                  </div>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Sender Email <span className="text-red-500">*</span>
                  </label>
                  <input
                    type="email"
                    placeholder="your-email@gmail.com"
                    value={emailConfig.sender_email}
                    onChange={(e) => setEmailConfig({ ...emailConfig, sender_email: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    App Password <span className="text-red-500">*</span>
                  </label>
                  <input
                    type="password"
                    placeholder="Your app password"
                    value={emailConfig.sender_password}
                    onChange={(e) => setEmailConfig({ ...emailConfig, sender_password: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                  />
                </div>
              </div>

              <div className="flex justify-end gap-3 mt-6">
                <button
                  onClick={() => setShowConfigModal(false)}
                  className="btn btn-secondary"
                >
                  Cancel
                </button>
                <button
                  onClick={handleConfigureEmail}
                  disabled={configuring || !emailConfig.sender_email || !emailConfig.sender_password}
                  className="btn btn-primary flex items-center gap-2 disabled:opacity-50"
                >
                  {configuring ? 'Configuring...' : 'Save Configuration'}
                </button>
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
