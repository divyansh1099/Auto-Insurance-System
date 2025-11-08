import { useQuery } from 'react-query'
import { driverAPI, riskAPI } from '../services/api'

export default function DrivingBehavior() {
  const driverId = 'DRV-0001'

  const { data: stats } = useQuery(
    ['stats', driverId],
    () => driverAPI.getStatistics(driverId)
  )

  const { data: riskBreakdown } = useQuery(
    ['riskBreakdown', driverId],
    () => riskAPI.getRiskBreakdown(driverId),
    { retry: false }
  )

  return (
    <div className="space-y-8">
      <h1 className="text-3xl font-bold text-gray-900">Driving Behavior</h1>

      <div className="bg-white rounded-lg shadow p-6">
        <h2 className="text-xl font-semibold mb-4">Risk Trend</h2>
        {riskBreakdown?.data ? (
          <div className="space-y-4">
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div className="p-4 bg-gray-50 rounded-lg">
                <div className="text-sm text-gray-600">Current Risk Score</div>
                <div className="text-2xl font-bold text-gray-900">
                  {riskBreakdown.data.risk_score?.toFixed(1) || 'N/A'}
                </div>
              </div>
              <div className="p-4 bg-gray-50 rounded-lg">
                <div className="text-sm text-gray-600">Risk Category</div>
                <div className="text-xl font-semibold text-gray-900 capitalize">
                  {riskBreakdown.data.risk_category || 'N/A'}
                </div>
              </div>
              <div className="p-4 bg-gray-50 rounded-lg">
                <div className="text-sm text-gray-600">Confidence</div>
                <div className="text-2xl font-bold text-gray-900">
                  {riskBreakdown.data.confidence ? (riskBreakdown.data.confidence * 100).toFixed(1) + '%' : 'N/A'}
                </div>
              </div>
              <div className="p-4 bg-gray-50 rounded-lg">
                <div className="text-sm text-gray-600">Trend</div>
                <div className="text-xl font-semibold text-gray-900 capitalize">
                  {riskBreakdown.data.trend || 'Stable'}
                </div>
              </div>
            </div>
            <p className="text-sm text-gray-500 mt-4">
              Note: Interactive charts showing risk score over time coming soon
            </p>
          </div>
        ) : (
          <p className="text-gray-600">Loading risk data...</p>
        )}
      </div>

      <div className="bg-white rounded-lg shadow p-6">
        <h2 className="text-xl font-semibold mb-4">Driving Metrics</h2>
        {stats?.data ? (
          <div className="space-y-6">
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div className="p-4 bg-blue-50 rounded-lg">
                <div className="text-sm text-gray-600">Harsh Braking</div>
                <div className="text-2xl font-bold text-blue-900">
                  {stats.data.harsh_braking_rate?.toFixed(2) || '0'} /100mi
                </div>
              </div>
              <div className="p-4 bg-orange-50 rounded-lg">
                <div className="text-sm text-gray-600">Rapid Acceleration</div>
                <div className="text-2xl font-bold text-orange-900">
                  {stats.data.rapid_accel_rate?.toFixed(2) || '0'} /100mi
                </div>
              </div>
              <div className="p-4 bg-red-50 rounded-lg">
                <div className="text-sm text-gray-600">Speeding</div>
                <div className="text-2xl font-bold text-red-900">
                  {stats.data.speeding_rate?.toFixed(2) || '0'} /100mi
                </div>
              </div>
              <div className="p-4 bg-purple-50 rounded-lg">
                <div className="text-sm text-gray-600">Max Speed</div>
                <div className="text-2xl font-bold text-purple-900">
                  {stats.data.max_speed?.toFixed(0) || '0'} mph
                </div>
              </div>
            </div>
            
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mt-6">
              <div className="p-4 bg-gray-50 rounded-lg">
                <div className="text-sm text-gray-600">Night Driving</div>
                <div className="text-xl font-semibold text-gray-900">
                  {stats.data.night_driving_pct?.toFixed(1) || '0'}%
                </div>
              </div>
              <div className="p-4 bg-gray-50 rounded-lg">
                <div className="text-sm text-gray-600">Rush Hour</div>
                <div className="text-xl font-semibold text-gray-900">
                  {stats.data.rush_hour_pct?.toFixed(1) || '0'}%
                </div>
              </div>
              <div className="p-4 bg-gray-50 rounded-lg">
                <div className="text-sm text-gray-600">Weekend Driving</div>
                <div className="text-xl font-semibold text-gray-900">
                  {stats.data.weekend_driving_pct?.toFixed(1) || '0'}%
                </div>
              </div>
            </div>
          </div>
        ) : (
          <p className="text-gray-600">Loading driving metrics...</p>
        )}
      </div>
    </div>
  )
}
