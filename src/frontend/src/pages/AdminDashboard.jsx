import { useQuery } from 'react-query'
import { adminAPI } from '../services/api'

export default function AdminDashboard() {
  const { data: stats, isLoading } = useQuery(
    'adminDashboardStats',
    () => adminAPI.getDashboardStats()
  )

  if (isLoading) {
    return <div className="p-8">Loading dashboard...</div>
  }

  const totals = stats?.data?.totals || {}

  return (
    <div className="space-y-8">
      <h1 className="text-3xl font-bold text-gray-900">Admin Dashboard</h1>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-6 gap-4">
        <div className="bg-white rounded-lg shadow p-6">
          <div className="text-sm text-gray-600">Total Drivers</div>
          <div className="text-3xl font-bold text-blue-900">{totals.drivers || 0}</div>
        </div>
        <div className="bg-white rounded-lg shadow p-6">
          <div className="text-sm text-gray-600">Total Users</div>
          <div className="text-3xl font-bold text-green-900">{totals.users || 0}</div>
        </div>
        <div className="bg-white rounded-lg shadow p-6">
          <div className="text-sm text-gray-600">Vehicles</div>
          <div className="text-3xl font-bold text-purple-900">{totals.vehicles || 0}</div>
        </div>
        <div className="bg-white rounded-lg shadow p-6">
          <div className="text-sm text-gray-600">Devices</div>
          <div className="text-3xl font-bold text-orange-900">{totals.devices || 0}</div>
        </div>
        <div className="bg-white rounded-lg shadow p-6">
          <div className="text-sm text-gray-600">Trips</div>
          <div className="text-3xl font-bold text-indigo-900">{totals.trips || 0}</div>
        </div>
        <div className="bg-white rounded-lg shadow p-6">
          <div className="text-sm text-gray-600">Events</div>
          <div className="text-3xl font-bold text-red-900">{totals.events || 0}</div>
        </div>
      </div>

      {/* Recent Activity */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-xl font-semibold mb-4">Recent Drivers</h2>
          {stats?.data?.recent_drivers?.length > 0 ? (
            <div className="space-y-2">
              {stats.data.recent_drivers.map((driver) => (
                <div key={driver.driver_id} className="flex justify-between items-center p-2 hover:bg-gray-50 rounded">
                  <div>
                    <div className="font-medium">{driver.first_name} {driver.last_name}</div>
                    <div className="text-sm text-gray-600">{driver.driver_id}</div>
                  </div>
                  <div className="text-sm text-gray-500">
                    {new Date(driver.created_at).toLocaleDateString()}
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-gray-500">No recent drivers</p>
          )}
        </div>

        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-xl font-semibold mb-4">Recent Users</h2>
          {stats?.data?.recent_users?.length > 0 ? (
            <div className="space-y-2">
              {stats.data.recent_users.map((user) => (
                <div key={user.user_id} className="flex justify-between items-center p-2 hover:bg-gray-50 rounded">
                  <div>
                    <div className="font-medium">{user.username}</div>
                    <div className="text-sm text-gray-600">{user.email}</div>
                  </div>
                  <div className="text-sm">
                    {user.is_admin && (
                      <span className="px-2 py-1 bg-purple-100 text-purple-800 rounded text-xs">Admin</span>
                    )}
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-gray-500">No recent users</p>
          )}
        </div>
      </div>
    </div>
  )
}

