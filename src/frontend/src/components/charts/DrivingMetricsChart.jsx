import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts'
import { useTheme } from '../../contexts/ThemeContext'

export default function DrivingMetricsChart({ stats }) {
  const { theme } = useTheme()
  const isDark = theme === 'dark'

  if (!stats) {
    return (
      <div className="h-64 flex items-center justify-center text-gray-500 dark:text-gray-400">
        Loading metrics...
      </div>
    )
  }

  const data = [
    {
      name: 'Harsh Braking',
      value: stats.harsh_braking_rate || 0,
      color: isDark ? '#f87171' : '#ef4444'
    },
    {
      name: 'Rapid Accel',
      value: stats.rapid_accel_rate || 0,
      color: isDark ? '#fb923c' : '#f97316'
    },
    {
      name: 'Speeding',
      value: stats.speeding_rate || 0,
      color: isDark ? '#ef4444' : '#dc2626'
    }
  ]

  // Custom tooltip
  const CustomTooltip = ({ active, payload }) => {
    if (active && payload && payload.length) {
      return (
        <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg shadow-lg p-3">
          <p className="text-sm font-semibold text-gray-900 dark:text-white mb-1">
            {payload[0].payload.name}
          </p>
          <p className="text-sm text-blue-600 dark:text-blue-400">
            <span className="font-bold">{payload[0].value.toFixed(2)}</span> events/100mi
          </p>
        </div>
      )
    }
    return null
  }

  return (
    <ResponsiveContainer width="100%" height={300}>
      <BarChart data={data}>
        <CartesianGrid
          strokeDasharray="3 3"
          stroke={isDark ? '#374151' : '#e5e7eb'}
          opacity={0.5}
        />
        <XAxis
          dataKey="name"
          tick={{
            fontSize: 12,
            fill: isDark ? '#9ca3af' : '#6b7280'
          }}
          stroke={isDark ? '#4b5563' : '#d1d5db'}
        />
        <YAxis
          label={{
            value: 'Events per 100mi',
            angle: -90,
            position: 'insideLeft',
            style: { fill: isDark ? '#9ca3af' : '#6b7280' }
          }}
          tick={{
            fontSize: 12,
            fill: isDark ? '#9ca3af' : '#6b7280'
          }}
          stroke={isDark ? '#4b5563' : '#d1d5db'}
        />
        <Tooltip content={<CustomTooltip />} />
        <Legend
          wrapperStyle={{
            paddingTop: '20px',
            color: isDark ? '#e5e7eb' : '#374151'
          }}
        />
        <Bar
          dataKey="value"
          fill={isDark ? '#60a5fa' : '#3b82f6'}
          radius={[8, 8, 0, 0]}
        />
      </BarChart>
    </ResponsiveContainer>
  )
}
