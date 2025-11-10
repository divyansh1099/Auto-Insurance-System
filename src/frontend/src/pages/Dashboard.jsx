import { useQuery } from 'react-query'
import { useNavigate } from 'react-router-dom'
import { dashboardAPI, driverAPI, pricingAPI, authAPI } from '../services/api'
import CircularProgressChart from '../components/charts/CircularProgressChart'
import RiskFactorBarChart from '../components/charts/RiskFactorBarChart'
import {
  CheckCircleIcon,
  ChartBarIcon,
  CurrencyDollarIcon,
  TrophyIcon,
  ExclamationTriangleIcon,
  MapPinIcon,
  ClockIcon,
  ArrowTrendingUpIcon
} from '@heroicons/react/24/outline'

export default function Dashboard() {
  const navigate = useNavigate()
  
  // Get current user to determine driver_id
  const { data: currentUser } = useQuery(
    ['currentUser'],
    () => authAPI.getCurrentUser(),
    { retry: false }
  )
  
  const driverId = currentUser?.data?.driver_id || 'DRV-0001'

  // Debug logging
  console.log('Dashboard Debug:', {
    currentUser: currentUser?.data,
    driverId,
    hasToken: !!localStorage.getItem('access_token')
  })

  const { data: summary, error: summaryError } = useQuery(
    ['dashboardSummary', driverId],
    () => dashboardAPI.getSummary(driverId),
    { 
      retry: false, 
      enabled: !!driverId,
      staleTime: 0, // Always consider stale to force refetch
      cacheTime: 0, // Don't cache
      onSuccess: (data) => console.log('Summary API Success:', data),
      onError: (error) => console.error('Summary API Error:', error)
    }
  )

  const { data: recentTrips } = useQuery(
    ['recentTrips', driverId],
    () => dashboardAPI.getRecentTrips(driverId, 5),
    { 
      retry: false, 
      enabled: !!driverId,
      staleTime: 0,
      cacheTime: 0
    }
  )

  const { data: alerts } = useQuery(
    ['safetyAlerts', driverId],
    () => dashboardAPI.getSafetyAlerts(driverId),
    { 
      retry: false, 
      enabled: !!driverId,
      staleTime: 0,
      cacheTime: 0
    }
  )

  const { data: riskFactors } = useQuery(
    ['riskFactors', driverId],
    () => dashboardAPI.getRiskFactors(driverId),
    { 
      retry: false, 
      enabled: !!driverId,
      staleTime: 0,
      cacheTime: 0
    }
  )

  const { data: premium } = useQuery(
    ['premium', driverId],
    () => pricingAPI.getCurrentPremium(driverId),
    { 
      retry: false, 
      enabled: !!driverId,
      staleTime: 0,
      cacheTime: 0
    }
  )

  const { data: premiumBreakdown } = useQuery(
    ['premiumBreakdown', driverId],
    () => pricingAPI.getPremiumBreakdown(driverId),
    { 
      retry: false, 
      enabled: !!driverId,
      staleTime: 0,
      cacheTime: 0,
      onSuccess: (data) => console.log('Premium Breakdown API Success:', data),
      onError: (error) => console.error('Premium Breakdown API Error:', error)
    }
  )

  const getRiskBadgeColor = (riskLevel) => {
    switch (riskLevel?.toLowerCase()) {
      case 'low':
        return 'bg-green-100 text-green-800'
      case 'medium':
        return 'bg-yellow-100 text-yellow-800'
      case 'high':
        return 'bg-orange-100 text-orange-800'
      default:
        return 'bg-gray-100 text-gray-800'
    }
  }

  const getScoreColor = (score) => {
    if (score >= 80) return 'text-green-600'
    if (score >= 60) return 'text-yellow-600'
    if (score >= 40) return 'text-orange-600'
    return 'text-red-600'
  }

  // Prepare risk factor chart data
  const riskFactorData = riskFactors?.data ? [
    { name: 'Speeding', value: riskFactors.data.speeding || 0 },
    { name: 'Hard Braking', value: riskFactors.data.hard_braking || 0 },
    { name: 'Acceleration', value: riskFactors.data.acceleration || 0 },
    { name: 'Night Driving', value: riskFactors.data.night_driving || 0 },
    { name: 'High Risk Areas', value: riskFactors.data.high_risk_areas || 0 },
    { name: 'Phone Usage', value: riskFactors.data.phone_usage || 0 },
  ] : []

  // Calculate premium values from real data
  const currentPremium = premiumBreakdown?.data?.monthly_premium || premium?.data?.monthly_premium || 0
  
  // Calculate traditional premium: monthly_premium + (annual_savings / 12)
  // savings_vs_traditional is annual savings, so traditional annual = current annual + savings
  const annualSavings = premiumBreakdown?.data?.savings_vs_traditional || 0
  const currentAnnualPremium = currentPremium * 12
  const traditionalAnnualPremium = currentAnnualPremium + annualSavings
  const traditionalPremium = traditionalAnnualPremium / 12
  
  // Total savings is annual savings
  const totalSavings = annualSavings || (traditionalPremium > 0 && currentPremium > 0 
    ? (traditionalPremium - currentPremium) * 12 
    : 0)
  
  // Calculate discount percentage
  const discountPercent = traditionalPremium > 0 && currentPremium > 0
    ? Math.round(((traditionalPremium - currentPremium) / traditionalPremium) * 100)
    : 0

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold text-gray-900">
          Welcome back, {summary?.data?.driver_name || currentUser?.data?.username || 'Driver'}
        </h1>
        <p className="mt-2 text-gray-600">Your driving performance at a glance</p>
      </div>

      {/* Score & Summary Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Safety Score Card */}
        <div className="bg-gradient-to-br from-green-500 to-green-600 rounded-xl shadow-lg p-6 text-white">
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm font-medium opacity-90">Safety Score</span>
            <CheckCircleIcon className="w-5 h-5" />
          </div>
          <div className="text-4xl font-bold mb-1">
            {Math.round(summary?.data?.safety_score || 83)}
          </div>
          <div className="text-sm opacity-80">Out of 100</div>
        </div>

        {/* Risk Score Card */}
        <div className="bg-gradient-to-br from-orange-400 to-yellow-500 rounded-xl shadow-lg p-6 text-white">
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm font-medium opacity-90">Risk Score</span>
            <ChartBarIcon className="w-5 h-5" />
          </div>
          <div className="text-4xl font-bold mb-1">
            {Math.round(summary?.data?.risk_score || 37)}
          </div>
          <div className="text-sm opacity-80">Lower is better</div>
        </div>

        {/* Total Savings Card */}
        <div className="bg-gradient-to-br from-purple-500 to-purple-600 rounded-xl shadow-lg p-6 text-white">
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm font-medium opacity-90">Total Savings</span>
            <CurrencyDollarIcon className="w-5 h-5" />
          </div>
          <div className="text-4xl font-bold mb-1">
            ${summary?.data?.total_savings?.toFixed(0) || totalSavings.toFixed(0)}
          </div>
          <div className="text-sm opacity-80">vs Traditional Policy</div>
        </div>

        {/* Reward Points Card */}
        <div className="bg-gradient-to-br from-orange-500 to-orange-600 rounded-xl shadow-lg p-6 text-white">
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm font-medium opacity-90">Reward Points</span>
            <TrophyIcon className="w-5 h-5" />
          </div>
          <div className="text-4xl font-bold mb-1">
            {summary?.data?.reward_points || 450}
          </div>
          <button 
            onClick={() => navigate('/rewards')}
            className="text-sm opacity-80 hover:opacity-100 underline"
          >
            View rewards
          </button>
        </div>
      </div>

      {/* Main Content Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Driving Performance Card */}
        <div className="bg-white rounded-xl shadow-md p-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-xl font-semibold text-gray-900">Driving Performance</h2>
            {summary?.data?.is_improving && (
              <div className="flex items-center gap-2 text-green-600">
                <span className="text-sm font-medium">Improving</span>
                <ArrowTrendingUpIcon className="w-5 h-5" />
              </div>
            )}
          </div>
          <div className="flex items-center gap-6">
            <CircularProgressChart score={Math.round(summary?.data?.safety_score || 83)} size={120} />
            <div className="flex-1 space-y-3">
              <div className="flex justify-between">
                <span className="text-gray-600">Total Trips</span>
                <span className="font-semibold">{Math.round(summary?.data?.total_trips || 125)}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">Miles Driven</span>
                <span className="font-semibold">{Math.round(summary?.data?.miles_driven || 5520)}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">Avg Trip Score</span>
                <span className="font-semibold">{Math.round(summary?.data?.avg_trip_score || 71)}</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-gray-600">Score Change</span>
                <span className="bg-blue-100 text-blue-700 px-3 py-1 rounded-full text-sm font-semibold">
                  {(() => {
                    const change = summary?.data?.score_change || '+7'
                    // Parse string like "+4.0" or "+7" and round to whole number
                    if (typeof change === 'string') {
                      const num = parseFloat(change.replace('+', ''))
                      if (!isNaN(num)) {
                        return `${num >= 0 ? '+' : ''}${Math.round(num)}`
                      }
                    }
                    // If it's already a number, round it
                    if (typeof change === 'number') {
                      return `${change >= 0 ? '+' : ''}${Math.round(change)}`
                    }
                    return change
                  })()}
                </span>
              </div>
            </div>
          </div>
        </div>

        {/* Safety Alerts Card */}
        <div className="bg-white rounded-xl shadow-md p-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-xl font-semibold text-gray-900">Safety Alerts</h2>
            {alerts?.data?.total_alerts > 0 && (
              <span className="bg-gray-100 text-gray-700 px-3 py-1 rounded-full text-sm font-semibold">
                {alerts.data.total_alerts}
              </span>
            )}
          </div>
          <div className="space-y-3">
            {alerts?.data?.alerts && alerts.data.alerts.length > 0 ? (
              alerts.data.alerts.map((alert, idx) => (
                <div key={idx} className="flex items-start gap-3 p-3 bg-yellow-50 rounded-lg">
                  <ExclamationTriangleIcon className="w-5 h-5 text-yellow-600 mt-0.5 flex-shrink-0" />
                  <div className="flex-1">
                    <div className="font-medium text-gray-900">{alert.description}</div>
                    <div className="text-sm text-gray-600">
                      {alert.incidents} {alert.type === 'hard_braking' ? 'incidents' : 'events'} in {alert.period}
                    </div>
                  </div>
                </div>
              ))
            ) : (
              <div className="text-center py-8 text-gray-500">
                <CheckCircleIcon className="w-12 h-12 mx-auto mb-2 text-green-500" />
                <p>No safety alerts</p>
                <p className="text-sm">Keep up the safe driving!</p>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Bottom Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Recent Trips */}
        <div className="bg-white rounded-xl shadow-md p-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-xl font-semibold text-gray-900">Recent Trips</h2>
            <button
              onClick={() => navigate('/trips')}
              className="text-sm text-blue-600 hover:text-blue-700 font-medium"
            >
              View All
            </button>
          </div>
                 <div className="space-y-3">
                   {(recentTrips?.data?.trips || recentTrips?.trips || []) && (recentTrips?.data?.trips || recentTrips?.trips || []).length > 0 ? (
                     (recentTrips?.data?.trips || recentTrips?.trips || []).slice(0, 4).map((trip) => {
                // Calculate trip score from distance and duration (simplified)
                const baseScore = 70
                const distanceBonus = Math.min(10, (trip.distance_miles || 0) / 5)
                const tripScore = Math.round(Math.min(100, baseScore + distanceBonus))
                const riskLevel = tripScore >= 80 ? 'low' : tripScore >= 60 ? 'medium' : 'high'
                const scoreColor = getScoreColor(tripScore)
                
                return (
                  <div key={trip.trip_id} className="flex items-center justify-between p-3 border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors">
                    <div className="flex items-center gap-4 flex-1">
                      <div className={`text-2xl font-bold ${scoreColor}`}>
                        {tripScore}
                      </div>
                      <div className="flex-1">
                        <div className="flex items-center gap-2 text-sm text-gray-600 mb-1">
                          <MapPinIcon className="w-4 h-4" />
                          <span>{(trip.distance_miles || 0).toFixed(1)} miles</span>
                        </div>
                        <div className="flex items-center gap-2 text-xs text-gray-500">
                          <ClockIcon className="w-4 h-4" />
                          <span>
                            {trip.start_time ? new Date(trip.start_time).toLocaleDateString('en-US', { 
                              month: 'short', 
                              day: 'numeric',
                              hour: 'numeric',
                              minute: '2-digit'
                            }) : 'N/A'}
                          </span>
                        </div>
                      </div>
                      <span className={`px-3 py-1 rounded-full text-xs font-semibold ${getRiskBadgeColor(riskLevel)}`}>
                        {riskLevel}
                      </span>
                    </div>
                  </div>
                )
              })
            ) : (
              <div className="text-center py-8 text-gray-500">
                <p>No recent trips</p>
                <p className="text-sm">Trips will appear here as you drive</p>
              </div>
            )}
          </div>
        </div>

        {/* Risk Factor Analysis */}
        <div className="bg-white rounded-xl shadow-md p-6">
          <h2 className="text-xl font-semibold text-gray-900 mb-4">Risk Factor Analysis</h2>
          <RiskFactorBarChart data={riskFactorData} />
        </div>
      </div>

      {/* Premium Savings Card */}
      <div className="bg-gradient-to-r from-blue-600 to-blue-700 rounded-xl shadow-lg p-8 text-white">
        <div className="flex items-center gap-3 mb-6">
          <CurrencyDollarIcon className="w-8 h-8" />
          <h2 className="text-2xl font-bold">Your Premium Savings</h2>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-6">
          <div>
            <div className="text-sm opacity-90 mb-2">Traditional Premium</div>
            <div className="text-3xl font-bold">${traditionalPremium.toFixed(2)}</div>
            <div className="text-sm opacity-80">per month</div>
          </div>
          <div>
            <div className="text-sm opacity-90 mb-2">Your Premium</div>
            <div className="text-3xl font-bold">${currentPremium.toFixed(2)}</div>
            <div className="text-sm opacity-80">per month</div>
          </div>
          <div>
            <div className="text-sm opacity-90 mb-2">Total Savings</div>
            <div className="text-3xl font-bold">
              {totalSavings > 0 ? `$${totalSavings.toFixed(2)}` : '$0.00'}
            </div>
            <div className="text-sm opacity-80">{discountPercent > 0 ? `${discountPercent}% discount` : 'per year'}</div>
          </div>
        </div>
        <div className="mb-4">
          <div className="flex justify-between text-sm mb-2">
            <span className="opacity-90">Current Discount</span>
            <span className="font-semibold">{discountPercent}%</span>
          </div>
          <div className="w-full bg-blue-500 rounded-full h-2">
            <div 
              className="bg-white h-2 rounded-full transition-all duration-300"
              style={{ width: `${Math.min(100, discountPercent)}%` }}
            />
          </div>
        </div>
        <p className="text-sm opacity-90">
          {discountPercent > 0 
            ? `You're saving ${discountPercent}% compared to traditional insurance. Keep up the safe driving!`
            : 'Continue safe driving to earn discounts on your premium!'}
        </p>
      </div>
    </div>
  )
}
