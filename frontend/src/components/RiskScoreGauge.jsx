export default function RiskScoreGauge({ score = 50 }) {
  const getRiskCategory = (score) => {
    if (score <= 20) return { label: 'Excellent', color: 'text-green-600', bg: 'bg-green-100' }
    if (score <= 40) return { label: 'Good', color: 'text-blue-600', bg: 'bg-blue-100' }
    if (score <= 60) return { label: 'Average', color: 'text-yellow-600', bg: 'bg-yellow-100' }
    if (score <= 80) return { label: 'Below Average', color: 'text-orange-600', bg: 'bg-orange-100' }
    return { label: 'High Risk', color: 'text-red-600', bg: 'bg-red-100' }
  }

  const category = getRiskCategory(score)

  return (
    <div className="flex flex-col items-center justify-center space-y-4">
      <div className="relative w-48 h-48">
        <svg className="w-full h-full" viewBox="0 0 100 100">
          {/* Background arc */}
          <path
            d="M 10 50 A 40 40 0 0 1 90 50"
            fill="none"
            stroke="#e5e7eb"
            strokeWidth="10"
          />
          {/* Score arc */}
          <path
            d="M 10 50 A 40 40 0 0 1 90 50"
            fill="none"
            stroke={
              score <= 20
                ? '#10b981'
                : score <= 40
                ? '#3b82f6'
                : score <= 60
                ? '#eab308'
                : score <= 80
                ? '#f97316'
                : '#ef4444'
            }
            strokeWidth="10"
            strokeDasharray={`${(score / 100) * 126} 126`}
            strokeLinecap="round"
          />
        </svg>
        <div className="absolute inset-0 flex flex-col items-center justify-center">
          <div className="text-4xl font-bold text-gray-900">{score.toFixed(0)}</div>
          <div className="text-sm text-gray-500">Risk Score</div>
        </div>
      </div>
      <div className={`px-4 py-2 rounded-full ${category.bg}`}>
        <span className={`font-semibold ${category.color}`}>{category.label}</span>
      </div>
    </div>
  )
}
