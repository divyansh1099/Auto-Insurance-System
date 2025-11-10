import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts'

export default function PremiumComparisonChart({ comparison }) {
  if (!comparison) {
    return (
      <div className="h-64 flex items-center justify-center text-gray-500">
        Loading comparison data...
      </div>
    )
  }

  const data = [
    {
      name: 'Traditional',
      monthly: comparison.traditional_monthly || 0,
      annual: (comparison.traditional_monthly || 0) * 12
    },
    {
      name: 'Telematics',
      monthly: comparison.telematics_monthly || 0,
      annual: (comparison.telematics_monthly || 0) * 12
    }
  ]

  return (
    <ResponsiveContainer width="100%" height={300}>
      <BarChart data={data}>
        <CartesianGrid strokeDasharray="3 3" />
        <XAxis dataKey="name" tick={{ fontSize: 12 }} />
        <YAxis 
          label={{ value: 'Premium ($)', angle: -90, position: 'insideLeft' }}
          tick={{ fontSize: 12 }}
        />
        <Tooltip 
          formatter={(value) => [`$${value.toFixed(2)}`, '']}
        />
        <Legend />
        <Bar dataKey="monthly" fill="#3b82f6" name="Monthly Premium" radius={[8, 8, 0, 0]} />
        <Bar dataKey="annual" fill="#10b981" name="Annual Premium" radius={[8, 8, 0, 0]} />
      </BarChart>
    </ResponsiveContainer>
  )
}

