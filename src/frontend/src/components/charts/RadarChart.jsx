import { RadarChart as RechartsRadarChart, Radar, PolarGrid, PolarAngleAxis, PolarRadiusAxis, ResponsiveContainer, Tooltip, Legend } from 'recharts'
import { useTheme } from '../../contexts/ThemeContext'

export default function RiskFactorRadarChart({ data = {} }) {
  const { theme } = useTheme()
  const isDark = theme === 'dark'

  if (!data || Object.keys(data).length === 0) {
    return (
      <div className="h-64 flex items-center justify-center text-gray-500 dark:text-gray-400">
        No risk factor data available
      </div>
    )
  }

  // Transform data for radar chart
  const chartData = [
    {
      category: 'Behavior',
      value: data.behavior || 0,
      fullMark: 100
    },
    {
      category: 'Mileage',
      value: data.mileage || 0,
      fullMark: 100
    },
    {
      category: 'Time Pattern',
      value: data.time_pattern || 0,
      fullMark: 100
    },
    {
      category: 'Location',
      value: data.location || 0,
      fullMark: 100
    }
  ]

  // Custom tooltip
  const CustomTooltip = ({ active, payload }) => {
    if (active && payload && payload.length) {
      return (
        <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg shadow-lg p-3">
          <p className="text-sm font-semibold text-gray-900 dark:text-white mb-1">
            {payload[0].payload.category}
          </p>
          <p className="text-sm text-blue-600 dark:text-blue-400">
            Score: <span className="font-bold">{payload[0].value.toFixed(1)}</span>
          </p>
        </div>
      )
    }
    return null
  }

  return (
    <ResponsiveContainer width="100%" height={300}>
      <RechartsRadarChart data={chartData}>
        <PolarGrid
          stroke={isDark ? '#4b5563' : '#d1d5db'}
          strokeWidth={1}
        />
        <PolarAngleAxis
          dataKey="category"
          tick={{
            fontSize: 12,
            fill: isDark ? '#e5e7eb' : '#374151',
            fontWeight: 500
          }}
        />
        <PolarRadiusAxis
          angle={90}
          domain={[0, 100]}
          tick={{
            fontSize: 10,
            fill: isDark ? '#9ca3af' : '#6b7280'
          }}
          stroke={isDark ? '#4b5563' : '#d1d5db'}
        />
        <Radar
          name="Risk Score"
          dataKey="value"
          stroke={isDark ? '#60a5fa' : '#3b82f6'}
          fill={isDark ? '#60a5fa' : '#3b82f6'}
          fillOpacity={isDark ? 0.4 : 0.6}
          strokeWidth={2}
        />
        <Tooltip content={<CustomTooltip />} />
        <Legend
          wrapperStyle={{
            paddingTop: '20px',
            color: isDark ? '#e5e7eb' : '#374151'
          }}
        />
      </RechartsRadarChart>
    </ResponsiveContainer>
  )
}
