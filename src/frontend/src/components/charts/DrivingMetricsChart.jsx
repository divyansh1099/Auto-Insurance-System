import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts'

export default function DrivingMetricsChart({ stats }) {
  if (!stats) {
    return (
      <div className="h-64 flex items-center justify-center text-gray-500">
        Loading metrics...
      </div>
    )
  }

  const data = [
    {
      name: 'Harsh Braking',
      value: stats.harsh_braking_rate || 0,
      color: '#ef4444'
    },
    {
      name: 'Rapid Accel',
      value: stats.rapid_accel_rate || 0,
      color: '#f97316'
    },
    {
      name: 'Speeding',
      value: stats.speeding_rate || 0,
      color: '#dc2626'
    }
  ]

  return (
    <ResponsiveContainer width="100%" height={300}>
      <BarChart data={data}>
        <CartesianGrid strokeDasharray="3 3" />
        <XAxis dataKey="name" tick={{ fontSize: 12 }} />
        <YAxis 
          label={{ value: 'Events per 100mi', angle: -90, position: 'insideLeft' }}
          tick={{ fontSize: 12 }}
        />
        <Tooltip 
          formatter={(value) => [value.toFixed(2), 'Events/100mi']}
        />
        <Legend />
        <Bar 
          dataKey="value" 
          fill="#3b82f6"
          radius={[8, 8, 0, 0]}
        />
      </BarChart>
    </ResponsiveContainer>
  )
}

