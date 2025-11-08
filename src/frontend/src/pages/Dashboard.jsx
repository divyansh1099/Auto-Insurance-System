import { useQuery } from 'react-query'
import { riskAPI, pricingAPI, driverAPI } from '../services/api'
import RiskScoreGauge from '../components/RiskScoreGauge'
import SavingsCard from '../components/SavingsCard'
import QuickStats from '../components/QuickStats'

export default function Dashboard() {
  // For demo, using a hardcoded driver ID
  // In production, this would come from auth context
  const driverId = 'DRV-0001'

  const { data: riskScore } = useQuery(
    ['riskScore', driverId],
    () => riskAPI.getRiskScore(driverId)
  )

  const { data: premium } = useQuery(
    ['premium', driverId],
    () => pricingAPI.getCurrentPremium(driverId)
  )

  const { data: stats } = useQuery(
    ['stats', driverId],
    () => driverAPI.getStatistics(driverId)
  )

  const { data: comparison } = useQuery(
    ['comparison', driverId],
    () => pricingAPI.getComparison(driverId)
  )

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-3xl font-bold text-gray-900">Dashboard</h1>
        <p className="mt-2 text-gray-600">
          Welcome back! Here's your driving summary.
        </p>
      </div>

      {/* Risk Score Section */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-xl font-semibold mb-4">Your Risk Score</h2>
          <RiskScoreGauge score={riskScore?.data?.risk_score || 45} />
        </div>

        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-xl font-semibold mb-4">Savings vs Traditional</h2>
          <SavingsCard
            telematicsPremium={premium?.data?.monthly_premium || 95}
            traditionalPremium={comparison?.data?.traditional_monthly || 120}
          />
        </div>
      </div>

      {/* Quick Stats */}
      <div className="bg-white rounded-lg shadow p-6">
        <h2 className="text-xl font-semibold mb-4">Last 30 Days</h2>
        <QuickStats stats={stats?.data} />
      </div>

      {/* Recent Activity */}
      <div className="bg-white rounded-lg shadow p-6">
        <h2 className="text-xl font-semibold mb-4">Recent Trips</h2>
        <p className="text-gray-600">
          View your complete trip history in the Trips section.
        </p>
      </div>
    </div>
  )
}
