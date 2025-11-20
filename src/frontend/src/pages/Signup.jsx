import { useState } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { authAPI } from '../services/api'
import {
  CheckCircleIcon,
  ShieldCheckIcon,
  ClockIcon,
  CurrencyDollarIcon,
  UserIcon,
  IdentificationIcon,
  MapPinIcon,
  TruckIcon,
  ArrowRightIcon,
  ArrowLeftIcon,
  SparklesIcon,
  LockClosedIcon,
  HomeIcon
} from '@heroicons/react/24/outline'

// InputField component moved outside to prevent recreation on each render
const InputField = ({ label, name, type = 'text', placeholder, required = false, icon: Icon, formData, focusedField, setFocusedField, handleChange, color = 'cyan', ...props }) => {
  const colorClasses = {
    cyan: {
      border: 'border-cyan-500',
      bg: 'bg-gradient-to-r from-cyan-50 to-blue-50',
      shadow: 'shadow-lg shadow-cyan-500/20',
      ring: 'focus:ring-cyan-500/30',
      icon: 'text-cyan-600',
      hover: 'hover:border-cyan-300'
    },
    purple: {
      border: 'border-purple-500',
      bg: 'bg-gradient-to-r from-purple-50 to-pink-50',
      shadow: 'shadow-lg shadow-purple-500/20',
      ring: 'focus:ring-purple-500/30',
      icon: 'text-purple-600',
      hover: 'hover:border-purple-300'
    },
    emerald: {
      border: 'border-emerald-500',
      bg: 'bg-gradient-to-r from-emerald-50 to-teal-50',
      shadow: 'shadow-lg shadow-emerald-500/20',
      ring: 'focus:ring-emerald-500/30',
      icon: 'text-emerald-600',
      hover: 'hover:border-emerald-300'
    },
    amber: {
      border: 'border-amber-500',
      bg: 'bg-gradient-to-r from-amber-50 to-orange-50',
      shadow: 'shadow-lg shadow-amber-500/20',
      ring: 'focus:ring-amber-500/30',
      icon: 'text-amber-600',
      hover: 'hover:border-amber-300'
    }
  }
  
  const colors = colorClasses[color] || colorClasses.cyan

  return (
    <div className="space-y-2">
      <label className="block text-sm font-bold text-gray-700 flex items-center gap-2">
        {Icon && <Icon className={`w-4 h-4 ${colors.icon}`} />}
        {label} {required && <span className="text-red-500">*</span>}
      </label>
      <div className="relative group">
        {Icon && (
          <div className={`absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none transition-all duration-300 ${
            focusedField === name ? `${colors.icon} scale-110` : 'text-gray-400'
          }`}>
            <Icon className="w-5 h-5" />
          </div>
        )}
        <input
          type={type}
          name={name}
          value={formData[name] || ''}
          onChange={handleChange}
          onFocus={() => setFocusedField(name)}
          onBlur={() => setFocusedField(null)}
          placeholder={placeholder}
          className={`w-full ${Icon ? 'pl-12' : 'pl-4'} pr-4 py-4 border-2 rounded-xl transition-all duration-300 font-medium ${
            focusedField === name
              ? `${colors.border} ${colors.bg} ${colors.shadow} focus:ring-4 ${colors.ring}`
              : `border-gray-200 bg-white ${colors.hover} hover:shadow-md focus:${colors.border} focus:ring-4 ${colors.ring}`
          }`}
          required={required}
          {...props}
        />
      </div>
    </div>
  )
}

export default function Signup() {
  const navigate = useNavigate()
  const [currentStep, setCurrentStep] = useState(1)
  const [formData, setFormData] = useState({
    first_name: '',
    last_name: '',
    email: '',
    phone: '',
    date_of_birth: '',
    license_number: '',
    license_state: '',
    years_licensed: '',
    address: '',
    city: '',
    state: '',
    zip_code: '',
    vehicle_make: '',
    vehicle_model: '',
    vehicle_year: '',
    annual_mileage: '',
    coverage_type: 'full'
  })
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const [quoteResult, setQuoteResult] = useState(null)
  const [focusedField, setFocusedField] = useState(null)

  const totalSteps = 4

  const handleChange = (e) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value
    })
  }

  const validateStep = (step) => {
    switch(step) {
      case 1:
        return formData.first_name && formData.last_name && formData.email && formData.phone && formData.date_of_birth
      case 2:
        return formData.license_number && formData.license_state && formData.years_licensed
      case 3:
        return formData.address && formData.city && formData.state && formData.zip_code
      default:
        return true
    }
  }

  const nextStep = () => {
    if (validateStep(currentStep) && currentStep < totalSteps) {
      setCurrentStep(currentStep + 1)
      setError('')
    } else if (!validateStep(currentStep)) {
      setError('Please fill in all required fields')
    }
  }

  const prevStep = () => {
    if (currentStep > 1) {
      setCurrentStep(currentStep - 1)
      setError('')
    }
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')
    setLoading(true)

    try {
      const submitData = {
        ...formData,
        date_of_birth: formData.date_of_birth,
        years_licensed: parseInt(formData.years_licensed) || 0,
        vehicle_year: formData.vehicle_year ? parseInt(formData.vehicle_year) : null,
        annual_mileage: formData.annual_mileage ? parseInt(formData.annual_mileage) : null,
      }

      const response = await authAPI.requestQuote(submitData)
      setQuoteResult(response.data)
    } catch (err) {
      console.error('Quote request error:', err)
      const errorMessage = err.response?.data?.detail || err.response?.data?.message || err.message || 'Failed to submit quote request. Please try again.'
      setError(errorMessage)
    } finally {
      setLoading(false)
    }
  }

  if (quoteResult) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-cyan-50 via-blue-50 to-purple-50 dark:from-gray-900 dark:via-gray-900 dark:to-gray-800 transition-colors duration-200 flex items-center justify-center px-4 py-12">
        <div className="max-w-2xl w-full bg-white/90 dark:bg-gray-800/90 backdrop-blur-xl rounded-3xl shadow-2xl border border-white/20 p-8 md:p-12">
          <div className="text-center mb-8">
            <div className="inline-flex p-4 bg-gradient-to-br from-green-500 to-emerald-500 rounded-full mb-4 animate-bounce">
              <CheckCircleIcon className="w-12 h-12 text-white" />
            </div>
            <h1 className="text-3xl md:text-4xl font-bold bg-gradient-to-r from-cyan-600 via-blue-600 to-purple-600 bg-clip-text text-transparent mb-2">
              Quote Request Received!
            </h1>
            <p className="text-gray-600 dark:text-gray-400">
              Quote ID: <span className="font-semibold text-gray-900 dark:text-white">{quoteResult.quote_id}</span>
            </p>
          </div>

          <div className="bg-gradient-to-br from-cyan-50 to-blue-50 rounded-2xl p-8 mb-6 border-2 border-cyan-200 shadow-lg">
            <div className="flex items-center gap-3 mb-6">
              <div className="p-3 bg-gradient-to-br from-cyan-500 to-blue-500 rounded-xl">
                <CurrencyDollarIcon className="w-8 h-8 text-white" />
              </div>
              <h2 className="text-2xl font-bold text-gray-900 dark:text-white">Your Estimated Premium</h2>
            </div>
            <div className="grid grid-cols-2 gap-6 mb-6">
              <div className="bg-white dark:bg-gray-800 rounded-xl p-6 shadow-md">
                <div className="text-sm text-gray-600 mb-2">Monthly Premium</div>
                <div className="text-4xl font-bold bg-gradient-to-r from-cyan-600 to-blue-600 bg-clip-text text-transparent">
                  ${quoteResult.estimated_monthly_premium.toFixed(2)}
                </div>
              </div>
              <div className="bg-white dark:bg-gray-800 rounded-xl p-6 shadow-md">
                <div className="text-sm text-gray-600 mb-2">Annual Premium</div>
                <div className="text-4xl font-bold bg-gradient-to-r from-purple-600 to-pink-600 bg-clip-text text-transparent">
                  ${quoteResult.estimated_annual_premium.toFixed(2)}
                </div>
              </div>
            </div>
            <div className="flex items-center gap-3 text-emerald-700 bg-emerald-100 rounded-xl p-4 border border-emerald-200">
              <ShieldCheckIcon className="w-6 h-6" />
              <span className="font-bold text-lg">
                Save up to {quoteResult.discount_percentage}% vs traditional insurance
              </span>
            </div>
          </div>

          <div className="bg-gradient-to-r from-blue-50 to-cyan-50 rounded-2xl p-6 mb-6 border border-blue-200">
            <div className="flex items-start gap-4">
              <div className="p-3 bg-gradient-to-br from-blue-500 to-cyan-500 rounded-xl flex-shrink-0">
                <ClockIcon className="w-6 h-6 text-white" />
              </div>
              <div>
                <h3 className="font-bold text-gray-900 mb-2 text-lg">What's Next?</h3>
                <p className="text-gray-700 leading-relaxed">
                  {quoteResult.message}
                </p>
              </div>
            </div>
          </div>

          <div className="flex flex-col sm:flex-row gap-4">
            <button
              onClick={() => {
                setQuoteResult(null)
                setCurrentStep(1)
                setFormData({
                  first_name: '',
                  last_name: '',
                  email: '',
                  phone: '',
                  date_of_birth: '',
                  license_number: '',
                  license_state: '',
                  years_licensed: '',
                  address: '',
                  city: '',
                  state: '',
                  zip_code: '',
                  vehicle_make: '',
                  vehicle_model: '',
                  vehicle_year: '',
                  annual_mileage: '',
                  coverage_type: 'full'
                })
              }}
              className="flex-1 px-6 py-3 bg-gray-100 text-gray-700 rounded-xl font-semibold hover:bg-gray-200 transition-all"
            >
              Request Another Quote
            </button>
            <Link
              to="/login"
              className="flex-1 px-6 py-3 bg-gradient-to-r from-cyan-600 to-blue-600 text-white rounded-xl font-semibold hover:from-cyan-700 hover:to-blue-700 transition-all text-center shadow-lg hover:shadow-xl"
            >
              Sign In
            </Link>
          </div>
        </div>
      </div>
    )
  }


  return (
    <div className="min-h-screen bg-gradient-to-br from-cyan-50 via-blue-50 via-indigo-50 to-purple-50 flex items-center justify-center px-4 py-12 relative overflow-hidden">
      {/* Enhanced Animated Background */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        <div className="absolute top-1/4 left-1/4 w-96 h-96 bg-cyan-200 rounded-full mix-blend-multiply filter blur-3xl opacity-20 animate-blob" />
        <div className="absolute top-1/3 right-1/4 w-96 h-96 bg-violet-200 rounded-full mix-blend-multiply filter blur-3xl opacity-20 animate-blob animation-delay-2000" />
        <div className="absolute bottom-1/4 left-1/3 w-96 h-96 bg-fuchsia-200 rounded-full mix-blend-multiply filter blur-3xl opacity-20 animate-blob animation-delay-4000" />
        <div className="absolute top-1/2 right-1/3 w-80 h-80 bg-emerald-200 rounded-full mix-blend-multiply filter blur-3xl opacity-15 animate-blob animation-delay-6000" />
        {/* Floating decorative elements */}
        <div className="absolute top-20 left-20 w-3 h-3 bg-yellow-200 rounded-full animate-float opacity-40" />
        <div className="absolute top-40 right-32 w-4 h-4 bg-pink-200 rounded-full animate-float-delay opacity-40" />
        <div className="absolute bottom-32 left-40 w-3 h-3 bg-cyan-200 rounded-full animate-float-delay-2 opacity-40" />
      </div>

      {/* Homepage Button */}
      <Link
        to="/home"
        className="absolute top-6 left-6 z-10 flex items-center gap-2 px-5 py-2.5 bg-white/90 dark:bg-gray-800/90 backdrop-blur-md rounded-full shadow-xl hover:shadow-2xl border-2 border-white/50 hover:border-cyan-300 transition-all group transform hover:scale-105"
      >
        <HomeIcon className="w-5 h-5 text-cyan-600 group-hover:text-purple-600 transition-colors" />
        <span className="text-sm font-semibold bg-gradient-to-r from-cyan-600 to-purple-600 bg-clip-text text-transparent">Home</span>
      </Link>

      <div className="max-w-4xl w-full relative z-10">
        {/* Enhanced Progress Bar */}
        <div className="mb-8">
          <div className="flex items-center justify-between mb-4">
            <h1 className="text-4xl md:text-5xl font-bold bg-gradient-to-r from-cyan-600 via-blue-600 to-purple-600 bg-clip-text text-transparent">
              Get Your Personalized Quote
            </h1>
            <div className="px-4 py-2 bg-white/90 dark:bg-gray-800/90 backdrop-blur-md rounded-full border-2 border-white/50 shadow-lg">
              <span className="text-sm font-bold bg-gradient-to-r from-cyan-600 to-purple-600 bg-clip-text text-transparent">
                Step {currentStep} of {totalSteps}
              </span>
            </div>
          </div>
          <div className="w-full bg-white/30 dark:bg-gray-800/30 backdrop-blur-sm rounded-full h-3 overflow-hidden shadow-inner border-2 border-white/30">
            <div 
              className="h-full bg-gradient-to-r from-cyan-400 via-blue-400 via-purple-400 to-pink-400 rounded-full transition-all duration-500 shadow-lg relative overflow-hidden"
              style={{ width: `${(currentStep / totalSteps) * 100}%` }}
            >
              <div className="absolute inset-0 bg-gradient-to-r from-transparent via-white/30 to-transparent animate-shimmer" />
            </div>
          </div>
        </div>

        {/* Main Form Card */}
        <div className="bg-white/95 dark:bg-gray-800/95 backdrop-blur-xl rounded-3xl shadow-2xl border-2 border-white/30 p-8 md:p-10 relative overflow-hidden">
          {/* Decorative gradient overlays */}
          <div className="absolute top-0 right-0 w-96 h-96 bg-gradient-to-br from-cyan-200/20 to-purple-200/20 rounded-full blur-3xl -mr-48 -mt-48" />
          <div className="absolute bottom-0 left-0 w-80 h-80 bg-gradient-to-tr from-pink-200/20 to-rose-200/20 rounded-full blur-3xl -ml-40 -mb-40" />
          {error && (
            <div className="mb-6 p-4 bg-gradient-to-r from-red-50 to-pink-50 border-l-4 border-red-500 rounded-xl animate-shake shadow-md relative z-10">
              <div className="flex items-center gap-3">
                <div className="p-2 bg-red-500 rounded-lg">
                  <svg className="w-5 h-5 text-white" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
                  </svg>
                </div>
                <p className="text-sm font-semibold text-red-800">{error}</p>
              </div>
            </div>
          )}

          <form onSubmit={handleSubmit}>
            {/* Step 1: Personal Information */}
            {currentStep === 1 && (
              <div className="space-y-6 animate-fadeIn relative z-10">
                <div className="flex items-center gap-4 mb-8 p-4 bg-gradient-to-r from-cyan-50 via-blue-50 to-purple-50 rounded-2xl border-2 border-cyan-200/50 shadow-lg">
                  <div className="p-4 bg-gradient-to-br from-cyan-500 via-blue-500 to-purple-500 rounded-2xl shadow-lg transform hover:scale-110 transition-transform">
                    <UserIcon className="w-8 h-8 text-white" />
                  </div>
                  <div>
                    <h2 className="text-3xl font-bold bg-gradient-to-r from-cyan-600 via-blue-600 to-purple-600 bg-clip-text text-transparent">
                      Personal Information
                    </h2>
                    <p className="text-sm text-gray-600 mt-1">Tell us about yourself</p>
                  </div>
                </div>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <InputField
                    label="First Name"
                    name="first_name"
                    placeholder="John"
                    required
                    icon={UserIcon}
                    color="cyan"
                    formData={formData}
                    focusedField={focusedField}
                    setFocusedField={setFocusedField}
                    handleChange={handleChange}
                  />
                  <InputField
                    label="Last Name"
                    name="last_name"
                    placeholder="Doe"
                    required
                    icon={UserIcon}
                    color="cyan"
                    formData={formData}
                    focusedField={focusedField}
                    setFocusedField={setFocusedField}
                    handleChange={handleChange}
                  />
                  <InputField
                    label="Email"
                    name="email"
                    type="email"
                    placeholder="john.doe@example.com"
                    required
                    icon={SparklesIcon}
                    color="purple"
                    formData={formData}
                    focusedField={focusedField}
                    setFocusedField={setFocusedField}
                    handleChange={handleChange}
                  />
                  <InputField
                    label="Phone"
                    name="phone"
                    type="tel"
                    placeholder="(555) 123-4567"
                    required
                    color="purple"
                    formData={formData}
                    focusedField={focusedField}
                    setFocusedField={setFocusedField}
                    handleChange={handleChange}
                  />
                  <InputField
                    label="Date of Birth"
                    name="date_of_birth"
                    type="date"
                    required
                    color="cyan"
                    formData={formData}
                    focusedField={focusedField}
                    setFocusedField={setFocusedField}
                    handleChange={handleChange}
                  />
                </div>
              </div>
            )}

            {/* Step 2: Driver's License */}
            {currentStep === 2 && (
              <div className="space-y-6 animate-fadeIn relative z-10">
                <div className="flex items-center gap-4 mb-8 p-4 bg-gradient-to-r from-purple-50 via-pink-50 to-rose-50 rounded-2xl border-2 border-purple-200/50 shadow-lg">
                  <div className="p-4 bg-gradient-to-br from-purple-500 via-pink-500 to-rose-500 rounded-2xl shadow-lg transform hover:scale-110 transition-transform">
                    <IdentificationIcon className="w-8 h-8 text-white" />
                  </div>
                  <div>
                    <h2 className="text-3xl font-bold bg-gradient-to-r from-purple-600 via-pink-600 to-rose-600 bg-clip-text text-transparent">
                      Driver's License Information
                    </h2>
                    <p className="text-sm text-gray-600 mt-1">Your driving credentials</p>
                  </div>
                </div>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <InputField
                    label="License Number"
                    name="license_number"
                    placeholder="D1234567"
                    required
                    icon={IdentificationIcon}
                    color="purple"
                    formData={formData}
                    focusedField={focusedField}
                    setFocusedField={setFocusedField}
                    handleChange={handleChange}
                  />
                  <InputField
                    label="License State"
                    name="license_state"
                    placeholder="CA"
                    maxLength="2"
                    required
                    color="purple"
                    formData={formData}
                    focusedField={focusedField}
                    setFocusedField={setFocusedField}
                    handleChange={handleChange}
                  />
                  <InputField
                    label="Years Licensed"
                    name="years_licensed"
                    type="number"
                    min="0"
                    max="80"
                    placeholder="5"
                    required
                    color="purple"
                    formData={formData}
                    focusedField={focusedField}
                    setFocusedField={setFocusedField}
                    handleChange={handleChange}
                  />
                </div>
              </div>
            )}

            {/* Step 3: Address */}
            {currentStep === 3 && (
              <div className="space-y-6 animate-fadeIn relative z-10">
                <div className="flex items-center gap-4 mb-8 p-4 bg-gradient-to-r from-emerald-50 via-teal-50 to-cyan-50 rounded-2xl border-2 border-emerald-200/50 shadow-lg">
                  <div className="p-4 bg-gradient-to-br from-emerald-500 via-teal-500 to-cyan-500 rounded-2xl shadow-lg transform hover:scale-110 transition-transform">
                    <MapPinIcon className="w-8 h-8 text-white" />
                  </div>
                  <div>
                    <h2 className="text-3xl font-bold bg-gradient-to-r from-emerald-600 via-teal-600 to-cyan-600 bg-clip-text text-transparent">
                      Address Information
                    </h2>
                    <p className="text-sm text-gray-600 mt-1">Where you're located</p>
                  </div>
                </div>
                <div className="space-y-6">
                  <InputField
                    label="Street Address"
                    name="address"
                    placeholder="123 Main Street"
                    required
                    icon={MapPinIcon}
                    color="emerald"
                    formData={formData}
                    focusedField={focusedField}
                    setFocusedField={setFocusedField}
                    handleChange={handleChange}
                  />
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                    <InputField
                      label="City"
                      name="city"
                      placeholder="San Francisco"
                      required
                      color="emerald"
                      formData={formData}
                      focusedField={focusedField}
                      setFocusedField={setFocusedField}
                      handleChange={handleChange}
                    />
                    <InputField
                      label="State"
                      name="state"
                      placeholder="CA"
                      maxLength="2"
                      required
                      color="emerald"
                      formData={formData}
                      focusedField={focusedField}
                      setFocusedField={setFocusedField}
                      handleChange={handleChange}
                    />
                    <InputField
                      label="ZIP Code"
                      name="zip_code"
                      placeholder="94102"
                      maxLength="10"
                      required
                      color="emerald"
                      formData={formData}
                      focusedField={focusedField}
                      setFocusedField={setFocusedField}
                      handleChange={handleChange}
                    />
                  </div>
                </div>
              </div>
            )}

            {/* Step 4: Vehicle Information */}
            {currentStep === 4 && (
              <div className="space-y-6 animate-fadeIn relative z-10">
                <div className="flex items-center gap-4 mb-8 p-4 bg-gradient-to-r from-amber-50 via-orange-50 to-yellow-50 rounded-2xl border-2 border-amber-200/50 shadow-lg">
                  <div className="p-4 bg-gradient-to-br from-amber-500 via-orange-500 to-yellow-500 rounded-2xl shadow-lg transform hover:scale-110 transition-transform">
                    <TruckIcon className="w-8 h-8 text-white" />
                  </div>
                  <div>
                    <h2 className="text-3xl font-bold bg-gradient-to-r from-amber-600 via-orange-600 to-yellow-600 bg-clip-text text-transparent">
                      Vehicle Information
                    </h2>
                    <p className="text-sm text-gray-600 mt-1">Optional - helps us provide better quotes</p>
                  </div>
                </div>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                  <InputField
                    label="Make"
                    name="vehicle_make"
                    placeholder="Toyota"
                    icon={TruckIcon}
                    color="amber"
                    formData={formData}
                    focusedField={focusedField}
                    setFocusedField={setFocusedField}
                    handleChange={handleChange}
                  />
                  <InputField
                    label="Model"
                    name="vehicle_model"
                    placeholder="Camry"
                    color="amber"
                    formData={formData}
                    focusedField={focusedField}
                    setFocusedField={setFocusedField}
                    handleChange={handleChange}
                  />
                  <InputField
                    label="Year"
                    name="vehicle_year"
                    type="number"
                    min="1900"
                    max={new Date().getFullYear() + 1}
                    placeholder="2020"
                    color="amber"
                    formData={formData}
                    focusedField={focusedField}
                    setFocusedField={setFocusedField}
                    handleChange={handleChange}
                  />
                  <div className="md:col-span-2">
                    <InputField
                      label="Annual Mileage"
                      name="annual_mileage"
                      type="number"
                      min="0"
                      placeholder="12000"
                      color="amber"
                      formData={formData}
                      focusedField={focusedField}
                      setFocusedField={setFocusedField}
                      handleChange={handleChange}
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-bold text-gray-700 mb-2 flex items-center gap-2">
                      <ShieldCheckIcon className="w-4 h-4 text-amber-600" />
                      Coverage Type
                    </label>
                    <select
                      name="coverage_type"
                      value={formData.coverage_type}
                      onChange={handleChange}
                      className="w-full px-4 py-4 border-2 border-gray-200 rounded-xl focus:border-amber-500 focus:ring-4 focus:ring-amber-500/20 bg-white hover:border-amber-300 transition-all font-medium"
                    >
                      <option value="full">Full Coverage</option>
                      <option value="liability">Liability Only</option>
                      <option value="comprehensive">Comprehensive</option>
                    </select>
                  </div>
                </div>
              </div>
            )}

            {/* Navigation Buttons */}
            <div className="flex items-center justify-between mt-8 pt-6 border-t-2 border-gradient-to-r from-cyan-200 via-purple-200 to-pink-200 relative z-10">
              <button
                type="button"
                onClick={prevStep}
                disabled={currentStep === 1}
                className={`flex items-center gap-2 px-6 py-3 rounded-xl font-bold transition-all ${
                  currentStep === 1
                    ? 'text-gray-400 cursor-not-allowed'
                    : 'text-gray-700 bg-white hover:bg-gradient-to-r hover:from-gray-50 hover:to-gray-100 border-2 border-gray-200 hover:border-gray-300 shadow-md hover:shadow-lg transform hover:scale-105'
                }`}
              >
                <ArrowLeftIcon className="w-5 h-5" />
                Previous
              </button>

              {currentStep < totalSteps ? (
                <button
                  type="button"
                  onClick={nextStep}
                  className="group flex items-center gap-2 px-8 py-4 bg-gradient-to-r from-cyan-600 via-blue-600 via-purple-600 to-pink-600 text-white rounded-xl font-bold hover:shadow-2xl hover:scale-105 transition-all relative overflow-hidden"
                >
                  <span className="relative z-10">Next</span>
                  <ArrowRightIcon className="w-5 h-5 relative z-10 group-hover:translate-x-1 transition-transform" />
                  <div className="absolute inset-0 bg-gradient-to-r from-pink-600 via-rose-600 to-orange-600 opacity-0 group-hover:opacity-100 transition-opacity duration-300" />
                </button>
              ) : (
                <button
                  type="submit"
                  disabled={loading}
                  className={`group flex items-center gap-2 px-8 py-4 rounded-xl font-bold transition-all relative overflow-hidden ${
                    loading
                      ? 'bg-gray-400 cursor-not-allowed text-white'
                      : 'bg-gradient-to-r from-cyan-600 via-blue-600 via-purple-600 to-pink-600 text-white hover:shadow-2xl hover:scale-105'
                  }`}
                >
                  {loading ? (
                    <>
                      <svg className="animate-spin h-5 w-5" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                        <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                      </svg>
                      Processing...
                    </>
                  ) : (
                    <>
                      <span className="relative z-10">Get My Quote</span>
                      <SparklesIcon className="w-5 h-5 relative z-10 group-hover:rotate-12 transition-transform" />
                      <div className="absolute inset-0 bg-gradient-to-r from-pink-600 via-rose-600 to-orange-600 opacity-0 group-hover:opacity-100 transition-opacity duration-300" />
                    </>
                  )}
                </button>
              )}
            </div>
          </form>

          {/* Footer Links */}
          <div className="mt-6 pt-6 border-t-2 border-gradient-to-r from-cyan-200 via-purple-200 to-pink-200 flex items-center justify-between relative z-10">
            <Link
              to="/login"
              className="text-sm font-semibold bg-gradient-to-r from-cyan-600 to-purple-600 bg-clip-text text-transparent hover:from-cyan-700 hover:to-purple-700 transition-all"
            >
              Already have an account? Sign in →
            </Link>
            <div className="flex items-center gap-2 px-3 py-2 bg-white/60 dark:bg-gray-800/60 backdrop-blur-sm rounded-full border border-white/50">
              <LockClosedIcon className="w-4 h-4 text-emerald-600" />
              <span className="text-xs font-semibold text-gray-700 dark:text-gray-300">Secure & Encrypted</span>
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
        @keyframes fadeIn {
          from {
            opacity: 0;
            transform: translateY(10px);
          }
          to {
            opacity: 1;
            transform: translateY(0);
          }
        }
        .animate-fadeIn {
          animation: fadeIn 0.3s ease-out;
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
        @keyframes shimmer {
          0% {
            transform: translateX(-100%);
          }
          100% {
            transform: translateX(100%);
          }
        }
        .animate-shimmer {
          animation: shimmer 2s infinite;
        }
        .animation-delay-6000 {
          animation-delay: 6s;
        }
      `}</style>
    </div>
  )
}
