import { useState, useEffect } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { authAPI } from '../services/api'
import {
  ShieldCheckIcon,
  LockClosedIcon,
  ArrowRightIcon,
  SparklesIcon,
  HomeIcon,
  StarIcon,
  BoltIcon,
  UserIcon
} from '@heroicons/react/24/outline'

export default function Login() {
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const [showPassword, setShowPassword] = useState(false)
  const [focusedField, setFocusedField] = useState(null)
  const navigate = useNavigate()

  // Redirect if already authenticated
  useEffect(() => {
    const token = localStorage.getItem('access_token')
    if (token) {
      // Verify token is still valid and redirect based on user role
      authAPI.getCurrentUser()
        .then((userRes) => {
          if (userRes.data?.is_admin) {
            navigate('/admin')
          } else {
            navigate('/')
          }
        })
        .catch((err) => {
          console.log('Token invalid or expired, removing from storage')
          localStorage.removeItem('access_token')
        })
    }
  }, [navigate])

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')
    setLoading(true)

    // Input validation
    if (!username.trim()) {
      setError('Username is required')
      setLoading(false)
      return
    }

    if (!password) {
      setError('Password is required')
      setLoading(false)
      return
    }

    try {
      console.log('Attempting login with:', { username: username.trim() })
      const response = await authAPI.login({ username: username.trim(), password })
      console.log('Login response:', response)

      if (response.data?.access_token) {
        localStorage.setItem('access_token', response.data.access_token)
        // Check if user is admin and redirect accordingly
        authAPI.getCurrentUser()
          .then((userRes) => {
            if (userRes.data?.is_admin) {
              navigate('/admin')
            } else {
              navigate('/')
            }
          })
          .catch(() => {
            // If we can't get user info, default to regular dashboard
            navigate('/')
          })
      } else {
        setError('Invalid response from server')
        console.error('No access token in response:', response)
      }
    } catch (err) {
      console.error('Login error:', err)
      console.error('Error response:', err.response)

      const errorMessage = err.response?.data?.detail || err.response?.data?.message || err.message || 'Login failed. Please check your credentials.'
      setError(errorMessage)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-cyan-50 via-blue-50 via-indigo-50 to-purple-50 dark:from-gray-900 dark:via-gray-900 dark:to-gray-800 flex items-center justify-center px-4 relative overflow-hidden transition-colors duration-200">
      {/* Enhanced Animated Background Elements */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        <div className="absolute top-1/4 left-1/4 w-96 h-96 bg-cyan-200 dark:bg-cyan-900 rounded-full mix-blend-multiply dark:mix-blend-screen filter blur-3xl opacity-20 animate-blob" />
        <div className="absolute top-1/3 right-1/4 w-96 h-96 bg-violet-200 dark:bg-violet-900 rounded-full mix-blend-multiply dark:mix-blend-screen filter blur-3xl opacity-20 animate-blob animation-delay-2000" />
        <div className="absolute bottom-1/4 left-1/3 w-96 h-96 bg-fuchsia-200 dark:bg-fuchsia-900 rounded-full mix-blend-multiply dark:mix-blend-screen filter blur-3xl opacity-20 animate-blob animation-delay-4000" />
        <div className="absolute top-1/2 right-1/3 w-80 h-80 bg-emerald-200 dark:bg-emerald-900 rounded-full mix-blend-multiply dark:mix-blend-screen filter blur-3xl opacity-15 animate-blob animation-delay-6000" />
        {/* Floating particles */}
        <div className="absolute top-20 left-20 w-2 h-2 bg-yellow-200 dark:bg-yellow-600 rounded-full animate-float opacity-40" />
        <div className="absolute top-40 right-32 w-3 h-3 bg-pink-200 dark:bg-pink-600 rounded-full animate-float-delay opacity-40" />
        <div className="absolute bottom-32 left-40 w-2 h-2 bg-cyan-200 dark:bg-cyan-600 rounded-full animate-float-delay-2 opacity-40" />
      </div>

      {/* Homepage Button */}
      <Link
        to="/home"
        className="absolute top-6 left-6 z-10 flex items-center gap-2 px-5 py-2.5 bg-white/90 dark:bg-gray-800/90 backdrop-blur-md rounded-full shadow-xl hover:shadow-2xl border-2 border-white/50 dark:border-gray-700/50 hover:border-cyan-300 dark:hover:border-cyan-600 transition-all group transform hover:scale-105"
      >
        <HomeIcon className="w-5 h-5 text-cyan-600 dark:text-cyan-400 group-hover:text-purple-600 dark:group-hover:text-purple-400 transition-colors" />
        <span className="text-sm font-semibold bg-gradient-to-r from-cyan-600 to-purple-600 dark:from-cyan-400 dark:to-purple-400 bg-clip-text text-transparent">Home</span>
      </Link>

      <div className="max-w-md w-full relative z-10">
        {/* Main Card with Enhanced Design */}
        <div className="bg-white/95 dark:bg-gray-800/95 backdrop-blur-xl rounded-3xl shadow-2xl border-2 border-white/30 dark:border-gray-700/30 p-8 md:p-10 relative overflow-hidden transition-colors duration-200">
          {/* Decorative gradient overlay */}
          <div className="absolute top-0 right-0 w-64 h-64 bg-gradient-to-br from-cyan-200/30 dark:from-cyan-900/30 to-purple-200/30 dark:to-purple-900/30 rounded-full blur-3xl -mr-32 -mt-32" />

          {/* Logo/Branding */}
          <div className="text-center mb-8 relative z-10">
            <div className="inline-flex items-center justify-center w-20 h-20 bg-gradient-to-br from-cyan-500 via-blue-500 via-purple-500 to-pink-500 rounded-2xl mb-4 shadow-xl transform hover:scale-110 transition-transform duration-300">
              <ShieldCheckIcon className="w-10 h-10 text-white" />
            </div>
            <h1 className="text-5xl font-bold bg-gradient-to-r from-cyan-600 via-blue-600 via-purple-600 to-pink-600 dark:from-cyan-400 dark:via-blue-400 dark:via-purple-400 dark:to-pink-400 bg-clip-text text-transparent mb-2">
              SmartDrive
            </h1>
            <p className="text-gray-600 dark:text-gray-400 font-medium">Welcome back! Sign in to continue</p>
          </div>

          {/* Error Message */}
          {error && (
            <div className="mb-6 p-4 bg-gradient-to-r from-red-50 to-pink-50 border-l-4 border-red-500 rounded-xl animate-shake relative z-10 shadow-md">
              <div className="flex items-center gap-3">
                <div className="flex-shrink-0 p-2 bg-red-500 rounded-lg">
                  <svg className="w-5 h-5 text-white" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
                  </svg>
                </div>
                <p className="text-sm font-semibold text-red-800">{error}</p>
              </div>
            </div>
          )}

          {/* Login Form */}
          <form onSubmit={handleSubmit} className="space-y-6 relative z-10">
            {/* Username Field */}
            <div className="space-y-2">
              <label className="block text-sm font-bold text-gray-700 dark:text-gray-300 mb-2 flex items-center gap-2">
                <UserIcon className="w-4 h-4 text-cyan-600 dark:text-cyan-400" />
                Username
              </label>
              <div className="relative group">
                <div className={`absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none transition-all duration-300 ${focusedField === 'username' ? 'text-cyan-600 dark:text-cyan-400 scale-110' : 'text-gray-400 dark:text-gray-500'
                  }`}>
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
                  </svg>
                </div>
                <input
                  type="text"
                  value={username}
                  onChange={(e) => setUsername(e.target.value)}
                  onFocus={() => setFocusedField('username')}
                  onBlur={() => setFocusedField(null)}
                  className={`w-full pl-12 pr-4 py-4 border-2 rounded-xl transition-all duration-300 font-medium bg-white dark:bg-gray-700 text-gray-900 dark:text-white placeholder-gray-400 dark:placeholder-gray-500 ${focusedField === 'username'
                      ? 'border-cyan-500 dark:border-cyan-400 bg-gradient-to-r from-cyan-50 to-blue-50 dark:from-cyan-900/20 dark:to-blue-900/20 shadow-lg shadow-cyan-500/20 focus:ring-4 focus:ring-cyan-500/30'
                      : 'border-gray-200 dark:border-gray-600 hover:border-cyan-300 dark:hover:border-cyan-600 hover:shadow-md focus:border-cyan-500 dark:focus:border-cyan-400 focus:ring-4 focus:ring-cyan-500/20'
                    }`}
                  placeholder="Enter your username"
                  required
                />
              </div>
            </div>

            {/* Password Field */}
            <div className="space-y-2">
              <label className="block text-sm font-bold text-gray-700 dark:text-gray-300 mb-2 flex items-center gap-2">
                <LockClosedIcon className="w-4 h-4 text-purple-600 dark:text-purple-400" />
                Password
              </label>
              <div className="relative group">
                <div className={`absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none transition-all duration-300 ${focusedField === 'password' ? 'text-purple-600 dark:text-purple-400 scale-110' : 'text-gray-400 dark:text-gray-500'
                  }`}>
                  <LockClosedIcon className="w-5 h-5" />
                </div>
                <input
                  type={showPassword ? 'text' : 'password'}
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  onFocus={() => setFocusedField('password')}
                  onBlur={() => setFocusedField(null)}
                  className={`w-full pl-12 pr-12 py-4 border-2 rounded-xl transition-all duration-300 font-medium bg-white dark:bg-gray-700 text-gray-900 dark:text-white placeholder-gray-400 dark:placeholder-gray-500 ${focusedField === 'password'
                      ? 'border-purple-500 dark:border-purple-400 bg-gradient-to-r from-purple-50 to-pink-50 dark:from-purple-900/20 dark:to-pink-900/20 shadow-lg shadow-purple-500/20 focus:ring-4 focus:ring-purple-500/30'
                      : 'border-gray-200 dark:border-gray-600 hover:border-purple-300 dark:hover:border-purple-600 hover:shadow-md focus:border-purple-500 dark:focus:border-purple-400 focus:ring-4 focus:ring-purple-500/20'
                    }`}
                  placeholder="Enter your password"
                  required
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute inset-y-0 right-0 pr-4 flex items-center text-gray-400 dark:text-gray-500 hover:text-purple-600 dark:hover:text-purple-400 transition-colors hover:scale-110"
                >
                  {showPassword ? (
                    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13.875 18.825A10.05 10.05 0 0112 19c-4.478 0-8.268-2.943-9.543-7a9.97 9.97 0 011.563-3.029m5.858.908a3 3 0 114.243 4.243M9.878 9.878l4.242 4.242M9.88 9.88l-3.29-3.29m7.532 7.532l3.29 3.29M3 3l3.59 3.59m0 0A9.953 9.953 0 0112 5c4.478 0 8.268 2.943 9.543 7a10.025 10.025 0 01-4.132 5.411m0 0L21 21" />
                    </svg>
                  ) : (
                    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
                    </svg>
                  )}
                </button>
              </div>
            </div>

            {/* Submit Button */}
            <button
              type="submit"
              disabled={loading}
              className={`group relative w-full py-4 rounded-xl font-bold text-lg shadow-xl transition-all duration-300 overflow-hidden transform hover:scale-[1.02] ${loading
                  ? 'bg-gray-400 cursor-not-allowed'
                  : 'bg-gradient-to-r from-cyan-600 via-blue-600 via-purple-600 to-pink-600 text-white hover:shadow-2xl'
                }`}
            >
              <span className="relative z-10 flex items-center justify-center gap-2">
                {loading ? (
                  <>
                    <svg className="animate-spin h-5 w-5" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                    </svg>
                    Signing in...
                  </>
                ) : (
                  <>
                    Sign In
                    <ArrowRightIcon className="w-5 h-5 group-hover:translate-x-1 transition-transform" />
                  </>
                )}
              </span>
              {!loading && (
                <div className="absolute inset-0 bg-gradient-to-r from-pink-600 via-rose-600 to-orange-600 opacity-0 group-hover:opacity-100 transition-opacity duration-300" />
              )}
            </button>
          </form>

          {/* Divider */}
          <div className="relative my-8">
            <div className="absolute inset-0 flex items-center">
              <div className="w-full border-t-2 border-gray-200 dark:border-gray-700"></div>
            </div>
            <div className="relative flex justify-center text-sm">
              <span className="px-4 bg-white dark:bg-gray-800 text-gray-500 dark:text-gray-400 font-medium">New to SmartDrive?</span>
            </div>
          </div>

          {/* Signup Link */}
          <Link
            to="/signup"
            className="flex items-center justify-center gap-2 w-full py-4 px-4 bg-gradient-to-r from-cyan-500 via-blue-500 to-purple-500 text-white rounded-xl font-bold hover:from-cyan-600 hover:via-blue-600 hover:to-purple-600 transition-all group shadow-lg hover:shadow-xl transform hover:scale-105 relative z-10"
          >
            <SparklesIcon className="w-5 h-5 group-hover:rotate-12 transition-transform" />
            Get a personalized quote
            <ArrowRightIcon className="w-5 h-5 group-hover:translate-x-1 transition-transform" />
          </Link>
        </div>
      </div>

      <style>{`
        @keyframes blob {
          0%, 100% {
            transform: translate(0px, 0px) scale(1);
          }
          33% {
            transform: translate(30px, -50px) scale(1.1);
          }
          66% {
            transform: translate(-20px, 20px) scale(0.9);
          }
        }
        .animate-blob {
          animation: blob 7s infinite;
        }
        .animation-delay-2000 {
          animation-delay: 2s;
        }
        .animation-delay-4000 {
          animation-delay: 4s;
        }
        .animation-delay-6000 {
          animation-delay: 6s;
        }
        @keyframes shake {
          0%, 100% { transform: translateX(0); }
          10%, 30%, 50%, 70%, 90% { transform: translateX(-5px); }
          20%, 40%, 60%, 80% { transform: translateX(5px); }
        }
        .animate-shake {
          animation: shake 0.5s;
        }
        @keyframes float {
          0%, 100% {
            transform: translateY(0px);
          }
          50% {
            transform: translateY(-20px);
          }
        }
        .animate-float {
          animation: float 3s ease-in-out infinite;
        }
        .animate-float-delay {
          animation: float 3s ease-in-out infinite 1s;
        }
        .animate-float-delay-2 {
          animation: float 3s ease-in-out infinite 2s;
        }
      `}</style>
    </div>
  )
}
