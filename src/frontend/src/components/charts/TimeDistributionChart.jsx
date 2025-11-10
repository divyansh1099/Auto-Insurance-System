import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip, Legend } from 'recharts'

export default function TimeDistributionChart({ stats }) {
  if (!stats) {
    return (
      <div className="h-64 flex items-center justify-center text-gray-500">
        Loading data...
      </div>
    )
  }

  const data = [
    { name: 'Daytime', value: 100 - (stats.night_driving_pct || 0), color: '#3b82f6' },
    { name: 'Night', value: stats.night_driving_pct || 0, color: '#1e293b' },
  ]

  const rushHourData = [
    { name: 'Rush Hour', value: stats.rush_hour_pct || 0, color: '#f97316' },
    { name: 'Other Times', value: 100 - (stats.rush_hour_pct || 0), color: '#e5e7eb' },
  ]

  const COLORS = ['#3b82f6', '#1e293b', '#f97316', '#e5e7eb']

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
      <div>
        <h3 className="text-lg font-semibold mb-4 text-center">Day vs Night Driving</h3>
        <ResponsiveContainer width="100%" height={250}>
          <PieChart>
            <Pie
              data={data}
              cx="50%"
              cy="50%"
              labelLine={false}
              label={({ name, percent }) => `${name}: ${(percent * 100).toFixed(1)}%`}
              outerRadius={80}
              fill="#8884d8"
              dataKey="value"
            >
              {data.map((entry, index) => (
                <Cell key={`cell-${index}`} fill={entry.color} />
              ))}
            </Pie>
            <Tooltip formatter={(value) => `${value.toFixed(1)}%`} />
          </PieChart>
        </ResponsiveContainer>
      </div>

      <div>
        <h3 className="text-lg font-semibold mb-4 text-center">Rush Hour Distribution</h3>
        <ResponsiveContainer width="100%" height={250}>
          <PieChart>
            <Pie
              data={rushHourData}
              cx="50%"
              cy="50%"
              labelLine={false}
              label={({ name, percent }) => `${name}: ${(percent * 100).toFixed(1)}%`}
              outerRadius={80}
              fill="#8884d8"
              dataKey="value"
            >
              {rushHourData.map((entry, index) => (
                <Cell key={`cell-${index}`} fill={entry.color} />
              ))}
            </Pie>
            <Tooltip formatter={(value) => `${value.toFixed(1)}%`} />
          </PieChart>
        </ResponsiveContainer>
      </div>
    </div>
  )
}

