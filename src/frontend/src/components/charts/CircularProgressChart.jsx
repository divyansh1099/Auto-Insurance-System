import { PieChart, Pie, Cell, ResponsiveContainer } from 'recharts'
import { useTheme } from '../../contexts/ThemeContext'

export default function CircularProgressChart({ score, size = 120 }) {
  const { theme } = useTheme()
  const isDark = theme === 'dark'

  const roundedScore = Math.round(score)
  const data = [
    { name: 'Score', value: roundedScore },
    { name: 'Remaining', value: 100 - roundedScore }
  ]

  // Dynamic colors based on score and theme
  const getScoreColor = (score) => {
    if (score >= 80) return isDark ? '#34d399' : '#10b981' // Green
    if (score >= 60) return isDark ? '#fbbf24' : '#f59e0b' // Yellow
    return isDark ? '#f87171' : '#ef4444' // Red
  }

  const COLORS = [
    getScoreColor(roundedScore),
    isDark ? '#374151' : '#e5e7eb'
  ]

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
            strokeWidth={0}
          >
            {data.map((entry, index) => (
              <Cell key={`cell-${index}`} fill={COLORS[index]} />
            ))}
          </Pie>
        </PieChart>
      </ResponsiveContainer>
      <div className="absolute inset-0 flex flex-col items-center justify-center">
        <div className="text-3xl font-bold text-gray-900 dark:text-white drop-shadow-sm">
          {Math.round(score)}
        </div>
        <div className="text-sm text-gray-500 dark:text-gray-400">Overall</div>
      </div>
    </div>
  )
}
