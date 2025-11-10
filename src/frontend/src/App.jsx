import { Routes, Route, Navigate } from 'react-router-dom'
import Layout from './components/Layout'
import Dashboard from './pages/Dashboard'
import DrivingBehavior from './pages/DrivingBehavior'
import Trips from './pages/Trips'
import Pricing from './pages/Pricing'
import DriveSimulator from './pages/DriveSimulator'
import Rewards from './pages/Rewards'
import InsuranceAdvisor from './pages/InsuranceAdvisor'
import LiveDriving from './pages/LiveDriving'
import Login from './pages/Login'
import Homepage from './pages/Homepage'
import AdminDashboard from './pages/AdminDashboard'
import AdminDrivers from './pages/AdminDrivers'
import AdminPolicies from './pages/AdminPolicies'
import Profile from './pages/Profile'
import ProtectedRoute from './components/ProtectedRoute'

function App() {
  return (
    <Routes>
      <Route path="/home" element={<Homepage />} />
      <Route path="/login" element={<Login />} />
      <Route path="/" element={<ProtectedRoute />}>
        <Route element={<Layout />}>
          <Route index element={<Dashboard />} />
          <Route path="driving" element={<DrivingBehavior />} />
          <Route path="trips" element={<Trips />} />
          <Route path="pricing" element={<Pricing />} />
          <Route path="simulator" element={<DriveSimulator />} />
          <Route path="rewards" element={<Rewards />} />
          <Route path="live" element={<LiveDriving />} />
          <Route path="advisor" element={<InsuranceAdvisor />} />
          <Route path="profile" element={<Profile />} />
          <Route path="admin" element={<AdminDashboard />} />
          <Route path="admin/drivers" element={<AdminDrivers />} />
          <Route path="admin/policies" element={<AdminPolicies />} />
        </Route>
      </Route>
      {/* Redirect any unknown routes to login */}
      <Route path="*" element={<Navigate to="/home" replace />} />
    </Routes>
  )
}

export default App
