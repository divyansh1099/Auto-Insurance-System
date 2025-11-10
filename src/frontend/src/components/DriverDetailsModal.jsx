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
      className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4"
      onClick={handleBackdropClick}
    >
      <div 
        className="bg-white rounded-xl shadow-2xl w-full max-w-4xl max-h-[90vh] overflow-hidden flex flex-col"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-gray-200">
          <div className="flex items-center gap-4">
            <div className="w-16 h-16 bg-blue-600 rounded-full flex items-center justify-center text-white font-semibold text-2xl">
              {getInitials(driverDetails.first_name, driverDetails.last_name)}
            </div>
            <div>
              <h2 className="text-2xl font-bold text-gray-900">
                {driverDetails.first_name} {driverDetails.last_name}
              </h2>
            </div>
          </div>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 transition-colors"
          >
            <XMarkIcon className="w-6 h-6" />
          </button>
        </div>

        {/* Tabs */}
        <div className="border-b border-gray-200 px-6">
          <nav className="flex space-x-8" aria-label="Tabs">
            {tabs.map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`
                  py-4 px-1 border-b-2 font-medium text-sm transition-colors
                  ${
                    activeTab === tab.id
                      ? 'border-blue-500 text-blue-600'
                      : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                  }
                `}
              >
                {tab.name}
              </button>
            ))}
          </nav>
        </div>

        {/* Tab Content */}
        <div className="flex-1 overflow-y-auto p-4">
          {activeTab === 'profile' && (
            <div className="space-y-4">
              {/* Contact Information Cards */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                {/* Email */}
                <div className="bg-white border border-gray-200 rounded-lg p-3">
                  <div className="flex items-center gap-2 mb-1.5">
                    <EnvelopeIcon className="w-4 h-4 text-gray-400" />
                    <label className="text-xs font-medium text-gray-500">Email</label>
                  </div>
                  <p className="text-sm text-gray-900">{driverDetails.email || 'N/A'}</p>
                </div>

                {/* Phone */}
                <div className="bg-white border border-gray-200 rounded-lg p-3">
                  <div className="flex items-center gap-2 mb-1.5">
                    <PhoneIcon className="w-4 h-4 text-gray-400" />
                    <label className="text-xs font-medium text-gray-500">Phone</label>
                  </div>
                  <p className="text-sm text-gray-900">{driverDetails.phone || 'N/A'}</p>
                </div>

                {/* Date of Birth */}
                <div className="bg-white border border-gray-200 rounded-lg p-3">
                  <div className="flex items-center gap-2 mb-1.5">
                    <CalendarIcon className="w-4 h-4 text-gray-400" />
                    <label className="text-xs font-medium text-gray-500">Date of Birth</label>
                  </div>
                  <p className="text-sm text-gray-900">
                    {formatDateOfBirth(driverDetails.date_of_birth)}
                  </p>
                </div>

                {/* License Number */}
                <div className="bg-white border border-gray-200 rounded-lg p-3">
                  <div className="flex items-center gap-2 mb-1.5">
                    <DocumentTextIcon className="w-4 h-4 text-gray-400" />
                    <label className="text-xs font-medium text-gray-500">License Number</label>
                  </div>
                  <p className="text-sm text-gray-900">{driverDetails.license_number || 'N/A'}</p>
                </div>

                {/* License State */}
                <div className="bg-white border border-gray-200 rounded-lg p-3">
                  <div className="flex items-center gap-2 mb-1.5">
                    <DocumentTextIcon className="w-4 h-4 text-gray-400" />
                    <label className="text-xs font-medium text-gray-500">License State</label>
                  </div>
                  <p className="text-sm text-gray-900">{driverDetails.license_state || 'N/A'}</p>
                </div>

                {/* Years Licensed */}
                <div className="bg-white border border-gray-200 rounded-lg p-3">
                  <div className="flex items-center gap-2 mb-1.5">
                    <CalendarIcon className="w-4 h-4 text-gray-400" />
                    <label className="text-xs font-medium text-gray-500">Years Licensed</label>
                  </div>
                  <p className="text-sm text-gray-900">{driverDetails.years_licensed ? `${driverDetails.years_licensed} years` : 'N/A'}</p>
                </div>

                {/* Gender */}
                <div className="bg-white border border-gray-200 rounded-lg p-3">
                  <div className="flex items-center gap-2 mb-1.5">
                    <label className="text-xs font-medium text-gray-500">Gender</label>
                  </div>
                  <p className="text-sm text-gray-900">{driverDetails.gender || 'N/A'}</p>
                </div>

                {/* Marital Status */}
                <div className="bg-white border border-gray-200 rounded-lg p-3">
                  <div className="flex items-center gap-2 mb-1.5">
                    <label className="text-xs font-medium text-gray-500">Marital Status</label>
                  </div>
                  <p className="text-sm text-gray-900">{driverDetails.marital_status || 'N/A'}</p>
                </div>

                {/* Address - Full Width */}
                <div className="bg-white border border-gray-200 rounded-lg p-3 md:col-span-2">
                  <div className="flex items-center gap-2 mb-1.5">
                    <MapPinIcon className="w-4 h-4 text-gray-400" />
                    <label className="text-xs font-medium text-gray-500">Address</label>
                  </div>
                  <p className="text-sm text-gray-900">
                    {driverDetails.full_address || formatAddress(driverDetails)}
                  </p>
                </div>
              </div>

              {/* Driving Metrics Cards */}
              <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                {/* Safety Score */}
                <div className="bg-green-100 rounded-lg p-4 text-center">
                  <p className="text-xs font-medium text-gray-600 mb-1.5">Safety Score</p>
                  <p className="text-2xl font-bold text-gray-900">
                    {driverDetails.safety_score?.toFixed(0) || 'N/A'}
                  </p>
                </div>

                {/* Risk Score */}
                <div className="bg-blue-100 rounded-lg p-4 text-center">
                  <p className="text-xs font-medium text-gray-600 mb-1.5">Risk Score</p>
                  <p className="text-2xl font-bold text-gray-900">
                    {driverDetails.risk_score?.toFixed(0) || 'N/A'}
                  </p>
                </div>

                {/* Total Miles */}
                <div className="bg-purple-100 rounded-lg p-4 text-center">
                  <p className="text-xs font-medium text-gray-600 mb-1.5">Total Miles</p>
                  <p className="text-2xl font-bold text-gray-900">
                    {driverDetails.total_miles?.toFixed(0) || '0'}
                  </p>
                </div>

                {/* Total Trips */}
                <div className="bg-yellow-100 rounded-lg p-4 text-center">
                  <p className="text-xs font-medium text-gray-600 mb-1.5">Total Trips</p>
                  <p className="text-2xl font-bold text-gray-900">
                    {driverDetails.total_trips || 0}
                  </p>
                </div>
              </div>
            </div>
          )}

          {activeTab === 'policy' && (
            <div className="space-y-4">
              {driverDetails.policy_type ? (
                <>
                  {/* Policy Status Tags */}
                  <div className="flex gap-2 mb-4">
                    {driverDetails.policy_type && (
                      <span className="px-3 py-1 rounded text-sm font-semibold bg-blue-100 text-blue-800">
                        {driverDetails.policy_type}
                      </span>
                    )}
                    {driverDetails.policy_status && (
                      <span className="px-3 py-1 rounded text-sm font-semibold bg-green-100 text-green-800">
                        {driverDetails.policy_status}
                      </span>
                    )}
                  </div>

                  {/* Policy Information Grid */}
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                    {/* Policy Number */}
                    <div className="bg-white border border-gray-200 rounded-lg p-3">
                      <p className="text-xs text-gray-500 mb-1">Policy Number</p>
                      <p className="text-sm font-semibold text-gray-900">
                        {driverDetails.policy_number || 'N/A'}
                      </p>
                    </div>

                    {/* Coverage Type */}
                    <div className="bg-white border border-gray-200 rounded-lg p-3">
                      <p className="text-xs text-gray-500 mb-1">Coverage Type</p>
                      <p className="text-sm font-semibold text-gray-900">
                        {driverDetails.coverage_type || 'N/A'}
                      </p>
                    </div>

                    {/* Base Premium */}
                    <div className="bg-blue-50 border border-blue-200 rounded-lg p-3">
                      <p className="text-xs text-gray-500 mb-1">Base Premium</p>
                      <p className="text-sm font-semibold text-gray-900 line-through">
                        ${driverDetails.base_premium?.toFixed(2) || 'N/A'}
                      </p>
                    </div>

                    {/* Current Premium */}
                    <div className="bg-green-50 border border-green-200 rounded-lg p-3">
                      <p className="text-xs text-gray-500 mb-1">Current Premium</p>
                      <p className="text-sm font-semibold text-green-700">
                        ${driverDetails.current_premium?.toFixed(2) || driverDetails.monthly_premium?.toFixed(2) || 'N/A'}
                      </p>
                    </div>

                    {/* Discount */}
                    <div className="bg-purple-50 border border-purple-200 rounded-lg p-3">
                      <p className="text-xs text-gray-500 mb-1">Discount</p>
                      <p className="text-sm font-semibold text-purple-700">
                        {driverDetails.discount_percentage?.toFixed(0) || 0}%
                      </p>
                    </div>

                    {/* Annual Savings */}
                    <div className="bg-orange-50 border border-orange-200 rounded-lg p-3">
                      <p className="text-xs text-gray-500 mb-1">Annual Savings</p>
                      <p className="text-sm font-semibold text-orange-700">
                        ${driverDetails.annual_savings?.toFixed(2) || '0.00'}
                      </p>
                    </div>

                    {/* Start Date */}
                    <div className="bg-white border border-gray-200 rounded-lg p-3">
                      <p className="text-xs text-gray-500 mb-1">Start Date</p>
                      <p className="text-sm font-semibold text-gray-900">
                        {driverDetails.effective_date ? formatDateOfBirth(driverDetails.effective_date) : 'N/A'}
                      </p>
                    </div>

                    {/* End Date */}
                    <div className="bg-white border border-gray-200 rounded-lg p-3">
                      <p className="text-xs text-gray-500 mb-1">End Date</p>
                      <p className="text-sm font-semibold text-gray-900">
                        {driverDetails.expiration_date ? formatDateOfBirth(driverDetails.expiration_date) : 'N/A'}
                      </p>
                    </div>
                  </div>

                  {/* Additional Policy Details */}
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-3 mt-4">
                    {/* Coverage Limit */}
                    <div className="bg-gray-50 rounded-lg p-3">
                      <p className="text-xs font-medium text-gray-500 mb-1">Coverage Limit</p>
                      <p className="text-sm font-semibold text-gray-900">
                        ${driverDetails.coverage_limit?.toLocaleString() || 'N/A'}
                      </p>
                    </div>

                    {/* Deductible */}
                    <div className="bg-gray-50 rounded-lg p-3">
                      <p className="text-xs font-medium text-gray-500 mb-1">Deductible</p>
                      <p className="text-sm font-semibold text-gray-900">
                        ${driverDetails.deductible?.toLocaleString() || 'N/A'}
                      </p>
                    </div>

                    {/* Miles Used (PAYD only) */}
                    {driverDetails.policy_type === 'PAYD' && driverDetails.total_miles_allowed && (
                      <div className="bg-gray-50 rounded-lg p-3">
                        <p className="text-xs font-medium text-gray-500 mb-1">Miles Used</p>
                        <p className="text-sm font-semibold text-gray-900">
                          {driverDetails.miles_used?.toLocaleString() || 0} / {driverDetails.total_miles_allowed?.toLocaleString()}
                        </p>
                      </div>
                    )}
                  </div>
                </>
              ) : (
                <div className="text-center py-12">
                  <p className="text-gray-500">No active policy found</p>
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

