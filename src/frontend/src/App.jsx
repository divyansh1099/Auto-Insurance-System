import { Routes, Route } from 'react-router-dom'
import Layout from './components/Layout'
import Dashboard from './pages/Dashboard'
import DrivingBehavior from './pages/DrivingBehavior'
import Trips from './pages/Trips'
import Pricing from './pages/Pricing'
import Login from './pages/Login'
import AdminDashboard from './pages/AdminDashboard'
import AdminDrivers from './pages/AdminDrivers'
import AdminUsers from './pages/AdminUsers'

function App() {
  return (
    <Routes>
      <Route path="/login" element={<Login />} />
      <Route path="/" element={<Layout />}>
        <Route index element={<Dashboard />} />
        <Route path="driving" element={<DrivingBehavior />} />
        <Route path="trips" element={<Trips />} />
        <Route path="pricing" element={<Pricing />} />
        <Route path="admin" element={<AdminDashboard />} />
        <Route path="admin/drivers" element={<AdminDrivers />} />
        <Route path="admin/users" element={<AdminUsers />} />
      </Route>
    </Routes>
  )
}

export default App
