import { Outlet, Link, useNavigate, useLocation } from 'react-router-dom'
import { useState, useEffect, useRef } from 'react'
import {
  HomeIcon,
  ChartBarIcon,
  MapIcon,
  CurrencyDollarIcon,
  ArrowRightOnRectangleIcon,
  ShieldCheckIcon,
  UserGroupIcon,
  UsersIcon,
  PlayIcon,
  TrophyIcon,
  DocumentTextIcon,
  BuildingOfficeIcon,
  UserCircleIcon,
  BoltIcon,
  SunIcon,
  MoonIcon
} from '@heroicons/react/24/outline'
import { authAPI } from '../services/api'
import { useQuery, useQueryClient } from 'react-query'
import { useTheme } from '../contexts/ThemeContext'

export default function Layout() {
  const navigate = useNavigate()
  const location = useLocation()
  const queryClient = useQueryClient()
  const [isAdmin, setIsAdmin] = useState(false)
  const [showUserMenu, setShowUserMenu] = useState(false)
  const userMenuRef = useRef(null)
  const { theme, toggleTheme } = useTheme()

  const { data: currentUser } = useQuery(
    ['currentUser'],
    () => authAPI.getCurrentUser(),
    {
      retry: false,
      onSuccess: (res) => setIsAdmin(res.data.is_admin),
      onError: () => setIsAdmin(false)
    }
  )

  // Close menu when clicking outside
  useEffect(() => {
    const handleClickOutside = (event) => {
      if (userMenuRef.current && !userMenuRef.current.contains(event.target)) {
        setShowUserMenu(false)
      }
    }

    if (showUserMenu) {
      document.addEventListener('mousedown', handleClickOutside)
    }

    return () => {
      document.removeEventListener('mousedown', handleClickOutside)
    }
  }, [showUserMenu])

  const handleLogout = () => {
    // Close menu immediately for better UX
    setShowUserMenu(false)

    // Clear localStorage immediately (don't wait for API)
    localStorage.removeItem('access_token')

    // Clear all React Query cache to prevent stale data
    queryClient.clear()

    // Navigate immediately
    navigate('/login', { replace: true })

    // Call logout API in background (fire and forget)
    // Don't wait for it - logout should be instant
    authAPI.logout().catch(() => {
      // Ignore errors - we've already logged out locally
    })
  }

  const getInitials = (username) => {
    if (!username) return 'U'
    return username.charAt(0).toUpperCase()
  }

  const navigation = [
    { name: 'Dashboard', href: '/', icon: HomeIcon },
    { name: 'Live Driving', href: '/live', icon: BoltIcon },
    { name: 'Trips', href: '/trips', icon: MapIcon },
    { name: 'Risk Profile', href: '/driving', icon: ChartBarIcon },
    { name: 'Policy', href: '/pricing', icon: DocumentTextIcon },
    { name: 'Rewards', href: '/rewards', icon: TrophyIcon },
    { name: 'Drive Simulator', href: '/simulator', icon: PlayIcon },
  ]

  const aiNavigation = [
    { name: 'Insurance Advisor', href: '/advisor', icon: BuildingOfficeIcon },
  ]

  const adminNavigation = [
    { name: 'Admin Dashboard', href: '/admin', icon: ShieldCheckIcon },
    { name: 'Drivers', href: '/admin/drivers', icon: UserGroupIcon },
    { name: 'Policies', href: '/admin/policies', icon: DocumentTextIcon },
  ]

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900 transition-colors duration-200">
      {/* Sidebar */}
      <div className="fixed inset-y-0 left-0 w-56 bg-white dark:bg-gray-800 border-r border-gray-200 dark:border-gray-700 transition-colors duration-200">
        <div className="flex flex-col h-full">
          {/* Logo */}
          <div className="flex items-center px-4 py-4 border-b border-gray-200 dark:border-gray-700">
            <div className="w-8 h-8 bg-blue-600 rounded-lg flex items-center justify-center mr-2">
              <svg className="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            </div>
            <div>
              <h1 className="text-base font-bold text-gray-900 dark:text-white">SmartDrive</h1>
              <p className="text-xs text-gray-500 dark:text-gray-400">Telematics</p>
            </div>
          </div>

          {/* Navigation */}
          <nav className="flex-1 px-3 py-3 space-y-0.5 overflow-y-auto">
            {/* Regular User Navigation - Only show if NOT admin */}
            {!isAdmin && (
              <>
                <div className="text-xs font-semibold text-gray-400 uppercase tracking-wider px-3 py-1.5">
                  NAVIGATION
                </div>
                {navigation.map((item) => {
                  const isActive = location.pathname === item.href ||
                    (item.href === '/' && location.pathname === '/')
                  return (
                    <Link
                      key={item.name}
                      to={item.href}
                      className={`flex items-center px-3 py-2 rounded-lg transition-colors ${isActive
                          ? 'bg-blue-600 text-white'
                          : 'text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700'
                        }`}
                    >
                      <item.icon className="w-4 h-4 mr-2.5" />
                      <span className="text-sm">{item.name}</span>
                    </Link>
                  )
                })}
              </>
            )}

            {/* Admin Navigation - Only show if admin, placed first for admins */}
            {isAdmin && (
              <>
                <div className="text-xs font-semibold text-gray-400 uppercase tracking-wider px-3 py-1.5">
                  ADMIN
                </div>
                {adminNavigation.map((item) => {
                  const isActive = location.pathname === item.href
                  return (
                    <Link
                      key={item.name}
                      to={item.href}
                      className={`flex items-center px-3 py-2 rounded-lg transition-colors ${isActive
                          ? 'bg-blue-600 text-white'
                          : 'text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700'
                        }`}
                    >
                      <item.icon className="w-4 h-4 mr-2.5" />
                      <span className="text-sm">{item.name}</span>
                    </Link>
                  )
                })}
              </>
            )}

            {/* AI Assistant Section - Show for all users */}
            <div className={!isAdmin ? "pt-3" : "pt-3"}>
              <div className="text-xs font-semibold text-gray-400 uppercase tracking-wider px-3 py-1.5">
                AI ASSISTANT
              </div>
              {aiNavigation.map((item) => {
                const isActive = location.pathname === item.href
                return (
                  <Link
                    key={item.name}
                    to={item.href}
                    className={`flex items-center px-3 py-2 rounded-lg transition-colors ${isActive
                        ? 'bg-blue-600 text-white'
                        : 'text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700'
                      }`}
                  >
                    <item.icon className="w-4 h-4 mr-2.5" />
                    <span className="text-sm">{item.name}</span>
                  </Link>
                )
              })}
            </div>
          </nav>

          {/* User Card */}
          <div className="px-3 py-3 border-t border-gray-200 dark:border-gray-700 relative" ref={userMenuRef}>
            {/* Theme Toggle */}
            <button
              onClick={toggleTheme}
              className="w-full flex items-center px-2 py-2 mb-2 rounded-lg text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors"
            >
              {theme === 'dark' ? (
                <>
                  <SunIcon className="w-5 h-5 mr-2 text-yellow-500" />
                  <span className="text-sm">Light Mode</span>
                </>
              ) : (
                <>
                  <MoonIcon className="w-5 h-5 mr-2 text-gray-500" />
                  <span className="text-sm">Dark Mode</span>
                </>
              )}
            </button>

            <div
              className="flex items-center px-2 py-1.5 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 cursor-pointer transition-colors"
              onClick={() => setShowUserMenu(!showUserMenu)}
            >
              <div className="w-8 h-8 bg-blue-100 dark:bg-blue-900 rounded-full flex items-center justify-center mr-2">
                <span className="text-blue-600 dark:text-blue-300 font-semibold text-sm">
                  {getInitials(currentUser?.data?.username)}
                </span>
              </div>
              <div className="flex-1 min-w-0">
                <div className="font-semibold text-gray-900 dark:text-white truncate text-sm">
                  {currentUser?.data?.username || 'User'}
                </div>
                <div className="text-xs text-gray-500 dark:text-gray-400 truncate">
                  {currentUser?.data?.email || 'Safe driving saves'}
                </div>
              </div>
              <svg
                className={`w-4 h-4 text-gray-400 transition-transform ${showUserMenu ? 'rotate-180' : ''}`}
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
              </svg>
            </div>

            {/* User Menu Dropdown */}
            {showUserMenu && (
              <div className="absolute bottom-full left-0 right-0 mb-2 mx-3 bg-white dark:bg-gray-800 rounded-lg shadow-lg border border-gray-200 dark:border-gray-700 py-2 z-50">
                <Link
                  to="/profile"
                  className="flex items-center px-4 py-2 text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors"
                  onClick={() => setShowUserMenu(false)}
                >
                  <UserCircleIcon className="w-5 h-5 mr-3 text-gray-400" />
                  <span>My Profile</span>
                </Link>
                <button
                  onClick={handleLogout}
                  className="w-full flex items-center px-4 py-2 text-red-600 hover:bg-red-50 dark:hover:bg-red-900/20 transition-colors"
                >
                  <ArrowRightOnRectangleIcon className="w-5 h-5 mr-3" />
                  <span>Logout</span>
                </button>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Main content */}
      <div className="ml-56 transition-all duration-200">
        <div className="p-8">
          <Outlet />
        </div>
      </div>
    </div>
  )
}
