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

export default function LiveDriving() {
  const [isConnected, setIsConnected] = useState(false)
  const [drivingData, setDrivingData] = useState(null)
  const [safetyAlerts, setSafetyAlerts] = useState([])
  const [pricing, setPricing] = useState(null)
  const [riskScore, setRiskScore] = useState(null)
  const [isDriveActive, setIsDriveActive] = useState(false)
  const [isStartingDrive, setIsStartingDrive] = useState(false)
  const [isStoppingDrive, setIsStoppingDrive] = useState(false)
  const wsRef = useRef(null)
  const alertTimeoutRef = useRef(null)
  const queryClient = useQueryClient()

  // Get current user
  const { data: currentUser } = useQuery(
    ['currentUser'],
    () => authAPI.getCurrentUser(),
    { retry: false }
  )

  const driverId = currentUser?.data?.driver_id || 'DRV-0001'

  // Fetch drive status
  const { data: driveStatus } = useQuery(
    ['driveStatus', driverId],
    () => realtimeAPI.getDriveStatus(driverId),
    {
      refetchInterval: isDriveActive ? 2000 : 5000, // Check more frequently when active
      retry: false,
      enabled: !!driverId
    }
  )


  useEffect(() => {
    if (driveStatus?.data) {
      const wasActive = isDriveActive
      const nowActive = driveStatus.data.is_active || false
      setIsDriveActive(nowActive)
      
      // If drive was just stopped, clear the data to show it's stopped
      if (wasActive && !nowActive) {
        console.log('Drive session stopped - clearing real-time data')
        // Optionally reset some state here if needed
      }
    }
  }, [driveStatus])

  // Fetch initial analysis on mount
  useEffect(() => {
    if (!driverId) return
    
    // Get initial analysis
    const fetchInitialAnalysis = async () => {
      try {
        const token = localStorage.getItem('access_token')
        const response = await fetch(`http://localhost:8000/api/v1/realtime/analysis/${driverId}`, {
          headers: {
            'Authorization': `Bearer ${token}`
          }
        })
        if (response.ok) {
          const data = await response.json()
          if (data.analysis) {
            setDrivingData({
              safety_score: data.analysis.safety_score,
              risk_score: data.analysis.risk_score,
              behavior_metrics: data.analysis.behavior_metrics
            })
          }
          if (data.pricing) {
            setPricing(data.pricing)
          }
        }
      } catch (error) {
        console.error('Error fetching initial analysis:', error)
      }
    }
    
    fetchInitialAnalysis()
  }, [driverId])

  // WebSocket connection
  useEffect(() => {
    if (!driverId) return

    const wsUrl = `ws://localhost:8000/api/v1/realtime/ws/${driverId}`
    const ws = new WebSocket(wsUrl)

    ws.onopen = () => {
      console.log('WebSocket connected')
      setIsConnected(true)
    }

    ws.onmessage = (event) => {
      const message = JSON.parse(event.data)
      handleWebSocketMessage(message)
    }

    ws.onerror = (error) => {
      console.error('WebSocket error:', error)
      setIsConnected(false)
    }

    ws.onclose = () => {
      console.log('WebSocket disconnected')
      setIsConnected(false)
      // Reconnect after 3 seconds
      setTimeout(() => {
        if (driverId) {
          wsRef.current = new WebSocket(wsUrl)
        }
      }, 3000)
    }

    wsRef.current = ws

    return () => {
      if (wsRef.current) {
        wsRef.current.close()
      }
      if (alertTimeoutRef.current) {
        clearTimeout(alertTimeoutRef.current)
      }
    }
  }, [driverId])

  const handleWebSocketMessage = (message) => {
    switch (message.type) {
      case 'driving_update':
        setDrivingData(message.data)
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
    // Add alert to list
    setSafetyAlerts(prev => [alert, ...prev].slice(0, 10)) // Keep last 10 alerts

    // Show popup alert
    showAlertPopup(alert)
  }

  const showAlertPopup = (alert) => {
    // Create and show alert popup
    const alertElement = document.createElement('div')
    alertElement.className = `fixed top-4 right-4 z-50 p-4 rounded-lg shadow-lg ${
      alert.severity === 'high' ? 'bg-red-500' : 'bg-yellow-500'
    } text-white max-w-md animate-pulse`
    alertElement.innerHTML = `
      <div class="flex items-center gap-3">
        <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
        </svg>
        <div>
          <div class="font-bold">${alert.type.replace('_', ' ').toUpperCase()}</div>
          <div class="text-sm">${alert.message}</div>
        </div>
      </div>
    `
    document.body.appendChild(alertElement)

    // Remove after 5 seconds
    alertTimeoutRef.current = setTimeout(() => {
      alertElement.remove()
    }, 5000)
  }

  const getRiskColor = (score) => {
    if (score >= 80) return 'text-green-600'
    if (score >= 60) return 'text-yellow-600'
    return 'text-red-600'
  }

  const getSeverityColor = (severity) => {
    switch (severity) {
      case 'high':
        return 'bg-red-100 text-red-800 border-red-300'
      case 'medium':
        return 'bg-yellow-100 text-yellow-800 border-yellow-300'
      default:
        return 'bg-blue-100 text-blue-800 border-blue-300'
    }
  }

  const handleStartDrive = async () => {
    setIsStartingDrive(true)
    try {
      await realtimeAPI.startDrive(driverId, {
        start_latitude: 37.7749,
        start_longitude: -122.4194,
        interval_seconds: 10.0
      })
      setIsDriveActive(true)
    } catch (error) {
      console.error('Failed to start drive:', error)
      alert('Failed to start drive session. Please try again.')
    } finally {
      setIsStartingDrive(false)
    }
  }

  const handleStopDrive = async () => {
    setIsStoppingDrive(true)
    try {
      await realtimeAPI.stopDrive(driverId)
      setIsDriveActive(false)
    } catch (error) {
      console.error('Failed to stop drive:', error)
      alert('Failed to stop drive session. Please try again.')
    } finally {
      setIsStoppingDrive(false)
    }
  }


  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Live Driving Dashboard</h1>
          <p className="text-gray-600 mt-1">Real-time driving behavior and safety monitoring</p>
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
            <span className="text-sm text-gray-600">
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

      {/* Safety Alerts Popup */}
      {safetyAlerts.length > 0 && (
        <div className="bg-red-50 border-l-4 border-red-500 p-4 rounded-lg">
          <div className="flex items-center gap-2 mb-2">
            <ExclamationTriangleSolid className="w-6 h-6 text-red-600" />
            <h2 className="text-lg font-bold text-red-900">Active Safety Alerts</h2>
          </div>
          <div className="space-y-2">
            {safetyAlerts.slice(0, 3).map((alert, idx) => (
              <div key={idx} className={`p-3 rounded border ${getSeverityColor(alert.severity)}`}>
                <div className="font-semibold">{alert.type.replace('_', ' ').toUpperCase()}</div>
                <div className="text-sm">{alert.message}</div>
                <div className="text-xs opacity-75 mt-1">
                  {new Date(alert.timestamp).toLocaleTimeString()}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Real-Time Metrics Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
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
        <div className="bg-white rounded-xl shadow-md p-6">
          <h2 className="text-xl font-semibold text-gray-900 mb-4">Driving Behavior</h2>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="bg-gray-50 rounded-lg p-4">
              <div className="text-sm text-gray-600 mb-1">Avg Speed</div>
              <div className="text-2xl font-bold text-gray-900">
                {Math.round(drivingData.behavior_metrics.avg_speed)} mph
              </div>
            </div>
            <div className="bg-gray-50 rounded-lg p-4">
              <div className="text-sm text-gray-600 mb-1">Max Speed</div>
              <div className="text-2xl font-bold text-gray-900">
                {Math.round(drivingData.behavior_metrics.max_speed)} mph
              </div>
            </div>
            <div className="bg-red-50 rounded-lg p-4">
              <div className="text-sm text-gray-600 mb-1">Harsh Braking</div>
              <div className="text-2xl font-bold text-red-600">
                {drivingData.behavior_metrics.harsh_braking_count}
              </div>
            </div>
            <div className="bg-yellow-50 rounded-lg p-4">
              <div className="text-sm text-gray-600 mb-1">Speeding</div>
              <div className="text-2xl font-bold text-yellow-600">
                {drivingData.behavior_metrics.speeding_count}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Recent Alerts */}
      {safetyAlerts.length > 0 && (
        <div className="bg-white rounded-xl shadow-md p-6">
          <h2 className="text-xl font-semibold text-gray-900 mb-4">Recent Safety Alerts</h2>
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

