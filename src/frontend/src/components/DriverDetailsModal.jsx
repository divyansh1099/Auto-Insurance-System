import { useState } from 'react'
import { useQuery } from 'react-query'
import { adminAPI } from '../services/api'
import {
  XMarkIcon,
  EnvelopeIcon,
  PhoneIcon,
  CalendarIcon,
  DocumentTextIcon,
  MapPinIcon,
  TrophyIcon,
  CheckCircleIcon,
} from '@heroicons/react/24/outline'

export default function DriverDetailsModal({ driverId, onClose }) {
  const [activeTab, setActiveTab] = useState('profile')

  // Fetch driver details
  const { data: driverDetails, isLoading } = useQuery(
    ['driverDetails', driverId],
    () => adminAPI.getDriverDetails(driverId),
    {
      retry: false,
      enabled: !!driverId,
      // Mock data transformation until backend is ready
      select: (data) => {
        const driver = data?.data || data || {}
        return {
          ...driver,
          // Mock enriched data
          safety_score: driver.safety_score || (100 - (driver.risk_score || 50)),
          risk_score: driver.risk_score || 50,
          total_miles: driver.total_miles || 0,
          total_trips: driver.total_trips || 0,
          full_address: driver.full_address || formatAddress(driver),
        }
      }
    }
  )

  const formatAddress = (driver) => {
    if (!driver) return 'N/A'
    const parts = []
    if (driver.address) parts.push(driver.address)
    if (driver.city) parts.push(driver.city)
    if (driver.state) parts.push(driver.state)
    if (driver.zip_code) parts.push(driver.zip_code)
    return parts.length > 0 ? parts.join(', ') : 'N/A'
  }

  const formatDateOfBirth = (dateString) => {
    if (!dateString) return 'N/A'
    try {
      const date = new Date(dateString)
      return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })
    } catch {
      return 'N/A'
    }
  }

  const getInitials = (firstName, lastName) => {
    const first = firstName?.charAt(0)?.toUpperCase() || ''
    return first
  }

  const tabs = [
    { id: 'profile', name: 'Profile' },
    { id: 'policy', name: 'Policy' },
    { id: 'rewards', name: 'Rewards' },
  ]

  if (isLoading) {
    return (
      <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
        <div className="bg-white rounded-lg p-12">
          <p className="text-gray-500">Loading driver details...</p>
        </div>
      </div>
    )
  }

  if (!driverDetails) {
    return null
  }

  const handleBackdropClick = (e) => {
    if (e.target === e.currentTarget) {
      onClose()
    }
  }

  return (
    <div
      className="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-50 p-4"
      onClick={handleBackdropClick}
    >
      <div
        className="bg-white dark:bg-gray-800 rounded-2xl shadow-2xl w-full max-w-4xl max-h-[90vh] overflow-hidden flex flex-col border border-gray-200 dark:border-gray-700"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-gray-200 dark:border-gray-700 bg-gradient-to-r from-blue-50 to-purple-50 dark:from-gray-800 dark:to-gray-800">
          <div className="flex items-center gap-4">
            <div className="w-16 h-16 bg-gradient-to-br from-blue-500 to-blue-600 dark:from-blue-600 dark:to-blue-700 rounded-full flex items-center justify-center text-white font-semibold text-2xl shadow-lg ring-4 ring-blue-100 dark:ring-blue-900/50">
              {getInitials(driverDetails.first_name, driverDetails.last_name)}
            </div>
            <div>
              <h2 className="text-2xl font-bold text-gray-900 dark:text-white">
                {driverDetails.first_name} {driverDetails.last_name}
              </h2>
            </div>
          </div>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 transition-colors p-2 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg"
          >
            <XMarkIcon className="w-6 h-6" />
          </button>
        </div>

        {/* Tabs */}
        <div className="border-b border-gray-200 dark:border-gray-700 px-6 bg-gray-50 dark:bg-gray-800/50">
          <nav className="flex space-x-8" aria-label="Tabs">
            {tabs.map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`
                  py-4 px-1 border-b-2 font-medium text-sm transition-colors
                  ${activeTab === tab.id
                    ? 'border-blue-500 text-blue-600 dark:text-blue-400'
                    : 'border-transparent text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-300 hover:border-gray-300 dark:hover:border-gray-600'
                  }
                `}
              >
                {tab.name}
              </button>
            ))}
          </nav>
        </div>

        {/* Tab Content */}
        <div className="flex-1 overflow-y-auto p-6 bg-gray-50 dark:bg-gray-900">
          {activeTab === 'profile' && (
            <div className="space-y-4">
              {/* Contact Information Cards */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                {/* Email */}
                <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-3">
                  <div className="flex items-center gap-2 mb-1.5">
                    <EnvelopeIcon className="w-4 h-4 text-gray-400 dark:text-gray-500" />
                    <label className="text-xs font-medium text-gray-500 dark:text-gray-400">Email</label>
                  </div>
                  <p className="text-sm text-gray-900 dark:text-white">{driverDetails.email || 'N/A'}</p>
                </div>

                {/* Phone */}
                <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-3">
                  <div className="flex items-center gap-2 mb-1.5">
                    <PhoneIcon className="w-4 h-4 text-gray-400 dark:text-gray-500" />
                    <label className="text-xs font-medium text-gray-500 dark:text-gray-400">Phone</label>
                  </div>
                  <p className="text-sm text-gray-900 dark:text-white">{driverDetails.phone || 'N/A'}</p>
                </div>

                {/* Date of Birth */}
                <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-3">
                  <div className="flex items-center gap-2 mb-1.5">
                    <CalendarIcon className="w-4 h-4 text-gray-400 dark:text-gray-500" />
                    <label className="text-xs font-medium text-gray-500 dark:text-gray-400">Date of Birth</label>
                  </div>
                  <p className="text-sm text-gray-900 dark:text-white">
                    {formatDateOfBirth(driverDetails.date_of_birth)}
                  </p>
                </div>

                {/* License Number */}
                <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-3">
                  <div className="flex items-center gap-2 mb-1.5">
                    <DocumentTextIcon className="w-4 h-4 text-gray-400 dark:text-gray-500" />
                    <label className="text-xs font-medium text-gray-500 dark:text-gray-400">License Number</label>
                  </div>
                  <p className="text-sm text-gray-900 dark:text-white">{driverDetails.license_number || 'N/A'}</p>
                </div>

                {/* License State */}
                <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-3">
                  <div className="flex items-center gap-2 mb-1.5">
                    <DocumentTextIcon className="w-4 h-4 text-gray-400 dark:text-gray-500" />
                    <label className="text-xs font-medium text-gray-500 dark:text-gray-400">License State</label>
                  </div>
                  <p className="text-sm text-gray-900 dark:text-white">{driverDetails.license_state || 'N/A'}</p>
                </div>

                {/* Years Licensed */}
                <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-3">
                  <div className="flex items-center gap-2 mb-1.5">
                    <CalendarIcon className="w-4 h-4 text-gray-400 dark:text-gray-500" />
                    <label className="text-xs font-medium text-gray-500 dark:text-gray-400">Years Licensed</label>
                  </div>
                  <p className="text-sm text-gray-900 dark:text-white">{driverDetails.years_licensed ? `${driverDetails.years_licensed} years` : 'N/A'}</p>
                </div>

                {/* Gender */}
                <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-3">
                  <div className="flex items-center gap-2 mb-1.5">
                    <label className="text-xs font-medium text-gray-500 dark:text-gray-400">Gender</label>
                  </div>
                  <p className="text-sm text-gray-900 dark:text-white">{driverDetails.gender || 'N/A'}</p>
                </div>

                {/* Marital Status */}
                <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-3">
                  <div className="flex items-center gap-2 mb-1.5">
                    <label className="text-xs font-medium text-gray-500 dark:text-gray-400">Marital Status</label>
                  </div>
                  <p className="text-sm text-gray-900 dark:text-white">{driverDetails.marital_status || 'N/A'}</p>
                </div>

                {/* Address - Full Width */}
                <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-3 md:col-span-2">
                  <div className="flex items-center gap-2 mb-1.5">
                    <MapPinIcon className="w-4 h-4 text-gray-400 dark:text-gray-500" />
                    <label className="text-xs font-medium text-gray-500 dark:text-gray-400">Address</label>
                  </div>
                  <p className="text-sm text-gray-900 dark:text-white">
                    {driverDetails.full_address || formatAddress(driverDetails)}
                  </p>
                </div>
              </div>

              {/* Driving Metrics Cards */}
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                {/* Safety Score */}
                <div className="bg-gradient-to-br from-green-500 to-green-600 dark:from-green-600 dark:to-green-700 rounded-xl p-5 text-center shadow-lg">
                  <p className="text-xs font-medium text-white/80 mb-2">Safety Score</p>
                  <p className="text-3xl font-bold text-white">
                    {driverDetails.safety_score?.toFixed(0) || 'N/A'}
                  </p>
                </div>

                {/* Risk Score */}
                <div className="bg-gradient-to-br from-blue-500 to-blue-600 dark:from-blue-600 dark:to-blue-700 rounded-xl p-5 text-center shadow-lg">
                  <p className="text-xs font-medium text-white/80 mb-2">Risk Score</p>
                  <p className="text-3xl font-bold text-white">
                    {driverDetails.risk_score?.toFixed(0) || 'N/A'}
                  </p>
                </div>

                {/* Total Miles */}
                <div className="bg-gradient-to-br from-purple-500 to-purple-600 dark:from-purple-600 dark:to-purple-700 rounded-xl p-5 text-center shadow-lg">
                  <p className="text-xs font-medium text-white/80 mb-2">Total Miles</p>
                  <p className="text-3xl font-bold text-white">
                    {driverDetails.total_miles?.toFixed(0) || '0'}
                  </p>
                </div>

                {/* Total Trips */}
                <div className="bg-gradient-to-br from-yellow-500 to-yellow-600 dark:from-yellow-600 dark:to-yellow-700 rounded-xl p-5 text-center shadow-lg">
                  <p className="text-xs font-medium text-white/80 mb-2">Total Trips</p>
                  <p className="text-3xl font-bold text-white">
                    {driverDetails.total_trips || 0}
                  </p>
                </div>
              </div>
            </div>
          )}

          {activeTab === 'policy' && (
            <div className="space-y-6">
              {driverDetails.policy_type ? (
                <>
                  {/* Policy Status Tags */}
                  <div className="flex gap-2">
                    {driverDetails.policy_type && (
                      <span className="px-4 py-2 rounded-lg text-sm font-semibold bg-blue-600 dark:bg-blue-500 text-white shadow-sm">
                        {driverDetails.policy_type}
                      </span>
                    )}
                    {driverDetails.policy_status && (
                      <span className="px-4 py-2 rounded-lg text-sm font-semibold bg-green-600 dark:bg-green-500 text-white shadow-sm">
                        {driverDetails.policy_status}
                      </span>
                    )}
                  </div>

                  {/* Policy Information Grid */}
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                    {/* Policy Number */}
                    <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-xl p-4 shadow-sm">
                      <p className="text-xs text-gray-500 dark:text-gray-400 mb-2">Policy Number</p>
                      <p className="text-sm font-semibold text-gray-900 dark:text-white">
                        {driverDetails.policy_number || 'N/A'}
                      </p>
                    </div>

                    {/* Coverage Type */}
                    <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-xl p-4 shadow-sm">
                      <p className="text-xs text-gray-500 dark:text-gray-400 mb-2">Coverage Type</p>
                      <p className="text-sm font-semibold text-gray-900 dark:text-white">
                        {driverDetails.coverage_type || 'N/A'}
                      </p>
                    </div>

                    {/* Base Premium */}
                    <div className="bg-gradient-to-br from-gray-100 to-gray-200 dark:from-gray-700 dark:to-gray-800 border border-gray-300 dark:border-gray-600 rounded-xl p-4 shadow-sm">
                      <p className="text-xs text-gray-600 dark:text-gray-400 mb-2">Base Premium</p>
                      <p className="text-sm font-semibold text-gray-700 dark:text-gray-300 line-through">
                        ${driverDetails.base_premium?.toFixed(2) || 'N/A'}
                      </p>
                    </div>

                    {/* Current Premium */}
                    <div className="bg-gradient-to-br from-green-500 to-green-600 dark:from-green-600 dark:to-green-700 rounded-xl p-4 shadow-lg">
                      <p className="text-xs text-white/80 mb-2">Current Premium</p>
                      <p className="text-lg font-bold text-white">
                        ${driverDetails.current_premium?.toFixed(2) || driverDetails.monthly_premium?.toFixed(2) || 'N/A'}
                      </p>
                    </div>

                    {/* Discount */}
                    <div className="bg-gradient-to-br from-purple-500 to-purple-600 dark:from-purple-600 dark:to-purple-700 rounded-xl p-4 shadow-lg">
                      <p className="text-xs text-white/80 mb-2">Discount</p>
                      <p className="text-lg font-bold text-white">
                        {driverDetails.discount_percentage?.toFixed(0) || 0}%
                      </p>
                    </div>

                    {/* Annual Savings */}
                    <div className="bg-gradient-to-br from-orange-500 to-orange-600 dark:from-orange-600 dark:to-orange-700 rounded-xl p-4 shadow-lg">
                      <p className="text-xs text-white/80 mb-2">Annual Savings</p>
                      <p className="text-lg font-bold text-white">
                        ${driverDetails.annual_savings?.toFixed(2) || '0.00'}
                      </p>
                    </div>

                    {/* Start Date */}
                    <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-xl p-4 shadow-sm">
                      <p className="text-xs text-gray-500 dark:text-gray-400 mb-2">Start Date</p>
                      <p className="text-sm font-semibold text-gray-900 dark:text-white">
                        {driverDetails.effective_date ? formatDateOfBirth(driverDetails.effective_date) : 'N/A'}
                      </p>
                    </div>

                    {/* End Date */}
                    <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-xl p-4 shadow-sm">
                      <p className="text-xs text-gray-500 dark:text-gray-400 mb-2">End Date</p>
                      <p className="text-sm font-semibold text-gray-900 dark:text-white">
                        {driverDetails.expiration_date ? formatDateOfBirth(driverDetails.expiration_date) : 'N/A'}
                      </p>
                    </div>
                  </div>

                  {/* Additional Policy Details */}
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                    {/* Coverage Limit */}
                    <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-xl p-4 shadow-sm">
                      <p className="text-xs font-medium text-gray-500 dark:text-gray-400 mb-2">Coverage Limit</p>
                      <p className="text-lg font-semibold text-gray-900 dark:text-white">
                        ${driverDetails.coverage_limit?.toLocaleString() || 'N/A'}
                      </p>
                    </div>

                    {/* Deductible */}
                    <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-xl p-4 shadow-sm">
                      <p className="text-xs font-medium text-gray-500 dark:text-gray-400 mb-2">Deductible</p>
                      <p className="text-lg font-semibold text-gray-900 dark:text-white">
                        ${driverDetails.deductible?.toLocaleString() || 'N/A'}
                      </p>
                    </div>

                    {/* Miles Used (PAYD only) */}
                    {driverDetails.policy_type === 'PAYD' && driverDetails.total_miles_allowed && (
                      <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-xl p-4 shadow-sm">
                        <p className="text-xs font-medium text-gray-500 dark:text-gray-400 mb-2">Miles Used</p>
                        <p className="text-lg font-semibold text-gray-900 dark:text-white">
                          {driverDetails.miles_used?.toLocaleString() || 0} / {driverDetails.total_miles_allowed?.toLocaleString()}
                        </p>
                      </div>
                    )}
                  </div>
                </>
              ) : (
                <div className="text-center py-12">
                  <p className="text-gray-500 dark:text-gray-400">No active policy found</p>
                </div>
              )}
            </div>
          )}

          {activeTab === 'rewards' && (
            <div className="space-y-6">
              {/* Total Reward Points Card */}
              <div className="bg-gradient-to-br from-orange-500 to-orange-600 rounded-xl shadow-lg p-8 text-white text-center">
                <p className="text-sm font-medium opacity-90 mb-2">Total Reward Points</p>
                <div className="text-5xl font-bold mb-2">
                  {driverDetails.reward_points || 0}
                </div>
                <TrophyIcon className="w-12 h-12 mx-auto opacity-80" />
              </div>

              {/* Achievements Section */}
              <div>
                <h3 className="text-lg font-semibold text-gray-900 mb-4">Achievements Earned</h3>
                {driverDetails.achievements && driverDetails.achievements.length > 0 ? (
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                    {driverDetails.achievements.map((achievement, idx) => (
                      <div
                        key={idx}
                        className="bg-green-100 border border-green-200 rounded-lg p-4 flex items-center gap-3"
                      >
                        <CheckCircleIcon className="w-6 h-6 text-green-600" />
                        <div>
                          <p className="text-sm font-semibold text-gray-900">
                            {achievement.achievement_name}
                          </p>
                          {achievement.achievement_description && (
                            <p className="text-xs text-gray-600">
                              {achievement.achievement_description}
                            </p>
                          )}
                        </div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="text-center py-8 text-gray-500">
                    <p>No achievements earned yet</p>
                    <p className="text-sm text-gray-400 mt-1">Keep driving safely to earn achievements!</p>
                  </div>
                )}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

