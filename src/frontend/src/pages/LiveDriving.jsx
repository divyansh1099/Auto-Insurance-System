import { useState, useEffect, useRef } from 'react'
import { useQuery, useQueryClient } from 'react-query'
import { authAPI, realtimeAPI } from '../services/api'
import {
  ExclamationTriangleIcon,
  CheckCircleIcon,
  ChartBarIcon,
  CurrencyDollarIcon,
  BoltIcon,
  ShieldExclamationIcon,
  PlayIcon,
  StopIcon
} from '@heroicons/react/24/outline'
import { ExclamationTriangleIcon as ExclamationTriangleSolid } from '@heroicons/react/24/solid'

import LiveMap from '../components/LiveMap'

export default function LiveDriving() {
  const [isConnected, setIsConnected] = useState(false)
  const [drivingData, setDrivingData] = useState(null)
  const [safetyAlerts, setSafetyAlerts] = useState([])
  const [pricing, setPricing] = useState(null)
  const [riskScore, setRiskScore] = useState(null)
  const [isDriveActive, setIsDriveActive] = useState(false)
  const [isStartingDrive, setIsStartingDrive] = useState(false)
  const [isStoppingDrive, setIsStoppingDrive] = useState(false)

  // Map State
  const [currentLocation, setCurrentLocation] = useState(null)
  const [pathHistory, setPathHistory] = useState([])

  const wsRef = useRef(null)
  const alertTimeoutRef = useRef(null)
  const queryClient = useQueryClient()

  // Fetch Current User
  const { data: currentUser } = useQuery(
    'currentUser',
    () => authAPI.getCurrentUser(),
    { retry: false }
  )

  const driverId = currentUser?.data?.id

  // Fetch Drive Status
  const { data: driveStatus, refetch: refetchDriveStatus } = useQuery(
    ['driveStatus', driverId],
    () => realtimeAPI.getDriveStatus(driverId),
    {
      enabled: !!driverId,
      refetchInterval: isDriveActive ? 5000 : false,
      onSuccess: (res) => {
        setIsDriveActive(res.data.is_active)
      }
    }
  )

  // Handle Start Drive
  const handleStartDrive = async () => {
    if (!driverId) return

    try {
      setIsStartingDrive(true)
      await realtimeAPI.startDrive(driverId, {
        source: 'simulation',
        update_interval: 1.0
      })
      setIsDriveActive(true)
      refetchDriveStatus()
    } catch (error) {
      console.error('Failed to start drive:', error)
    } finally {
      setIsStartingDrive(false)
    }
  }

  // Handle Stop Drive
  const handleStopDrive = async () => {
    if (!driverId) return

    try {
      setIsStoppingDrive(true)
      await realtimeAPI.stopDrive(driverId)
      setIsDriveActive(false)
      refetchDriveStatus()
    } catch (error) {
      console.error('Failed to stop drive:', error)
    } finally {
      setIsStoppingDrive(false)
    }
  }

  // Handle WebSocket messages
  const handleWebSocketMessage = (message) => {
    switch (message.type) {
      case 'driving_update':
        setDrivingData(message.data)
        if (message.data.location) {
          const newLoc = message.data.location
          setCurrentLocation(newLoc)
          setPathHistory(prev => [...prev, newLoc])
        }
        break
      case 'safety_alert':
        handleSafetyAlert(message.data)
        break
      case 'pricing_update':
        setPricing(message.data)
        break
      case 'risk_score_update':
        setRiskScore(message.data)
        break
      default:
        console.log('Unknown message type:', message.type)
    }
  }

  const handleSafetyAlert = (alert) => {
    setSafetyAlerts(prev => [alert, ...prev].slice(0, 5))

    // Clear alert after 5 seconds
    if (alertTimeoutRef.current) clearTimeout(alertTimeoutRef.current)
    alertTimeoutRef.current = setTimeout(() => {
      // Optional: Auto-dismiss logic if needed
    }, 5000)
  }

  const getSeverityColor = (severity) => {
    switch (severity) {
      case 'critical':
        return 'bg-red-50 border-red-200 text-red-800'
      case 'high':
        return 'bg-orange-50 border-orange-200 text-orange-800'
      case 'medium':
        return 'bg-yellow-50 border-yellow-200 text-yellow-800'
      default:
        return 'bg-blue-50 border-blue-200 text-blue-800'
    }
  }

  // WebSocket Connection
  useEffect(() => {
    if (!driverId) return

    const WS_BASE_URL = import.meta.env.VITE_WS_URL || 'ws://localhost:8000'
    const token = localStorage.getItem('access_token')

    if (!token) {
      console.error('No auth token found')
      return
    }

    const wsUrl = `${WS_BASE_URL}/api/v1/realtime/ws/${driverId}?token=${token}`

    try {
      const ws = new WebSocket(wsUrl)
      wsRef.current = ws

      ws.onopen = () => {
        console.log('WebSocket connected')
        setIsConnected(true)
      }

      ws.onmessage = (event) => {
        try {
          const message = JSON.parse(event.data)
          handleWebSocketMessage(message)
        } catch (error) {
          console.error('Failed to parse WebSocket message:', error)
        }
      }

      ws.onerror = (error) => {
        console.error('WebSocket error:', error)
        setIsConnected(false)
      }

      ws.onclose = () => {
        console.log('WebSocket disconnected')
        setIsConnected(false)
      }

      return () => {
        if (ws.readyState === WebSocket.OPEN) {
          ws.close()
        }
      }
    } catch (error) {
      console.error('Failed to create WebSocket:', error)
    }
  }, [driverId])

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (alertTimeoutRef.current) {
        clearTimeout(alertTimeoutRef.current)
      }
    }
  }, [])


  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white">Live Driving Dashboard</h1>
          <p className="text-gray-600 dark:text-gray-400 mt-1">Real-time driving behavior and safety monitoring</p>
        </div>
        <div className="flex items-center gap-4">
          {/* Drive Control Button */}
          {!isDriveActive ? (
            <button
              onClick={handleStartDrive}
              disabled={isStartingDrive}
              className="flex items-center gap-2 px-6 py-3 bg-green-600 hover:bg-green-700 text-white font-semibold rounded-lg shadow-md transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <PlayIcon className="w-5 h-5" />
              {isStartingDrive ? 'Starting...' : 'Start Live Drive'}
            </button>
          ) : (
            <button
              onClick={handleStopDrive}
              disabled={isStoppingDrive}
              className="flex items-center gap-2 px-6 py-3 bg-red-600 hover:bg-red-700 text-white font-semibold rounded-lg shadow-md transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <StopIcon className="w-5 h-5" />
              {isStoppingDrive ? 'Stopping...' : 'End Live Drive'}
            </button>
          )}

          {/* Connection Status */}
          <div className="flex items-center gap-2">
            <div className={`w-3 h-3 rounded-full ${isConnected ? 'bg-green-500' : 'bg-red-500'}`} />
            <span className="text-sm text-gray-600 dark:text-gray-400">
              {isConnected ? 'Connected' : 'Disconnected'}
            </span>
          </div>
        </div>
      </div>

      {/* Drive Status Banner */}
      {isDriveActive && (
        <div className="bg-green-50 border-l-4 border-green-500 p-4 rounded-lg">
          <div className="flex items-center gap-2">
            <BoltIcon className="w-5 h-5 text-green-600" />
            <div>
              <div className="font-semibold text-green-900">Live Drive Active</div>
              <div className="text-sm text-green-700">
                Generating telematics data. Events are being processed in real-time.
                {driveStatus?.data?.session_info && (
                  <span className="ml-2">
                    ({driveStatus.data.session_info.events_generated} events generated)
                  </span>
                )}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Map Section */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2">
          <LiveMap currentLocation={currentLocation} pathHistory={pathHistory} />
        </div>

        {/* Metrics Sidebar */}
        <div className="space-y-4">
          {/* Safety Score */}
          <div className="bg-gradient-to-br from-green-500 to-green-600 rounded-xl shadow-lg p-6 text-white">
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm font-medium opacity-90">Safety Score</span>
              <CheckCircleIcon className="w-5 h-5" />
            </div>
            <div className="text-4xl font-bold mb-1">
              {drivingData?.safety_score ? Math.round(drivingData.safety_score) : '--'}
            </div>
            <div className="text-sm opacity-80">Real-time</div>
          </div>

          {/* Risk Score */}
          <div className="bg-gradient-to-br from-orange-400 to-yellow-500 rounded-xl shadow-lg p-6 text-white">
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm font-medium opacity-90">Risk Score</span>
              <ChartBarIcon className="w-5 h-5" />
            </div>
            <div className="text-4xl font-bold mb-1">
              {drivingData?.risk_score ? Math.round(drivingData.risk_score) : '--'}
            </div>
            <div className="text-sm opacity-80">Lower is better</div>
          </div>
        </div>
      </div>

      {/* Real-Time Metrics Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Current Speed */}
        <div className="bg-gradient-to-br from-blue-500 to-blue-600 rounded-xl shadow-lg p-6 text-white">
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm font-medium opacity-90">Current Speed</span>
            <BoltIcon className="w-5 h-5" />
          </div>
          <div className="text-4xl font-bold mb-1">
            {drivingData?.behavior_metrics?.current_speed
              ? Math.round(drivingData.behavior_metrics.current_speed)
              : '--'}
          </div>
          <div className="text-sm opacity-80">mph</div>
        </div>

        {/* Premium Savings */}
        <div className="bg-gradient-to-br from-purple-500 to-purple-600 rounded-xl shadow-lg p-6 text-white">
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm font-medium opacity-90">Monthly Premium</span>
            <CurrencyDollarIcon className="w-5 h-5" />
          </div>
          <div className="text-4xl font-bold mb-1">
            ${pricing?.adjusted_premium ? pricing.adjusted_premium.toFixed(0) : '--'}
          </div>
          <div className="text-sm opacity-80">
            {pricing?.discount_percent ? `${pricing.discount_percent.toFixed(0)}% discount` : 'Calculating...'}
          </div>
        </div>
      </div>

      {/* Behavior Metrics */}
      {drivingData?.behavior_metrics && (
        <div className="bg-white dark:bg-gray-800 rounded-xl shadow-md p-6">
          <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-4">Driving Behavior</h2>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="bg-gray-50 dark:bg-gray-700 rounded-lg p-4">
              <div className="text-sm text-gray-600 dark:text-gray-400 mb-1">Avg Speed</div>
              <div className="text-2xl font-bold text-gray-900 dark:text-white">
                {Math.round(drivingData.behavior_metrics.avg_speed)} mph
              </div>
            </div>
            <div className="bg-gray-50 dark:bg-gray-700 rounded-lg p-4">
              <div className="text-sm text-gray-600 dark:text-gray-400 mb-1">Max Speed</div>
              <div className="text-2xl font-bold text-gray-900 dark:text-white">
                {Math.round(drivingData.behavior_metrics.max_speed)} mph
              </div>
            </div>
            <div className="bg-red-50 rounded-lg p-4">
              <div className="text-sm text-gray-600 dark:text-gray-400 mb-1">Harsh Braking</div>
              <div className="text-2xl font-bold text-red-600">
                {drivingData.behavior_metrics.harsh_braking_count}
              </div>
            </div>
            <div className="bg-yellow-50 rounded-lg p-4">
              <div className="text-sm text-gray-600 dark:text-gray-400 mb-1">Speeding</div>
              <div className="text-2xl font-bold text-yellow-600">
                {drivingData.behavior_metrics.speeding_count}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Recent Alerts */}
      {safetyAlerts.length > 0 && (
        <div className="bg-white dark:bg-gray-800 rounded-xl shadow-md p-6">
          <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-4">Recent Safety Alerts</h2>
          <div className="space-y-2">
            {safetyAlerts.map((alert, idx) => (
              <div key={idx} className={`p-3 rounded border ${getSeverityColor(alert.severity)}`}>
                <div className="flex items-center justify-between">
                  <div>
                    <div className="font-semibold">{alert.type.replace('_', ' ').toUpperCase()}</div>
                    <div className="text-sm">{alert.message}</div>
                  </div>
                  <div className="text-xs opacity-75">
                    {new Date(alert.timestamp).toLocaleTimeString()}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Connection Status */}
      {!isConnected && (
        <div className="bg-yellow-50 border-l-4 border-yellow-500 p-4 rounded-lg">
          <div className="flex items-center gap-2">
            <ExclamationTriangleIcon className="w-5 h-5 text-yellow-600" />
            <div>
              <div className="font-semibold text-yellow-900">Not Connected</div>
              <div className="text-sm text-yellow-700">
                Waiting for real-time updates... Make sure you're generating telematics data.
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

