import axios from 'axios'

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

const api = axios.create({
  baseURL: `${API_BASE_URL}/api/v1`,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Request interceptor to add auth token
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('access_token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// Response interceptor for error handling
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('access_token')
      window.location.href = '/login'
    }
    return Promise.reject(error)
  }
)

// Auth API
export const authAPI = {
  login: (credentials) => api.post('/auth/login', credentials),
  register: (userData) => api.post('/auth/register', userData),
  logout: () => api.post('/auth/logout'),
  getCurrentUser: () => api.get('/auth/me'),
}

// Driver API
export const driverAPI = {
  getDriver: (driverId) => api.get(`/drivers/${driverId}`),
  updateDriver: (driverId, data) => api.patch(`/drivers/${driverId}`, data),
  getTrips: (driverId, page = 1, pageSize = 20) =>
    api.get(`/drivers/${driverId}/trips?page=${page}&page_size=${pageSize}`),
  getStatistics: (driverId, periodDays = 30) =>
    api.get(`/drivers/${driverId}/statistics?period_days=${periodDays}`),
}

// Risk Scoring API
export const riskAPI = {
  getRiskScore: (driverId) => api.get(`/risk/${driverId}/score`),
  getRiskBreakdown: (driverId) => api.get(`/risk/${driverId}/breakdown`),
  getRiskHistory: (driverId, days = 90) =>
    api.get(`/risk/${driverId}/history?days=${days}`),
  getRecommendations: (driverId) => api.get(`/risk/${driverId}/recommendations`),
}

// Pricing API
export const pricingAPI = {
  getCurrentPremium: (driverId) => api.get(`/pricing/${driverId}/current`),
  getPremiumBreakdown: (driverId) => api.get(`/pricing/${driverId}/breakdown`),
  simulatePremium: (driverId, assumptions) =>
    api.post(`/pricing/${driverId}/simulate`, assumptions),
  getComparison: (driverId) => api.get(`/pricing/${driverId}/comparison`),
  getPremiumHistory: (driverId, months = 12) =>
    api.get(`/pricing/${driverId}/history?months=${months}`),
}

// Admin API
export const adminAPI = {
  // Dashboard
  getDashboardStats: () => api.get('/admin/dashboard/stats'),
  
  // Drivers
  listDrivers: (skip = 0, limit = 100, search = '') =>
    api.get(`/admin/drivers?skip=${skip}&limit=${limit}&search=${search}`),
  getDriver: (driverId) => api.get(`/admin/drivers/${driverId}`),
  createDriver: (data) => api.post('/admin/drivers', data),
  updateDriver: (driverId, data) => api.patch(`/admin/drivers/${driverId}`, data),
  deleteDriver: (driverId) => api.delete(`/admin/drivers/${driverId}`),
  
  // Users
  listUsers: (skip = 0, limit = 100, search = '') =>
    api.get(`/admin/users?skip=${skip}&limit=${limit}&search=${search}`),
  getUser: (userId) => api.get(`/admin/users/${userId}`),
  createUser: (data) => api.post('/admin/users', data),
  updateUser: (userId, data) => api.patch(`/admin/users/${userId}`, data),
  deleteUser: (userId) => api.delete(`/admin/users/${userId}`),
  
  // Vehicles
  listVehicles: (skip = 0, limit = 100, driverId = '') =>
    api.get(`/admin/vehicles?skip=${skip}&limit=${limit}&driver_id=${driverId}`),
  getVehicle: (vehicleId) => api.get(`/admin/vehicles/${vehicleId}`),
  deleteVehicle: (vehicleId) => api.delete(`/admin/vehicles/${vehicleId}`),
  
  // Devices
  listDevices: (skip = 0, limit = 100, driverId = '') =>
    api.get(`/admin/devices?skip=${skip}&limit=${limit}&driver_id=${driverId}`),
  getDevice: (deviceId) => api.get(`/admin/devices/${deviceId}`),
  deleteDevice: (deviceId) => api.delete(`/admin/devices/${deviceId}`),
  
  // Trips
  listTrips: (skip = 0, limit = 100, driverId = '') =>
    api.get(`/admin/trips?skip=${skip}&limit=${limit}&driver_id=${driverId}`),
  getTrip: (tripId) => api.get(`/admin/trips/${tripId}`),
  deleteTrip: (tripId) => api.delete(`/admin/trips/${tripId}`),
  
  // Events
  listEvents: (skip = 0, limit = 100, driverId = '', eventType = '') =>
    api.get(`/admin/events?skip=${skip}&limit=${limit}&driver_id=${driverId}&event_type=${eventType}`),
  getEventStats: () => api.get('/admin/events/stats'),
}

export default api
