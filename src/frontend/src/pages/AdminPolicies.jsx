import { useState, useMemo } from 'react'
import { useQuery } from 'react-query'
import { adminAPI } from '../services/api'
import {
  DocumentTextIcon,
  MagnifyingGlassIcon,
  ShieldCheckIcon,
  CurrencyDollarIcon,
  ChartBarIcon,
  CalendarIcon,
} from '@heroicons/react/24/outline'

export default function AdminPolicies() {
  const [page, setPage] = useState(1)
  const [search, setSearch] = useState('')
  const [policyTypeFilter, setPolicyTypeFilter] = useState('All')
  const limit = 20

  // Fetch policy summary
  const { data: summary, isLoading: isLoadingSummary } = useQuery(
    ['adminPoliciesSummary'],
    () => adminAPI.getPoliciesSummary(),
    { retry: false }
  )

  // Fetch policies list
  const { data: policiesData, isLoading: isLoadingPolicies } = useQuery(
    ['adminPolicies', page, search, policyTypeFilter],
    () => adminAPI.listPolicies((page - 1) * limit, limit, search, policyTypeFilter === 'All' ? null : policyTypeFilter),
    {
      retry: false,
      // Mock data transformation until backend is ready
      select: (data) => {
        const policies = data?.data || data || []
        return policies.map(policy => ({
          ...policy,
          // Mock enriched data
          policy_id: policy.policy_id || `POL-2024-${String(policy.premium_id || 1).padStart(3, '0')}`,
          driver_name: policy.driver_name || 'Unknown Driver',
          policy_type: policy.policy_type || 'PHYD',
          status: policy.status || 'active',
          discount_percentage: policy.discount_percentage || calculateDiscount(policy),
          annual_savings: policy.annual_savings || calculateAnnualSavings(policy),
          coverage_type: policy.coverage_type || 'Comprehensive',
          coverage_limit: policy.coverage_limit || 100000,
          miles_used: policy.miles_used || null,
          total_miles_allowed: policy.total_miles_allowed || null,
        }))
      }
    }
  )

  const policies = policiesData || []

  // Helper functions
  function calculateDiscount(policy) {
    if (policy.base_premium && policy.current_premium) {
      return ((policy.base_premium - policy.current_premium) / policy.base_premium) * 100
    }
    return 0
  }

  function calculateAnnualSavings(policy) {
    if (policy.base_premium && policy.current_premium) {
      return (policy.base_premium - policy.current_premium) * 12
    }
    return 0
  }

  const formatCurrency = (value) => {
    if (!value && value !== 0) return 'N/A'
    return `$${value.toFixed(2)}`
  }

  const formatPolicyPeriod = (startDate, endDate) => {
    if (!startDate || !endDate) return 'N/A'
    try {
      const start = new Date(startDate)
      const end = new Date(endDate)
      const startStr = start.toLocaleDateString('en-US', { month: 'short', year: 'numeric' })
      const endStr = end.toLocaleDateString('en-US', { month: 'short', year: 'numeric' })
      return `${startStr} - ${endStr}`
    } catch {
      return 'N/A'
    }
  }

  const formatMiles = (miles) => {
    if (!miles && miles !== 0) return '0'
    return miles.toLocaleString('en-US')
  }

  const getPolicyTypeColor = (policyType) => {
    switch (policyType?.toUpperCase()) {
      case 'PHYD':
      case 'PAYD':
      case 'HYBRID':
        return 'bg-blue-100 text-blue-800'
      default:
        return 'bg-gray-100 text-gray-800'
    }
  }

  const getStatusColor = (status) => {
    switch (status?.toLowerCase()) {
      case 'active':
        return 'bg-green-100 text-green-800'
      case 'inactive':
        return 'bg-gray-100 text-gray-800'
      default:
        return 'bg-yellow-100 text-yellow-800'
    }
  }

  // Summary cards data
  const summaryCards = [
    {
      title: 'Total Policies',
      value: summary?.total_policies || 0,
      icon: DocumentTextIcon,
      bgColor: 'bg-white',
      textColor: 'text-gray-900',
    },
    {
      title: 'Active Policies',
      value: summary?.active_policies || 0,
      icon: ShieldCheckIcon,
      bgColor: 'bg-white',
      textColor: 'text-green-600',
    },
    {
      title: 'Monthly Revenue',
      value: formatCurrency(summary?.monthly_revenue || 0),
      icon: CurrencyDollarIcon,
      bgColor: 'bg-white',
      textColor: 'text-blue-600',
    },
    {
      title: 'Total Savings',
      value: formatCurrency(summary?.total_savings || 0),
      icon: ChartBarIcon,
      bgColor: 'bg-white',
      textColor: 'text-purple-600',
    },
  ]

  // Filter policies based on search and policy type
  const filteredPolicies = useMemo(() => {
    return policies.filter(policy => {
      // Policy type filter is handled by backend query parameter
      return true
    })
  }, [policies])

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center gap-3">
        <DocumentTextIcon className="w-8 h-8 text-blue-600" />
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Policy Management</h1>
          <p className="text-gray-600 mt-1">View and manage insurance policies</p>
        </div>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {summaryCards.map((card, index) => (
          <div
            key={index}
            className={`${card.bgColor} rounded-xl shadow-lg p-6 flex items-center justify-between`}
          >
            <div>
              <p className="text-sm font-medium text-gray-600 mb-1">{card.title}</p>
              <p className={`text-3xl font-bold ${card.textColor}`}>
                {isLoadingSummary ? '...' : card.value}
              </p>
            </div>
            <card.icon className={`w-10 h-10 ${card.textColor} opacity-50`} />
          </div>
        ))}
      </div>

      {/* Search and Filter */}
      <div className="bg-white rounded-lg shadow p-4">
        <div className="flex flex-col md:flex-row gap-4">
          {/* Search Bar */}
          <div className="flex-1 relative">
            <MagnifyingGlassIcon className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-400" />
            <input
              type="text"
              placeholder="Search by policy number or driver name..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
          </div>

          {/* Filter Buttons */}
          <div className="flex gap-2">
            {['All', 'PAYD', 'PHYD', 'Hybrid'].map((filter) => (
              <button
                key={filter}
                onClick={() => setPolicyTypeFilter(filter)}
                className={`px-4 py-2 rounded-lg font-medium transition-colors ${
                  policyTypeFilter === filter
                    ? 'bg-gray-900 text-white'
                    : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                }`}
              >
                {filter}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Policy Cards */}
      <div className="space-y-4">
        {isLoadingPolicies ? (
          <div className="bg-white rounded-lg shadow p-12 text-center">
            <p className="text-gray-500">Loading policies...</p>
          </div>
        ) : filteredPolicies.length === 0 ? (
          <div className="bg-white rounded-lg shadow p-12 text-center">
            <p className="text-gray-500 mb-2">No policies found</p>
            <p className="text-sm text-gray-400">
              {search || policyTypeFilter !== 'All'
                ? 'Try adjusting your search or filter criteria'
                : 'Policies will appear here once created'}
            </p>
          </div>
        ) : (
          filteredPolicies.map((policy) => (
            <div
              key={policy.premium_id}
              className="bg-white rounded-lg shadow-lg p-6 hover:shadow-xl transition-shadow"
            >
              <div className="flex flex-col lg:flex-row gap-6">
                {/* Left Section - Policy Info */}
                <div className="flex-1">
                  {/* Status Tags */}
                  <div className="flex gap-2 mb-4">
                    {policy.policy_type && (
                      <span className={`px-3 py-1 rounded text-sm font-semibold ${getPolicyTypeColor(policy.policy_type)}`}>
                        {policy.policy_type}
                      </span>
                    )}
                    {policy.status && (
                      <span className={`px-3 py-1 rounded text-sm font-semibold ${getStatusColor(policy.status)}`}>
                        {policy.status}
                      </span>
                    )}
                  </div>

                  {/* Policy ID */}
                  <h3 className="text-xl font-bold text-gray-900 mb-2">
                    Policy #{policy.policy_id}
                  </h3>

                  {/* Driver Name */}
                  <p className="text-lg text-gray-700 mb-6">{policy.driver_name}</p>

                  {/* Financial Details - 4 Boxes */}
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                    {/* Base Premium */}
                    <div className="bg-white border border-gray-200 rounded-lg p-4">
                      <p className="text-xs text-gray-500 mb-1">Base Premium</p>
                      <p className="text-xl font-bold text-gray-900">
                        {formatCurrency(policy.base_premium)}
                      </p>
                    </div>

                    {/* Current Premium */}
                    <div className="bg-green-50 border border-green-200 rounded-lg p-4">
                      <p className="text-xs text-gray-500 mb-1">Current Premium</p>
                      <p className="text-xl font-bold text-gray-900">
                        {formatCurrency(policy.current_premium)}
                      </p>
                    </div>

                    {/* Discount */}
                    <div className="bg-purple-50 border border-purple-200 rounded-lg p-4">
                      <p className="text-xs text-gray-500 mb-1">Discount</p>
                      <p className="text-xl font-bold text-gray-900">
                        {policy.discount_percentage?.toFixed(0) || 0}%
                      </p>
                    </div>

                    {/* Annual Savings */}
                    <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                      <p className="text-xs text-gray-500 mb-1">Annual Savings</p>
                      <p className="text-xl font-bold text-gray-900">
                        {formatCurrency(policy.annual_savings)}
                      </p>
                    </div>
                  </div>
                </div>

                {/* Right Section - Coverage Details (Consolidated) */}
                <div className="lg:w-56">
                  <div className="bg-gray-50 rounded-lg p-4 space-y-3">
                    {/* Coverage */}
                    <div>
                      <div className="flex items-center gap-2 mb-1">
                        <div className="w-4 h-4 rounded-full bg-blue-500 flex items-center justify-center">
                          <div className="w-1.5 h-1.5 bg-white rounded-full"></div>
                        </div>
                        <label className="text-xs font-medium text-gray-500">Coverage</label>
                      </div>
                      <p className="text-sm font-semibold text-gray-900 ml-6">
                        {policy.coverage_type || 'N/A'}
                      </p>
                    </div>

                    {/* Limit */}
                    <div>
                      <div className="flex items-center gap-2 mb-1">
                        <CurrencyDollarIcon className="w-4 h-4 text-gray-400" />
                        <label className="text-xs font-medium text-gray-500">Limit</label>
                      </div>
                      <p className="text-sm font-semibold text-gray-900 ml-6">
                        {formatCurrency(policy.coverage_limit)}
                      </p>
                    </div>

                    {/* Period */}
                    <div>
                      <div className="flex items-center gap-2 mb-1">
                        <CalendarIcon className="w-4 h-4 text-gray-400" />
                        <label className="text-xs font-medium text-gray-500">Period</label>
                      </div>
                      <p className="text-sm font-semibold text-gray-900 ml-6">
                        {formatPolicyPeriod(policy.effective_date, policy.expiration_date)}
                      </p>
                    </div>

                    {/* Miles Used (PAYD only) */}
                    {policy.policy_type === 'PAYD' && policy.total_miles_allowed && (
                      <div>
                        <label className="text-xs font-medium text-gray-500 mb-1 block">Miles Used</label>
                        <p className="text-sm font-semibold text-gray-900 ml-6">
                          {formatMiles(policy.miles_used || 0)} / {formatMiles(policy.total_miles_allowed)}
                        </p>
                      </div>
                    )}
                  </div>
                </div>
              </div>
            </div>
          ))
        )}
      </div>

      {/* Pagination */}
      {filteredPolicies.length > 0 && (
        <div className="flex justify-between items-center">
          <div className="text-sm text-gray-700">
            Showing {(page - 1) * limit + 1} to {Math.min(page * limit, filteredPolicies.length)} of {filteredPolicies.length}
          </div>
          <div className="flex gap-2">
            <button
              onClick={() => setPage(p => Math.max(1, p - 1))}
              disabled={page === 1}
              className="px-4 py-2 border border-gray-300 rounded-lg disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-50"
            >
              Previous
            </button>
            <button
              onClick={() => setPage(p => p + 1)}
              disabled={filteredPolicies.length < limit}
              className="px-4 py-2 border border-gray-300 rounded-lg disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-50"
            >
              Next
            </button>
          </div>
        </div>
      )}
    </div>
  )
}
