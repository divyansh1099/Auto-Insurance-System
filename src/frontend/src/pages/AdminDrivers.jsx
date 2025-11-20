import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from 'react-query'
import { adminAPI } from '../services/api'
import DriverForm from '../components/forms/DriverForm'
import DriverDetailsModal from '../components/DriverDetailsModal'
import {
  UserGroupIcon,
  PhoneIcon,
  MapPinIcon,
  EyeIcon,
  EnvelopeIcon,
} from '@heroicons/react/24/outline'
import { MagnifyingGlassIcon } from '@heroicons/react/24/solid'

export default function AdminDrivers() {
  const [page, setPage] = useState(1)
  const [search, setSearch] = useState('')
  const [showCreateModal, setShowCreateModal] = useState(false)
  const [editingDriver, setEditingDriver] = useState(null)
  const [viewingDriverId, setViewingDriverId] = useState(null)
  const limit = 20

  const queryClient = useQueryClient()

  const { data, isLoading } = useQuery(
    ['adminDrivers', page, search],
    () => adminAPI.listDrivers((page - 1) * limit, limit, search),
    {
      retry: false,
      // Transform data to include enriched fields (will be replaced when backend is ready)
      select: (data) => {
        const drivers = data?.data || data || []
        return drivers.map(driver => ({
          ...driver,
          // Mock enriched data - will be replaced by backend
          safety_score: driver.safety_score || (100 - (driver.risk_score || 50)),
          risk_score: driver.risk_score || 50,
          total_trips: driver.total_trips || 0,
          reward_points: driver.reward_points || Math.floor((driver.safety_score || 50) * 5),
          policy_type: driver.policy_type || 'PHYD',
          policy_status: driver.policy_status || 'active',
          monthly_premium: driver.monthly_premium || 127.50,
          discount_percentage: driver.discount_percentage || 15,
        }))
      }
    }
  )

  const deleteMutation = useMutation(
    (driverId) => adminAPI.deleteDriver(driverId),
    {
      onSuccess: () => {
        queryClient.invalidateQueries('adminDrivers')
      }
    }
  )

  const drivers = data || []
  const total = drivers.length

  const handleDelete = async (driverId) => {
    if (window.confirm('Are you sure you want to delete this driver?')) {
      try {
        await deleteMutation.mutateAsync(driverId)
      } catch (error) {
        alert('Error deleting driver: ' + error.response?.data?.detail)
      }
    }
  }

  const getInitials = (firstName, lastName) => {
    const first = firstName?.charAt(0)?.toUpperCase() || ''
    return first
  }

  const formatPhone = (phone) => {
    if (!phone) return 'N/A'
    // Format phone number if needed
    return phone
  }

  const formatLocation = (city, state) => {
    if (!city && !state) return 'N/A'
    if (city && state) return `${city}, ${state}`
    return city || state || 'N/A'
  }

  const formatPremium = (premium) => {
    if (!premium) return 'N/A'
    return `$${premium.toFixed(2)}/mo`
  }

  const getPolicyTypeColor = (policyType) => {
    switch (policyType?.toUpperCase()) {
      case 'PHYD':
      case 'PAYD':
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

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center gap-3">
        <UserGroupIcon className="w-8 h-8 text-blue-600 dark:text-blue-400" />
        <div>
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white">Driver Management</h1>
          <p className="text-gray-600 dark:text-gray-400 mt-1">View and manage all drivers in the system</p>
        </div>
      </div>

      {/* Search Bar */}
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-4 transition-colors duration-200">
        <div className="relative">
          <MagnifyingGlassIcon className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-400" />
          <input
            type="text"
            placeholder="Search by name or email..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full pl-10 pr-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent bg-white dark:bg-gray-700 text-gray-900 dark:text-white placeholder-gray-500 dark:placeholder-gray-400"
          />
        </div>
      </div>

      {/* Driver Cards */}
      <div className="space-y-4">
        {isLoading ? (
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-12 text-center transition-colors duration-200">
            <p className="text-gray-500 dark:text-gray-400">Loading drivers...</p>
          </div>
        ) : drivers.length === 0 ? (
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-12 text-center transition-colors duration-200">
            <p className="text-gray-500 dark:text-gray-400 mb-2">No drivers found</p>
            <p className="text-sm text-gray-400 dark:text-gray-500">
              {search ? 'Try adjusting your search criteria' : 'Get started by adding a driver'}
            </p>
          </div>
        ) : (
          drivers.map((driver) => (
            <div
              key={driver.driver_id}
              className="bg-white dark:bg-gray-800 rounded-lg shadow-lg p-6 hover:shadow-xl transition-all duration-200 relative"
            >
              <div className="flex flex-col lg:flex-row gap-6">
                {/* Left Section - Profile & Contact */}
                <div className="flex items-start gap-4 flex-1">
                  {/* Avatar */}
                  <div className="w-16 h-16 bg-blue-600 dark:bg-blue-500 rounded-full flex items-center justify-center text-white font-semibold text-2xl flex-shrink-0">
                    {getInitials(driver.first_name, driver.last_name)}
                  </div>

                  {/* Name & Contact Info */}
                  <div className="flex-1 min-w-0">
                    <h3 className="text-xl font-bold text-gray-900 dark:text-white mb-3">
                      {driver.first_name} {driver.last_name}
                    </h3>

                    {/* Contact Information with Icons */}
                    <div className="space-y-2 text-sm text-gray-600 dark:text-gray-400">
                      <div className="flex items-center gap-2">
                        <EnvelopeIcon className="w-4 h-4 text-gray-400 flex-shrink-0" />
                        <span className="truncate">{driver.email || 'N/A'}</span>
                      </div>
                      <div className="flex items-center gap-2">
                        <PhoneIcon className="w-4 h-4 text-gray-400 flex-shrink-0" />
                        <span>{formatPhone(driver.phone)}</span>
                      </div>
                      <div className="flex items-center gap-2">
                        <MapPinIcon className="w-4 h-4 text-gray-400 flex-shrink-0" />
                        <span>{formatLocation(driver.city, driver.state)}</span>
                      </div>
                    </div>
                  </div>
                </div>

                {/* Middle Section - Performance Metrics (2x2 Grid) */}
                <div className="grid grid-cols-2 gap-4 flex-1 max-w-md">
                  <div>
                    <p className="text-xs text-gray-500 dark:text-gray-400 mb-1">Safety Score</p>
                    <p className="text-3xl font-bold text-green-600 dark:text-green-400">
                      {driver.safety_score?.toFixed(0) || 'N/A'}
                    </p>
                  </div>
                  <div>
                    <p className="text-xs text-gray-500 dark:text-gray-400 mb-1">Risk Score</p>
                    <p className="text-3xl font-bold text-orange-600 dark:text-orange-400">
                      {driver.risk_score?.toFixed(0) || 'N/A'}
                    </p>
                  </div>
                  <div>
                    <p className="text-xs text-gray-500 dark:text-gray-400 mb-1">Total Trips</p>
                    <p className="text-3xl font-bold text-gray-900 dark:text-white">
                      {driver.total_trips || 0}
                    </p>
                  </div>
                  <div>
                    <p className="text-xs text-gray-500 dark:text-gray-400 mb-1">Reward Points</p>
                    <p className="text-3xl font-bold text-orange-600 dark:text-orange-400">
                      {driver.reward_points || 0}
                    </p>
                  </div>
                </div>

                {/* Right Section - Policy Details */}
                <div className="flex flex-col items-end justify-between gap-3 min-w-[200px]">
                  {/* Policy Badges */}
                  <div className="flex flex-wrap gap-2 justify-end">
                    {driver.policy_type && (
                      <span className="px-3 py-1 rounded text-xs font-semibold bg-blue-600 text-white">
                        {driver.policy_type}
                      </span>
                    )}
                    {driver.policy_status && (
                      <span className={`px-3 py-1 rounded text-xs font-semibold ${getStatusColor(driver.policy_status)}`}>
                        {driver.policy_status}
                      </span>
                    )}
                  </div>

                  {/* Premium & Discount */}
                  {driver.monthly_premium && (
                    <div className="text-right">
                      <p className="text-sm text-gray-900 dark:text-white font-medium">
                        Premium: <span className="font-semibold">{formatPremium(driver.monthly_premium)}</span>
                      </p>
                      {driver.discount_percentage && driver.discount_percentage > 0 && (
                        <div className="flex items-center justify-end gap-1 mt-1">
                          <svg className="w-4 h-4 text-green-600 dark:text-green-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                          </svg>
                          <span className="text-sm font-semibold text-green-600 dark:text-green-400">
                            {driver.discount_percentage.toFixed(0)}% discount
                          </span>
                        </div>
                      )}
                    </div>
                  )}

                  {/* View Details Button */}
                  <button
                    onClick={() => setViewingDriverId(driver.driver_id)}
                    className="inline-flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors text-sm font-medium shadow-sm"
                  >
                    <EyeIcon className="w-4 h-4" />
                    View Details
                  </button>
                </div>
              </div>
            </div>
          ))
        )}
      </div>

      {/* Pagination */}
      {total > 0 && (
        <div className="flex justify-between items-center">
          <div className="text-sm text-gray-700 dark:text-gray-300">
            Showing {(page - 1) * limit + 1} to {Math.min(page * limit, total)} of {total}
          </div>
          <div className="flex gap-2">
            <button
              onClick={() => setPage(p => Math.max(1, p - 1))}
              disabled={page === 1}
              className="px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-50 dark:hover:bg-gray-700 text-gray-700 dark:text-gray-200 bg-white dark:bg-gray-800"
            >
              Previous
            </button>
            <button
              onClick={() => setPage(p => p + 1)}
              disabled={drivers.length < limit}
              className="px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-50 dark:hover:bg-gray-700 text-gray-700 dark:text-gray-200 bg-white dark:bg-gray-800"
            >
              Next
            </button>
          </div>
        </div>
      )}

      {/* Driver Details Modal */}
      {viewingDriverId && (
        <DriverDetailsModal
          driverId={viewingDriverId}
          onClose={() => setViewingDriverId(null)}
        />
      )}

      {/* Create/Edit Modal */}
      {(showCreateModal || editingDriver) && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 backdrop-blur-sm">
          <div className="bg-white dark:bg-gray-800 rounded-lg p-6 max-w-4xl w-full max-h-[90vh] overflow-y-auto shadow-xl border border-gray-200 dark:border-gray-700">
            <h2 className="text-2xl font-bold mb-4 text-gray-900 dark:text-white">
              {editingDriver ? 'Edit Driver' : 'Create Driver'}
            </h2>
            <DriverForm
              driver={editingDriver}
              onSuccess={() => {
                setShowCreateModal(false)
                setEditingDriver(null)
                queryClient.invalidateQueries('adminDrivers')
              }}
              onCancel={() => {
                setShowCreateModal(false)
                setEditingDriver(null)
              }}
            />
          </div>
        </div>
      )}
    </div>
  )
}
