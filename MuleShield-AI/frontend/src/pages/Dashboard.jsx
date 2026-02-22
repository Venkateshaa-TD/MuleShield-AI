/**
 * MuleShield AI - Dashboard Page
 * Main overview dashboard with key metrics and charts
 */

import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import { dashboardApi } from '../api'
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend,
  PieChart, Pie, Cell, ResponsiveContainer, LineChart, Line
} from 'recharts'
import {
  UserGroupIcon,
  ExclamationTriangleIcon,
  ArrowTrendingUpIcon,
  ShieldExclamationIcon,
  CurrencyDollarIcon,
} from '@heroicons/react/24/outline'

const RISK_COLORS = {
  low: '#22c55e',
  medium: '#f59e0b',
  high: '#ef4444',
}

export default function Dashboard() {
  const [stats, setStats] = useState(null)
  const [riskDistribution, setRiskDistribution] = useState(null)
  const [recentActivity, setRecentActivity] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetchDashboardData()
  }, [])

  const fetchDashboardData = async () => {
    try {
      const [statsRes, riskRes, activityRes] = await Promise.all([
        dashboardApi.getStats(),
        dashboardApi.getRiskDistribution(),
        dashboardApi.getRecentActivity(),
      ])
      setStats(statsRes.data)
      setRiskDistribution(riskRes.data)
      setRecentActivity(activityRes.data)
    } catch (error) {
      console.error('Failed to fetch dashboard data:', error)
    } finally {
      setLoading(false)
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="spinner" />
        <span className="ml-3 text-gray-600">Loading dashboard...</span>
      </div>
    )
  }

  // Format data for pie chart
  const pieData = riskDistribution ? [
    { name: 'Low Risk', value: riskDistribution.categories.low, color: RISK_COLORS.low },
    { name: 'Medium Risk', value: riskDistribution.categories.medium, color: RISK_COLORS.medium },
    { name: 'High Risk', value: riskDistribution.categories.high, color: RISK_COLORS.high },
  ] : []

  // Format data for bar chart
  const barData = riskDistribution ? Object.entries(riskDistribution.distribution).map(([range, count]) => ({
    range,
    count,
  })) : []

  return (
    <div className="space-y-6">
      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <StatCard
          title="Total Accounts"
          value={stats?.accounts?.total || 0}
          subtitle={`${stats?.accounts?.high_risk || 0} high risk`}
          icon={UserGroupIcon}
          color="blue"
        />
        <StatCard
          title="Active Alerts"
          value={stats?.alerts?.open || 0}
          subtitle={`${stats?.alerts?.total || 0} total alerts`}
          icon={ExclamationTriangleIcon}
          color="red"
        />
        <StatCard
          title="Mule Network"
          value={stats?.mule_network?.detected_accounts || 0}
          subtitle={`${stats?.mule_network?.clusters_identified || 0} clusters identified`}
          icon={ShieldExclamationIcon}
          color="yellow"
        />
        <StatCard
          title="Transaction Volume"
          value={`$${((stats?.transactions?.total_volume || 0) / 1000).toFixed(1)}K`}
          subtitle={`${stats?.transactions?.suspicious || 0} suspicious`}
          icon={CurrencyDollarIcon}
          color="green"
        />
      </div>

      {/* Charts Row */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Risk Category Distribution */}
        <div className="card">
          <div className="card-header">
            <h3 className="text-lg font-medium">Risk Category Distribution</h3>
          </div>
          <div className="card-body">
            <ResponsiveContainer width="100%" height={300}>
              <PieChart>
                <Pie
                  data={pieData}
                  cx="50%"
                  cy="50%"
                  innerRadius={60}
                  outerRadius={100}
                  paddingAngle={2}
                  dataKey="value"
                  label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                >
                  {pieData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Pie>
                <Tooltip />
                <Legend />
              </PieChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Risk Score Distribution */}
        <div className="card">
          <div className="card-header">
            <h3 className="text-lg font-medium">Risk Score Distribution</h3>
          </div>
          <div className="card-body">
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={barData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="range" />
                <YAxis />
                <Tooltip />
                <Bar dataKey="count" fill="#0ea5e9" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      {/* Recent Activity Tables */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Recent Alerts */}
        <div className="card">
          <div className="card-header flex items-center justify-between">
            <h3 className="text-lg font-medium">Recent Alerts</h3>
            <Link to="/alerts" className="text-sm text-mule-600 hover:text-mule-700">
              View all →
            </Link>
          </div>
          <div className="overflow-x-auto">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Account</th>
                  <th>Type</th>
                  <th>Severity</th>
                  <th>Score</th>
                </tr>
              </thead>
              <tbody>
                {recentActivity?.recent_alerts?.slice(0, 5).map((alert) => (
                  <tr key={alert.id}>
                    <td className="font-medium">{alert.account_name || 'N/A'}</td>
                    <td className="text-gray-600">{alert.alert_type}</td>
                    <td>
                      <span className={`risk-badge risk-badge-${alert.severity}`}>
                        {alert.severity}
                      </span>
                    </td>
                    <td className="font-medium">{alert.risk_score?.toFixed(1)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        {/* Recent Suspicious Transactions */}
        <div className="card">
          <div className="card-header flex items-center justify-between">
            <h3 className="text-lg font-medium">Suspicious Transactions</h3>
            <Link to="/accounts" className="text-sm text-mule-600 hover:text-mule-700">
              View all →
            </Link>
          </div>
          <div className="overflow-x-auto">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Reference</th>
                  <th>Amount</th>
                  <th>Reason</th>
                  <th>Risk</th>
                </tr>
              </thead>
              <tbody>
                {recentActivity?.recent_suspicious_transactions?.slice(0, 5).map((txn) => (
                  <tr key={txn.id}>
                    <td className="font-mono text-sm">{txn.transaction_reference}</td>
                    <td className="font-medium">${txn.amount?.toLocaleString()}</td>
                    <td className="text-gray-600 text-sm truncate max-w-[200px]">
                      {txn.suspicious_reason}
                    </td>
                    <td>
                      <span className={`risk-badge ${
                        txn.risk_score > 70 ? 'risk-badge-high' :
                        txn.risk_score > 40 ? 'risk-badge-medium' : 'risk-badge-low'
                      }`}>
                        {txn.risk_score?.toFixed(0)}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>

      {/* Quick Actions */}
      <div className="card">
        <div className="card-header">
          <h3 className="text-lg font-medium">Quick Actions</h3>
        </div>
        <div className="card-body">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <Link
              to="/alerts?status=open"
              className="flex items-center gap-3 p-4 rounded-lg bg-red-50 hover:bg-red-100 transition-colors"
            >
              <ExclamationTriangleIcon className="h-8 w-8 text-red-600" />
              <div>
                <p className="font-medium text-red-900">Review Alerts</p>
                <p className="text-sm text-red-600">{stats?.alerts?.open || 0} pending</p>
              </div>
            </Link>
            <Link
              to="/network"
              className="flex items-center gap-3 p-4 rounded-lg bg-blue-50 hover:bg-blue-100 transition-colors"
            >
              <ArrowTrendingUpIcon className="h-8 w-8 text-blue-600" />
              <div>
                <p className="font-medium text-blue-900">Network Analysis</p>
                <p className="text-sm text-blue-600">View patterns</p>
              </div>
            </Link>
            <Link
              to="/accounts?risk_category=high"
              className="flex items-center gap-3 p-4 rounded-lg bg-yellow-50 hover:bg-yellow-100 transition-colors"
            >
              <UserGroupIcon className="h-8 w-8 text-yellow-600" />
              <div>
                <p className="font-medium text-yellow-900">High Risk Accounts</p>
                <p className="text-sm text-yellow-600">{stats?.accounts?.high_risk || 0} flagged</p>
              </div>
            </Link>
            <Link
              to="/cases"
              className="flex items-center gap-3 p-4 rounded-lg bg-green-50 hover:bg-green-100 transition-colors"
            >
              <ShieldExclamationIcon className="h-8 w-8 text-green-600" />
              <div>
                <p className="font-medium text-green-900">Active Cases</p>
                <p className="text-sm text-green-600">{stats?.cases?.open || 0} open</p>
              </div>
            </Link>
          </div>
        </div>
      </div>
    </div>
  )
}

// Stat Card Component
function StatCard({ title, value, subtitle, icon: Icon, color }) {
  const colorClasses = {
    blue: 'bg-blue-50 text-blue-600',
    red: 'bg-red-50 text-red-600',
    yellow: 'bg-yellow-50 text-yellow-600',
    green: 'bg-green-50 text-green-600',
  }

  return (
    <div className="card">
      <div className="card-body">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-sm font-medium text-gray-500">{title}</p>
            <p className="mt-1 text-3xl font-bold text-gray-900">{value}</p>
            <p className="mt-1 text-sm text-gray-600">{subtitle}</p>
          </div>
          <div className={`p-3 rounded-lg ${colorClasses[color]}`}>
            <Icon className="h-6 w-6" />
          </div>
        </div>
      </div>
    </div>
  )
}
