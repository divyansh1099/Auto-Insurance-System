import { useState } from 'react'
import { adminAPI } from '../../services/api'

export default function UserForm({ user, onSuccess, onCancel }) {
  const [formData, setFormData] = useState({
    username: user?.username || '',
    email: user?.email || '',
    password: '',
    driver_id: user?.driver_id || '',
    is_active: user?.is_active ?? true,
    is_admin: user?.is_admin ?? false,
  })
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const handleSubmit = async (e) => {
    e.preventDefault()
    setLoading(true)
    setError('')

    try {
      if (user) {
        // Update - only send changed fields
        const updateData = {}
        if (formData.username !== user.username) updateData.username = formData.username
        if (formData.email !== user.email) updateData.email = formData.email
        if (formData.password) updateData.password = formData.password
        if (formData.driver_id !== user.driver_id) updateData.driver_id = formData.driver_id
        if (formData.is_active !== user.is_active) updateData.is_active = formData.is_active
        if (formData.is_admin !== user.is_admin) updateData.is_admin = formData.is_admin
        
        await adminAPI.updateUser(user.user_id, updateData)
      } else {
        // Create
        await adminAPI.createUser(formData)
      }
      onSuccess()
    } catch (err) {
      setError(err.response?.data?.detail || 'Error saving user')
    } finally {
      setLoading(false)
    }
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      {error && (
        <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded">
          {error}
        </div>
      )}

      <div className="grid grid-cols-2 gap-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Username *
          </label>
          <input
            type="text"
            required
            value={formData.username}
            onChange={(e) => setFormData({ ...formData, username: e.target.value })}
            className="w-full px-3 py-2 border rounded-lg"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Email *
          </label>
          <input
            type="email"
            required
            value={formData.email}
            onChange={(e) => setFormData({ ...formData, email: e.target.value })}
            className="w-full px-3 py-2 border rounded-lg"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Password {user ? '(leave blank to keep current)' : '*'}
          </label>
          <input
            type="password"
            required={!user}
            value={formData.password}
            onChange={(e) => setFormData({ ...formData, password: e.target.value })}
            className="w-full px-3 py-2 border rounded-lg"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Driver ID
          </label>
          <input
            type="text"
            value={formData.driver_id}
            onChange={(e) => setFormData({ ...formData, driver_id: e.target.value })}
            className="w-full px-3 py-2 border rounded-lg"
            placeholder="Optional"
          />
        </div>

        <div className="col-span-2">
          <div className="flex items-center gap-6">
            <label className="flex items-center gap-2">
              <input
                type="checkbox"
                checked={formData.is_active}
                onChange={(e) => setFormData({ ...formData, is_active: e.target.checked })}
                className="rounded"
              />
              <span className="text-sm font-medium text-gray-700">Active</span>
            </label>

            <label className="flex items-center gap-2">
              <input
                type="checkbox"
                checked={formData.is_admin}
                onChange={(e) => setFormData({ ...formData, is_admin: e.target.checked })}
                className="rounded"
              />
              <span className="text-sm font-medium text-gray-700">Admin</span>
            </label>
          </div>
        </div>
      </div>

      <div className="flex justify-end gap-2 pt-4">
        <button
          type="button"
          onClick={onCancel}
          className="px-4 py-2 border rounded-lg hover:bg-gray-50"
          disabled={loading}
        >
          Cancel
        </button>
        <button
          type="submit"
          className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50"
          disabled={loading}
        >
          {loading ? 'Saving...' : user ? 'Update' : 'Create'}
        </button>
      </div>
    </form>
  )
}

