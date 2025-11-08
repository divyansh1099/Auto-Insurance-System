import { useQuery } from 'react-query'
import { driverAPI } from '../services/api'

export default function Trips() {
  const driverId = 'DRV-0001'

  const { data: tripsData, isLoading } = useQuery(
    ['trips', driverId],
    () => driverAPI.getTrips(driverId, 1, 20)
  )

  const trips = tripsData?.data?.trips || []
  const totalTrips = tripsData?.data?.total || 0

  return (
    <div className="space-y-8">
      <h1 className="text-3xl font-bold text-gray-900">Trip History</h1>

      <div className="bg-white rounded-lg shadow p-6">
        <h2 className="text-xl font-semibold mb-4">Recent Trips</h2>
        
        {isLoading ? (
          <p className="text-gray-600">Loading trips...</p>
        ) : totalTrips === 0 ? (
          <div className="text-center py-12">
            <p className="text-gray-600 mb-4">No trips found yet.</p>
            <p className="text-sm text-gray-500">
              Trips are created when you complete a driving session. 
              Your telematics events are being processed and trips will appear here once created.
            </p>
            <div className="mt-6 p-4 bg-blue-50 rounded-lg">
              <p className="text-sm text-blue-800">
                <strong>Note:</strong> Currently, events are being stored but trips haven't been created yet. 
                This feature will be enhanced to automatically group events into trips.
              </p>
            </div>
          </div>
        ) : (
          <div className="space-y-4">
            <div className="text-sm text-gray-600 mb-4">
              Showing {trips.length} of {totalTrips} trips
            </div>
            {trips.map((trip) => (
              <div key={trip.trip_id} className="border rounded-lg p-4 hover:bg-gray-50">
                <div className="flex justify-between items-start">
                  <div>
                    <div className="font-semibold text-gray-900">
                      Trip {trip.trip_id}
                    </div>
                    <div className="text-sm text-gray-600 mt-1">
                      {new Date(trip.start_time).toLocaleString()}
                    </div>
                    {trip.distance_miles && (
                      <div className="text-sm text-gray-600 mt-1">
                        Distance: {trip.distance_miles.toFixed(2)} miles
                      </div>
                    )}
                  </div>
                  {trip.duration_minutes && (
                    <div className="text-right">
                      <div className="text-sm font-semibold text-gray-900">
                        {Math.floor(trip.duration_minutes)} min
                      </div>
                    </div>
                  )}
                </div>
                <p className="text-xs text-gray-500 mt-2">
                  Map view and detailed event breakdown coming soon
                </p>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
