import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from 'react-query'
import { pricingAPI, authAPI } from '../services/api'
import {
  CheckCircleIcon,
  CalendarIcon,
  ShieldCheckIcon,
  CurrencyDollarIcon,
  ChartBarIcon,
  BoltIcon
} from '@heroicons/react/24/outline'

export default function Pricing() {
  const queryClient = useQueryClient()
  const [isRecalculating, setIsRecalculating] = useState(false)

  // Get current user to determine driver_id
  const { data: currentUser } = useQuery(
    ['currentUser'],
    () => authAPI.getCurrentUser(),
    { retry: false }
  )
  
  const driverId = currentUser?.data?.driver_id || 'DRV-0001'

  // Fetch policy details
  const { data: policyDetails } = useQuery(
    ['policyDetails', driverId],
    () => pricingAPI.getPolicyDetails(driverId),
    { 
      retry: false,
      enabled: !!driverId,
      // Fallback to existing endpoints if new one doesn't exist
      onError: () => {
        // Will fallback to getCurrentPremium and getComparison
      }
    }
  )

  // Fallback: Use existing endpoints
  const { data: premium } = useQuery(
    ['premium', driverId],
    () => pricingAPI.getCurrentPremium(driverId),
    { retry: false, enabled: !!driverId }
  )

  const { data: comparison } = useQuery(
    ['comparison', driverId],
    () => pricingAPI.getComparison(driverId),
    { retry: false, enabled: !!driverId }
  )

  // Recalculate premium mutation
  const recalculateMutation = useMutation(
    () => pricingAPI.recalculatePremium(driverId),
    {
      onSuccess: () => {
        queryClient.invalidateQueries(['policyDetails', driverId])
        queryClient.invalidateQueries(['premium', driverId])
        queryClient.invalidateQueries(['comparison', driverId])
        setIsRecalculating(false)
      },
      onError: () => {
        setIsRecalculating(false)
      }
    }
  )

  const handleRecalculate = () => {
    setIsRecalculating(true)
    recalculateMutation.mutate()
  }

  // Extract data with fallbacks
  // Get traditional premium from policyDetails (preferred) or comparison API
  const traditionalMonthly = 
    policyDetails?.data?.traditional_monthly_premium ||
    comparison?.data?.comparison_details?.traditional_monthly ||
    comparison?.data?.traditional_monthly ||
    150.00
  
  const monthlyPremium = 
    policyDetails?.data?.monthly_premium ||
    premium?.data?.monthly_premium ||
    127.50

  // If policyDetails exists, use it and map field names
  const policy = policyDetails?.data ? {
    ...policyDetails.data,
    // Map API field names to component field names
    traditional_premium: policyDetails.data.traditional_monthly_premium || traditionalMonthly,
    start_date: policyDetails.data.effective_date,
    end_date: policyDetails.data.expiration_date,
  } : {
    policy_number: premium?.data?.policy_number || `POL-2024-${String(premium?.data?.premium_id || 1).padStart(3, '0')}`,
    policy_status: premium?.data?.status || 'active',
    policy_type: 'PHYD',
    monthly_premium: monthlyPremium,
    traditional_premium: traditionalMonthly,
    monthly_savings: traditionalMonthly - monthlyPremium,
    annual_savings: (traditionalMonthly - monthlyPremium) * 12,
    discount_percentage: 
      comparison?.data?.savings_percentage ||
      15.0,
    start_date: premium?.data?.effective_date || '2023-12-31',
    end_date: premium?.data?.expiration_date || '2024-12-30',
    last_updated: premium?.data?.effective_date || null,
    coverage_type: 'Comprehensive',
    coverage_limit: 100000.00,
    deductible: 1000.00
  }
  
  // Ensure all numeric fields are valid numbers
  if (isNaN(policy.traditional_premium) || !isFinite(policy.traditional_premium)) {
    policy.traditional_premium = 150.00
  }
  if (isNaN(policy.monthly_premium) || !isFinite(policy.monthly_premium)) {
    policy.monthly_premium = monthlyPremium
  }
  if (isNaN(policy.monthly_savings) || !isFinite(policy.monthly_savings)) {
    policy.monthly_savings = policy.traditional_premium - policy.monthly_premium
  }
  if (isNaN(policy.annual_savings) || !isFinite(policy.annual_savings)) {
    policy.annual_savings = policy.monthly_savings * 12
  }

  // Format dates
  const formatDate = (dateString) => {
    if (!dateString) return 'Never'
    const date = new Date(dateString)
    return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })
  }

  // Format currency
  const formatCurrency = (amount) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 2
    }).format(amount)
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-cyan-50 via-blue-50 via-indigo-50 to-purple-50 relative overflow-hidden">
      {/* Animated Background Elements */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        <div className="absolute top-1/4 left-1/4 w-96 h-96 bg-cyan-200 rounded-full mix-blend-multiply filter blur-3xl opacity-20 animate-blob" />
        <div className="absolute top-1/3 right-1/4 w-96 h-96 bg-violet-200 rounded-full mix-blend-multiply filter blur-3xl opacity-20 animate-blob animation-delay-2000" />
        <div className="absolute bottom-1/4 left-1/3 w-96 h-96 bg-fuchsia-200 rounded-full mix-blend-multiply filter blur-3xl opacity-20 animate-blob animation-delay-4000" />
      </div>

      <div className="relative z-10 space-y-6 p-6">
        {/* Header */}
        <div className="bg-white/80 backdrop-blur-xl rounded-2xl shadow-lg border border-white/30 p-6">
          <div className="flex justify-between items-start">
            <div>
              <h1 className="text-3xl md:text-4xl font-bold bg-gradient-to-r from-cyan-600 via-blue-600 to-purple-600 bg-clip-text text-transparent">Insurance Policy</h1>
              <p className="text-gray-600 mt-1 text-lg">Your usage-based insurance details</p>
            </div>
            <button
              onClick={handleRecalculate}
              disabled={isRecalculating}
              className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              <BoltIcon className="w-5 h-5" />
              {isRecalculating ? 'Recalculating...' : 'Recalculate Premium'}
            </button>
          </div>
        </div>

      {/* Policy Status Banner */}
      <div className="bg-gradient-to-r from-green-500 to-green-600 rounded-xl shadow-lg p-6 text-white">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            <div className="w-12 h-12 bg-white/20 rounded-full flex items-center justify-center backdrop-blur-sm">
              <CheckCircleIcon className="w-7 h-7 text-white" />
            </div>
            <div>
              <div className="text-lg font-semibold mb-1">Policy Active</div>
              <div className="text-sm text-green-100">Policy #{policy.policy_number}</div>
            </div>
          </div>
          <div className="px-4 py-2 bg-white/20 rounded-lg backdrop-blur-sm">
            <span className="text-sm font-medium">{policy.policy_type}</span>
          </div>
        </div>
      </div>

      {/* Policy Details Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Monthly Premium Card */}
        <div className="bg-white rounded-xl shadow-lg p-6">
          <div className="flex items-center gap-2 mb-4">
            <CurrencyDollarIcon className="w-6 h-6 text-gray-400" />
            <h2 className="text-xl font-semibold text-gray-900">$ Monthly Premium</h2>
          </div>
          <div className="space-y-3">
            <div className="flex items-center gap-2">
              <span className="text-sm text-gray-500 line-through">
                {formatCurrency(policy.traditional_premium)}
              </span>
              <span className="text-xs text-gray-400">Traditional Premium</span>
            </div>
            <div className="text-4xl font-bold text-green-600">
              {formatCurrency(policy.monthly_premium)}
            </div>
            <div className="flex items-center gap-2 text-sm text-green-700 font-medium">
              <ChartBarIcon className="w-4 h-4" />
              <span>Save {formatCurrency(policy.monthly_savings)}/month</span>
            </div>
          </div>
        </div>

        {/* Your Savings Card */}
        <div className="bg-white rounded-xl shadow-lg p-6">
          <h2 className="text-xl font-semibold text-gray-900 mb-4">Your Savings</h2>
          <div className="space-y-4">
            {/* Discount Progress Bar */}
            <div>
              <div className="flex justify-between items-center mb-2">
                <span className="text-sm font-medium text-gray-700">Discount Earned</span>
                <span className="text-sm font-bold text-green-600">{policy.discount_percentage.toFixed(0)}%</span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-3">
                <div 
                  className="bg-green-600 h-3 rounded-full transition-all"
                  style={{ width: `${Math.min(100, policy.discount_percentage)}%` }}
                />
              </div>
            </div>
            <div className="grid grid-cols-2 gap-4 pt-2">
              <div>
                <p className="text-sm text-gray-600">Monthly Savings</p>
                <p className="text-2xl font-bold text-gray-900">{formatCurrency(policy.monthly_savings)}</p>
              </div>
              <div>
                <p className="text-sm text-gray-600">Annual Savings</p>
                <p className="text-2xl font-bold text-gray-900">{formatCurrency(policy.annual_savings)}</p>
              </div>
            </div>
          </div>
        </div>

        {/* Policy Period Card */}
        <div className="bg-white rounded-xl shadow-lg p-6">
          <div className="flex items-center gap-2 mb-4">
            <CalendarIcon className="w-6 h-6 text-gray-400" />
            <h2 className="text-xl font-semibold text-gray-900">Policy Period</h2>
          </div>
          <div className="space-y-3">
            <div>
              <p className="text-sm text-gray-600 mb-1">Start Date</p>
              <p className="text-lg font-semibold text-gray-900">{formatDate(policy.start_date)}</p>
            </div>
            <div>
              <p className="text-sm text-gray-600 mb-1">End Date</p>
              <p className="text-lg font-semibold text-gray-900">{formatDate(policy.end_date)}</p>
            </div>
            <div className="pt-2 border-t border-gray-200">
              <p className="text-sm text-gray-600 mb-1">Last Updated</p>
              <p className="text-sm font-medium text-gray-900">{formatDate(policy.last_updated)}</p>
            </div>
          </div>
        </div>

        {/* Coverage Details Card */}
        <div className="bg-white rounded-xl shadow-lg p-6">
          <div className="flex items-center gap-2 mb-4">
            <ShieldCheckIcon className="w-6 h-6 text-gray-400" />
            <h2 className="text-xl font-semibold text-gray-900">Coverage Details</h2>
          </div>
          <div className="space-y-4">
            <div>
              <p className="text-sm text-gray-600 mb-1">Coverage Type</p>
              <p className="text-lg font-semibold text-gray-900">{policy.coverage_type}</p>
            </div>
            <div>
              <p className="text-sm text-gray-600 mb-1">Coverage Limit</p>
              <p className="text-2xl font-bold text-gray-900">{formatCurrency(policy.coverage_limit)}</p>
            </div>
            <div>
              <p className="text-sm text-gray-600 mb-1">Deductible</p>
              <p className="text-2xl font-bold text-gray-900">{formatCurrency(policy.deductible)}</p>
            </div>
          </div>
        </div>
      </div>
      </div>

      <style>{`
        @keyframes blob {
          0%, 100% {
            transform: translate(0px, 0px) scale(1);
          }
          33% {
            transform: translate(30px, -50px) scale(1.1);
          }
          66% {
            transform: translate(-20px, 20px) scale(0.9);
          }
        }
        .animate-blob {
          animation: blob 7s infinite;
        }
        .animation-delay-2000 {
          animation-delay: 2s;
        }
        .animation-delay-4000 {
          animation-delay: 4s;
        }
      `}</style>
    </div>
  )
}
