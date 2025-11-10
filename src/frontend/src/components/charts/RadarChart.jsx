import { RadarChart as RechartsRadarChart, Radar, PolarGrid, PolarAngleAxis, PolarRadiusAxis, ResponsiveContainer, Tooltip, Legend } from 'recharts'

export default function RiskFactorRadarChart({ data = {} }) {
  if (!data || Object.keys(data).length === 0) {
    return (
      <div className="h-64 flex items-center justify-center text-gray-500">
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

  return (
    <ResponsiveContainer width="100%" height={300}>
      <RechartsRadarChart data={chartData}>
        <PolarGrid />
        <PolarAngleAxis 
          dataKey="category" 
          tick={{ fontSize: 12 }}
        />
        <PolarRadiusAxis 
          angle={90} 
          domain={[0, 100]}
          tick={{ fontSize: 10 }}
        />
        <Radar
          name="Risk Score"
          dataKey="value"
          stroke="#3b82f6"
          fill="#3b82f6"
          fillOpacity={0.6}
        />
        <Tooltip 
          formatter={(value) => [value.toFixed(1), 'Score']}
        />
        <Legend />
      </RechartsRadarChart>
    </ResponsiveContainer>
  )
}

