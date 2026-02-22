/**
 * MuleShield AI - Accounts Page
 * List all accounts with filtering, sorting, and risk indicators
 */

import { useState, useEffect } from 'react'
import { Link, useSearchParams } from 'react-router-dom'
import { accountsApi } from '../api'
import {
  MagnifyingGlassIcon,
  FunnelIcon,
  ChevronUpIcon,
  ChevronDownIcon,
  UserCircleIcon,
} from '@heroicons/react/24/outline'

export default function Accounts() {
  const [searchParams, setSearchParams] = useSearchParams()
  const [accounts, setAccounts] = useState([])
  const [loading, setLoading] = useState(true)
  const [searchTerm, setSearchTerm] = useState('')
  const [filters, setFilters] = useState({
    risk_category: searchParams.get('risk_category') || '',
    account_type: '',
    mule_suspected: '',
  })
  const [sortConfig, setSortConfig] = useState({
    key: 'composite_risk_score',
    direction: 'desc',
  })
  const [pagination, setPagination] = useState({
    page: 1,
    pageSize: 20,
    total: 0,
  })

  useEffect(() => {
    fetchAccounts()
  }, [filters, sortConfig, pagination.page])

  const fetchAccounts = async () => {
    setLoading(true)
    try {
      const params = {
        skip: (pagination.page - 1) * pagination.pageSize,
        limit: pagination.pageSize,
        ...filters,
      }
      const response = await accountsApi.getList(params)
      let data = response.data

      // Apply local sorting
      data = data.sort((a, b) => {
        const aVal = a[sortConfig.key] ?? 0
        const bVal = b[sortConfig.key] ?? 0
        return sortConfig.direction === 'asc' ? aVal - bVal : bVal - aVal
      })

      setAccounts(data)
      setPagination(prev => ({ ...prev, total: data.length }))
    } catch (error) {
      console.error('Failed to fetch accounts:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleSort = (key) => {
    setSortConfig(prev => ({
      key,
      direction: prev.key === key && prev.direction === 'desc' ? 'asc' : 'desc',
    }))
  }

  const handleFilterChange = (key, value) => {
    setFilters(prev => ({ ...prev, [key]: value }))
    setPagination(prev => ({ ...prev, page: 1 }))
  }

  const filteredAccounts = accounts.filter(account => {
    if (searchTerm) {
      const term = searchTerm.toLowerCase()
      return (
        account.account_name?.toLowerCase().includes(term) ||
        account.account_number?.toLowerCase().includes(term) ||
        account.email?.toLowerCase().includes(term)
      )
    }
    return true
  })

  const getRiskCategory = (score) => {
    if (score >= 70) return 'high'
    if (score >= 40) return 'medium'
    return 'low'
  }

  const SortIcon = ({ column }) => {
    if (sortConfig.key !== column) return null
    return sortConfig.direction === 'asc' 
      ? <ChevronUpIcon className="h-4 w-4 inline ml-1" />
      : <ChevronDownIcon className="h-4 w-4 inline ml-1" />
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Accounts</h1>
          <p className="text-gray-600">Monitor and analyze account risk profiles</p>
        </div>
        <div className="flex items-center gap-3">
          {/* Search */}
          <div className="relative">
            <MagnifyingGlassIcon className="h-5 w-5 absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
            <input
              type="text"
              placeholder="Search accounts..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-mule-500 focus:border-mule-500"
            />
          </div>
        </div>
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
              value={filters.risk_category}
              onChange={(e) => handleFilterChange('risk_category', e.target.value)}
              className="px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-mule-500"
            >
              <option value="">All Risk Levels</option>
              <option value="low">Low Risk</option>
              <option value="medium">Medium Risk</option>
              <option value="high">High Risk</option>
            </select>

            <select
              value={filters.account_type}
              onChange={(e) => handleFilterChange('account_type', e.target.value)}
              className="px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-mule-500"
            >
              <option value="">All Account Types</option>
              <option value="checking">Checking</option>
              <option value="savings">Savings</option>
              <option value="money_market">Money Market</option>
            </select>

            <select
              value={filters.mule_suspected}
              onChange={(e) => handleFilterChange('mule_suspected', e.target.value)}
              className="px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-mule-500"
            >
              <option value="">All Accounts</option>
              <option value="true">Suspected Mule Only</option>
              <option value="false">Normal Only</option>
            </select>

            {(filters.risk_category || filters.account_type || filters.mule_suspected) && (
              <button
                onClick={() => setFilters({ risk_category: '', account_type: '', mule_suspected: '' })}
                className="text-sm text-mule-600 hover:text-mule-700"
              >
                Clear filters
              </button>
            )}
          </div>
        </div>
      </div>

      {/* Accounts Table */}
      <div className="card overflow-hidden">
        {loading ? (
          <div className="flex items-center justify-center h-64">
            <div className="spinner" />
            <span className="ml-3 text-gray-600">Loading accounts...</span>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="data-table">
              <thead>
                <tr>
                  <th className="cursor-pointer" onClick={() => handleSort('account_name')}>
                    Account <SortIcon column="account_name" />
                  </th>
                  <th className="cursor-pointer" onClick={() => handleSort('account_type')}>
                    Type <SortIcon column="account_type" />
                  </th>
                  <th className="cursor-pointer" onClick={() => handleSort('composite_risk_score')}>
                    Risk Score <SortIcon column="composite_risk_score" />
                  </th>
                  <th className="cursor-pointer" onClick={() => handleSort('mule_probability')}>
                    Mule Prob. <SortIcon column="mule_probability" />
                  </th>
                  <th>Status</th>
                  <th className="cursor-pointer" onClick={() => handleSort('account_age_days')}>
                    Age (days) <SortIcon column="account_age_days" />
                  </th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {filteredAccounts.map((account) => (
                  <tr key={account.id} className="hover:bg-gray-50">
                    <td>
                      <div className="flex items-center gap-3">
                        <div className="h-10 w-10 rounded-full bg-gray-100 flex items-center justify-center">
                          <UserCircleIcon className="h-6 w-6 text-gray-400" />
                        </div>
                        <div>
                          <p className="font-medium text-gray-900">{account.account_name}</p>
                          <p className="text-sm text-gray-500">{account.account_number}</p>
                        </div>
                      </div>
                    </td>
                    <td>
                      <span className="capitalize">{account.account_type?.replace('_', ' ')}</span>
                    </td>
                    <td>
                      <div className="flex items-center gap-2">
                        <div className="w-16 h-2 bg-gray-200 rounded-full overflow-hidden">
                          <div
                            className={`h-full rounded-full ${
                              account.composite_risk_score >= 70 ? 'bg-red-500' :
                              account.composite_risk_score >= 40 ? 'bg-yellow-500' : 'bg-green-500'
                            }`}
                            style={{ width: `${account.composite_risk_score}%` }}
                          />
                        </div>
                        <span className={`font-medium ${
                          account.composite_risk_score >= 70 ? 'text-red-600' :
                          account.composite_risk_score >= 40 ? 'text-yellow-600' : 'text-green-600'
                        }`}>
                          {account.composite_risk_score?.toFixed(1)}
                        </span>
                      </div>
                    </td>
                    <td>
                      <span className={`font-medium ${
                        account.mule_probability >= 0.7 ? 'text-red-600' :
                        account.mule_probability >= 0.4 ? 'text-yellow-600' : 'text-green-600'
                      }`}>
                        {(account.mule_probability * 100).toFixed(0)}%
                      </span>
                    </td>
                    <td>
                      {account.mule_suspected ? (
                        <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-red-100 text-red-800">
                          Suspected Mule
                        </span>
                      ) : (
                        <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-green-100 text-green-800">
                          Normal
                        </span>
                      )}
                    </td>
                    <td>{account.account_age_days}</td>
                    <td>
                      <Link
                        to={`/accounts/${account.id}`}
                        className="btn btn-secondary text-sm"
                      >
                        View Details
                      </Link>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        {/* Pagination */}
        {!loading && filteredAccounts.length > 0 && (
          <div className="px-6 py-4 border-t border-gray-200 flex items-center justify-between">
            <p className="text-sm text-gray-600">
              Showing {filteredAccounts.length} accounts
            </p>
            <div className="flex items-center gap-2">
              <button
                onClick={() => setPagination(prev => ({ ...prev, page: prev.page - 1 }))}
                disabled={pagination.page === 1}
                className="btn btn-secondary text-sm disabled:opacity-50"
              >
                Previous
              </button>
              <span className="px-3 py-1 text-sm text-gray-600">Page {pagination.page}</span>
              <button
                onClick={() => setPagination(prev => ({ ...prev, page: prev.page + 1 }))}
                disabled={filteredAccounts.length < pagination.pageSize}
                className="btn btn-secondary text-sm disabled:opacity-50"
              >
                Next
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
