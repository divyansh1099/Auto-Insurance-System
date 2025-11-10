import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from 'react-query'
import { driverAPI, riskAPI, authAPI } from '../services/api'
import RiskTrendChart from '../components/charts/RiskTrendChart'
import RiskFactorRadarChart from '../components/charts/RadarChart'
import {
  ChartBarIcon,
  CalendarIcon,
  ArrowTrendingDownIcon,
  ArrowTrendingUpIcon,
  BoltIcon,
  MapPinIcon
} from '@heroicons/react/24/outline'

export default function DrivingBehavior() {
  const queryClient = useQueryClient()
  
  // Get current user to determine driver_id
  const { data: currentUser, isLoading: isLoadingUser } = useQuery(
    ['currentUser'],
    () => authAPI.getCurrentUser(),
    { retry: false }
  )
  
  // Only use driver_id from authenticated user - no fallback to prevent showing wrong user's data
  const driverId = currentUser?.data?.driver_id
  const [isRecalculating, setIsRecalculating] = useState(false)
  
  // Debug logging to verify correct driver_id is being used
  if (currentUser?.data) {
    console.log('Risk Profile Debug:', {
      currentUser: currentUser.data,
      driverId,
      username: currentUser.data.username,
      isAdmin: currentUser.data.is_admin
    })
  }

  // Fetch risk profile summary (for top cards)
  const { data: riskSummary } = useQuery(
    ['riskProfileSummary', driverId],
    () => riskAPI.getRiskProfileSummary(driverId),
    { 
      retry: false,
      enabled: !!driverId,
      staleTime: 0, // Always consider stale to force refetch
      cacheTime: 0, // Don't cache
      // Fallback to existing endpoints if new ones don't exist
      onSuccess: (data) => {
        console.log('Risk Profile Summary API Response:', {
          driverId,
          totalTrips: data?.data?.total_trips,
          totalMiles: data?.data?.total_miles,
          response: data
        })
      },
      onError: (error) => {
        console.error('Risk Profile Summary API Error:', error)
        // Fallback logic will be handled in the component
      }
    }
  )

  // Fetch risk score trend (for line chart)
  const { data: riskTrend } = useQuery(
    ['riskScoreTrend', driverId],
    () => riskAPI.getRiskScoreTrend(driverId, '30d', 'daily'),
    { 
      retry: false,
      enabled: !!driverId,
      // Fallback to existing history endpoint
      onError: () => {
        // Will fallback to riskHistory
      }
    }
  )

  // Fallback: Use existing risk history endpoint
  const { data: riskHistory } = useQuery(
    ['riskHistory', driverId],
    () => riskAPI.getRiskHistory(driverId, 30),
    { retry: false, enabled: !!driverId }
  )

  // Fetch risk factor breakdown (for radar chart and detailed factors)
  const { data: riskBreakdown } = useQuery(
    ['riskFactorBreakdown', driverId],
    () => riskAPI.getRiskFactorBreakdown(driverId),
    { 
      retry: false,
      enabled: !!driverId,
      // Fallback to existing breakdown endpoint
      onError: () => {
        // Will fallback to getRiskBreakdown
      }
    }
  )

  // Fallback: Use existing breakdown endpoint
  const { data: existingBreakdown } = useQuery(
    ['riskBreakdown', driverId],
    () => riskAPI.getRiskBreakdown(driverId),
    { retry: false, enabled: !!driverId }
  )

  // Recalculate risk mutation
  const recalculateMutation = useMutation(
    () => riskAPI.recalculateRisk(driverId),
    {
      onSuccess: () => {
        queryClient.invalidateQueries(['riskProfileSummary', driverId])
        queryClient.invalidateQueries(['riskScoreTrend', driverId])
        queryClient.invalidateQueries(['riskFactorBreakdown', driverId])
        queryClient.invalidateQueries(['riskHistory', driverId])
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
  
  // Show loading state while user is being fetched
  if (isLoadingUser) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading your risk profile...</p>
        </div>
      </div>
    )
  }
  
  // Show error if user is not authenticated or doesn't have a driver_id
  if (!currentUser?.data || !driverId) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <p className="text-red-600 text-lg font-semibold">Unable to load your risk profile</p>
          <p className="text-gray-600 mt-2">Please ensure you are logged in and have a valid driver account.</p>
        </div>
      </div>
    )
  }

  // Extract data with fallbacks - use trip statistics from risk profile summary
  const summary = riskSummary?.data || {
    overall_risk_score: existingBreakdown?.data?.risk_score || 50,
    behavior_score: 87,
    last_updated: existingBreakdown?.data?.calculated_at || new Date().toISOString(),
    change_from_previous: 7,
    overall_risk_trend_status: existingBreakdown?.data?.trend || 'stable',
    total_trips: 0,
    total_miles: 0,
    avg_trip_score: null,
    perfect_trips: 0,
    low_risk_trips: 0,
    high_risk_trips: 0,
    total_incidents: 0
  }
  
  // Trip metrics from risk profile summary (includes ALL trips, not just paginated subset)
  const tripMetrics = {
    totalTrips: summary.total_trips || 0,
    totalMiles: summary.total_miles || 0,
    avgTripScore: summary.avg_trip_score ? Math.round(summary.avg_trip_score) : 0,
    perfectTrips: summary.perfect_trips || 0,
    lowRiskTrips: summary.low_risk_trips || 0,
    highRiskTrips: summary.high_risk_trips || 0,
    totalIncidents: summary.total_incidents || 0
  }

  // Prepare trend chart data
  const trendData = riskTrend?.data?.scores?.map(item => ({
    date: new Date(item.date).toLocaleDateString('en-US', { month: 'short', day: 'numeric' }),
    risk_score: item.risk_score
  })) || riskHistory?.data?.scores?.map(item => ({
    date: new Date(item.calculated_at).toLocaleDateString('en-US', { month: 'short', day: 'numeric' }),
    risk_score: item.risk_score
  })) || []

  // Extract category scores and detailed factors (fields are at top level of response)
  const breakdownData = riskBreakdown?.data || {}
  const categoryScores = {
    behavior: breakdownData.behavior ?? summary.behavior_score ?? 87,
    mileage: breakdownData.mileage ?? 75,
    time_pattern: breakdownData.time_pattern ?? 25,
    location: breakdownData.location ?? 45
  }

  const detailedFactors = {
    speeding_frequency: breakdownData.speeding_frequency ?? 0.1,
    acceleration_pattern: breakdownData.acceleration_pattern ?? 0.1,
    high_risk_area_exposure: breakdownData.high_risk_area_exposure ?? 25.0,
    weather_risk_exposure: breakdownData.weather_risk_exposure ?? 18.0,
    hard_braking_frequency: breakdownData.hard_braking_frequency ?? 0.1,
    night_driving_percentage: breakdownData.night_driving_percentage ?? 12.0,
    phone_usage_incidents: breakdownData.phone_usage_incidents ?? 0
  }

  // Format last updated date
  const formatLastUpdated = (dateString) => {
    if (!dateString) return 'Unknown'
    const date = new Date(dateString)
    return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })
  }

  // Get trend icon and color
  const getTrendIndicator = (status) => {
    if (status === 'improving') {
      return {
        icon: ArrowTrendingDownIcon,
        color: 'text-green-600',
        bgColor: 'bg-green-100',
        label: 'Improving'
      }
    } else if (status === 'declining') {
      return {
        icon: ArrowTrendingUpIcon,
        color: 'text-red-600',
        bgColor: 'bg-red-100',
        label: 'Declining'
      }
    }
    return {
      icon: ArrowTrendingUpIcon,
      color: 'text-gray-600',
      bgColor: 'bg-gray-100',
      label: 'Stable'
    }
  }

  const trendInfo = getTrendIndicator(summary.overall_risk_trend_status)

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
              <h1 className="text-3xl md:text-4xl font-bold bg-gradient-to-r from-cyan-600 via-blue-600 to-purple-600 bg-clip-text text-transparent">Risk Profile</h1>
              <p className="text-gray-600 mt-1 text-lg">Detailed analysis of your driving risk factors</p>
            </div>
            <button
              onClick={handleRecalculate}
              disabled={isRecalculating}
              className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              <BoltIcon className="w-5 h-5" />
              {isRecalculating ? 'Recalculating...' : 'Recalculate Risk'}
            </button>
          </div>
        </div>

      {/* Top Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {/* Overall Risk Score Card */}
        <div className="bg-blue-600 rounded-lg shadow-lg p-6 text-white">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-2">
              <ChartBarIcon className="w-6 h-6" />
              <h2 className="text-lg font-semibold">Overall Risk Score</h2>
            </div>
            <div className={`px-3 py-1 rounded-full text-xs font-medium ${trendInfo.bgColor} ${trendInfo.color}`}>
              <div className="flex items-center gap-1">
                <trendInfo.icon className="w-4 h-4" />
                <span>{trendInfo.label}</span>
              </div>
            </div>
          </div>
          <div className="text-5xl font-bold mb-2">{Math.round(summary.overall_risk_score || 35)}</div>
          <p className="text-blue-100 text-sm">Lower score means lower risk</p>
        </div>

        {/* Behavior Score Card */}
        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center gap-2 mb-4">
            <ChartBarIcon className="w-5 h-5 text-gray-400" />
            <h2 className="text-lg font-semibold text-gray-900">Behavior Score</h2>
          </div>
          <div className="text-5xl font-bold text-gray-900 mb-2">{summary.behavior_score || 87}</div>
          <p className="text-gray-600 text-sm">Driving behavior analysis</p>
        </div>

        {/* Trip Statistics Card */}
        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center gap-2 mb-4">
            <MapPinIcon className="w-5 h-5 text-gray-400" />
            <h2 className="text-lg font-semibold text-gray-900">Trip Statistics</h2>
          </div>
          <div className="space-y-2">
            <div className="flex justify-between">
              <span className="text-sm text-gray-600">Total Trips</span>
              <span className="text-lg font-bold text-gray-900">{Math.round(tripMetrics.totalTrips || 0)}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-sm text-gray-600">Total Miles</span>
              <span className="text-lg font-bold text-gray-900">{Math.round(tripMetrics.totalMiles || 0)}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-sm text-gray-600">Avg Score</span>
              <span className="text-lg font-bold text-gray-900">{Math.round(tripMetrics.avgTripScore || 0)}</span>
            </div>
          </div>
        </div>

        {/* Last Updated Card */}
        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center gap-2 mb-4">
            <CalendarIcon className="w-5 h-5 text-gray-400" />
            <h2 className="text-lg font-semibold text-gray-900">Last Updated</h2>
          </div>
          <div className="text-xl font-semibold text-gray-900 mb-2">
            {formatLastUpdated(summary.last_updated_date || summary.last_updated)}
          </div>
          {summary.change_from_previous !== undefined && summary.change_from_previous !== 0 && (
            <p className={`text-sm font-medium ${
              summary.change_from_previous < 0 ? 'text-green-600' : 'text-red-600'
            }`}>
              {summary.change_from_previous > 0 ? '+' : ''}{summary.change_from_previous} from previous
            </p>
          )}
        </div>
      </div>

      {/* Charts Section */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Risk Score Trend Chart */}
        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-xl font-semibold text-gray-900 mb-4">Risk Score Trend</h2>
          <RiskTrendChart data={trendData} />
        </div>

        {/* Risk Factor Breakdown Radar Chart */}
        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-xl font-semibold text-gray-900 mb-4">Risk Factor Breakdown</h2>
          <RiskFactorRadarChart data={categoryScores} />
        </div>
      </div>

      {/* Trip Performance Summary */}
      <div className="bg-white rounded-lg shadow p-6">
        <h2 className="text-xl font-semibold text-gray-900 mb-6">Trip Performance Summary</h2>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
          <div className="bg-green-50 rounded-lg p-4">
            <div className="text-sm text-gray-600 mb-1">Perfect Trips</div>
            <div className="text-3xl font-bold text-green-600">{tripMetrics.perfectTrips}</div>
            <div className="text-xs text-gray-500">Score ≥ 95</div>
          </div>
          <div className="bg-blue-50 rounded-lg p-4">
            <div className="text-sm text-gray-600 mb-1">Low Risk Trips</div>
            <div className="text-3xl font-bold text-blue-600">{tripMetrics.lowRiskTrips}</div>
            <div className="text-xs text-gray-500">Score ≥ 80</div>
          </div>
          <div className="bg-orange-50 rounded-lg p-4">
            <div className="text-sm text-gray-600 mb-1">High Risk Trips</div>
            <div className="text-3xl font-bold text-orange-600">{tripMetrics.highRiskTrips}</div>
            <div className="text-xs text-gray-500">Score &lt; 60</div>
          </div>
          <div className="bg-red-50 rounded-lg p-4">
            <div className="text-sm text-gray-600 mb-1">Total Incidents</div>
            <div className="text-3xl font-bold text-red-600">{tripMetrics.totalIncidents}</div>
            <div className="text-xs text-gray-500">All safety events</div>
          </div>
        </div>
      </div>

      {/* Detailed Risk Factors Section */}
      <div className="bg-white rounded-lg shadow p-6">
        <h2 className="text-xl font-semibold text-gray-900 mb-6">Detailed Risk Factors</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* Left Column */}
          <div className="space-y-6">
            {/* Speeding Frequency */}
            <div>
              <div className="flex justify-between items-center mb-2">
                <span className="text-sm font-medium text-gray-700">Speeding Frequency</span>
                <span className="text-sm font-semibold text-gray-900">{detailedFactors.speeding_frequency?.toFixed(1) || 0.1}</span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-2">
                <div 
                  className="bg-blue-600 h-2 rounded-full transition-all"
                  style={{ width: `${Math.min(100, (detailedFactors.speeding_frequency || 0.1) * 10)}%` }}
                />
              </div>
            </div>

            {/* Acceleration Pattern */}
            <div>
              <div className="flex justify-between items-center mb-2">
                <span className="text-sm font-medium text-gray-700">Acceleration Pattern</span>
                <span className="text-sm font-semibold text-gray-900">{detailedFactors.acceleration_pattern?.toFixed(1) || 0.1}</span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-2">
                <div 
                  className="bg-blue-600 h-2 rounded-full transition-all"
                  style={{ width: `${Math.min(100, (detailedFactors.acceleration_pattern || 0.1) * 10)}%` }}
                />
              </div>
            </div>

            {/* High Risk Area Exposure */}
            <div>
              <div className="flex justify-between items-center mb-2">
                <span className="text-sm font-medium text-gray-700">High Risk Area Exposure</span>
                <span className="text-sm font-semibold text-gray-900">{detailedFactors.high_risk_area_exposure?.toFixed(1) || 25.0}</span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-2">
                <div 
                  className="bg-yellow-600 h-2 rounded-full transition-all"
                  style={{ width: `${Math.min(100, detailedFactors.high_risk_area_exposure || 25.0)}%` }}
                />
              </div>
            </div>

            {/* Weather Risk Exposure */}
            <div>
              <div className="flex justify-between items-center mb-2">
                <span className="text-sm font-medium text-gray-700">Weather Risk Exposure</span>
                <span className="text-sm font-semibold text-gray-900">{detailedFactors.weather_risk_exposure?.toFixed(1) || 18.0}</span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-2">
                <div 
                  className="bg-orange-600 h-2 rounded-full transition-all"
                  style={{ width: `${Math.min(100, detailedFactors.weather_risk_exposure || 18.0)}%` }}
                />
              </div>
            </div>
          </div>

          {/* Right Column */}
          <div className="space-y-6">
            {/* Hard Braking Frequency */}
            <div>
              <div className="flex justify-between items-center mb-2">
                <span className="text-sm font-medium text-gray-700">Hard Braking Frequency</span>
                <span className="text-sm font-semibold text-gray-900">{detailedFactors.hard_braking_frequency?.toFixed(1) || 0.1}</span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-2">
                <div 
                  className="bg-blue-600 h-2 rounded-full transition-all"
                  style={{ width: `${Math.min(100, (detailedFactors.hard_braking_frequency || 0.1) * 10)}%` }}
                />
              </div>
            </div>

            {/* Night Driving Percentage */}
            <div>
              <div className="flex justify-between items-center mb-2">
                <span className="text-sm font-medium text-gray-700">Night Driving Percentage</span>
                <span className="text-sm font-semibold text-gray-900">{detailedFactors.night_driving_percentage?.toFixed(1) || 12.0}%</span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-2">
                <div 
                  className="bg-purple-600 h-2 rounded-full transition-all"
                  style={{ width: `${Math.min(100, detailedFactors.night_driving_percentage || 12.0)}%` }}
                />
              </div>
            </div>

            {/* Phone Usage Incidents */}
            <div>
              <div className="flex justify-between items-center mb-2">
                <span className="text-sm font-medium text-gray-700">Phone Usage Incidents</span>
                <span className="text-sm font-semibold text-gray-900">{detailedFactors.phone_usage_incidents || 0}</span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-2">
                <div 
                  className="bg-red-600 h-2 rounded-full transition-all"
                  style={{ width: `${Math.min(100, (detailedFactors.phone_usage_incidents || 0) * 10)}%` }}
                />
              </div>
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
