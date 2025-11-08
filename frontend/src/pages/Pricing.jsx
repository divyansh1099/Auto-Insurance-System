import { useQuery } from 'react-query'
import { pricingAPI } from '../services/api'

export default function Pricing() {
  const driverId = 'DRV-0001'

  const { data: premium } = useQuery(
    ['premium', driverId],
    () => pricingAPI.getCurrentPremium(driverId)
  )

  const { data: breakdown } = useQuery(
    ['breakdown', driverId],
    () => pricingAPI.getPremiumBreakdown(driverId),
    { retry: false }
  )

  const { data: comparison } = useQuery(
    ['comparison', driverId],
    () => pricingAPI.getComparison(driverId)
  )

  return (
    <div className="space-y-8">
      <h1 className="text-3xl font-bold text-gray-900">Pricing & Savings</h1>

      <div className="bg-white rounded-lg shadow p-6">
        <h2 className="text-xl font-semibold mb-4">Premium Breakdown</h2>
        {breakdown?.data ? (
          <div className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="p-4 bg-blue-50 rounded-lg">
                <div className="text-sm text-gray-600">Monthly Premium</div>
                <div className="text-3xl font-bold text-blue-900">
                  ${breakdown.data.monthly_premium?.toFixed(2) || '0.00'}
                </div>
              </div>
              <div className="p-4 bg-green-50 rounded-lg">
                <div className="text-sm text-gray-600">Annual Savings</div>
                <div className="text-3xl font-bold text-green-900">
                  ${breakdown.data.savings_vs_traditional?.toFixed(2) || '0.00'}
                </div>
              </div>
            </div>
            
            {breakdown.data.components && breakdown.data.components.length > 0 && (
              <div className="mt-6">
                <h3 className="text-lg font-semibold mb-3">Premium Components</h3>
                <div className="space-y-2">
                  {breakdown.data.components.map((component, index) => (
                    <div key={index} className="flex justify-between items-center p-3 bg-gray-50 rounded">
                      <span className="text-gray-700">{component.name}</span>
                      <span className="font-semibold text-gray-900">
                        ${component.amount?.toFixed(2) || '0.00'}
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        ) : premium?.data ? (
          <div className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="p-4 bg-blue-50 rounded-lg">
                <div className="text-sm text-gray-600">Monthly Premium</div>
                <div className="text-3xl font-bold text-blue-900">
                  ${premium.data.monthly_premium?.toFixed(2) || '0.00'}
                </div>
              </div>
              <div className="p-4 bg-gray-50 rounded-lg">
                <div className="text-sm text-gray-600">Annual Premium</div>
                <div className="text-3xl font-bold text-gray-900">
                  ${premium.data.final_premium?.toFixed(2) || '0.00'}
                </div>
              </div>
            </div>
            {comparison?.data && (
              <div className="mt-4 p-4 bg-green-50 rounded-lg">
                <div className="text-sm text-green-800">
                  <strong>Savings:</strong> You're saving ${(comparison.data.traditional_monthly - premium.data.monthly_premium).toFixed(2)}/month 
                  vs traditional insurance (${comparison.data.traditional_monthly}/month)
                </div>
              </div>
            )}
            <p className="text-sm text-gray-500 mt-4">
              Detailed component breakdown coming soon
            </p>
          </div>
        ) : (
          <p className="text-gray-600">Loading premium information...</p>
        )}
      </div>

      <div className="bg-white rounded-lg shadow p-6">
        <h2 className="text-xl font-semibold mb-4">What-If Calculator</h2>
        <div className="space-y-4">
          <p className="text-gray-600">
            See how improving your driving could lower your premium
          </p>
          {comparison?.data && (
            <div className="p-4 bg-yellow-50 rounded-lg">
              <div className="text-sm text-yellow-800">
                <strong>Current Savings:</strong> You're already saving{' '}
                {((comparison.data.traditional_monthly - (premium?.data?.monthly_premium || 0)) / comparison.data.traditional_monthly * 100).toFixed(1)}% 
                {' '}compared to traditional insurance.
              </div>
              <div className="text-sm text-yellow-700 mt-2">
                By reducing harsh braking and speeding events, you could potentially save even more!
              </div>
            </div>
          )}
          <p className="text-sm text-gray-500">
            Interactive calculator with scenario modeling coming soon
          </p>
        </div>
      </div>
    </div>
  )
}
