import { PieChart, Pie, Cell, ResponsiveContainer } from 'recharts'

export default function CircularProgressChart({ score, size = 120 }) {
  const roundedScore = Math.round(score)
  const data = [
    { name: 'Score', value: roundedScore },
    { name: 'Remaining', value: 100 - roundedScore }
  ]

  const COLORS = ['#10b981', '#e5e7eb'] // Green for score, gray for remaining

  return (
    <div className="relative" style={{ width: size, height: size }}>
      <ResponsiveContainer width="100%" height="100%">
        <PieChart>
          <Pie
            data={data}
            cx="50%"
            cy="50%"
            innerRadius={size * 0.35}
            outerRadius={size * 0.5}
            startAngle={90}
            endAngle={-270}
            dataKey="value"
          >
            {data.map((entry, index) => (
              <Cell key={`cell-${index}`} fill={COLORS[index]} />
            ))}
          </Pie>
        </PieChart>
      </ResponsiveContainer>
      <div className="absolute inset-0 flex flex-col items-center justify-center">
        <div className="text-3xl font-bold text-gray-900">{Math.round(score)}</div>
        <div className="text-sm text-gray-500">Overall</div>
      </div>
    </div>
  )
}

