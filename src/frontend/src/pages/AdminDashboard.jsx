import { useMemo } from 'react'
import { useQuery } from 'react-query'
import { adminAPI } from '../services/api'
import {
  UserGroupIcon,
  TruckIcon,
  CurrencyDollarIcon,
  ChartBarIcon,
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

export default function AdminDashboard() {
  // Debug: Log that AdminDashboard is rendering
  console.log('AdminDashboard component is rendering')
  
  // Fetch summary data (4 cards)
  const { data: summary, isLoading: isLoadingSummary, error: summaryError } = useQuery(
    ['adminDashboardSummary'],
    () => adminAPI.getDashboardSummary(),
    { 
      retry: false,
      onError: (error) => console.error('AdminDashboard API Error:', error)
    }
  )

  // Fetch trip activity data (7 days)
  const { data: tripActivity, isLoading: isLoadingTripActivity } = useQuery(
    ['adminTripActivity'],
    () => adminAPI.getTripActivity(7),
    { retry: false }
  )

  // Fetch risk distribution data
  const { data: riskDistribution, isLoading: isLoadingRiskDistribution } = useQuery(
    ['adminRiskDistribution'],
    () => adminAPI.getRiskDistribution(),
    { retry: false }
  )

  // Fetch safety events breakdown data
  const { data: safetyEvents, isLoading: isLoadingSafetyEvents } = useQuery(
    ['adminSafetyEvents'],
    () => adminAPI.getSafetyEventsBreakdown(),
    { retry: false }
  )

  // Fetch policy type distribution data
  const { data: policyTypes, isLoading: isLoadingPolicyTypes } = useQuery(
    ['adminPolicyTypes'],
    () => adminAPI.getPolicyTypeDistribution(),
    { retry: false }
  )

  // Summary cards data
  const summaryCards = [
    {
      title: 'Total Drivers',
      value: summary?.data?.total_drivers || summary?.total_drivers || 0,
      subtitle: 'Active policyholders',
      icon: UserGroupIcon,
      bgColor: 'from-blue-500 to-blue-600',
    },
    {
      title: 'Total Vehicles',
      value: summary?.data?.total_vehicles || summary?.total_vehicles || 0,
      subtitle: 'Insured vehicles',
      icon: TruckIcon,
      bgColor: 'from-purple-500 to-purple-600',
    },
    {
      title: 'Monthly Revenue',
      value: `$${((summary?.data?.monthly_revenue || summary?.monthly_revenue || 0)).toFixed(0)}`,
      subtitle: 'Current premium total',
      icon: CurrencyDollarIcon,
      bgColor: 'from-green-500 to-emerald-600',
    },
    {
      title: 'Avg Risk Score',
      value: (summary?.data?.avg_risk_score || summary?.avg_risk_score || 0)?.toFixed(0) || 0,
      subtitle: 'Portfolio average',
      icon: ChartBarIcon,
      bgColor: 'from-orange-500 to-amber-600',
    },
  ]

  // Process trip activity data for line chart
  const tripActivityData = useMemo(() => {
    // Handle axios response structure
    const activityData = tripActivity?.data || tripActivity || []
    
    if (!Array.isArray(activityData) || activityData.length === 0) {
      // Generate empty data for last 7 days if no data
      const dates = []
      const today = new Date()
      for (let i = 6; i >= 0; i--) {
        const date = new Date(today)
        date.setDate(date.getDate() - i)
        dates.push({
          date: date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' }),
          trip_count: 0,
        })
      }
      return dates
    }
    return activityData.map(item => ({
      date: new Date(item.date).toLocaleDateString('en-US', { month: 'short', day: 'numeric' }),
      trip_count: item.trip_count || 0,
    }))
  }, [tripActivity])

  // Process risk distribution data for pie chart
  const riskDistributionData = useMemo(() => {
    // Handle axios response structure
    const distribution = riskDistribution?.data || riskDistribution
    if (!distribution) return []
    
    const total = distribution.total_drivers || 0
    if (total === 0) return []

    const data = [
      {
        name: 'Low Risk',
        value: distribution.low_risk_count || 0,
        percentage: distribution.low_risk_percentage || 0,
        color: '#10B981', // Green
      },
      {
        name: 'Medium Risk',
        value: distribution.medium_risk_count || 0,
        percentage: distribution.medium_risk_percentage || 0,
        color: '#F59E0B', // Yellow/Orange
      },
      {
        name: 'High Risk',
        value: distribution.high_risk_count || 0,
        percentage: distribution.high_risk_percentage || 0,
        color: '#EF4444', // Red
      },
    ]
    
    return data.filter(item => item.value > 0) // Only show segments with values
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
    // Handle axios response structure
    const eventsData = safetyEvents?.data || safetyEvents || []
    
    if (!Array.isArray(eventsData) || eventsData.length === 0) {
      return [
        { name: 'Hard Braking', count: 0 },
        { name: 'Rapid Accel', count: 0 },
        { name: 'Sharp Turns', count: 0 },
        { name: 'Speeding', count: 0 },
      ]
    }
    return eventsData.map(event => ({
      name: event.event_type,
      count: event.count || 0,
    }))
  }, [safetyEvents])

  // Process policy type distribution data for pie chart
  const policyTypeData = useMemo(() => {
    // Handle axios response structure
    const typesData = policyTypes?.data || policyTypes || []
    
    if (!Array.isArray(typesData) || typesData.length === 0) return []
    return typesData.map(policy => ({
      name: policy.policy_type,
      value: policy.count || 0,
    }))
  }, [policyTypes])

  const POLICY_COLORS = ['#3B82F6', '#6366F1', '#EC4899', '#14B8A6', '#F97316'] // Blue, Indigo, Pink, Teal, Orange

  // Custom label for policy type pie chart
  const renderPolicyLabel = ({ name, percent, value }) => {
    if (percent === 0) return null
    return `${name}: ${value}`
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
      <h1 className="text-3xl font-bold text-gray-900">Admin Dashboard</h1>
          <p className="text-gray-600 mt-1">System-wide metrics and analytics</p>
        </div>
        <div className="flex space-x-3">
          <button className="inline-flex items-center px-4 py-2 border border-gray-300 text-sm font-medium rounded-md shadow-sm text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500">
            Share
          </button>
          <button className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500">
            Publish
          </button>
        </div>
      </div>

      {/* Top Row - Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {summaryCards.map((card, index) => (
          <div
            key={index}
            className={`bg-gradient-to-br ${card.bgColor} rounded-xl shadow-lg p-6 text-white flex flex-col justify-between`}
          >
            <div className="flex items-center justify-between mb-4">
              <p className="text-sm font-medium text-white/80">{card.title}</p>
              <card.icon className="w-6 h-6 text-white/80" />
            </div>
            <p className="text-4xl font-bold leading-none">
              {isLoadingSummary ? '...' : card.value}
            </p>
            <p className="mt-2 text-sm text-white/70">{card.subtitle}</p>
          </div>
        ))}
      </div>

      {/* Middle Row - Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Trip Activity (7 Days) - Line Chart */}
        <div className="bg-white rounded-xl shadow-lg p-6">
          <h2 className="text-xl font-semibold text-gray-900 mb-4">Trip Activity (7 Days)</h2>
          {isLoadingTripActivity ? (
            <div className="h-64 flex items-center justify-center text-gray-500">
              Loading trip activity...
            </div>
          ) : (
            <ResponsiveContainer width="100%" height={300}>
              <LineChart
                data={tripActivityData}
                margin={{ top: 5, right: 30, left: 20, bottom: 5 }}
              >
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis 
                  dataKey="date" 
                  tick={{ fontSize: 12 }}
                />
                <YAxis 
                  domain={[0, 'dataMax + 10']}
                  tick={{ fontSize: 12 }}
                />
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
            <div className="h-64 flex items-center justify-center text-gray-500">
              Loading risk distribution...
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
                    props.payload.name
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
            <div className="h-64 flex items-center justify-center text-gray-500">
              Loading safety events...
            </div>
          ) : (
            <ResponsiveContainer width="100%" height={300}>
              <BarChart
                data={safetyEventsData}
                margin={{ top: 5, right: 30, left: 20, bottom: 5 }}
              >
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis 
                  dataKey="name" 
                  tick={{ fontSize: 12 }}
                  angle={-45}
                  textAnchor="end"
                  height={80}
                />
                <YAxis 
                  domain={[0, 'dataMax + 2']}
                  tick={{ fontSize: 12 }}
                />
                <Tooltip 
                  formatter={(value) => [value, 'Events']}
                />
                <Legend />
                <Bar 
                  dataKey="count" 
                  fill="#F59E0B" 
                  name="Event Count"
                  radius={[4, 4, 0, 0]}
                />
              </BarChart>
            </ResponsiveContainer>
          )}
        </div>

        {/* Policy Type Distribution - Pie Chart */}
        <div className="bg-white rounded-xl shadow-lg p-6">
          <h2 className="text-xl font-semibold text-gray-900 mb-4">Policy Type Distribution</h2>
          {isLoadingPolicyTypes ? (
            <div className="h-64 flex items-center justify-center text-gray-500">
              Loading policy types...
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
                    <Cell 
                      key={`cell-${index}`} 
                      fill={POLICY_COLORS[index % POLICY_COLORS.length]} 
                    />
                  ))}
                </Pie>
                <Tooltip 
                  formatter={(value, name, props) => [
                    `${value} policies`,
                    props.payload.name
                  ]}
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
