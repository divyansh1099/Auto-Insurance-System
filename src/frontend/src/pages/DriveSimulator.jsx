import { useState, useMemo } from 'react'
import { useQuery, useMutation } from 'react-query'
import { simulatorAPI, driverAPI, adminAPI, authAPI } from '../services/api'
import {
  BoltIcon,
  TruckIcon,
  CloudIcon,
  SunIcon,
  MoonIcon,
  ClockIcon,
  MapPinIcon,
  ExclamationTriangleIcon,
  ChartBarIcon,
  SparklesIcon
} from '@heroicons/react/24/outline'

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
    { retry: false, enabled: false }
  )

  const { data: vehiclesData } = useQuery(
    ['vehicles'],
    () => adminAPI.listVehicles(0, 100),
    { retry: false, enabled: false }
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
    if (score >= 80) return { level: 'LOW', color: 'text-green-600', bgColor: 'bg-green-100 dark:bg-green-900/30', borderColor: 'border-green-500' }
    if (score >= 60) return { level: 'MEDIUM', color: 'text-yellow-600', bgColor: 'bg-yellow-100 dark:bg-yellow-900/30', borderColor: 'border-yellow-500' }
    return { level: 'HIGH', color: 'text-red-600', bgColor: 'bg-red-100 dark:bg-red-900/30', borderColor: 'border-red-500' }
  }

  const riskInfo = result ? getRiskLevel(result.trip_score || result.safety_score || 100) : getRiskLevel(100)

  // Weather icons
  const getWeatherIcon = (weather) => {
    switch (weather) {
      case 'clear': return <SunIcon className="w-5 h-5" />
      case 'rain': case 'storm': return <CloudIcon className="w-5 h-5" />
      default: return <CloudIcon className="w-5 h-5" />
    }
  }

  // Time of day icons
  const getTimeIcon = (time) => {
    if (time === 'night' || time === 'late_night') return <MoonIcon className="w-5 h-5" />
    return <SunIcon className="w-5 h-5" />
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-cyan-50 via-blue-50 via-indigo-50 to-purple-50 dark:from-gray-900 dark:via-gray-900 dark:to-gray-800 relative overflow-hidden transition-colors duration-200">
      {/* Animated Background Elements */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        <div className="absolute top-1/4 left-1/4 w-96 h-96 bg-cyan-200 dark:bg-cyan-900 rounded-full mix-blend-multiply dark:mix-blend-screen filter blur-3xl opacity-20 animate-blob" />
        <div className="absolute top-1/3 right-1/4 w-96 h-96 bg-violet-200 dark:bg-violet-900 rounded-full mix-blend-multiply dark:mix-blend-screen filter blur-3xl opacity-20 animate-blob animation-delay-2000" />
        <div className="absolute bottom-1/4 left-1/3 w-96 h-96 bg-fuchsia-200 dark:bg-fuchsia-900 rounded-full mix-blend-multiply dark:mix-blend-screen filter blur-3xl opacity-20 animate-blob animation-delay-4000" />
      </div>

      <div className="relative z-10 space-y-6 p-6">
        {/* Header */}
        <div className="bg-white/80 dark:bg-gray-800/80 backdrop-blur-xl rounded-2xl shadow-lg border border-white/30 dark:border-gray-700/30 p-6 transition-colors duration-200">
          <div className="flex items-center gap-3">
            <div className="w-12 h-12 bg-gradient-to-br from-blue-500 to-purple-600 rounded-xl flex items-center justify-center">
              <TruckIcon className="w-7 h-7 text-white" />
            </div>
            <div>
              <h1 className="text-3xl md:text-4xl font-bold bg-gradient-to-r from-cyan-600 via-blue-600 to-purple-600 dark:from-cyan-400 dark:via-blue-400 dark:to-purple-400 bg-clip-text text-transparent">Drive Simulator</h1>
              <p className="text-gray-600 dark:text-gray-400 mt-1 text-lg">Create and test driving scenarios with real-time scoring</p>
            </div>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Left Side - Input Cards */}
          <div className="lg:col-span-2 space-y-6">
            {/* Select Driver & Vehicle Card */}
            <div className="bg-white/90 dark:bg-gray-800/90 backdrop-blur-xl rounded-2xl shadow-lg border border-white/50 dark:border-gray-700/50 p-6 transition-all duration-200 hover:shadow-xl">
              <div className="flex items-center gap-2 mb-4">
                <div className="w-8 h-8 bg-gradient-to-br from-blue-500 to-blue-600 rounded-lg flex items-center justify-center">
                  <TruckIcon className="w-5 h-5 text-white" />
                </div>
                <h2 className="text-xl font-semibold text-gray-900 dark:text-white">Select Driver & Vehicle</h2>
              </div>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">Driver</label>
                  <select
                    value={params.driver_id}
                    onChange={(e) => handleSelectChange('driver_id', e.target.value)}
                    className="w-full px-4 py-3 border border-gray-300 dark:border-gray-600 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-transparent bg-white dark:bg-gray-700 text-gray-900 dark:text-white transition-all"
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
                    className="w-full px-4 py-3 border border-gray-300 dark:border-gray-600 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-transparent bg-white dark:bg-gray-700 text-gray-900 dark:text-white transition-all"
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
            <div className="bg-white/90 dark:bg-gray-800/90 backdrop-blur-xl rounded-2xl shadow-lg border border-white/50 dark:border-gray-700/50 p-6 transition-all duration-200 hover:shadow-xl">
              <div className="flex items-center gap-2 mb-6">
                <div className="w-8 h-8 bg-gradient-to-br from-purple-500 to-pink-600 rounded-lg flex items-center justify-center">
                  <MapPinIcon className="w-5 h-5 text-white" />
                </div>
                <h2 className="text-xl font-semibold text-gray-900 dark:text-white">Trip Parameters</h2>
              </div>

              {error && (
                <div className="mb-4 p-4 bg-red-50 dark:bg-red-900/20 border-l-4 border-red-500 text-red-700 dark:text-red-400 rounded-lg">
                  <div className="flex items-center gap-2">
                    <ExclamationTriangleIcon className="w-5 h-5" />
                    <span>{error}</span>
                  </div>
                </div>
              )}

              <div className="space-y-6">
                {/* Distance Slider */}
                <div className="group">
                  <div className="flex justify-between items-center mb-3">
                    <label className="text-sm font-medium text-gray-700 dark:text-gray-300 flex items-center gap-2">
                      <MapPinIcon className="w-4 h-4 text-blue-500" />
                      Distance
                    </label>
                    <div className="px-3 py-1 bg-blue-50 dark:bg-blue-900/30 rounded-lg">
                      <span className="text-lg font-bold text-blue-600 dark:text-blue-400">{params.distance_miles}</span>
                      <span className="text-sm text-gray-600 dark:text-gray-400 ml-1">mi</span>
                    </div>
                  </div>
                  <input
                    type="range"
                    min="0"
                    max="500"
                    step="1"
                    value={params.distance_miles}
                    onChange={(e) => handleSliderChange('distance_miles', e.target.value)}
                    className="w-full h-3 bg-gradient-to-r from-blue-200 to-blue-100 dark:from-blue-900/50 dark:to-blue-800/50 rounded-full appearance-none cursor-pointer accent-blue-600 transition-all hover:scale-y-110"
                  />
                </div>

                {/* Duration Slider */}
                <div className="group">
                  <div className="flex justify-between items-center mb-3">
                    <label className="text-sm font-medium text-gray-700 dark:text-gray-300 flex items-center gap-2">
                      <ClockIcon className="w-4 h-4 text-purple-500" />
                      Duration
                    </label>
                    <div className="px-3 py-1 bg-purple-50 dark:bg-purple-900/30 rounded-lg">
                      <span className="text-lg font-bold text-purple-600 dark:text-purple-400">{params.duration_minutes}</span>
                      <span className="text-sm text-gray-600 dark:text-gray-400 ml-1">min</span>
                    </div>
                  </div>
                  <input
                    type="range"
                    min="0"
                    max="300"
                    step="1"
                    value={params.duration_minutes}
                    onChange={(e) => handleSliderChange('duration_minutes', e.target.value)}
                    className="w-full h-3 bg-gradient-to-r from-purple-200 to-purple-100 dark:from-purple-900/50 dark:to-purple-800/50 rounded-full appearance-none cursor-pointer accent-purple-600 transition-all hover:scale-y-110"
                  />
                </div>

                {/* Average Speed Slider */}
                <div className="group">
                  <div className="flex justify-between items-center mb-3">
                    <label className="text-sm font-medium text-gray-700 dark:text-gray-300 flex items-center gap-2">
                      <ChartBarIcon className="w-4 h-4 text-green-500" />
                      Average Speed
                    </label>
                    <div className="px-3 py-1 bg-green-50 dark:bg-green-900/30 rounded-lg">
                      <span className="text-lg font-bold text-green-600 dark:text-green-400">{params.average_speed_mph}</span>
                      <span className="text-sm text-gray-600 dark:text-gray-400 ml-1">mph</span>
                    </div>
                  </div>
                  <input
                    type="range"
                    min="0"
                    max="100"
                    step="1"
                    value={params.average_speed_mph}
                    onChange={(e) => handleSliderChange('average_speed_mph', e.target.value)}
                    className="w-full h-3 bg-gradient-to-r from-green-200 to-green-100 dark:from-green-900/50 dark:to-green-800/50 rounded-full appearance-none cursor-pointer accent-green-600 transition-all hover:scale-y-110"
                  />
                </div>

                {/* Max Speed Slider */}
                <div className="group">
                  <div className="flex justify-between items-center mb-3">
                    <label className="text-sm font-medium text-gray-700 dark:text-gray-300 flex items-center gap-2">
                      <BoltIcon className="w-4 h-4 text-orange-500" />
                      Max Speed
                    </label>
                    <div className="px-3 py-1 bg-orange-50 dark:bg-orange-900/30 rounded-lg">
                      <span className="text-lg font-bold text-orange-600 dark:text-orange-400">{params.max_speed_mph}</span>
                      <span className="text-sm text-gray-600 dark:text-gray-400 ml-1">mph</span>
                    </div>
                  </div>
                  <input
                    type="range"
                    min="0"
                    max="120"
                    step="1"
                    value={params.max_speed_mph}
                    onChange={(e) => handleSliderChange('max_speed_mph', e.target.value)}
                    className="w-full h-3 bg-gradient-to-r from-orange-200 to-orange-100 dark:from-orange-900/50 dark:to-orange-800/50 rounded-full appearance-none cursor-pointer accent-orange-600 transition-all hover:scale-y-110"
                  />
                </div>

                {/* Time & Weather Grid */}
                <div className="grid grid-cols-2 gap-4 pt-2">
                  {/* Time of Day */}
                  <div>
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2 flex items-center gap-2">
                      {getTimeIcon(params.time_of_day)}
                      Time of Day
                    </label>
                    <select
                      value={params.time_of_day}
                      onChange={(e) => handleSelectChange('time_of_day', e.target.value)}
                      className="w-full px-4 py-3 border border-gray-300 dark:border-gray-600 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-transparent bg-white dark:bg-gray-700 text-gray-900 dark:text-white transition-all"
                    >
                      <option value="morning">🌅 Morning</option>
                      <option value="afternoon">☀️ Afternoon</option>
                      <option value="evening">🌆 Evening</option>
                      <option value="night">🌙 Night</option>
                      <option value="late_night">🌃 Late Night</option>
                    </select>
                  </div>

                  {/* Weather */}
                  <div>
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2 flex items-center gap-2">
                      {getWeatherIcon(params.weather)}
                      Weather
                    </label>
                    <select
                      value={params.weather}
                      onChange={(e) => handleSelectChange('weather', e.target.value)}
                      className="w-full px-4 py-3 border border-gray-300 dark:border-gray-600 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-transparent bg-white dark:bg-gray-700 text-gray-900 dark:text-white transition-all"
                    >
                      <option value="clear">☀️ Clear</option>
                      <option value="rain">🌧️ Rain</option>
                      <option value="snow">❄️ Snow</option>
                      <option value="fog">🌫️ Fog</option>
                      <option value="storm">⛈️ Storm</option>
                    </select>
                  </div>
                </div>
              </div>
            </div>

            {/* Safety Events Card */}
            <div className="bg-white/90 dark:bg-gray-800/90 backdrop-blur-xl rounded-2xl shadow-lg border border-white/50 dark:border-gray-700/50 p-6 transition-all duration-200 hover:shadow-xl">
              <div className="flex items-center gap-2 mb-6">
                <div className="w-8 h-8 bg-gradient-to-br from-red-500 to-orange-600 rounded-lg flex items-center justify-center">
                  <ExclamationTriangleIcon className="w-5 h-5 text-white" />
                </div>
                <h2 className="text-xl font-semibold text-gray-900 dark:text-white">Safety Events</h2>
              </div>

              <div className="grid grid-cols-2 gap-6">
                {/* Hard Braking */}
                <div className="group">
                  <div className="flex justify-between items-center mb-3">
                    <label className="text-sm font-medium text-gray-700 dark:text-gray-300">Hard Braking</label>
                    <div className="px-3 py-1 bg-red-50 dark:bg-red-900/30 rounded-lg">
                      <span className="text-lg font-bold text-red-600 dark:text-red-400">{params.hard_braking_count}</span>
                    </div>
                  </div>
                  <input
                    type="range"
                    min="0"
                    max="20"
                    step="1"
                    value={params.hard_braking_count}
                    onChange={(e) => handleSliderChange('hard_braking_count', parseInt(e.target.value))}
                    className="w-full h-3 bg-gradient-to-r from-red-200 to-red-100 dark:from-red-900/50 dark:to-red-800/50 rounded-full appearance-none cursor-pointer accent-red-600 transition-all hover:scale-y-110"
                  />
                </div>

                {/* Rapid Acceleration */}
                <div className="group">
                  <div className="flex justify-between items-center mb-3">
                    <label className="text-sm font-medium text-gray-700 dark:text-gray-300">Rapid Accel</label>
                    <div className="px-3 py-1 bg-yellow-50 dark:bg-yellow-900/30 rounded-lg">
                      <span className="text-lg font-bold text-yellow-600 dark:text-yellow-400">{params.rapid_acceleration_count}</span>
                    </div>
                  </div>
                  <input
                    type="range"
                    min="0"
                    max="20"
                    step="1"
                    value={params.rapid_acceleration_count}
                    onChange={(e) => handleSliderChange('rapid_acceleration_count', parseInt(e.target.value))}
                    className="w-full h-3 bg-gradient-to-r from-yellow-200 to-yellow-100 dark:from-yellow-900/50 dark:to-yellow-800/50 rounded-full appearance-none cursor-pointer accent-yellow-600 transition-all hover:scale-y-110"
                  />
                </div>

                {/* Sharp Turns */}
                <div className="group">
                  <div className="flex justify-between items-center mb-3">
                    <label className="text-sm font-medium text-gray-700 dark:text-gray-300">Sharp Turns</label>
                    <div className="px-3 py-1 bg-orange-50 dark:bg-orange-900/30 rounded-lg">
                      <span className="text-lg font-bold text-orange-600 dark:text-orange-400">{params.sharp_turn_count}</span>
                    </div>
                  </div>
                  <input
                    type="range"
                    min="0"
                    max="20"
                    step="1"
                    value={params.sharp_turn_count}
                    onChange={(e) => handleSliderChange('sharp_turn_count', parseInt(e.target.value))}
                    className="w-full h-3 bg-gradient-to-r from-orange-200 to-orange-100 dark:from-orange-900/50 dark:to-orange-800/50 rounded-full appearance-none cursor-pointer accent-orange-600 transition-all hover:scale-y-110"
                  />
                </div>

                {/* Speeding */}
                <div className="group">
                  <div className="flex justify-between items-center mb-3">
                    <label className="text-sm font-medium text-gray-700 dark:text-gray-300">Speeding</label>
                    <div className="px-3 py-1 bg-pink-50 dark:bg-pink-900/30 rounded-lg">
                      <span className="text-lg font-bold text-pink-600 dark:text-pink-400">{params.speeding_incidents}</span>
                    </div>
                  </div>
                  <input
                    type="range"
                    min="0"
                    max="20"
                    step="1"
                    value={params.speeding_incidents}
                    onChange={(e) => handleSliderChange('speeding_incidents', parseInt(e.target.value))}
                    className="w-full h-3 bg-gradient-to-r from-pink-200 to-pink-100 dark:from-pink-900/50 dark:to-pink-800/50 rounded-full appearance-none cursor-pointer accent-pink-600 transition-all hover:scale-y-110"
                  />
                </div>
              </div>
            </div>
          </div>

          {/* Right Side - Results Panel */}
          <div className="lg:col-span-1">
            <div className="sticky top-6 space-y-4">
              {/* Simulate Button */}
              <button
                onClick={handleSimulate}
                disabled={loading}
                className="w-full bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700 text-white py-4 px-6 rounded-2xl font-bold text-lg shadow-lg hover:shadow-xl disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-200 transform hover:scale-105 active:scale-95 flex items-center justify-center gap-3"
              >
                {loading ? (
                  <>
                    <div className="w-6 h-6 border-3 border-white border-t-transparent rounded-full animate-spin" />
                    Simulating...
                  </>
                ) : (
                  <>
                    <SparklesIcon className="w-6 h-6" />
                    Simulate Trip
                  </>
                )}
              </button>

              {/* Results Card */}
              <div className="bg-gradient-to-br from-blue-500 to-purple-600 rounded-2xl shadow-lg p-6 text-white">
                <div className="text-center mb-6">
                  <p className="text-sm text-blue-100 mb-2 flex items-center justify-center gap-2">
                    <ChartBarIcon className="w-4 h-4" />
                    Estimated Trip Score
                  </p>
                  <div className="relative">
                    <p className="text-7xl font-bold mb-3 drop-shadow-lg">
                      {result ? (result.trip_score || result.safety_score || 100) : 100}
                    </p>
                    <div className={`inline-flex items-center gap-2 px-4 py-2 rounded-full text-sm font-bold ${riskInfo.bgColor} ${riskInfo.color} border-2 ${riskInfo.borderColor} shadow-lg`}>
                      <div className={`w-2 h-2 rounded-full ${riskInfo.color.replace('text-', 'bg-')} animate-pulse`} />
                      {result?.risk_level || riskInfo.level}
                    </div>
                  </div>
                </div>

                {/* Trip Summary */}
                <div className="space-y-3 pt-6 border-t border-white/20">
                  <div className="flex justify-between items-center p-3 bg-white/10 rounded-xl backdrop-blur-sm">
                    <span className="text-sm text-blue-100 flex items-center gap-2">
                      <MapPinIcon className="w-4 h-4" />
                      Distance
                    </span>
                    <span className="text-lg font-bold">{params.distance_miles} mi</span>
                  </div>
                  <div className="flex justify-between items-center p-3 bg-white/10 rounded-xl backdrop-blur-sm">
                    <span className="text-sm text-blue-100 flex items-center gap-2">
                      <ClockIcon className="w-4 h-4" />
                      Duration
                    </span>
                    <span className="text-lg font-bold">{params.duration_minutes} min</span>
                  </div>
                  <div className="flex justify-between items-center p-3 bg-white/10 rounded-xl backdrop-blur-sm">
                    <span className="text-sm text-blue-100 flex items-center gap-2">
                      <ExclamationTriangleIcon className="w-4 h-4" />
                      Safety Events
                    </span>
                    <span className="text-lg font-bold">{totalSafetyEvents}</span>
                  </div>
                  <div className="flex justify-between items-center p-3 bg-white/10 rounded-xl backdrop-blur-sm">
                    <span className="text-sm text-blue-100 flex items-center gap-2">
                      <BoltIcon className="w-4 h-4" />
                      Avg Speed
                    </span>
                    <span className="text-lg font-bold">{params.average_speed_mph} mph</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
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
        
        /* Custom slider styling */
        input[type="range"]::-webkit-slider-thumb {
          appearance: none;
          width: 24px;
          height: 24px;
          border-radius: 50%;
          background: white;
          cursor: pointer;
          box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1), 0 0 0 4px rgba(59, 130, 246, 0.3);
          transition: all 0.2s;
        }
        
        input[type="range"]::-webkit-slider-thumb:hover {
          transform: scale(1.2);
          box-shadow: 0 6px 8px rgba(0, 0, 0, 0.15), 0 0 0 6px rgba(59, 130, 246, 0.4);
        }
        
        input[type="range"]::-moz-range-thumb {
          width: 24px;
          height: 24px;
          border-radius: 50%;
          background: white;
          cursor: pointer;
          border: none;
          box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1), 0 0 0 4px rgba(59, 130, 246, 0.3);
          transition: all 0.2s;
        }
        
        input[type="range"]::-moz-range-thumb:hover {
          transform: scale(1.2);
          box-shadow: 0 6px 8px rgba(0, 0, 0, 0.15), 0 0 0 6px rgba(59, 130, 246, 0.4);
        }
      `}</style>
    </div>
  )
}
