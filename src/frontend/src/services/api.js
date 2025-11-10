import axios from "axios";

const API_BASE_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

const api = axios.create({
  baseURL: `${API_BASE_URL}/api/v1`,
  headers: {
    "Content-Type": "application/json",
  },
});

// Request interceptor to add auth token
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem("access_token");
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor for error handling
api.interceptors.response.use(
  (response) => response,
  (error) => {
    // Handle 401 Unauthorized - redirect to login
    if (error.response?.status === 401) {
      localStorage.removeItem("access_token");
      // Only redirect if not already on login page
      if (window.location.pathname !== "/login") {
        window.location.href = "/login";
      }
    }

    // Handle 403 Forbidden
    if (error.response?.status === 403) {
      console.error("Forbidden:", error.response.data);
    }

    // Handle 404 Not Found
    if (error.response?.status === 404) {
      console.error("Not Found:", error.response.data);
    }

    // Handle 422 Validation Error
    if (error.response?.status === 422) {
      console.error("Validation Error:", error.response.data);
    }

    // Handle 500+ Server Errors
    if (error.response?.status >= 500) {
      console.error("Server Error:", error.response.data);
    }

    // Handle network errors
    if (!error.response) {
      console.error("Network Error:", error.message);
      error.response = {
        data: {
          detail: "Network error. Please check your connection and try again.",
          error_code: "NETWORK_ERROR",
        },
      };
    }

    return Promise.reject(error);
  }
);

// Auth API
export const authAPI = {
  login: (credentials) => api.post("/auth/login", credentials),
  register: (userData) => api.post("/auth/register", userData),
  logout: () => api.post("/auth/logout"),
  getCurrentUser: () => api.get("/auth/me"),
  requestQuote: (quoteData) => api.post("/auth/quote-request", quoteData),
};

// Driver API
export const driverAPI = {
  getDriver: (driverId) => api.get(`/drivers/${driverId}`),
  updateDriver: (driverId, data) => api.patch(`/drivers/${driverId}`, data),
  getTrips: (driverId, page = 1, pageSize = 20, riskLevel = null, search = null) => {
    const params = new URLSearchParams({ page: page.toString(), page_size: pageSize.toString() })
    if (riskLevel) params.append('risk_level', riskLevel)
    if (search) params.append('search', search)
    return api.get(`/drivers/${driverId}/trips?${params.toString()}`)
  },
  getTripSummary: (driverId) => api.get(`/drivers/${driverId}/trips/summary`),
  getStatistics: (driverId, periodDays = 30) =>
    api.get(`/drivers/${driverId}/statistics?period_days=${periodDays}`),
};

// Risk Scoring API
export const riskAPI = {
  getRiskScore: (driverId) => api.get(`/risk/${driverId}/score`),
  getRiskBreakdown: (driverId) => api.get(`/risk/${driverId}/breakdown`),
  getRiskHistory: (driverId, days = 90) =>
    api.get(`/risk/${driverId}/history?days=${days}`),
  getRecommendations: (driverId) =>
    api.get(`/risk/${driverId}/recommendations`),
  // New Risk Profile endpoints
  getRiskProfileSummary: (driverId) => api.get(`/risk/${driverId}/risk-profile-summary`),
  getRiskScoreTrend: (driverId, period = '30d', interval = 'daily') =>
    api.get(`/risk/${driverId}/risk-score-trend?period=${period}&interval=${interval}`),
  getRiskFactorBreakdown: (driverId) => api.get(`/risk/${driverId}/risk-factor-breakdown`),
  recalculateRisk: (driverId) => api.post(`/risk/${driverId}/recalculate-risk`),
};

// Pricing API
export const pricingAPI = {
  getCurrentPremium: (driverId) => api.get(`/pricing/${driverId}/current`),
  getPremiumBreakdown: (driverId) => api.get(`/pricing/${driverId}/breakdown`),
  simulatePremium: (driverId, assumptions) =>
    api.post(`/pricing/${driverId}/simulate`, assumptions),
  getComparison: (driverId) => api.get(`/pricing/${driverId}/comparison`),
  getPremiumHistory: (driverId, months = 12) =>
    api.get(`/pricing/${driverId}/history?months=${months}`),
  // New Policy endpoints
  getPolicyDetails: (driverId) => api.get(`/pricing/${driverId}/policy-details`),
  recalculatePremium: (driverId) => api.post(`/pricing/${driverId}/recalculate-premium`),
};

// Rewards API
export const rewardsAPI = {
  getRewardsSummary: (driverId) => api.get(`/rewards/${driverId}/summary`),
  getMilestones: (driverId) => api.get(`/rewards/${driverId}/milestones`),
  getAchievements: (driverId) => api.get(`/rewards/${driverId}/achievements`),
  getPointsRules: () => api.get(`/rewards/rules`),
  awardPoints: (driverId, data) => api.post(`/rewards/${driverId}/award-points`, data),
};

// Admin API
export const adminAPI = {
  // Dashboard
  getDashboardStats: () => api.get("/admin/dashboard/stats"),
  getDashboardSummary: () => api.get("/admin/dashboard/summary"),
  getTripActivity: (days = 7) => api.get(`/admin/dashboard/trip-activity?days=${days}`),
  getRiskDistribution: () => api.get("/admin/dashboard/risk-distribution"),
  getSafetyEventsBreakdown: () => api.get("/admin/dashboard/safety-events-breakdown"),
  getPolicyTypeDistribution: () => api.get("/admin/dashboard/policy-type-distribution"),

  // Policies
  getPoliciesSummary: () => api.get("/admin/policies/summary"),
  listPolicies: (skip = 0, limit = 100, search = "", policyType = null) => {
    const params = new URLSearchParams({ skip: skip.toString(), limit: limit.toString() })
    if (search) params.append('search', search)
    if (policyType) params.append('policy_type', policyType)
    return api.get(`/admin/policies?${params.toString()}`)
  },
  getPolicy: (policyId) => api.get(`/admin/policies/${policyId}`),
  createPolicy: (data) => api.post("/admin/policies", data),
  updatePolicy: (policyId, data) => api.patch(`/admin/policies/${policyId}`, data),
  deletePolicy: (policyId) => api.delete(`/admin/policies/${policyId}`),

  // Drivers
  listDrivers: (skip = 0, limit = 100, search = "") =>
    api.get(`/admin/drivers?skip=${skip}&limit=${limit}&search=${search}`),
  getDriver: (driverId) => api.get(`/admin/drivers/${driverId}`),
  getDriverDetails: (driverId) => api.get(`/admin/drivers/${driverId}/details`),
  createDriver: (data) => api.post("/admin/drivers", data),
  updateDriver: (driverId, data) =>
    api.patch(`/admin/drivers/${driverId}`, data),
  deleteDriver: (driverId) => api.delete(`/admin/drivers/${driverId}`),

  // Users
  listUsers: (skip = 0, limit = 100, search = "") =>
    api.get(`/admin/users?skip=${skip}&limit=${limit}&search=${search}`),
  getUser: (userId) => api.get(`/admin/users/${userId}`),
  createUser: (data) => api.post("/admin/users", data),
  updateUser: (userId, data) => api.patch(`/admin/users/${userId}`, data),
  deleteUser: (userId) => api.delete(`/admin/users/${userId}`),

  // Vehicles
  listVehicles: (skip = 0, limit = 100, driverId = "") =>
    api.get(
      `/admin/vehicles?skip=${skip}&limit=${limit}&driver_id=${driverId}`
    ),
  getVehicle: (vehicleId) => api.get(`/admin/vehicles/${vehicleId}`),
  deleteVehicle: (vehicleId) => api.delete(`/admin/vehicles/${vehicleId}`),

  // Devices
  listDevices: (skip = 0, limit = 100, driverId = "") =>
    api.get(`/admin/devices?skip=${skip}&limit=${limit}&driver_id=${driverId}`),
  getDevice: (deviceId) => api.get(`/admin/devices/${deviceId}`),
  deleteDevice: (deviceId) => api.delete(`/admin/devices/${deviceId}`),

  // Trips
  listTrips: (skip = 0, limit = 100, driverId = "") =>
    api.get(`/admin/trips?skip=${skip}&limit=${limit}&driver_id=${driverId}`),
  getTrip: (tripId) => api.get(`/admin/trips/${tripId}`),
  deleteTrip: (tripId) => api.delete(`/admin/trips/${tripId}`),

  // Events
  listEvents: (skip = 0, limit = 100, driverId = "", eventType = "") =>
    api.get(
      `/admin/events?skip=${skip}&limit=${limit}&driver_id=${driverId}&event_type=${eventType}`
    ),
  getEventStats: () => api.get("/admin/events/stats"),
};

// Simulator API
export const simulatorAPI = {
  calculateScore: (params) => api.post("/simulator/calculate-score", params),
};

// Dashboard API
export const dashboardAPI = {
  getSummary: (driverId) => api.get(`/drivers/${driverId}/summary`),
  getRecentTrips: (driverId, limit = 5) =>
    api.get(`/drivers/${driverId}/trips?page=1&page_size=${limit}`),
  getSafetyAlerts: (driverId) => api.get(`/drivers/${driverId}/alerts`),
  getRiskFactors: (driverId) => api.get(`/drivers/${driverId}/risk-factors`),
  getPremiumDetails: (driverId) => api.get(`/pricing/${driverId}/current`),
};

// Real-Time API
export const realtimeAPI = {
  getAnalysis: (driverId) => api.get(`/realtime/analysis/${driverId}`),
  processEvent: (driverId, event) => api.post(`/realtime/process-event/${driverId}`, event),
  startDrive: (driverId, params) => api.post(`/realtime/start-drive/${driverId}`, params),
  stopDrive: (driverId) => api.post(`/realtime/stop-drive/${driverId}`),
  getDriveStatus: (driverId) => api.get(`/realtime/drive-status/${driverId}`),
};

export default api;
