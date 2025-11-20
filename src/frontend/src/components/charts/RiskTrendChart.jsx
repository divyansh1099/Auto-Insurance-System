import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts'
import { useTheme } from '../../contexts/ThemeContext'

export default function RiskTrendChart({ data = [] }) {
  const { theme } = useTheme()
  const isDark = theme === 'dark'

  // If no data, show placeholder
  if (!data || data.length === 0) {
    return (
      <div className="h-64 flex items-center justify-center text-gray-500 dark:text-gray-400">
        No historical data available
      </div>
    )
  }

  // Custom tooltip for better dark mode support
  const CustomTooltip = ({ active, payload, label }) => {
    if (active && payload && payload.length) {
      return (
        <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg shadow-lg p-3">
          <p className="text-sm font-semibold text-gray-900 dark:text-white mb-1">
            {label}
          </p>
          <p className="text-sm text-blue-600 dark:text-blue-400">
            Risk Score: <span className="font-bold">{payload[0].value.toFixed(1)}</span>
          </p>
        </div>
      )
    }
    return null
  }

  return (
    <ResponsiveContainer width="100%" height={300}>
      <LineChart data={data} margin={{ top: 5, right: 20, left: 0, bottom: 5 }}>
        <CartesianGrid
          strokeDasharray="3 3"
          stroke={isDark ? '#374151' : '#e5e7eb'}
          opacity={0.5}
        />
        <XAxis
          dataKey="date"
          tick={{ fontSize: 12, fill: isDark ? '#9ca3af' : '#6b7280' }}
          stroke={isDark ? '#4b5563' : '#d1d5db'}
          angle={-45}
          textAnchor="end"
          height={80}
        />
        <YAxis
          domain={[0, 100]}
          tick={{ fontSize: 12, fill: isDark ? '#9ca3af' : '#6b7280' }}
          stroke={isDark ? '#4b5563' : '#d1d5db'}
          label={{
            value: 'Risk Score',
            angle: -90,
            position: 'insideLeft',
            style: { fill: isDark ? '#9ca3af' : '#6b7280' }
          }}
        />
        <Tooltip content={<CustomTooltip />} />
        <Legend
          wrapperStyle={{
            paddingTop: '20px',
            color: isDark ? '#e5e7eb' : '#374151'
          }}
        />
        <Line
          type="monotone"
          dataKey="risk_score"
          stroke={isDark ? '#60a5fa' : '#3b82f6'}
          strokeWidth={3}
          dot={{
            r: 5,
            fill: isDark ? '#60a5fa' : '#3b82f6',
            strokeWidth: 2,
            stroke: isDark ? '#1e40af' : '#1d4ed8'
          }}
          activeDot={{ r: 7 }}
          name="Risk Score"
        />
      </LineChart>
    </ResponsiveContainer>
  )
}
