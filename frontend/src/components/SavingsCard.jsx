export default function SavingsCard({ telematicsPremium = 95, traditionalPremium = 120 }) {
  const savings = traditionalPremium - telematicsPremium
  const savingsPercent = (savings / traditionalPremium) * 100

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-2 gap-4">
        <div className="text-center p-4 bg-blue-50 rounded-lg">
          <div className="text-sm text-gray-600">Your Premium</div>
          <div className="text-2xl font-bold text-blue-600">${telematicsPremium}/mo</div>
        </div>
        <div className="text-center p-4 bg-gray-50 rounded-lg">
          <div className="text-sm text-gray-600">Traditional Premium</div>
          <div className="text-2xl font-bold text-gray-600">${traditionalPremium}/mo</div>
        </div>
      </div>

      <div className="text-center p-6 bg-green-50 rounded-lg border-2 border-green-200">
        <div className="text-sm text-gray-600 mb-1">You're Saving</div>
        <div className="text-3xl font-bold text-green-600">
          ${savings.toFixed(0)}/mo
        </div>
        <div className="text-sm text-green-600 mt-1">
          ({savingsPercent.toFixed(0)}% discount)
        </div>
      </div>

      <div className="text-sm text-gray-500 text-center">
        Annual savings: ${(savings * 12).toFixed(0)}
      </div>
    </div>
  )
}
