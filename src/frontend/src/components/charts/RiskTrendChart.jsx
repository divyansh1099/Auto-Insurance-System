import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts'

export default function RiskTrendChart({ data = [] }) {
  // If no data, show placeholder
  if (!data || data.length === 0) {
    return (
      <div className="h-64 flex items-center justify-center text-gray-500">
        No historical data available
      </div>
    )
  }

  return (
    <ResponsiveContainer width="100%" height={300}>
      <LineChart data={data}>
        <CartesianGrid strokeDasharray="3 3" />
        <XAxis 
          dataKey="date" 
          tick={{ fontSize: 12 }}
          angle={-45}
          textAnchor="end"
          height={80}
        />
        <YAxis 
          domain={[0, 100]}
          tick={{ fontSize: 12 }}
          label={{ value: 'Risk Score', angle: -90, position: 'insideLeft' }}
        />
        <Tooltip 
          formatter={(value) => [value.toFixed(1), 'Risk Score']}
          labelFormatter={(label) => `Date: ${label}`}
        />
        <Legend />
        <Line 
          type="monotone" 
          dataKey="risk_score" 
          stroke="#3b82f6" 
          strokeWidth={2}
          dot={{ r: 4 }}
          name="Risk Score"
        />
      </LineChart>
    </ResponsiveContainer>
  )
}

