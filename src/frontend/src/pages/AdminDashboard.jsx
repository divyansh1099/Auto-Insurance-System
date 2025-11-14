import { useState, useEffect, useMemo, useCallback } from 'react'
import { useQuery } from 'react-query'
import { adminAPI } from '../services/api'
import {
  UserGroupIcon,
  TruckIcon,
  CurrencyDollarIcon,
  ChartBarIcon,
  ArrowPathIcon,
  ArrowDownTrayIcon,
  ClockIcon,
  ExclamationTriangleIcon,
} from '@heroicons/react/24/outline'
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
  BarChart,
  Bar,
  Legend,
} from 'recharts'
import LoadingSkeleton, { CardSkeleton, ChartSkeleton } from '../components/LoadingSkeleton'
import ErrorMessage from '../components/ErrorMessage'
import { useToast } from '../components/Toast'

export default function AdminDashboard() {
  const [tripActivityDays, setTripActivityDays] = useState(7)
  const [lastUpdated, setLastUpdated] = useState(null)
  const [autoRefreshCountdown, setAutoRefreshCountdown] = useState(30)
  const { showToast, ToastComponent } = useToast()

  // Fetch summary data (4 cards)
  const {
    data: summary,
    isLoading: isLoadingSummary,
    error: summaryError,
    refetch: refetchSummary,
  } = useQuery(
    ['adminDashboardSummary'],
    () => adminAPI.getDashboardSummary(),
    {
      retry: 2,
      refetchInterval: 30000, // Auto-refresh every 30 seconds
      onError: (error) => {
        console.error('Admin Dashboard Summary Error:', error)
        showToast('Failed to load dashboard summary', 'error')
      },
      onSuccess: () => {
        setLastUpdated(new Date())
      },
    }
  )

  // Fetch trip activity data
  const {
    data: tripActivity,
    isLoading: isLoadingTripActivity,
    error: tripActivityError,
    refetch: refetchTripActivity,
  } = useQuery(
    ['adminTripActivity', tripActivityDays],
    () => adminAPI.getTripActivity(tripActivityDays),
    {
      retry: 2,
      refetchInterval: 30000,
      onError: (error) => {
        console.error('Trip Activity Error:', error)
      },
    }
  )

  // Fetch risk distribution data
  const {
    data: riskDistribution,
    isLoading: isLoadingRiskDistribution,
    error: riskDistributionError,
    refetch: refetchRiskDistribution,
  } = useQuery(
    ['adminRiskDistribution'],
    () => adminAPI.getRiskDistribution(),
    {
      retry: 2,
      refetchInterval: 30000,
      onError: (error) => {
        console.error('Risk Distribution Error:', error)
      },
    }
  )

  // Fetch safety events breakdown data
  const {
    data: safetyEvents,
    isLoading: isLoadingSafetyEvents,
    error: safetyEventsError,
    refetch: refetchSafetyEvents,
  } = useQuery(
    ['adminSafetyEvents'],
    () => adminAPI.getSafetyEventsBreakdown(),
    {
      retry: 2,
      refetchInterval: 30000,
      onError: (error) => {
        console.error('Safety Events Error:', error)
      },
    }
  )

  // Fetch policy type distribution data
  const {
    data: policyTypes,
    isLoading: isLoadingPolicyTypes,
    error: policyTypesError,
    refetch: refetchPolicyTypes,
  } = useQuery(
    ['adminPolicyTypes'],
    () => adminAPI.getPolicyTypeDistribution(),
    {
      retry: 2,
      refetchInterval: 30000,
      onError: (error) => {
        console.error('Policy Types Error:', error)
      },
    }
  )

  // Auto-refresh countdown
  useEffect(() => {
    const timer = setInterval(() => {
      setAutoRefreshCountdown((prev) => {
        if (prev <= 1) {
          return 30 // Reset to 30 seconds
        }
        return prev - 1
      })
    }, 1000)

    return () => clearInterval(timer)
  }, [])

  // Manual refresh all data
  const handleRefreshAll = useCallback(async () => {
    showToast('Refreshing dashboard data...', 'info', 1500)
    setAutoRefreshCountdown(30)

    try {
      await Promise.all([
        refetchSummary(),
        refetchTripActivity(),
        refetchRiskDistribution(),
        refetchSafetyEvents(),
        refetchPolicyTypes(),
      ])
      showToast('Dashboard data refreshed successfully', 'success')
      setLastUpdated(new Date())
    } catch (error) {
      showToast('Failed to refresh dashboard data', 'error')
    }
  }, [
    refetchSummary,
    refetchTripActivity,
    refetchRiskDistribution,
    refetchSafetyEvents,
    refetchPolicyTypes,
    showToast,
  ])

  // Export dashboard data to CSV
  const handleExportCSV = useCallback(() => {
    try {
      const summaryData = summary?.data || summary
      const tripData = tripActivity?.data || tripActivity || []
      const riskData = riskDistribution?.data || riskDistribution
      const safetyData = safetyEvents?.data || safetyEvents || []

      // Create CSV content
      let csv = 'Auto Insurance System - Dashboard Export\n'
      csv += `Generated: ${new Date().toLocaleString()}\n\n`

      // Summary section
      csv += 'SUMMARY METRICS\n'
      csv += 'Metric,Value\n'
      csv += `Total Drivers,${summaryData?.total_drivers || 0}\n`
      csv += `Total Vehicles,${summaryData?.total_vehicles || 0}\n`
      csv += `Monthly Revenue,$${summaryData?.monthly_revenue || 0}\n`
      csv += `Average Risk Score,${summaryData?.avg_risk_score || 0}\n\n`

      // Trip activity section
      csv += 'TRIP ACTIVITY (LAST ' + tripActivityDays + ' DAYS)\n'
      csv += 'Date,Trip Count\n'
      tripData.forEach((item) => {
        csv += `${item.date},${item.trip_count}\n`
      })
      csv += '\n'

      // Risk distribution section
      csv += 'RISK DISTRIBUTION\n'
      csv += 'Risk Level,Count,Percentage\n'
      csv += `Low Risk,${riskData?.low_risk_count || 0},${riskData?.low_risk_percentage || 0}%\n`
      csv += `Medium Risk,${riskData?.medium_risk_count || 0},${riskData?.medium_risk_percentage || 0}%\n`
      csv += `High Risk,${riskData?.high_risk_count || 0},${riskData?.high_risk_percentage || 0}%\n\n`

      // Safety events section
      csv += 'SAFETY EVENTS BREAKDOWN\n'
      csv += 'Event Type,Count\n'
      safetyData.forEach((event) => {
        csv += `${event.event_type},${event.count}\n`
      })

      // Download CSV
      const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' })
      const link = document.createElement('a')
      const url = URL.createObjectURL(blob)
      link.setAttribute('href', url)
      link.setAttribute('download', `dashboard-export-${Date.now()}.csv`)
      link.style.visibility = 'hidden'
      document.body.appendChild(link)
      link.click()
      document.body.removeChild(link)

      showToast('Dashboard data exported successfully', 'success')
    } catch (error) {
      console.error('Export error:', error)
      showToast('Failed to export dashboard data', 'error')
    }
  }, [summary, tripActivity, riskDistribution, safetyEvents, tripActivityDays, showToast])

  // Summary cards data
  const summaryCards = useMemo(
    () => [
      {
        title: 'Total Drivers',
        value: summary?.data?.total_drivers || summary?.total_drivers || 0,
        subtitle: 'Active policyholders',
        icon: UserGroupIcon,
        bgColor: 'from-blue-500 to-blue-600',
        trend: '+12%',
      },
      {
        title: 'Total Vehicles',
        value: summary?.data?.total_vehicles || summary?.total_vehicles || 0,
        subtitle: 'Insured vehicles',
        icon: TruckIcon,
        bgColor: 'from-purple-500 to-purple-600',
        trend: '+8%',
      },
      {
        title: 'Monthly Revenue',
        value: `$${((summary?.data?.monthly_revenue || summary?.monthly_revenue || 0)).toFixed(0)}`,
        subtitle: 'Current premium total',
        icon: CurrencyDollarIcon,
        bgColor: 'from-green-500 to-emerald-600',
        trend: '+15%',
      },
      {
        title: 'Avg Risk Score',
        value: (summary?.data?.avg_risk_score || summary?.avg_risk_score || 0)?.toFixed(0) || 0,
        subtitle: 'Portfolio average',
        icon: ChartBarIcon,
        bgColor: 'from-orange-500 to-amber-600',
        trend: '-3%',
        trendPositive: false,
      },
    ],
    [summary]
  )

  // Process trip activity data for line chart
  const tripActivityData = useMemo(() => {
    const activityData = tripActivity?.data || tripActivity || []

    if (!Array.isArray(activityData) || activityData.length === 0) {
      const dates = []
      const today = new Date()
      for (let i = tripActivityDays - 1; i >= 0; i--) {
        const date = new Date(today)
        date.setDate(date.getDate() - i)
        dates.push({
          date: date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' }),
          trip_count: 0,
        })
      }
      return dates
    }
    return activityData.map((item) => ({
      date: new Date(item.date).toLocaleDateString('en-US', { month: 'short', day: 'numeric' }),
      trip_count: item.trip_count || 0,
    }))
  }, [tripActivity, tripActivityDays])

  // Process risk distribution data for pie chart
  const riskDistributionData = useMemo(() => {
    const distribution = riskDistribution?.data || riskDistribution
    if (!distribution) return []

    const total = distribution.total_drivers || 0
    if (total === 0) return []

    const data = [
      {
        name: 'Low Risk',
        value: distribution.low_risk_count || 0,
        percentage: distribution.low_risk_percentage || 0,
        color: '#10B981',
      },
      {
        name: 'Medium Risk',
        value: distribution.medium_risk_count || 0,
        percentage: distribution.medium_risk_percentage || 0,
        color: '#F59E0B',
      },
      {
        name: 'High Risk',
        value: distribution.high_risk_count || 0,
        percentage: distribution.high_risk_percentage || 0,
        color: '#EF4444',
      },
    ]

    return data.filter((item) => item.value > 0)
  }, [riskDistribution])

  // Custom label for risk distribution pie chart
  const renderRiskLabel = ({ cx, cy, midAngle, innerRadius, outerRadius, percent, name, percentage }) => {
    if (percent === 0) return null

    const RADIAN = Math.PI / 180
    const radius = innerRadius + (outerRadius - innerRadius) * 0.5
    const x = cx + radius * Math.cos(-midAngle * RADIAN)
    const y = cy + radius * Math.sin(-midAngle * RADIAN)

    return (
      <text
        x={x}
        y={y}
        fill="white"
        textAnchor={x > cx ? 'start' : 'end'}
        dominantBaseline="central"
        className="text-sm font-semibold"
      >
        {`${name}: ${percentage.toFixed(0)}%`}
      </text>
    )
  }

  // Process safety events data for bar chart
  const safetyEventsData = useMemo(() => {
    const eventsData = safetyEvents?.data || safetyEvents || []

    if (!Array.isArray(eventsData) || eventsData.length === 0) {
      return [
        { name: 'Hard Braking', count: 0 },
        { name: 'Rapid Accel', count: 0 },
        { name: 'Sharp Turns', count: 0 },
        { name: 'Speeding', count: 0 },
      ]
    }
    return eventsData.map((event) => ({
      name: event.event_type,
      count: event.count || 0,
    }))
  }, [safetyEvents])

  // Process policy type distribution data for pie chart
  const policyTypeData = useMemo(() => {
    const typesData = policyTypes?.data || policyTypes || []

    if (!Array.isArray(typesData) || typesData.length === 0) return []
    return typesData.map((policy) => ({
      name: policy.policy_type,
      value: policy.count || 0,
    }))
  }, [policyTypes])

  const POLICY_COLORS = ['#3B82F6', '#6366F1', '#EC4899', '#14B8A6', '#F97316']

  // Custom label for policy type pie chart
  const renderPolicyLabel = ({ name, percent, value }) => {
    if (percent === 0) return null
    return `${name}: ${value}`
  }

  // Check if there are any errors
  const hasErrors =
    summaryError || tripActivityError || riskDistributionError || safetyEventsError || policyTypesError

  // Check if initial loading
  const isInitialLoading =
    isLoadingSummary && isLoadingTripActivity && isLoadingRiskDistribution && isLoadingSafetyEvents && isLoadingPolicyTypes

  // Show full skeleton loader on initial load
  if (isInitialLoading) {
    return (
      <div>
        <LoadingSkeleton type="dashboard" />
        {ToastComponent}
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Toast Notifications */}
      {ToastComponent}

      {/* Header */}
      <div className="flex flex-col md:flex-row md:justify-between md:items-center gap-4">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Admin Dashboard</h1>
          <p className="text-gray-600 mt-1 flex items-center gap-2">
            <span>System-wide metrics and analytics</span>
            {lastUpdated && (
              <span className="text-xs text-gray-500 flex items-center gap-1">
                <ClockIcon className="w-3 h-3" />
                Updated {lastUpdated.toLocaleTimeString()}
              </span>
            )}
          </p>
        </div>
        <div className="flex flex-wrap gap-3">
          {/* Auto-refresh indicator */}
          <div className="inline-flex items-center px-3 py-2 border border-gray-300 text-xs font-medium rounded-md text-gray-700 bg-white">
            <ArrowPathIcon className="w-4 h-4 mr-2 animate-spin-slow" />
            Auto-refresh in {autoRefreshCountdown}s
          </div>

          {/* Refresh button */}
          <button
            onClick={handleRefreshAll}
            className="inline-flex items-center px-4 py-2 border border-gray-300 text-sm font-medium rounded-md shadow-sm text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 transition-colors"
          >
            <ArrowPathIcon className="w-4 h-4 mr-2" />
            Refresh Now
          </button>

          {/* Export button */}
          <button
            onClick={handleExportCSV}
            className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 transition-colors"
          >
            <ArrowDownTrayIcon className="w-4 h-4 mr-2" />
            Export CSV
          </button>
        </div>
      </div>

      {/* Error Messages */}
      {summaryError && (
        <ErrorMessage error={summaryError} onDismiss={() => window.location.reload()} />
      )}

      {/* Top Row - Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {summaryCards.map((card, index) => (
          <div
            key={index}
            className={`bg-gradient-to-br ${card.bgColor} rounded-xl shadow-lg p-6 text-white flex flex-col justify-between transition-transform hover:scale-105`}
          >
            {isLoadingSummary ? (
              <CardSkeleton />
            ) : (
              <>
                <div className="flex items-center justify-between mb-4">
                  <p className="text-sm font-medium text-white/80">{card.title}</p>
                  <card.icon className="w-6 h-6 text-white/80" />
                </div>
                <p className="text-4xl font-bold leading-none">{card.value}</p>
                <div className="mt-2 flex items-center justify-between">
                  <p className="text-sm text-white/70">{card.subtitle}</p>
                  {card.trend && (
                    <span
                      className={`text-xs font-semibold px-2 py-1 rounded ${
                        card.trendPositive === false ? 'bg-red-500/20' : 'bg-green-500/20'
                      }`}
                    >
                      {card.trend}
                    </span>
                  )}
                </div>
              </>
            )}
          </div>
        ))}
      </div>

      {/* Middle Row - Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Trip Activity - Line Chart */}
        <div className="bg-white rounded-xl shadow-lg p-6">
          <div className="flex justify-between items-center mb-4">
            <h2 className="text-xl font-semibold text-gray-900">
              Trip Activity ({tripActivityDays} Days)
            </h2>
            <select
              value={tripActivityDays}
              onChange={(e) => setTripActivityDays(Number(e.target.value))}
              className="px-3 py-1 text-sm border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value={7}>7 Days</option>
              <option value={14}>14 Days</option>
              <option value={30}>30 Days</option>
            </select>
          </div>
          {isLoadingTripActivity ? (
            <ChartSkeleton />
          ) : tripActivityError ? (
            <div className="h-64 flex flex-col items-center justify-center text-gray-500">
              <ExclamationTriangleIcon className="w-12 h-12 text-red-400 mb-2" />
              <p>Failed to load trip activity</p>
              <button
                onClick={() => refetchTripActivity()}
                className="mt-2 text-sm text-blue-600 hover:underline"
              >
                Try again
              </button>
            </div>
          ) : (
            <ResponsiveContainer width="100%" height={300}>
              <LineChart data={tripActivityData} margin={{ top: 5, right: 30, left: 20, bottom: 5 }}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="date" tick={{ fontSize: 12 }} />
                <YAxis domain={[0, 'dataMax + 10']} tick={{ fontSize: 12 }} />
                <Tooltip
                  formatter={(value) => [value, 'Trips']}
                  labelFormatter={(label) => `Date: ${label}`}
                />
                <Legend />
                <Line
                  type="monotone"
                  dataKey="trip_count"
                  stroke="#10B981"
                  strokeWidth={2}
                  activeDot={{ r: 6 }}
                  name="Trips"
                />
              </LineChart>
            </ResponsiveContainer>
          )}
        </div>

        {/* Risk Distribution - Pie Chart */}
        <div className="bg-white rounded-xl shadow-lg p-6">
          <h2 className="text-xl font-semibold text-gray-900 mb-4">Risk Distribution</h2>
          {isLoadingRiskDistribution ? (
            <ChartSkeleton />
          ) : riskDistributionError ? (
            <div className="h-64 flex flex-col items-center justify-center text-gray-500">
              <ExclamationTriangleIcon className="w-12 h-12 text-red-400 mb-2" />
              <p>Failed to load risk distribution</p>
              <button
                onClick={() => refetchRiskDistribution()}
                className="mt-2 text-sm text-blue-600 hover:underline"
              >
                Try again
              </button>
            </div>
          ) : riskDistributionData.length === 0 ? (
            <div className="h-64 flex items-center justify-center text-gray-500">
              No risk distribution data available
            </div>
          ) : (
            <ResponsiveContainer width="100%" height={300}>
              <PieChart>
                <Pie
                  data={riskDistributionData}
                  cx="50%"
                  cy="50%"
                  labelLine={false}
                  label={renderRiskLabel}
                  outerRadius={100}
                  fill="#8884d8"
                  dataKey="value"
                >
                  {riskDistributionData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Pie>
                <Tooltip
                  formatter={(value, name, props) => [
                    `${value} drivers (${props.payload.percentage.toFixed(0)}%)`,
                    props.payload.name,
                  ]}
                />
                <Legend />
              </PieChart>
            </ResponsiveContainer>
          )}
        </div>
      </div>

      {/* Bottom Row - Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Safety Events Breakdown - Bar Chart */}
        <div className="bg-white rounded-xl shadow-lg p-6">
          <h2 className="text-xl font-semibold text-gray-900 mb-4 flex items-center gap-2">
            <span className="text-orange-500">▲</span>
            Safety Events Breakdown
          </h2>
          {isLoadingSafetyEvents ? (
            <ChartSkeleton />
          ) : safetyEventsError ? (
            <div className="h-64 flex flex-col items-center justify-center text-gray-500">
              <ExclamationTriangleIcon className="w-12 h-12 text-red-400 mb-2" />
              <p>Failed to load safety events</p>
              <button
                onClick={() => refetchSafetyEvents()}
                className="mt-2 text-sm text-blue-600 hover:underline"
              >
                Try again
              </button>
            </div>
          ) : (
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={safetyEventsData} margin={{ top: 5, right: 30, left: 20, bottom: 5 }}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis
                  dataKey="name"
                  tick={{ fontSize: 12 }}
                  angle={-45}
                  textAnchor="end"
                  height={80}
                />
                <YAxis domain={[0, 'dataMax + 2']} tick={{ fontSize: 12 }} />
                <Tooltip formatter={(value) => [value, 'Events']} />
                <Legend />
                <Bar dataKey="count" fill="#F59E0B" name="Event Count" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          )}
        </div>

        {/* Policy Type Distribution - Pie Chart */}
        <div className="bg-white rounded-xl shadow-lg p-6">
          <h2 className="text-xl font-semibold text-gray-900 mb-4">Policy Type Distribution</h2>
          {isLoadingPolicyTypes ? (
            <ChartSkeleton />
          ) : policyTypesError ? (
            <div className="h-64 flex flex-col items-center justify-center text-gray-500">
              <ExclamationTriangleIcon className="w-12 h-12 text-red-400 mb-2" />
              <p>Failed to load policy types</p>
              <button
                onClick={() => refetchPolicyTypes()}
                className="mt-2 text-sm text-blue-600 hover:underline"
              >
                Try again
              </button>
            </div>
          ) : policyTypeData.length === 0 ? (
            <div className="h-64 flex items-center justify-center text-gray-500">
              No policy type data available
            </div>
          ) : (
            <ResponsiveContainer width="100%" height={300}>
              <PieChart>
                <Pie
                  data={policyTypeData}
                  cx="50%"
                  cy="50%"
                  labelLine={false}
                  outerRadius={100}
                  fill="#8884d8"
                  dataKey="value"
                  label={renderPolicyLabel}
                >
                  {policyTypeData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={POLICY_COLORS[index % POLICY_COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip
                  formatter={(value, name, props) => [`${value} policies`, props.payload.name]}
                />
                <Legend />
              </PieChart>
            </ResponsiveContainer>
          )}
        </div>
      </div>
    </div>
  )
}
