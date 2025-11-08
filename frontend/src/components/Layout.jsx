import { Outlet, Link, useNavigate } from 'react-router-dom'
import { useState, useEffect } from 'react'
import {
  HomeIcon,
  ChartBarIcon,
  MapIcon,
  CurrencyDollarIcon,
  ArrowRightOnRectangleIcon,
  ShieldCheckIcon,
  UserGroupIcon,
  UsersIcon
} from '@heroicons/react/24/outline'
import { authAPI } from '../services/api'

export default function Layout() {
  const navigate = useNavigate()
  const [isAdmin, setIsAdmin] = useState(false)

  useEffect(() => {
    // Check if user is admin
    authAPI.getCurrentUser()
      .then(res => setIsAdmin(res.data.is_admin))
      .catch(() => setIsAdmin(false))
  }, [])

  const handleLogout = () => {
    localStorage.removeItem('access_token')
    navigate('/login')
  }

  const navigation = [
    { name: 'Dashboard', href: '/', icon: HomeIcon },
    { name: 'Driving Behavior', href: '/driving', icon: ChartBarIcon },
    { name: 'Trips', href: '/trips', icon: MapIcon },
    { name: 'Pricing', href: '/pricing', icon: CurrencyDollarIcon },
  ]

  const adminNavigation = [
    { name: 'Admin Dashboard', href: '/admin', icon: ShieldCheckIcon },
    { name: 'Manage Drivers', href: '/admin/drivers', icon: UserGroupIcon },
    { name: 'Manage Users', href: '/admin/users', icon: UsersIcon },
  ]

  return (
    <div className="min-h-screen bg-gray-100">
      {/* Sidebar */}
      <div className="fixed inset-y-0 left-0 w-64 bg-blue-900">
        <div className="flex flex-col h-full">
          {/* Logo */}
          <div className="flex items-center px-6 py-8">
            <h1 className="text-2xl font-bold text-white">
              Telematics<br/>Insurance
            </h1>
          </div>

          {/* Navigation */}
          <nav className="flex-1 px-4 space-y-2 overflow-y-auto">
            {navigation.map((item) => (
              <Link
                key={item.name}
                to={item.href}
                className="flex items-center px-4 py-3 text-white rounded-lg hover:bg-blue-800 transition-colors"
              >
                <item.icon className="w-6 h-6 mr-3" />
                {item.name}
              </Link>
            ))}
            
            {/* Admin Navigation */}
            {isAdmin && (
              <>
                <div className="pt-4 pb-2">
                  <div className="px-4 text-xs font-semibold text-blue-300 uppercase tracking-wider">
                    Admin
                  </div>
                </div>
                {adminNavigation.map((item) => (
                  <Link
                    key={item.name}
                    to={item.href}
                    className="flex items-center px-4 py-3 text-white rounded-lg hover:bg-blue-800 transition-colors"
                  >
                    <item.icon className="w-6 h-6 mr-3" />
                    {item.name}
                  </Link>
                ))}
              </>
            )}
          </nav>

          {/* Logout */}
          <div className="px-4 py-4">
            <button
              onClick={handleLogout}
              className="flex items-center w-full px-4 py-3 text-white rounded-lg hover:bg-blue-800 transition-colors"
            >
              <ArrowRightOnRectangleIcon className="w-6 h-6 mr-3" />
              Logout
            </button>
          </div>
        </div>
      </div>

      {/* Main content */}
      <div className="ml-64">
        <div className="p-8">
          <Outlet />
        </div>
      </div>
    </div>
  )
}
