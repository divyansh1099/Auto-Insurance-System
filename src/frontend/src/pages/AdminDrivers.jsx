import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from 'react-query'
import { adminAPI } from '../services/api'

export default function AdminDrivers() {
  const [page, setPage] = useState(1)
  const [search, setSearch] = useState('')
  const [showCreateModal, setShowCreateModal] = useState(false)
  const [editingDriver, setEditingDriver] = useState(null)
  const limit = 20

  const queryClient = useQueryClient()

  const { data, isLoading } = useQuery(
    ['adminDrivers', page, search],
    () => adminAPI.listDrivers((page - 1) * limit, limit, search)
  )

  const deleteMutation = useMutation(
    (driverId) => adminAPI.deleteDriver(driverId),
    {
      onSuccess: () => {
        queryClient.invalidateQueries('adminDrivers')
      }
    }
  )

  const drivers = data?.data || []
  const total = drivers.length

  const handleDelete = async (driverId) => {
    if (window.confirm('Are you sure you want to delete this driver?')) {
      try {
        await deleteMutation.mutateAsync(driverId)
      } catch (error) {
        alert('Error deleting driver: ' + error.response?.data?.detail)
      }
    }
  }

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-3xl font-bold text-gray-900">Manage Drivers</h1>
        <button
          onClick={() => setShowCreateModal(true)}
          className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
        >
          + Add Driver
        </button>
      </div>

      {/* Search */}
      <div className="bg-white rounded-lg shadow p-4">
        <input
          type="text"
          placeholder="Search drivers..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="w-full px-4 py-2 border rounded-lg"
        />
      </div>

      {/* Table */}
      <div className="bg-white rounded-lg shadow overflow-hidden">
        {isLoading ? (
          <div className="p-8 text-center">Loading...</div>
        ) : drivers.length === 0 ? (
          <div className="p-8 text-center text-gray-500">No drivers found</div>
        ) : (
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Driver ID</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Name</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Email</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Phone</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Created</th>
                <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">Actions</th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {drivers.map((driver) => (
                <tr key={driver.driver_id} className="hover:bg-gray-50">
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                    {driver.driver_id}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    {driver.first_name} {driver.last_name}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {driver.email}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {driver.phone || '-'}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {new Date(driver.created_at).toLocaleDateString()}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                    <button
                      onClick={() => setEditingDriver(driver)}
                      className="text-blue-600 hover:text-blue-900 mr-4"
                    >
                      Edit
                    </button>
                    <button
                      onClick={() => handleDelete(driver.driver_id)}
                      className="text-red-600 hover:text-red-900"
                    >
                      Delete
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      {/* Pagination */}
      {total > 0 && (
        <div className="flex justify-between items-center">
          <div className="text-sm text-gray-700">
            Showing {(page - 1) * limit + 1} to {Math.min(page * limit, total)} of {total}
          </div>
          <div className="flex gap-2">
            <button
              onClick={() => setPage(p => Math.max(1, p - 1))}
              disabled={page === 1}
              className="px-4 py-2 border rounded-lg disabled:opacity-50"
            >
              Previous
            </button>
            <button
              onClick={() => setPage(p => p + 1)}
              disabled={drivers.length < limit}
              className="px-4 py-2 border rounded-lg disabled:opacity-50"
            >
              Next
            </button>
          </div>
        </div>
      )}

      {/* Create/Edit Modal */}
      {(showCreateModal || editingDriver) && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 max-w-2xl w-full max-h-[90vh] overflow-y-auto">
            <h2 className="text-2xl font-bold mb-4">
              {editingDriver ? 'Edit Driver' : 'Create Driver'}
            </h2>
            <p className="text-gray-600 mb-4">
              Driver creation form coming soon. Use API directly for now.
            </p>
            <div className="flex justify-end gap-2">
              <button
                onClick={() => {
                  setShowCreateModal(false)
                  setEditingDriver(null)
                }}
                className="px-4 py-2 border rounded-lg"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

