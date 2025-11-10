import { useState, useMemo } from 'react'
import { useQuery } from 'react-query'
import { driverAPI, authAPI } from '../services/api'
import {
  MapPinIcon,
  CalendarIcon,
  ClockIcon,
  ExclamationTriangleIcon,
  BoltIcon,
  ArrowTrendingUpIcon,
  ChartBarIcon
} from '@heroicons/react/24/outline'
import { MagnifyingGlassIcon } from '@heroicons/react/24/solid'

export default function Trips() {
  // Get current user to determine driver_id
  const { data: currentUser } = useQuery(
    ['currentUser'],
    () => authAPI.getCurrentUser(),
    { retry: false }
  )
  
  const driverId = currentUser?.data?.driver_id || 'DRV-0001'
  const [searchQuery, setSearchQuery] = useState('')
  const [riskFilter, setRiskFilter] = useState('all')

  const [currentPage, setCurrentPage] = useState(1)
  const pageSize = 20

  // Reset to page 1 when filters change
  const handleSearchChange = (value) => {
    setSearchQuery(value)
    setCurrentPage(1)
  }

  const handleRiskFilterChange = (value) => {
    setRiskFilter(value)
    setCurrentPage(1)
  }

  const { data: tripsData, isLoading } = useQuery(
    ['trips', driverId, currentPage, riskFilter, searchQuery],
    () => driverAPI.getTrips(driverId, currentPage, pageSize, riskFilter !== 'all' ? riskFilter : undefined, searchQuery || undefined)
  )

  // Fetch trip summary for accurate statistics (all trips, not just current page)
  const { data: tripSummary } = useQuery(
    ['tripSummary', driverId],
    () => driverAPI.getTripSummary(driverId),
    { retry: false, enabled: !!driverId }
  )

  // Handle axios response structure: axios wraps in .data, FastAPI returns the model directly
  const trips = tripsData?.data?.trips || tripsData?.trips || []
  const totalTrips = tripsData?.data?.total || tripsData?.total || 0
  
  // Debug logging
  if (tripsData && trips.length === 0) {
    console.log('Trips API Response:', tripsData)
  }

  // Calculate summary statistics - use trip summary API for accurate totals
  const summary = useMemo(() => {
    // Use trip summary API data if available (calculates from ALL trips)
    if (tripSummary?.data) {
      return {
        totalTrips: tripSummary.data.total_trips || 0,
        totalMiles: Math.round(tripSummary.data.total_miles || 0),
        avgTripScore: tripSummary.data.avg_trip_score ? Math.round(tripSummary.data.avg_trip_score) : 0
      }
    }
    
    // Fallback: calculate from current page trips (less accurate)
    const totalMiles = trips.reduce((sum, trip) => sum + (trip.distance_miles || 0), 0)
    
    // Calculate trip scores (if not available, estimate from events)
    const tripScores = trips.map(trip => {
      if (trip.trip_score !== undefined && trip.trip_score !== null) {
        return trip.trip_score
      }
      // Estimate score from events (100 - deductions)
      let score = 100
      score -= (trip.harsh_braking_count || 0) * 5
      score -= (trip.rapid_accel_count || 0) * 3
      score -= (trip.speeding_count || 0) * 8
      score -= (trip.harsh_corner_count || 0) * 4
      return Math.max(0, Math.min(100, score))
    })
    
    const avgTripScore = tripScores.length > 0
      ? Math.round(tripScores.reduce((sum, score) => sum + score, 0) / tripScores.length)
      : 0

    return {
      totalTrips: totalTrips || trips.length,
      totalMiles: Math.round(totalMiles),
      avgTripScore
    }
  }, [trips, totalTrips, tripSummary])

  // Helper function to get location string from coordinates
  const getLocationString = (lat, lon, isStart = true) => {
    // For now, return a placeholder. In production, this would use geocoding
    if (lat && lon) {
      // Simple approximation - in production, use reverse geocoding API
      return `${isStart ? 'Origin' : 'Destination'} Location`
    }
    return 'Unknown Location'
  }

  // Helper function to format route
  const formatRoute = (trip) => {
    if (trip.origin_city && trip.origin_state && trip.destination_city && trip.destination_state) {
      return `${trip.origin_city}, ${trip.origin_state} → ${trip.destination_city}, ${trip.destination_state}`
    }
    // Fallback: use coordinates or placeholder
    const origin = getLocationString(trip.start_latitude, trip.start_longitude, true)
    const destination = getLocationString(trip.end_latitude, trip.end_longitude, false)
    return `${origin} → ${destination}`
  }

  // Helper function to calculate trip score
  const calculateTripScore = (trip) => {
    if (trip.trip_score !== undefined && trip.trip_score !== null) {
      return trip.trip_score
    }
    // Estimate score from events
    let score = 100
    score -= (trip.harsh_braking_count || 0) * 5
    score -= (trip.rapid_accel_count || 0) * 3
    score -= (trip.speeding_count || 0) * 8
    score -= (trip.harsh_corner_count || 0) * 4
    return Math.max(0, Math.min(100, score))
  }

  // Helper function to determine risk level
  const getRiskLevel = (score) => {
    if (score >= 80) return { level: 'low', label: 'Low Risk', color: 'green' }
    if (score >= 60) return { level: 'medium', label: 'Medium', color: 'yellow' }
    return { level: 'high', label: 'High Risk', color: 'red' }
  }

  // Server-side filtering is now handled by the API
  // No need for client-side filtering since filters are passed to the API
  const filteredTrips = trips

  // Format date and time
  const formatDateTime = (timestamp) => {
    if (!timestamp) return 'Unknown'
    const date = new Date(timestamp)
    const dateStr = date.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })
    const timeStr = date.toLocaleTimeString('en-US', { hour: 'numeric', minute: '2-digit', hour12: true })
    return `${dateStr}, ${timeStr}`
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
          <h1 className="text-3xl md:text-4xl font-bold bg-gradient-to-r from-cyan-600 via-blue-600 to-purple-600 bg-clip-text text-transparent">Trip History</h1>
          <p className="text-gray-600 mt-1 text-lg">View and analyze all your trips</p>
        </div>

      {/* Summary Cards - All on Same Line */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        {/* Total Trips - Blue Card */}
        <div className="bg-gradient-to-br from-blue-500 to-blue-600 rounded-xl shadow-lg p-6 text-white">
          <div className="flex items-center justify-between h-full">
            <div>
              <p className="text-sm font-medium text-blue-100 mb-1">Total Trips</p>
              <p className="text-4xl font-bold mt-2">{summary.totalTrips}</p>
              <p className="text-sm text-blue-100 mt-2">All time trips</p>
            </div>
            <div className="w-12 h-12 bg-white/20 rounded-xl flex items-center justify-center backdrop-blur-sm">
              <MapPinIcon className="w-6 h-6 text-white" />
            </div>
          </div>
        </div>

        {/* Total Miles - Purple Card */}
        <div className="bg-gradient-to-br from-purple-500 to-purple-600 rounded-xl shadow-lg p-6 text-white">
          <div className="flex items-center justify-between h-full">
            <div>
              <p className="text-sm font-medium text-purple-100 mb-1">Total Miles</p>
              <p className="text-4xl font-bold mt-2">{summary.totalMiles}</p>
              <p className="text-sm text-purple-100 mt-2">Miles driven</p>
            </div>
            <div className="w-12 h-12 bg-white/20 rounded-xl flex items-center justify-center backdrop-blur-sm">
              <ArrowTrendingUpIcon className="w-6 h-6 text-white" />
            </div>
          </div>
        </div>

        {/* Avg Trip Score - Green Card */}
        <div className="bg-gradient-to-br from-green-500 to-emerald-600 rounded-xl shadow-lg p-6 text-white">
          <div className="flex items-center justify-between h-full">
            <div>
              <p className="text-sm font-medium text-green-100 mb-1">Avg Score</p>
              <p className="text-4xl font-bold mt-2">{summary.avgTripScore}</p>
            </div>
            <div className="w-12 h-12 bg-white/20 rounded-xl flex items-center justify-center backdrop-blur-sm">
              <ArrowTrendingUpIcon className="w-6 h-6 text-white" />
            </div>
          </div>
        </div>

        {/* Risk Level - Orange Card */}
        <div className="bg-gradient-to-br from-orange-500 to-amber-600 rounded-xl shadow-lg p-6 text-white">
          <div className="flex items-center justify-between h-full">
            <div>
              <p className="text-sm font-medium text-orange-100 mb-1">Risk Level</p>
              <p className="text-4xl font-bold mt-2">
                {summary.avgTripScore >= 80 ? 'Low' : summary.avgTripScore >= 60 ? 'Medium' : 'High'}
              </p>
            </div>
            <div className="w-12 h-12 bg-white/20 rounded-xl flex items-center justify-center backdrop-blur-sm">
              <ChartBarIcon className="w-6 h-6 text-white" />
            </div>
          </div>
        </div>
      </div>

      {/* Search and Filters */}
      <div className="bg-white rounded-lg shadow p-4">
        <div className="flex flex-col md:flex-row gap-4">
          {/* Search Bar */}
          <div className="flex-1 relative">
            <MagnifyingGlassIcon className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-400" />
            <input
              type="text"
              placeholder="Search by location..."
              value={searchQuery}
              onChange={(e) => handleSearchChange(e.target.value)}
              className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
          </div>

          {/* Risk Filters */}
          <div className="flex gap-2">
            {['all', 'low', 'medium', 'high'].map((filter) => (
              <button
                key={filter}
                onClick={() => handleRiskFilterChange(filter)}
                className={`px-4 py-2 rounded-lg font-medium transition-colors ${
                  riskFilter === filter
                    ? 'bg-gray-900 text-white'
                    : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                }`}
              >
                {filter === 'all' ? 'All' : filter === 'low' ? 'Low Risk' : filter === 'medium' ? 'Medium' : 'High Risk'}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Trip List */}
      <div className="space-y-4">
        {isLoading ? (
          <div className="bg-white rounded-lg shadow p-12 text-center">
          <p className="text-gray-600">Loading trips...</p>
          </div>
        ) : filteredTrips.length === 0 ? (
          <div className="bg-white rounded-lg shadow p-12 text-center">
            <p className="text-gray-600 mb-2">No trips found</p>
            <p className="text-sm text-gray-500">
              {searchQuery || riskFilter !== 'all'
                ? 'Try adjusting your search or filter criteria'
                : 'Trips will appear here once you start driving'}
            </p>
          </div>
        ) : (
          filteredTrips.map((trip) => {
            const tripScore = calculateTripScore(trip)
            const risk = getRiskLevel(tripScore)
            const route = formatRoute(trip)

            return (
              <div key={trip.trip_id} className="bg-white rounded-lg shadow p-4 hover:shadow-md transition-shadow">
                <div className="flex items-center justify-between gap-4">
                  {/* Left Side - Route and Details (Compact) */}
                  <div className="flex-1 min-w-0">
                    {/* Route - Single Line */}
                    <div className="flex items-center gap-2 mb-2">
                      <MapPinIcon className="w-4 h-4 text-gray-400 flex-shrink-0" />
                      <span className="font-semibold text-gray-900 text-sm truncate">{route}</span>
                    </div>

                    {/* Date, Time, and Trip Details - Single Line */}
                    <div className="flex flex-wrap items-center gap-3 text-xs text-gray-600">
                      <div className="flex items-center gap-1">
                        <CalendarIcon className="w-3.5 h-3.5" />
                        <span>{formatDateTime(trip.start_time)}</span>
                      </div>
                      {trip.distance_miles && (
                        <span>{trip.distance_miles.toFixed(1)} miles</span>
                      )}
                      {trip.duration_minutes && (
                        <span className="flex items-center gap-1">
                          <ClockIcon className="w-3.5 h-3.5" />
                          {Math.floor(trip.duration_minutes)} min
                        </span>
                      )}
                      {trip.avg_speed && (
                        <span>Avg: {Math.round(trip.avg_speed)} mph</span>
                      )}
                    </div>

                    {/* Incidents - Compact with Icons */}
                    {(trip.harsh_braking_count > 0 || trip.rapid_accel_count > 0 || trip.speeding_count > 0) && (
                      <div className="flex flex-wrap items-center gap-2 mt-2">
                        {trip.harsh_braking_count > 0 && (
                          <div className="flex items-center gap-1 text-xs font-medium">
                            <div className="flex items-center justify-center w-4 h-4 rounded-full bg-orange-100">
                              <ExclamationTriangleIcon className="w-3 h-3 text-orange-600" />
                            </div>
                            <span className="text-orange-700">{trip.harsh_braking_count} hard braking</span>
                          </div>
                        )}
                        {trip.rapid_accel_count > 0 && (
                          <div className="flex items-center gap-1 text-xs font-medium">
                            <div className="flex items-center justify-center w-4 h-4 rounded-full bg-amber-100">
                              <BoltIcon className="w-3 h-3 text-amber-600" />
                            </div>
                            <span className="text-amber-700">{trip.rapid_accel_count} rapid accel</span>
                          </div>
                        )}
                        {trip.speeding_count > 0 && (
                          <div className="flex items-center gap-1 text-xs font-medium">
                            <div className="flex items-center justify-center w-4 h-4 rounded-full bg-red-100">
                              <svg className="w-3 h-3 text-red-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                              </svg>
                            </div>
                            <span className="text-red-700">{trip.speeding_count} speeding</span>
                          </div>
                        )}
                      </div>
                    )}
                  </div>

                  {/* Right Side - Trip Score (Compact) */}
                  <div className="flex flex-col items-end gap-1.5 flex-shrink-0">
                    <div className={`px-2 py-0.5 rounded-full text-xs font-semibold ${
                      risk.color === 'green' ? 'bg-green-100 text-green-800' :
                      risk.color === 'yellow' ? 'bg-yellow-100 text-yellow-800' :
                      'bg-red-100 text-red-800'
                    }`}>
                      {risk.level}
                    </div>
                    <div className={`text-3xl font-bold leading-none ${
                      risk.color === 'green' ? 'text-green-600' :
                      risk.color === 'yellow' ? 'text-yellow-600' :
                      'text-red-600'
                    }`}>
                      {tripScore}
                    </div>
                  </div>
                </div>
              </div>
            )
          })
        )}
      </div>

      {/* Pagination */}
      {totalTrips > pageSize && (
        <div className="flex items-center justify-between bg-white rounded-lg shadow p-4">
          <div className="text-sm text-gray-600">
            Showing {(currentPage - 1) * pageSize + 1} to {Math.min(currentPage * pageSize, totalTrips)} of {totalTrips} trips
          </div>
          <div className="flex gap-2">
            <button
              onClick={() => setCurrentPage(p => Math.max(1, p - 1))}
              disabled={currentPage === 1}
              className="px-4 py-2 border border-gray-300 rounded-lg text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              Previous
            </button>
            <button
              onClick={() => setCurrentPage(p => p + 1)}
              disabled={currentPage * pageSize >= totalTrips}
              className="px-4 py-2 border border-gray-300 rounded-lg text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              Next
            </button>
          </div>
        </div>
      )}
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
