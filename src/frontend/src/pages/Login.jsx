import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { authAPI } from '../services/api'

export default function Login() {
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const navigate = useNavigate()

  // Redirect if already authenticated
  useEffect(() => {
    const token = localStorage.getItem('access_token')
    if (token) {
      // Verify token is still valid
      authAPI.getCurrentUser()
        .then(() => navigate('/'))
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
        navigate('/')
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
    <div className="min-h-screen bg-gradient-to-br from-blue-900 to-blue-700 flex items-center justify-center px-4">
      <div className="max-w-md w-full bg-white rounded-lg shadow-xl p-8">
        <div className="text-center mb-8">
          <h1 className="text-3xl font-bold text-gray-900">Telematics Insurance</h1>
          <p className="mt-2 text-gray-600">Sign in to your account</p>
        </div>

        {error && (
          <div className="mb-4 p-3 bg-red-100 border border-red-400 text-red-700 rounded">
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-6">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Username
            </label>
            <input
              type="text"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              required
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Password
            </label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              required
            />
          </div>

          <button
            type="submit"
            disabled={loading}
            className={`w-full py-3 rounded-lg font-semibold transition-colors ${
              loading
                ? 'bg-gray-400 cursor-not-allowed'
                : 'bg-blue-600 text-white hover:bg-blue-700'
            }`}
          >
            {loading ? 'Signing in...' : 'Sign In'}
          </button>
        </form>

        <div className="mt-6 text-center text-sm text-gray-600">
          <p className="mb-2">Demo credentials:</p>
          <p>
            Username: <code className="bg-gray-100 px-2 py-1 rounded">demo</code>
            {' '}Password: <code className="bg-gray-100 px-2 py-1 rounded">demo123</code>
          </p>
          <p className="mt-2">
            Admin: <code className="bg-gray-100 px-2 py-1 rounded">admin</code>
            {' '}/ <code className="bg-gray-100 px-2 py-1 rounded">admin123</code>
          </p>
        </div>
      </div>
    </div>
  )
}
