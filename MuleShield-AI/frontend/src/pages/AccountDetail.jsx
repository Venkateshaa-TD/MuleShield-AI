/**
 * MuleShield AI - Account Detail Page
 * Comprehensive view of account risk analysis and transaction history
 */

import { useState, useEffect } from 'react'
import { useParams, Link, useNavigate } from 'react-router-dom'
import { accountsApi, graphApi } from '../api'
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend,
  ResponsiveContainer, RadarChart, PolarGrid, PolarAngleAxis,
  PolarRadiusAxis, Radar
} from 'recharts'
import {
  ArrowLeftIcon,
  ExclamationTriangleIcon,
  UserCircleIcon,
  ClockIcon,
  DevicePhoneMobileIcon,
  CurrencyDollarIcon,
  DocumentTextIcon,
  ChartBarIcon,
} from '@heroicons/react/24/outline'

export default function AccountDetail() {
  const { id } = useParams()
  const navigate = useNavigate()
  const [account, setAccount] = useState(null)
  const [riskAnalysis, setRiskAnalysis] = useState(null)
  const [transactions, setTransactions] = useState([])
  const [networkData, setNetworkData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [activeTab, setActiveTab] = useState('overview')

  useEffect(() => {
    fetchAccountData()
  }, [id])

  const fetchAccountData = async () => {
    try {
      const [accountRes, riskRes, txnRes] = await Promise.all([
        accountsApi.getById(id),
        accountsApi.getRiskAnalysis(id),
        accountsApi.getTransactions(id),
      ])
      setAccount(accountRes.data)
      setRiskAnalysis(riskRes.data)
      setTransactions(txnRes.data)

      // Fetch network data for this account
      try {
        const networkRes = await graphApi.getAccount(id)
        setNetworkData(networkRes.data)
      } catch (e) {
        console.log('Network data not available')
      }
    } catch (error) {
      console.error('Failed to fetch account data:', error)
    } finally {
      setLoading(false)
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="spinner" />
        <span className="ml-3 text-gray-600">Loading account details...</span>
      </div>
    )
  }

  if (!account) {
    return (
      <div className="text-center py-12">
        <h2 className="text-xl font-semibold text-gray-900">Account not found</h2>
        <Link to="/accounts" className="text-mule-600 hover:text-mule-700 mt-4 inline-block">
          ← Back to accounts
        </Link>
      </div>
    )
  }

  // Prepare radar chart data for risk components
  const radarData = riskAnalysis?.risk_components ? [
    { component: 'Transaction Velocity', score: riskAnalysis.risk_components.transaction_velocity_score || 0, fullMark: 100 },
    { component: 'Beneficiary Diversity', score: riskAnalysis.risk_components.beneficiary_diversity_score || 0, fullMark: 100 },
    { component: 'Account Age', score: riskAnalysis.risk_components.account_age_score || 0, fullMark: 100 },
    { component: 'Device Reuse', score: riskAnalysis.risk_components.device_reuse_score || 0, fullMark: 100 },
    { component: 'Graph Centrality', score: riskAnalysis.risk_components.graph_centrality_score || 0, fullMark: 100 },
    { component: 'Behavior Deviation', score: riskAnalysis.risk_components.behavior_deviation_score || 0, fullMark: 100 },
  ] : []

  const tabs = [
    { id: 'overview', label: 'Overview', icon: UserCircleIcon },
    { id: 'risk', label: 'Risk Analysis', icon: ChartBarIcon },
    { id: 'transactions', label: 'Transactions', icon: CurrencyDollarIcon },
    { id: 'network', label: 'Network', icon: DocumentTextIcon },
  ]

  return (
    <div className="space-y-6">
      {/* Back Button & Header */}
      <div className="flex items-center gap-4">
        <button
          onClick={() => navigate(-1)}
          className="p-2 rounded-lg hover:bg-gray-100 transition-colors"
        >
          <ArrowLeftIcon className="h-5 w-5 text-gray-600" />
        </button>
        <div className="flex-1">
          <h1 className="text-2xl font-bold text-gray-900">{account.account_name}</h1>
          <p className="text-gray-600">{account.account_number}</p>
        </div>
        
        {/* Risk Badge */}
        <div className={`px-4 py-2 rounded-lg ${
          account.composite_risk_score >= 70 ? 'bg-red-100' :
          account.composite_risk_score >= 40 ? 'bg-yellow-100' : 'bg-green-100'
        }`}>
          <p className="text-sm font-medium text-gray-600">Risk Score</p>
          <p className={`text-2xl font-bold ${
            account.composite_risk_score >= 70 ? 'text-red-600' :
            account.composite_risk_score >= 40 ? 'text-yellow-600' : 'text-green-600'
          }`}>
            {account.composite_risk_score?.toFixed(1)}
          </p>
        </div>
      </div>

      {/* Mule Warning Banner */}
      {account.mule_suspected && (
        <div className="alert alert-warning flex items-start gap-3">
          <ExclamationTriangleIcon className="h-6 w-6 text-yellow-600 flex-shrink-0" />
          <div>
            <h3 className="font-semibold text-yellow-800">Suspected Mule Account</h3>
            <p className="text-yellow-700">
              This account has been flagged with {(account.mule_probability * 100).toFixed(0)}% mule probability.
              {riskAnalysis?.ai_reasoning && (
                <span className="block mt-1">{riskAnalysis.ai_reasoning}</span>
              )}
            </p>
          </div>
        </div>
      )}

      {/* Tabs */}
      <div className="border-b border-gray-200">
        <nav className="flex space-x-8">
          {tabs.map((tab) => {
            const Icon = tab.icon
            return (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`flex items-center gap-2 py-4 px-1 border-b-2 font-medium text-sm transition-colors ${
                  activeTab === tab.id
                    ? 'border-mule-500 text-mule-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }`}
              >
                <Icon className="h-5 w-5" />
                {tab.label}
              </button>
            )
          })}
        </nav>
      </div>

      {/* Tab Content */}
      {activeTab === 'overview' && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Account Info */}
          <div className="card">
            <div className="card-header">
              <h3 className="text-lg font-medium">Account Information</h3>
            </div>
            <div className="card-body space-y-4">
              <InfoRow label="Account Type" value={account.account_type?.replace('_', ' ')} />
              <InfoRow label="Email" value={account.email} />
              <InfoRow label="Phone" value={account.phone_number} />
              <InfoRow label="Account Age" value={`${account.account_age_days} days`} />
              <InfoRow label="KYC Status" value={account.kyc_verified ? 'Verified' : 'Pending'} />
              <InfoRow label="Created" value={new Date(account.created_at).toLocaleDateString()} />
            </div>
          </div>

          {/* Quick Stats */}
          <div className="card">
            <div className="card-header">
              <h3 className="text-lg font-medium">Activity Summary</h3>
            </div>
            <div className="card-body">
              <div className="grid grid-cols-2 gap-4">
                <StatBox
                  label="Total Transactions"
                  value={transactions.length}
                  icon={CurrencyDollarIcon}
                />
                <StatBox
                  label="Mule Probability"
                  value={`${(account.mule_probability * 100).toFixed(0)}%`}
                  icon={ExclamationTriangleIcon}
                />
                <StatBox
                  label="Unique Beneficiaries"
                  value={riskAnalysis?.network_info?.unique_counterparties || 0}
                  icon={UserCircleIcon}
                />
                <StatBox
                  label="Device Fingerprints"
                  value={riskAnalysis?.device_info?.unique_devices || 0}
                  icon={DevicePhoneMobileIcon}
                />
              </div>
            </div>
          </div>

          {/* AI Reasoning */}
          {riskAnalysis?.ai_reasoning && (
            <div className="card lg:col-span-2">
              <div className="card-header">
                <h3 className="text-lg font-medium">AI Risk Assessment</h3>
              </div>
              <div className="card-body">
                <div className="bg-gray-50 rounded-lg p-4">
                  <p className="text-gray-700">{riskAnalysis.ai_reasoning}</p>
                </div>
                {riskAnalysis.risk_factors && riskAnalysis.risk_factors.length > 0 && (
                  <div className="mt-4">
                    <h4 className="font-medium text-gray-900 mb-2">Key Risk Factors:</h4>
                    <ul className="space-y-2">
                      {riskAnalysis.risk_factors.map((factor, idx) => (
                        <li key={idx} className="flex items-start gap-2">
                          <span className={`inline-block w-2 h-2 mt-2 rounded-full ${
                            factor.severity === 'high' ? 'bg-red-500' :
                            factor.severity === 'medium' ? 'bg-yellow-500' : 'bg-green-500'
                          }`} />
                          <span className="text-gray-700">{factor.description}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            </div>
          )}
        </div>
      )}

      {activeTab === 'risk' && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Risk Radar Chart */}
          <div className="card">
            <div className="card-header">
              <h3 className="text-lg font-medium">Risk Component Analysis</h3>
            </div>
            <div className="card-body">
              <ResponsiveContainer width="100%" height={350}>
                <RadarChart data={radarData}>
                  <PolarGrid />
                  <PolarAngleAxis dataKey="component" />
                  <PolarRadiusAxis angle={30} domain={[0, 100]} />
                  <Radar
                    name="Risk Score"
                    dataKey="score"
                    stroke="#0ea5e9"
                    fill="#0ea5e9"
                    fillOpacity={0.5}
                  />
                  <Tooltip />
                </RadarChart>
              </ResponsiveContainer>
            </div>
          </div>

          {/* Risk Components Table */}
          <div className="card">
            <div className="card-header">
              <h3 className="text-lg font-medium">Risk Score Breakdown</h3>
            </div>
            <div className="card-body space-y-4">
              {radarData.map((item) => (
                <div key={item.component}>
                  <div className="flex justify-between text-sm mb-1">
                    <span className="text-gray-600">{item.component}</span>
                    <span className="font-medium">{item.score.toFixed(1)}</span>
                  </div>
                  <div className="w-full h-2 bg-gray-200 rounded-full overflow-hidden">
                    <div
                      className={`h-full rounded-full ${
                        item.score >= 70 ? 'bg-red-500' :
                        item.score >= 40 ? 'bg-yellow-500' : 'bg-green-500'
                      }`}
                      style={{ width: `${item.score}%` }}
                    />
                  </div>
                </div>
              ))}

              {/* Composite Score */}
              <div className="pt-4 border-t border-gray-200">
                <div className="flex justify-between text-sm mb-1">
                  <span className="font-semibold text-gray-900">Composite Risk Score</span>
                  <span className="font-bold text-lg">{account.composite_risk_score?.toFixed(1)}</span>
                </div>
              </div>
            </div>
          </div>

          {/* Behavioral Profile */}
          {riskAnalysis?.behavioral_profile && (
            <div className="card lg:col-span-2">
              <div className="card-header">
                <h3 className="text-lg font-medium">Behavioral Profile</h3>
              </div>
              <div className="card-body">
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                  <div className="bg-gray-50 rounded-lg p-4">
                    <p className="text-sm text-gray-600">Avg Transaction</p>
                    <p className="text-xl font-bold">${riskAnalysis.behavioral_profile.avg_transaction_amount?.toFixed(0) || 0}</p>
                  </div>
                  <div className="bg-gray-50 rounded-lg p-4">
                    <p className="text-sm text-gray-600">Monthly Volume</p>
                    <p className="text-xl font-bold">${riskAnalysis.behavioral_profile.typical_monthly_volume?.toFixed(0) || 0}</p>
                  </div>
                  <div className="bg-gray-50 rounded-lg p-4">
                    <p className="text-sm text-gray-600">Peak Hours</p>
                    <p className="text-xl font-bold">{riskAnalysis.behavioral_profile.primary_transaction_hours || 'N/A'}</p>
                  </div>
                  <div className="bg-gray-50 rounded-lg p-4">
                    <p className="text-sm text-gray-600">Anomaly Score</p>
                    <p className={`text-xl font-bold ${
                      riskAnalysis.behavioral_profile.anomaly_score >= 0.7 ? 'text-red-600' : 'text-green-600'
                    }`}>
                      {(riskAnalysis.behavioral_profile.anomaly_score * 100)?.toFixed(0) || 0}%
                    </p>
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>
      )}

      {activeTab === 'transactions' && (
        <div className="card">
          <div className="card-header flex items-center justify-between">
            <h3 className="text-lg font-medium">Transaction History</h3>
            <span className="text-sm text-gray-500">{transactions.length} transactions</span>
          </div>
          <div className="overflow-x-auto">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Date</th>
                  <th>Reference</th>
                  <th>Type</th>
                  <th>Amount</th>
                  <th>Counterparty</th>
                  <th>Risk</th>
                </tr>
              </thead>
              <tbody>
                {transactions.map((txn) => (
                  <tr key={txn.id} className={txn.is_suspicious ? 'bg-red-50' : ''}>
                    <td className="text-gray-600">
                      {new Date(txn.transaction_date).toLocaleDateString()}
                    </td>
                    <td className="font-mono text-sm">{txn.transaction_reference}</td>
                    <td className="capitalize">{txn.transaction_type}</td>
                    <td className={`font-medium ${
                      txn.transaction_type === 'credit' ? 'text-green-600' : 'text-red-600'
                    }`}>
                      {txn.transaction_type === 'credit' ? '+' : '-'}${txn.amount?.toLocaleString()}
                    </td>
                    <td>{txn.counterparty_name || txn.counterparty_account}</td>
                    <td>
                      <span className={`risk-badge ${
                        txn.risk_score >= 70 ? 'risk-badge-high' :
                        txn.risk_score >= 40 ? 'risk-badge-medium' : 'risk-badge-low'
                      }`}>
                        {txn.risk_score?.toFixed(0) || 0}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {activeTab === 'network' && (
        <div className="card">
          <div className="card-header">
            <h3 className="text-lg font-medium">Network Connections</h3>
          </div>
          <div className="card-body">
            {networkData ? (
              <div className="space-y-4">
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
                  <StatBox
                    label="Network Degree"
                    value={networkData.centrality_metrics?.degree || 0}
                    subtitle="Direct connections"
                  />
                  <StatBox
                    label="Betweenness"
                    value={(networkData.centrality_metrics?.betweenness * 100)?.toFixed(1) || 0}
                    subtitle="Bridge influence"
                  />
                  <StatBox
                    label="Cluster ID"
                    value={networkData.cluster_id || 'N/A'}
                    subtitle="Community group"
                  />
                  <StatBox
                    label="PageRank"
                    value={(networkData.centrality_metrics?.pagerank * 100)?.toFixed(2) || 0}
                    subtitle="Network importance"
                  />
                </div>
                <Link
                  to={`/network?highlight=${id}`}
                  className="btn btn-primary"
                >
                  View in Network Graph →
                </Link>
              </div>
            ) : (
              <p className="text-gray-500 text-center py-8">
                No network data available for this account.
              </p>
            )}
          </div>
        </div>
      )}
    </div>
  )
}

// Helper Components
function InfoRow({ label, value }) {
  return (
    <div className="flex justify-between">
      <span className="text-gray-600">{label}</span>
      <span className="font-medium text-gray-900 capitalize">{value}</span>
    </div>
  )
}

function StatBox({ label, value, icon: Icon, subtitle }) {
  return (
    <div className="bg-gray-50 rounded-lg p-4 text-center">
      {Icon && <Icon className="h-6 w-6 mx-auto mb-2 text-gray-400" />}
      <p className="text-2xl font-bold text-gray-900">{value}</p>
      <p className="text-sm text-gray-600">{label}</p>
      {subtitle && <p className="text-xs text-gray-400">{subtitle}</p>}
    </div>
  )
}
