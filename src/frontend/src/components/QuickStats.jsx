export default function QuickStats({ stats }) {
  const statItems = [
    {
      label: 'Total Miles',
      value: stats?.total_miles?.toFixed(0) || '0',
      unit: 'mi'
    },
    {
      label: 'Total Trips',
      value: stats?.total_trips || '0',
      unit: ''
    },
    {
      label: 'Avg Speed',
      value: stats?.avg_speed?.toFixed(0) || '0',
      unit: 'mph'
    },
    {
      label: 'Harsh Braking',
      value: stats?.harsh_braking_rate?.toFixed(1) || '0',
      unit: '/100mi'
    }
  ]

  return (
    <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
      {statItems.map((stat, index) => (
        <div key={index} className="p-4 bg-gray-50 rounded-lg">
          <div className="text-sm text-gray-600">{stat.label}</div>
          <div className="mt-1">
            <span className="text-2xl font-bold text-gray-900">{stat.value}</span>
            {stat.unit && <span className="text-sm text-gray-500 ml-1">{stat.unit}</span>}
          </div>
        </div>
      ))}
    </div>
  )
}
