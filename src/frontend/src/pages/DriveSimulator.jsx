import { useState, useMemo } from 'react'
import { useQuery, useMutation } from 'react-query'
import { simulatorAPI, driverAPI, adminAPI, authAPI } from '../services/api'
import { BoltIcon, TruckIcon } from '@heroicons/react/24/outline'

export default function DriveSimulator() {
  // Get current user
  const { data: currentUser } = useQuery(
    ['currentUser'],
    () => authAPI.getCurrentUser(),
    { retry: false }
  )
  
  const driverId = currentUser?.data?.driver_id || 'DRV-0001'

  // Fetch drivers and vehicles for dropdowns
  const { data: driversData } = useQuery(
    ['drivers'],
    () => adminAPI.listDrivers(0, 100),
    { retry: false, enabled: false } // Disabled for now, can enable when needed
  )

  const { data: vehiclesData } = useQuery(
    ['vehicles'],
    () => adminAPI.listVehicles(0, 100),
    { retry: false, enabled: false } // Disabled for now, can enable when needed
  )

  const [params, setParams] = useState({
    driver_id: driverId,
    vehicle_id: '',
    distance_miles: 10,
    duration_minutes: 20,
    average_speed_mph: 35,
    max_speed_mph: 55,
    time_of_day: 'afternoon',
    weather: 'clear',
    hard_braking_count: 0,
    rapid_acceleration_count: 0,
    sharp_turn_count: 0,
    speeding_incidents: 0,
  })

  const [result, setResult] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const handleSliderChange = (name, value) => {
    setParams({
      ...params,
      [name]: parseFloat(value)
    })
  }

  const handleSelectChange = (name, value) => {
    setParams({
      ...params,
      [name]: value
    })
  }

  const simulateMutation = useMutation(
    (simParams) => simulatorAPI.calculateScore(simParams),
    {
      onSuccess: (response) => {
        setResult(response.data)
        setError('')
      },
      onError: (err) => {
        setError(err.response?.data?.detail || 'Failed to simulate trip')
      }
    }
  )

  const handleSimulate = async () => {
    setLoading(true)
    setResult(null)
    setError('')
    
    try {
      await simulateMutation.mutateAsync(params)
    } finally {
      setLoading(false)
    }
  }

  // Calculate total safety events
  const totalSafetyEvents = useMemo(() => {
    return params.hard_braking_count + 
           params.rapid_acceleration_count + 
           params.sharp_turn_count + 
           params.speeding_incidents
  }, [params])

  // Get risk level and color
  const getRiskLevel = (score) => {
    if (score >= 80) return { level: 'LOW', color: 'text-green-600', bgColor: 'bg-green-100' }
    if (score >= 60) return { level: 'MEDIUM', color: 'text-yellow-600', bgColor: 'bg-yellow-100' }
    return { level: 'HIGH', color: 'text-red-600', bgColor: 'bg-red-100' }
  }

  const riskInfo = result ? getRiskLevel(result.trip_score || result.safety_score || 100) : getRiskLevel(100)

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center gap-3">
        <TruckIcon className="w-8 h-8 text-blue-600" />
        <div>
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white">Drive Simulator</h1>
          <p className="text-gray-600 dark:text-gray-400 mt-1">Simulate driving scenarios for POC and testing</p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Side - Input Cards */}
        <div className="lg:col-span-2 space-y-6">
          {/* Select Driver & Vehicle Card */}
          <div className="bg-white dark:bg-gray-800 rounded-xl shadow-lg p-6">
            <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-4">Select Driver & Vehicle</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">Driver</label>
                <select
                  value={params.driver_id}
                  onChange={(e) => handleSelectChange('driver_id', e.target.value)}
                  className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                >
                  <option value={driverId}>Current Driver</option>
                  {driversData?.data?.map((driver) => (
                    <option key={driver.driver_id} value={driver.driver_id}>
                      {driver.first_name} {driver.last_name}
                    </option>
                  ))}
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">Vehicle</label>
                <select
                  value={params.vehicle_id}
                  onChange={(e) => handleSelectChange('vehicle_id', e.target.value)}
                  className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                >
                  <option value="">Select a vehicle</option>
                  {vehiclesData?.data?.map((vehicle) => (
                    <option key={vehicle.vehicle_id} value={vehicle.vehicle_id}>
                      {vehicle.year} {vehicle.make} {vehicle.model}
                    </option>
                  ))}
                </select>
              </div>
            </div>
          </div>

          {/* Trip Parameters Card */}
          <div className="bg-white dark:bg-gray-800 rounded-xl shadow-lg p-6">
            <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-6">Trip Parameters</h2>
            
            {error && (
              <div className="mb-4 p-3 bg-red-100 border border-red-400 text-red-700 rounded-lg">
                {error}
              </div>
            )}

            <div className="space-y-6">
              {/* Distance Slider */}
              <div>
                <div className="flex justify-between items-center mb-2">
                  <label className="text-sm font-medium text-gray-700 dark:text-gray-300">Distance (miles)</label>
                  <span className="text-lg font-semibold text-gray-900 dark:text-white">{params.distance_miles}</span>
                </div>
                <input
                  type="range"
                  min="0"
                  max="500"
                  step="1"
                  value={params.distance_miles}
                  onChange={(e) => handleSliderChange('distance_miles', e.target.value)}
                  className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer accent-blue-600"
                />
              </div>

              {/* Duration Slider */}
              <div>
                <div className="flex justify-between items-center mb-2">
                  <label className="text-sm font-medium text-gray-700 dark:text-gray-300">Duration (minutes)</label>
                  <span className="text-lg font-semibold text-gray-900 dark:text-white">{params.duration_minutes}</span>
                </div>
                <input
                  type="range"
                  min="0"
                  max="300"
                  step="1"
                  value={params.duration_minutes}
                  onChange={(e) => handleSliderChange('duration_minutes', e.target.value)}
                  className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer accent-blue-600"
                />
              </div>

              {/* Average Speed Slider */}
              <div>
                <div className="flex justify-between items-center mb-2">
                  <label className="text-sm font-medium text-gray-700 dark:text-gray-300">Average Speed (mph)</label>
                  <span className="text-lg font-semibold text-gray-900 dark:text-white">{params.average_speed_mph}</span>
                </div>
                <input
                  type="range"
                  min="0"
                  max="100"
                  step="1"
                  value={params.average_speed_mph}
                  onChange={(e) => handleSliderChange('average_speed_mph', e.target.value)}
                  className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer accent-blue-600"
                />
              </div>

              {/* Max Speed Slider */}
              <div>
                <div className="flex justify-between items-center mb-2">
                  <label className="text-sm font-medium text-gray-700 dark:text-gray-300">Max Speed (mph)</label>
                  <span className="text-lg font-semibold text-gray-900 dark:text-white">{params.max_speed_mph}</span>
                </div>
                <input
                  type="range"
                  min="0"
                  max="120"
                  step="1"
                  value={params.max_speed_mph}
                  onChange={(e) => handleSliderChange('max_speed_mph', e.target.value)}
                  className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer accent-blue-600"
                />
              </div>

              {/* Time of Day Dropdown */}
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">Time of Day</label>
                <select
                  value={params.time_of_day}
                  onChange={(e) => handleSelectChange('time_of_day', e.target.value)}
                  className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                >
                  <option value="morning">Morning</option>
                  <option value="afternoon">Afternoon</option>
                  <option value="evening">Evening</option>
                  <option value="night">Night</option>
                  <option value="late_night">Late Night</option>
                </select>
              </div>

              {/* Weather Dropdown */}
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">Weather</label>
                <select
                  value={params.weather}
                  onChange={(e) => handleSelectChange('weather', e.target.value)}
                  className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                >
                  <option value="clear">Clear</option>
                  <option value="rain">Rain</option>
                  <option value="snow">Snow</option>
                  <option value="fog">Fog</option>
                  <option value="storm">Storm</option>
                </select>
              </div>
            </div>
          </div>

          {/* Safety Events Card */}
          <div className="bg-white dark:bg-gray-800 rounded-xl shadow-lg p-6">
            <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-6">Safety Events</h2>
            
            <div className="space-y-6">
              {/* Rapid Acceleration Count Slider */}
              <div>
                <div className="flex justify-between items-center mb-2">
                  <label className="text-sm font-medium text-gray-700 dark:text-gray-300">Rapid Acceleration Count</label>
                  <span className="text-lg font-semibold text-gray-900 dark:text-white">{params.rapid_acceleration_count}</span>
                </div>
                <input
                  type="range"
                  min="0"
                  max="20"
                  step="1"
                  value={params.rapid_acceleration_count}
                  onChange={(e) => handleSliderChange('rapid_acceleration_count', parseInt(e.target.value))}
                  className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer accent-blue-600"
                />
              </div>

              {/* Sharp Turn Count Slider */}
              <div>
                <div className="flex justify-between items-center mb-2">
                  <label className="text-sm font-medium text-gray-700 dark:text-gray-300">Sharp Turn Count</label>
                  <span className="text-lg font-semibold text-gray-900 dark:text-white">{params.sharp_turn_count}</span>
                </div>
                <input
                  type="range"
                  min="0"
                  max="20"
                  step="1"
                  value={params.sharp_turn_count}
                  onChange={(e) => handleSliderChange('sharp_turn_count', parseInt(e.target.value))}
                  className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer accent-blue-600"
                />
              </div>

              {/* Speeding Incidents Slider */}
              <div>
                <div className="flex justify-between items-center mb-2">
                  <label className="text-sm font-medium text-gray-700 dark:text-gray-300">Speeding Incidents</label>
                  <span className="text-lg font-semibold text-gray-900 dark:text-white">{params.speeding_incidents}</span>
                </div>
                <input
                  type="range"
                  min="0"
                  max="20"
                  step="1"
                  value={params.speeding_incidents}
                  onChange={(e) => handleSliderChange('speeding_incidents', parseInt(e.target.value))}
                  className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer accent-blue-600"
                />
              </div>
            </div>
          </div>
        </div>

        {/* Right Side - Simulate Trip Panel */}
        <div className="lg:col-span-1">
          <div className="bg-gradient-to-br from-blue-500 to-blue-600 rounded-xl shadow-lg p-6 text-white sticky top-6">
            <button
              onClick={handleSimulate}
              disabled={loading}
              className="w-full flex items-center justify-center gap-2 bg-white text-blue-600 py-3 px-4 rounded-lg font-semibold hover:bg-blue-50 disabled:opacity-50 disabled:cursor-not-allowed transition-colors mb-6"
            >
              {loading ? (
                <>
                  <div className="w-5 h-5 border-2 border-blue-600 border-t-transparent rounded-full animate-spin" />
                  Simulating...
                </>
              ) : (
                <>
                  <BoltIcon className="w-5 h-5" />
                  Simulate Trip
                </>
              )}
            </button>

            {result ? (
              <div className="space-y-4">
                <div className="text-center">
                  <p className="text-sm text-blue-100 mb-2">Estimated Trip Score</p>
                  <p className="text-6xl font-bold mb-2">{result.trip_score || result.safety_score || 100}</p>
                  <div className={`inline-block px-3 py-1 rounded-full text-xs font-semibold ${riskInfo.bgColor} ${riskInfo.color}`}>
                    {result.risk_level || riskInfo.level}
                  </div>
                </div>
              </div>
            ) : (
              <div className="text-center">
                <p className="text-sm text-blue-100 mb-2">Estimated Trip Score</p>
                <p className="text-6xl font-bold mb-2">100</p>
                <div className="inline-block px-3 py-1 rounded-full text-xs font-semibold bg-green-100 text-green-600">
                  LOW
                </div>
              </div>
            )}

            {/* Summary */}
            <div className="mt-6 pt-6 border-t border-white/20 space-y-3">
              <div className="flex justify-between items-center">
                <span className="text-sm text-blue-100">Distance</span>
                <span className="text-sm font-semibold">{params.distance_miles} mi</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-sm text-blue-100">Duration</span>
                <span className="text-sm font-semibold">{params.duration_minutes} min</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-sm text-blue-100">Safety Events</span>
                <span className="text-sm font-semibold">{totalSafetyEvents}</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
