import { useState } from 'react'
import { adminAPI } from '../../services/api'

export default function DriverForm({ driver, onSuccess, onCancel }) {
  const [formData, setFormData] = useState({
    driver_id: driver?.driver_id || '',
    first_name: driver?.first_name || '',
    last_name: driver?.last_name || '',
    email: driver?.email || '',
    phone: driver?.phone || '',
    date_of_birth: driver?.date_of_birth || '',
    license_number: driver?.license_number || '',
    license_state: driver?.license_state || '',
    years_licensed: driver?.years_licensed || 0,
    gender: driver?.gender || '',
    marital_status: driver?.marital_status || '',
    address: driver?.address || '',
    city: driver?.city || '',
    state: driver?.state || '',
    zip_code: driver?.zip_code || '',
  })
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const handleSubmit = async (e) => {
    e.preventDefault()
    setLoading(true)
    setError('')

    try {
      if (driver) {
        // Update
        await adminAPI.updateDriver(driver.driver_id, formData)
      } else {
        // Create
        await adminAPI.createDriver(formData)
      }
      onSuccess()
    } catch (err) {
      setError(err.response?.data?.detail || 'Error saving driver')
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
            Driver ID *
          </label>
          <input
            type="text"
            required
            value={formData.driver_id}
            onChange={(e) => setFormData({ ...formData, driver_id: e.target.value })}
            className="w-full px-3 py-2 border rounded-lg"
            disabled={!!driver}
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
            First Name *
          </label>
          <input
            type="text"
            required
            value={formData.first_name}
            onChange={(e) => setFormData({ ...formData, first_name: e.target.value })}
            className="w-full px-3 py-2 border rounded-lg"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Last Name *
          </label>
          <input
            type="text"
            required
            value={formData.last_name}
            onChange={(e) => setFormData({ ...formData, last_name: e.target.value })}
            className="w-full px-3 py-2 border rounded-lg"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Phone
          </label>
          <input
            type="tel"
            value={formData.phone}
            onChange={(e) => setFormData({ ...formData, phone: e.target.value })}
            className="w-full px-3 py-2 border rounded-lg"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Date of Birth *
          </label>
          <input
            type="date"
            required
            value={formData.date_of_birth}
            onChange={(e) => setFormData({ ...formData, date_of_birth: e.target.value })}
            className="w-full px-3 py-2 border rounded-lg"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            License Number *
          </label>
          <input
            type="text"
            required
            value={formData.license_number}
            onChange={(e) => setFormData({ ...formData, license_number: e.target.value })}
            className="w-full px-3 py-2 border rounded-lg"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            License State *
          </label>
          <input
            type="text"
            required
            maxLength={2}
            value={formData.license_state}
            onChange={(e) => setFormData({ ...formData, license_state: e.target.value.toUpperCase() })}
            className="w-full px-3 py-2 border rounded-lg"
            placeholder="CA"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Years Licensed *
          </label>
          <input
            type="number"
            required
            min="0"
            value={formData.years_licensed}
            onChange={(e) => setFormData({ ...formData, years_licensed: parseInt(e.target.value) || 0 })}
            className="w-full px-3 py-2 border rounded-lg"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Gender
          </label>
          <select
            value={formData.gender}
            onChange={(e) => setFormData({ ...formData, gender: e.target.value })}
            className="w-full px-3 py-2 border rounded-lg"
          >
            <option value="">Select...</option>
            <option value="M">Male</option>
            <option value="F">Female</option>
            <option value="Other">Other</option>
          </select>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Marital Status
          </label>
          <select
            value={formData.marital_status}
            onChange={(e) => setFormData({ ...formData, marital_status: e.target.value })}
            className="w-full px-3 py-2 border rounded-lg"
          >
            <option value="">Select...</option>
            <option value="Single">Single</option>
            <option value="Married">Married</option>
            <option value="Divorced">Divorced</option>
            <option value="Widowed">Widowed</option>
          </select>
        </div>

        <div className="col-span-2">
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Address
          </label>
          <input
            type="text"
            value={formData.address}
            onChange={(e) => setFormData({ ...formData, address: e.target.value })}
            className="w-full px-3 py-2 border rounded-lg"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            City
          </label>
          <input
            type="text"
            value={formData.city}
            onChange={(e) => setFormData({ ...formData, city: e.target.value })}
            className="w-full px-3 py-2 border rounded-lg"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            State
          </label>
          <input
            type="text"
            maxLength={2}
            value={formData.state}
            onChange={(e) => setFormData({ ...formData, state: e.target.value.toUpperCase() })}
            className="w-full px-3 py-2 border rounded-lg"
            placeholder="CA"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            ZIP Code
          </label>
          <input
            type="text"
            value={formData.zip_code}
            onChange={(e) => setFormData({ ...formData, zip_code: e.target.value })}
            className="w-full px-3 py-2 border rounded-lg"
          />
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
          {loading ? 'Saving...' : driver ? 'Update' : 'Create'}
        </button>
      </div>
    </form>
  )
}

