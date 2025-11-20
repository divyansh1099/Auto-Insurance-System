import { useState, useEffect, useRef } from 'react'
import { useNavigate } from 'react-router-dom'
import { useQuery } from 'react-query'
import { authAPI, dashboardAPI } from '../services/api'
import {
  ShieldCheckIcon,
  ChartBarIcon,
  CurrencyDollarIcon,
  TrophyIcon,
  BoltIcon,
  ArrowRightIcon,
  CheckCircleIcon,
  PlayIcon,
  CpuChipIcon,
  LockClosedIcon,
  SparklesIcon,
  MapPinIcon,
  LightBulbIcon,
  AcademicCapIcon
} from '@heroicons/react/24/outline'

export default function Homepage() {
  const navigate = useNavigate()
  const [mousePosition, setMousePosition] = useState({ x: 0, y: 0 })
  const [isVisible, setIsVisible] = useState(false)
  const [counters, setCounters] = useState({ users: 0, savings: 0, trips: 0, score: 0 })
  const heroRef = useRef(null)
  const featuresRef = useRef(null)
  const statsRef = useRef(null)
  const howItWorksRef = useRef(null)

  // Check if user is authenticated
  const { data: currentUser } = useQuery(
    ['currentUser'],
    () => authAPI.getCurrentUser(),
    { retry: false }
  )

  const driverId = currentUser?.data?.driver_id || 'DRV-0001'
  const isAuthenticated = !!currentUser?.data

  // Get dashboard summary if authenticated
  const { data: summary } = useQuery(
    ['dashboardSummary', driverId],
    () => dashboardAPI.getSummary(driverId),
    {
      retry: false,
      enabled: isAuthenticated && !!driverId,
      staleTime: 30000
    }
  )

  // Mouse tracking for parallax effect
  useEffect(() => {
    const handleMouseMove = (e) => {
      setMousePosition({
        x: (e.clientX / window.innerWidth - 0.5) * 20,
        y: (e.clientY / window.innerHeight - 0.5) * 20
      })
    }
    window.addEventListener('mousemove', handleMouseMove)
    return () => window.removeEventListener('mousemove', handleMouseMove)
  }, [])


  // Intersection Observer for scroll animations
  useEffect(() => {
    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            setIsVisible(true)
            // Animate counters when stats section is visible
            if (entry.target === statsRef.current) {
              animateCounters()
            }
          }
        })
      },
      { threshold: 0.1 }
    )

    if (heroRef.current) observer.observe(heroRef.current)
    if (featuresRef.current) observer.observe(featuresRef.current)
    if (statsRef.current) observer.observe(statsRef.current)
    if (howItWorksRef.current) observer.observe(howItWorksRef.current)

    return () => {
      if (heroRef.current) observer.unobserve(heroRef.current)
      if (featuresRef.current) observer.unobserve(featuresRef.current)
      if (statsRef.current) observer.unobserve(statsRef.current)
      if (howItWorksRef.current) observer.unobserve(howItWorksRef.current)
    }
  }, [])

  // Animate counters
  const animateCounters = () => {
    const duration = 2000
    const steps = 60
    const stepTime = duration / steps

    const targetValues = {
      users: 50000,
      savings: 2500000,
      trips: 1000000,
      score: 95
    }

    let currentStep = 0
    const interval = setInterval(() => {
      currentStep++
      const progress = currentStep / steps
      const easeOut = 1 - Math.pow(1 - progress, 3)

      setCounters({
        users: Math.floor(targetValues.users * easeOut),
        savings: Math.floor(targetValues.savings * easeOut),
        trips: Math.floor(targetValues.trips * easeOut),
        score: Math.floor(targetValues.score * easeOut)
      })

      if (currentStep >= steps) {
        clearInterval(interval)
        setCounters(targetValues)
      }
    }, stepTime)
  }

  const features = [
    {
      icon: CpuChipIcon,
      title: 'AI-Powered Analysis',
      description: 'Machine learning algorithms analyze your driving patterns in real-time for accurate risk assessment',
      color: 'from-cyan-500 via-blue-500 to-indigo-600',
      bgColor: 'from-cyan-50 to-blue-50',
      delay: '0'
    },
    {
      icon: ShieldCheckIcon,
      title: 'Real-Time Protection',
      description: 'Advanced telematics technology tracks your driving behavior with 24/7 monitoring',
      color: 'from-emerald-500 via-teal-500 to-cyan-500',
      bgColor: 'from-emerald-50 to-teal-50',
      delay: '100'
    },
    {
      icon: ChartBarIcon,
      title: 'Smart Analytics',
      description: 'Comprehensive insights into your driving patterns and safety metrics with predictive modeling',
      color: 'from-purple-500 via-violet-500 to-fuchsia-600',
      bgColor: 'from-purple-50 to-violet-50',
      delay: '200'
    },
    {
      icon: CurrencyDollarIcon,
      title: 'Dynamic Pricing',
      description: 'Save up to 40% with usage-based insurance that rewards safe driving habits',
      color: 'from-green-500 via-emerald-500 to-teal-500',
      bgColor: 'from-green-50 to-emerald-50',
      delay: '300'
    },
    {
      icon: TrophyIcon,
      title: 'Rewards Program',
      description: 'Earn points and unlock exclusive rewards for maintaining safe driving habits',
      color: 'from-amber-500 via-orange-500 to-rose-500',
      bgColor: 'from-amber-50 to-orange-50',
      delay: '400'
    },
    {
      icon: BoltIcon,
      title: 'Live Monitoring',
      description: 'Track your trips in real-time with instant feedback and safety alerts',
      color: 'from-yellow-400 via-amber-500 to-orange-500',
      bgColor: 'from-yellow-50 to-amber-50',
      delay: '500'
    }
  ]

  const benefits = [
    { icon: CheckCircleIcon, text: 'Save up to 40% on premiums' },
    { icon: CheckCircleIcon, text: 'Real-time driving feedback' },
    { icon: CheckCircleIcon, text: 'AI-powered risk assessment' },
    { icon: CheckCircleIcon, text: '24/7 roadside assistance' },
    { icon: CheckCircleIcon, text: 'Earn rewards for safe driving' },
    { icon: CheckCircleIcon, text: 'No hidden fees or surprises' }
  ]

  const howItWorks = [
    {
      step: '01',
      title: 'Install & Connect',
      description: 'Connect your device or use our mobile app to start tracking your driving',
      icon: CpuChipIcon,
      color: 'from-cyan-500 to-blue-500'
    },
    {
      step: '02',
      title: 'Drive & Track',
      description: 'Our AI analyzes your driving patterns, speed, braking, and route safety',
      icon: MapPinIcon,
      color: 'from-purple-500 to-pink-500'
    },
    {
      step: '03',
      title: 'Get Insights',
      description: 'Receive real-time feedback and detailed analytics on your driving performance',
      icon: LightBulbIcon,
      color: 'from-emerald-500 to-teal-500'
    },
    {
      step: '04',
      title: 'Save & Earn',
      description: 'Watch your premiums decrease and earn rewards as you improve your driving',
      icon: TrophyIcon,
      color: 'from-amber-500 to-orange-500'
    }
  ]

  const stats = [
    { label: 'Safety Score', value: Math.round(summary?.data?.safety_score || 85), suffix: '/100', color: 'text-green-500' },
    { label: 'Total Savings', value: `$${Math.round(summary?.data?.total_savings || 0)}`, suffix: '', color: 'text-blue-500' },
    { label: 'Reward Points', value: summary?.data?.reward_points || 0, suffix: '', color: 'text-orange-500' },
    { label: 'Trips Tracked', value: summary?.data?.total_trips || 0, suffix: '', color: 'text-purple-500' }
  ]

  return (
    <div className="min-h-screen bg-gradient-to-br from-cyan-50 via-blue-50 via-indigo-50 to-purple-50 dark:from-gray-900 dark:via-gray-900 dark:to-gray-800 overflow-hidden transition-colors duration-200">
      {/* Animated Background Elements - More vibrant colors */}
      <div className="fixed inset-0 overflow-hidden pointer-events-none">
        <div
          className="absolute top-1/4 left-1/4 w-96 h-96 bg-cyan-400 dark:bg-cyan-900 rounded-full mix-blend-multiply dark:mix-blend-screen filter blur-3xl opacity-30 animate-blob"
          style={{
            transform: `translate(${mousePosition.x * 0.5}px, ${mousePosition.y * 0.5}px)`
          }}
        />
        <div
          className="absolute top-1/3 right-1/4 w-96 h-96 bg-violet-400 dark:bg-violet-900 rounded-full mix-blend-multiply dark:mix-blend-screen filter blur-3xl opacity-30 animate-blob animation-delay-2000"
          style={{
            transform: `translate(${-mousePosition.x * 0.3}px, ${mousePosition.y * 0.3}px)`
          }}
        />
        <div
          className="absolute bottom-1/4 left-1/3 w-96 h-96 bg-fuchsia-400 dark:bg-fuchsia-900 rounded-full mix-blend-multiply dark:mix-blend-screen filter blur-3xl opacity-30 animate-blob animation-delay-4000"
          style={{
            transform: `translate(${mousePosition.x * 0.4}px, ${-mousePosition.y * 0.4}px)`
          }}
        />
        <div
          className="absolute top-1/2 right-1/3 w-80 h-80 bg-emerald-300 dark:bg-emerald-900 rounded-full mix-blend-multiply dark:mix-blend-screen filter blur-3xl opacity-25 animate-blob animation-delay-6000"
          style={{
            transform: `translate(${-mousePosition.x * 0.2}px, ${mousePosition.y * 0.2}px)`
          }}
        />
      </div>

      {/* Hero Section */}
      <section
        ref={heroRef}
        className="relative min-h-screen flex items-center justify-center px-4 py-20"
      >
        {/* Decorative Floating Elements */}
        <div className="absolute top-20 left-10 opacity-20 animate-float">
          <div className="w-20 h-20 bg-gradient-to-br from-cyan-400 to-blue-500 rounded-2xl rotate-12 blur-sm"></div>
        </div>
        <div className="absolute top-40 right-16 opacity-20 animate-float-delay">
          <div className="w-16 h-16 bg-gradient-to-br from-purple-400 to-pink-500 rounded-full blur-sm"></div>
        </div>
        <div className="absolute bottom-32 left-20 opacity-15 animate-float-delay-2">
          <div className="w-24 h-24 bg-gradient-to-br from-emerald-400 to-teal-500 rounded-3xl -rotate-12 blur-sm"></div>
        </div>
        <div className="absolute bottom-40 right-24 opacity-20 animate-float">
          <div className="w-16 h-16 bg-gradient-to-br from-amber-400 to-orange-500 rounded-xl rotate-45 blur-sm"></div>
        </div>
        <div className="max-w-7xl mx-auto text-center z-10">
          {/* Animated Badge */}
          <div className={`inline-flex items-center gap-2 px-5 py-2.5 rounded-full bg-gradient-to-r from-cyan-500/20 via-blue-500/20 to-purple-500/20 dark:from-cyan-900/40 dark:via-blue-900/40 dark:to-purple-900/40 backdrop-blur-md border border-cyan-300/50 dark:border-cyan-700/50 shadow-xl mb-8 transition-all duration-1000 ${isVisible ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-4'}`}>
            <SparklesIcon className="w-5 h-5 text-cyan-600 dark:text-cyan-400 animate-pulse" />
            <span className="text-sm font-semibold bg-gradient-to-r from-cyan-700 to-blue-700 dark:from-cyan-400 dark:to-blue-400 bg-clip-text text-transparent">AI-Powered Telematics Insurance</span>
          </div>

          {/* Main Heading */}
          <h1 className={`text-6xl md:text-7xl lg:text-8xl font-bold mb-6 transition-all duration-1000 delay-200 ${isVisible ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-8'}`}>
            <span className="bg-gradient-to-r from-cyan-600 via-blue-600 via-purple-600 to-pink-600 dark:from-cyan-400 dark:via-blue-400 dark:via-purple-400 dark:to-pink-400 bg-clip-text text-transparent animate-gradient">
              Drive Smarter,
            </span>
            <br />
            <span className="bg-gradient-to-r from-indigo-600 via-cyan-600 to-teal-600 dark:from-indigo-400 dark:via-cyan-400 dark:to-teal-400 bg-clip-text text-transparent animate-gradient-delay">
              Save More
            </span>
          </h1>

          {/* Subheading */}
          <p className={`text-xl md:text-2xl text-gray-600 dark:text-gray-300 mb-8 max-w-3xl mx-auto transition-all duration-1000 delay-300 ${isVisible ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-8'}`}>
            Experience the future of auto insurance with real-time driving analytics,
            personalized pricing, and rewards for safe driving.
          </p>

          {/* Quick Feature Highlights */}
          <div className={`flex flex-wrap justify-center gap-4 mb-8 max-w-4xl mx-auto transition-all duration-1000 delay-350 ${isVisible ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-8'}`}>
            <div className="group flex items-center gap-2 px-4 py-2 bg-white/70 dark:bg-gray-800/70 backdrop-blur-sm rounded-full border border-cyan-200/50 dark:border-cyan-700/50 shadow-md hover:border-cyan-400 hover:bg-gradient-to-r hover:from-cyan-50 hover:to-blue-50 hover:shadow-xl hover:shadow-cyan-500/20 hover:scale-110 transition-all duration-300 cursor-pointer">
              <ShieldCheckIcon className="w-4 h-4 text-cyan-600 group-hover:scale-125 group-hover:rotate-12 transition-transform duration-300" />
              <span className="text-sm font-medium text-gray-700 dark:text-gray-300 group-hover:text-cyan-700 dark:group-hover:text-cyan-400 group-hover:font-semibold transition-all duration-300">Real-Time Tracking</span>
            </div>
            <div className="group flex items-center gap-2 px-4 py-2 bg-white/70 dark:bg-gray-800/70 backdrop-blur-sm rounded-full border border-purple-200/50 dark:border-purple-700/50 shadow-md hover:border-purple-400 hover:bg-gradient-to-r hover:from-purple-50 hover:to-pink-50 hover:shadow-xl hover:shadow-purple-500/20 hover:scale-110 transition-all duration-300 cursor-pointer">
              <CpuChipIcon className="w-4 h-4 text-purple-600 group-hover:scale-125 group-hover:rotate-12 transition-transform duration-300" />
              <span className="text-sm font-medium text-gray-700 dark:text-gray-300 group-hover:text-purple-700 dark:group-hover:text-purple-400 group-hover:font-semibold transition-all duration-300">AI-Powered</span>
            </div>
            <div className="group flex items-center gap-2 px-4 py-2 bg-white/70 dark:bg-gray-800/70 backdrop-blur-sm rounded-full border border-emerald-200/50 dark:border-emerald-700/50 shadow-md hover:border-emerald-400 hover:bg-gradient-to-r hover:from-emerald-50 hover:to-teal-50 hover:shadow-xl hover:shadow-emerald-500/20 hover:scale-110 transition-all duration-300 cursor-pointer">
              <CurrencyDollarIcon className="w-4 h-4 text-emerald-600 group-hover:scale-125 group-hover:rotate-12 transition-transform duration-300" />
              <span className="text-sm font-medium text-gray-700 dark:text-gray-300 group-hover:text-emerald-700 dark:group-hover:text-emerald-400 group-hover:font-semibold transition-all duration-300">Save Up to 40%</span>
            </div>
            <div className="group flex items-center gap-2 px-4 py-2 bg-white/70 dark:bg-gray-800/70 backdrop-blur-sm rounded-full border border-amber-200/50 dark:border-amber-700/50 shadow-md hover:border-amber-400 hover:bg-gradient-to-r hover:from-amber-50 hover:to-orange-50 hover:shadow-xl hover:shadow-amber-500/20 hover:scale-110 transition-all duration-300 cursor-pointer">
              <TrophyIcon className="w-4 h-4 text-amber-600 group-hover:scale-125 group-hover:rotate-12 transition-transform duration-300" />
              <span className="text-sm font-medium text-gray-700 dark:text-gray-300 group-hover:text-amber-700 dark:group-hover:text-amber-400 group-hover:font-semibold transition-all duration-300">Earn Rewards</span>
            </div>
          </div>

          {/* CTA Buttons */}
          <div className={`flex flex-col sm:flex-row gap-4 justify-center items-center mb-12 transition-all duration-1000 delay-400 ${isVisible ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-8'}`}>
            {isAuthenticated ? (
              <>
                <button
                  onClick={() => navigate('/')}
                  className="group relative px-8 py-4 bg-gradient-to-r from-cyan-600 via-blue-600 to-purple-600 text-white rounded-full font-semibold text-lg shadow-xl hover:shadow-2xl transform hover:scale-105 transition-all duration-300 overflow-hidden"
                >
                  <span className="relative z-10 flex items-center gap-2">
                    Go to Dashboard
                    <ArrowRightIcon className="w-5 h-5 group-hover:translate-x-1 transition-transform" />
                  </span>
                  <div className="absolute inset-0 bg-gradient-to-r from-purple-600 via-pink-600 to-rose-600 opacity-0 group-hover:opacity-100 transition-opacity duration-300" />
                </button>
                <button
                  onClick={() => navigate('/live')}
                  className="px-8 py-4 bg-white/90 dark:bg-gray-800/90 backdrop-blur-sm text-gray-700 dark:text-gray-200 rounded-full font-semibold text-lg shadow-lg hover:shadow-xl border-2 border-cyan-200 hover:border-cyan-400 hover:bg-gradient-to-r hover:from-cyan-50 hover:to-blue-50 transform hover:scale-105 transition-all duration-300 flex items-center gap-2"
                >
                  <BoltIcon className="w-5 h-5 text-cyan-600" />
                  Live Driving
                </button>
              </>
            ) : (
              <>
                <button
                  onClick={() => navigate('/signup')}
                  className="group relative px-8 py-4 bg-gradient-to-r from-cyan-600 via-blue-600 to-purple-600 text-white rounded-full font-semibold text-lg shadow-xl hover:shadow-2xl transform hover:scale-105 transition-all duration-300 overflow-hidden"
                >
                  <span className="relative z-10 flex items-center gap-2">
                    Get Your Quote
                    <ArrowRightIcon className="w-5 h-5 group-hover:translate-x-1 transition-transform" />
                  </span>
                  <div className="absolute inset-0 bg-gradient-to-r from-purple-600 via-pink-600 to-rose-600 opacity-0 group-hover:opacity-100 transition-opacity duration-300" />
                </button>
                <button
                  onClick={() => navigate('/login')}
                  className="px-8 py-4 bg-white/90 dark:bg-gray-800/90 backdrop-blur-sm text-gray-700 dark:text-gray-200 rounded-full font-semibold text-lg shadow-lg hover:shadow-xl border-2 border-cyan-200 hover:border-cyan-400 hover:bg-gradient-to-r hover:from-cyan-50 hover:to-blue-50 transform hover:scale-105 transition-all duration-300"
                >
                  Sign In
                </button>
              </>
            )}
          </div>

          {/* Stats Grid (if authenticated) */}
          {isAuthenticated && summary?.data && (
            <div className={`grid grid-cols-2 md:grid-cols-4 gap-6 max-w-4xl mx-auto transition-all duration-1000 delay-500 ${isVisible ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-8'}`}>
              {stats.map((stat, idx) => (
                <div
                  key={idx}
                  className="group bg-white/60 dark:bg-gray-800/60 backdrop-blur-md rounded-2xl p-6 border border-white/20 dark:border-gray-700/20 shadow-lg hover:shadow-xl transform hover:scale-105 transition-all duration-300"
                >
                  <div className={`text-3xl md:text-4xl font-bold mb-2 ${stat.color}`}>
                    {stat.value}
                    {stat.suffix && <span className="text-lg text-gray-500">/100</span>}
                  </div>
                  <div className="text-sm text-gray-600 dark:text-gray-400 dark:text-gray-400 font-medium">{stat.label}</div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Scroll Indicator */}
        <div className="absolute bottom-8 left-1/2 transform -translate-x-1/2 animate-bounce">
          <div className="w-6 h-10 border-2 border-gray-400 dark:border-gray-600 rounded-full flex justify-center">
            <div className="w-1 h-3 bg-gray-400 dark:bg-gray-600 rounded-full mt-2 animate-pulse" />
          </div>
        </div>
      </section>

      {/* Statistics Section */}
      <section ref={statsRef} className="relative py-12 px-4 z-10 bg-gradient-to-br from-white/60 via-cyan-50/60 to-blue-50/60 dark:from-gray-800/60 dark:via-gray-800/60 dark:to-gray-900/60 backdrop-blur-sm">
        <div className="max-w-5xl mx-auto">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="text-center p-4 bg-white/80 dark:bg-gray-800/80 backdrop-blur-md rounded-xl border border-cyan-200/50 dark:border-cyan-700/50 shadow-md hover:shadow-lg transform hover:scale-105 transition-all">
              <div className="text-3xl md:text-4xl font-bold bg-gradient-to-r from-cyan-600 to-blue-600 bg-clip-text text-transparent mb-1">
                {counters.users.toLocaleString()}+
              </div>
              <div className="text-xs md:text-sm font-semibold text-gray-700 dark:text-gray-300">Active Users</div>
            </div>
            <div className="text-center p-4 bg-white/80 dark:bg-gray-800/80 backdrop-blur-md rounded-xl border border-purple-200/50 dark:border-purple-700/50 shadow-md hover:shadow-lg transform hover:scale-105 transition-all">
              <div className="text-3xl md:text-4xl font-bold bg-gradient-to-r from-purple-600 to-pink-600 bg-clip-text text-transparent mb-1">
                ${(counters.savings / 1000000).toFixed(1)}M+
              </div>
              <div className="text-xs md:text-sm font-semibold text-gray-700 dark:text-gray-300">Total Savings</div>
            </div>
            <div className="text-center p-4 bg-white/80 dark:bg-gray-800/80 backdrop-blur-md rounded-xl border border-emerald-200/50 dark:border-emerald-700/50 shadow-md hover:shadow-lg transform hover:scale-105 transition-all">
              <div className="text-3xl md:text-4xl font-bold bg-gradient-to-r from-emerald-600 to-teal-600 bg-clip-text text-transparent mb-1">
                {counters.trips.toLocaleString()}+
              </div>
              <div className="text-xs md:text-sm font-semibold text-gray-700 dark:text-gray-300">Trips Tracked</div>
            </div>
            <div className="text-center p-4 bg-white/80 dark:bg-gray-800/80 backdrop-blur-md rounded-xl border border-amber-200/50 dark:border-amber-700/50 shadow-md hover:shadow-lg transform hover:scale-105 transition-all">
              <div className="text-3xl md:text-4xl font-bold bg-gradient-to-r from-amber-600 to-orange-600 bg-clip-text text-transparent mb-1">
                {counters.score}%
              </div>
              <div className="text-xs md:text-sm font-semibold text-gray-700 dark:text-gray-300">Avg Safety Score</div>
            </div>
          </div>
        </div>
      </section>

      {/* Real-Time Monitoring Section */}
      <section className="relative py-32 px-4 z-10 bg-gradient-to-br from-white via-cyan-50/30 to-blue-50/30 dark:from-gray-900 dark:via-gray-900/30 dark:to-gray-800/30">
        <div className="max-w-6xl mx-auto">
          <div className="text-center mb-20">
            <h2 className="text-4xl md:text-5xl font-bold mb-6 bg-gradient-to-r from-cyan-700 via-blue-700 to-purple-700 bg-clip-text text-transparent">
              Real-Time Monitoring
            </h2>
            <p className="text-xl text-gray-700 dark:text-gray-300 mb-12 max-w-3xl mx-auto">
              Our advanced telematics system tracks your driving behavior in real-time,
              providing instant feedback and helping you become a safer driver.
            </p>
          </div>

          {/* Simple Car Illustration - Static but elegant */}
          <div className="mb-16 flex justify-center">
            <div className="relative">
              <svg
                viewBox="0 0 400 200"
                className="w-full max-w-3xl mx-auto"
                style={{
                  filter: 'drop-shadow(0 20px 40px rgba(0,0,0,0.1))'
                }}
              >
                {/* Car Body */}
                <g>
                  {/* Main Body */}
                  <rect x="80" y="100" width="240" height="60" rx="30" fill="url(#carGradient)" />
                  {/* Roof */}
                  <path d="M 120 100 Q 200 60 280 100 L 280 140 L 120 140 Z" fill="url(#carGradient2)" />
                  {/* Windows */}
                  <rect x="140" y="80" width="60" height="30" rx="5" fill="rgba(255,255,255,0.3)" />
                  <rect x="220" y="80" width="60" height="30" rx="5" fill="rgba(255,255,255,0.3)" />
                  {/* Wheels */}
                  <circle cx="140" cy="160" r="25" fill="#1a1a1a" />
                  <circle cx="140" cy="160" r="18" fill="#333" />
                  <circle cx="140" cy="160" r="12" fill="#555" />
                  <circle cx="260" cy="160" r="25" fill="#1a1a1a" />
                  <circle cx="260" cy="160" r="18" fill="#333" />
                  <circle cx="260" cy="160" r="12" fill="#555" />
                  {/* Headlights */}
                  <ellipse cx="320" cy="130" rx="15" ry="8" fill="url(#headlightGradient)" opacity="0.8" />
                  {/* Telematics Device Indicator */}
                  <circle cx="200" cy="50" r="8" fill="#10b981">
                    <animate attributeName="opacity" values="0.5;1;0.5" dur="2s" repeatCount="indefinite" />
                  </circle>
                  <path d="M 200 50 L 200 100" stroke="#10b981" strokeWidth="2" strokeDasharray="5,5" />
                </g>

                {/* Gradient Definitions */}
                <defs>
                  <linearGradient id="carGradient" x1="0%" y1="0%" x2="100%" y2="0%">
                    <stop offset="0%" stopColor="#06b6d4" />
                    <stop offset="50%" stopColor="#3b82f6" />
                    <stop offset="100%" stopColor="#8b5cf6" />
                  </linearGradient>
                  <linearGradient id="carGradient2" x1="0%" y1="0%" x2="100%" y2="0%">
                    <stop offset="0%" stopColor="#0891b2" />
                    <stop offset="50%" stopColor="#2563eb" />
                    <stop offset="100%" stopColor="#7c3aed" />
                  </linearGradient>
                  <radialGradient id="headlightGradient" cx="50%" cy="50%">
                    <stop offset="0%" stopColor="#fef3c7" />
                    <stop offset="100%" stopColor="#fbbf24" />
                  </radialGradient>
                </defs>
              </svg>
            </div>
          </div>

          {/* Feature Cards - Clean grid layout */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            <div className="p-8 bg-white/80 backdrop-blur-md rounded-2xl border border-gray-200 shadow-lg hover:shadow-xl transform hover:scale-105 transition-all">
              <div className="inline-flex p-4 bg-gradient-to-br from-cyan-500 to-blue-500 rounded-xl mb-6">
                <CpuChipIcon className="w-8 h-8 text-white" />
              </div>
              <h3 className="text-xl font-bold text-gray-900 dark:text-white mb-3">AI Analysis</h3>
              <p className="text-gray-600">Machine learning algorithms analyze every trip in real-time for accurate risk assessment</p>
            </div>
            <div className="p-8 bg-white/80 backdrop-blur-md rounded-2xl border border-gray-200 shadow-lg hover:shadow-xl transform hover:scale-105 transition-all">
              <div className="inline-flex p-4 bg-gradient-to-br from-purple-500 to-pink-500 rounded-xl mb-6">
                <BoltIcon className="w-8 h-8 text-white" />
              </div>
              <h3 className="text-xl font-bold text-gray-900 dark:text-white mb-3">Instant Feedback</h3>
              <p className="text-gray-600">Get real-time alerts and recommendations to improve your driving habits</p>
            </div>
            <div className="p-8 bg-white/80 backdrop-blur-md rounded-2xl border border-gray-200 shadow-lg hover:shadow-xl transform hover:scale-105 transition-all">
              <div className="inline-flex p-4 bg-gradient-to-br from-emerald-500 to-teal-500 rounded-xl mb-6">
                <ChartBarIcon className="w-8 h-8 text-white" />
              </div>
              <h3 className="text-xl font-bold text-gray-900 dark:text-white mb-3">Detailed Insights</h3>
              <p className="text-gray-600">Comprehensive analytics and reports help you understand your driving patterns</p>
            </div>
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section
        ref={featuresRef}
        className="relative py-32 px-4 z-10"
      >
        <div className="max-w-7xl mx-auto">
          <div className="text-center mb-20">
            <h2 className="text-4xl md:text-5xl font-bold mb-4 bg-gradient-to-r from-cyan-700 via-blue-700 to-purple-700 bg-clip-text text-transparent">
              Powerful Features
            </h2>
            <p className="text-xl text-gray-700 dark:text-gray-300 max-w-2xl mx-auto">
              Everything you need to monitor, improve, and save on your insurance
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
            {features.map((feature, idx) => {
              const Icon = feature.icon
              return (
                <div
                  key={idx}
                  className="group relative bg-gradient-to-br from-white to-gray-50/50 dark:from-gray-800 dark:to-gray-900/50 backdrop-blur-md rounded-3xl p-8 border-2 border-gray-200/50 dark:border-gray-700/50 shadow-xl hover:shadow-2xl transform hover:scale-105 hover:-translate-y-2 transition-all duration-500 overflow-hidden"
                  style={{
                    animationDelay: `${feature.delay}ms`,
                    animation: isVisible ? 'fadeInUp 0.6s ease-out forwards' : 'none'
                  }}
                >
                  {/* Gradient Background on Hover */}
                  <div className={`absolute inset-0 bg-gradient-to-br ${feature.color} opacity-0 group-hover:opacity-15 transition-opacity duration-500`} />

                  {/* Icon */}
                  <div className={`relative z-10 inline-flex p-5 rounded-2xl bg-gradient-to-br ${feature.color} mb-6 transform group-hover:rotate-12 group-hover:scale-110 transition-all duration-300 shadow-lg`}>
                    <Icon className="w-8 h-8 text-white" />
                  </div>

                  {/* Content */}
                  <h3 className="text-xl font-bold text-gray-900 dark:text-white mb-3 relative z-10 group-hover:text-transparent group-hover:bg-gradient-to-r group-hover:from-gray-900 group-hover:to-gray-700 group-hover:bg-clip-text transition-all">
                    {feature.title}
                  </h3>
                  <p className="text-gray-600 dark:text-gray-400 leading-relaxed relative z-10">
                    {feature.description}
                  </p>

                  {/* Arrow Indicator */}
                  <div className="absolute bottom-6 right-6 opacity-0 group-hover:opacity-100 transform translate-x-2 group-hover:translate-x-0 transition-all duration-300 relative z-10">
                    <ArrowRightIcon className={`w-6 h-6 bg-gradient-to-r ${feature.color} bg-clip-text text-transparent`} />
                  </div>
                </div>
              )
            })}
          </div>
        </div>
      </section>

      {/* Benefits Section */}
      <section className="relative py-20 px-4 z-10 bg-gradient-to-r from-cyan-600 via-blue-600 to-purple-600">
        <div className="max-w-6xl mx-auto">
          <div className="text-center mb-12">
            <h2 className="text-4xl md:text-5xl font-bold text-white mb-4">
              Why Choose SmartDrive?
            </h2>
            <p className="text-xl text-cyan-100 max-w-2xl mx-auto">
              Join thousands of drivers saving money while becoming safer on the road
            </p>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {benefits.map((benefit, idx) => {
              const Icon = benefit.icon
              return (
                <div key={idx} className="flex items-start gap-4 bg-white/10 backdrop-blur-md rounded-xl p-6 border border-white/20 hover:bg-white/20 transition-all">
                  <div className="flex-shrink-0 p-2 bg-white/20 rounded-lg">
                    <Icon className="w-6 h-6 text-white" />
                  </div>
                  <p className="text-white font-medium text-lg">{benefit.text}</p>
                </div>
              )
            })}
          </div>
        </div>
      </section>

      {/* How It Works Section */}
      <section ref={howItWorksRef} className="relative py-32 px-4 z-10">
        <div className="max-w-7xl mx-auto">
          <div className="text-center mb-20">
            <h2 className="text-4xl md:text-5xl font-bold mb-4 bg-gradient-to-r from-indigo-700 via-purple-700 to-pink-700 bg-clip-text text-transparent">
              How It Works
            </h2>
            <p className="text-xl text-gray-700 dark:text-gray-300 max-w-2xl mx-auto">
              Get started in minutes and start saving today
            </p>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-8">
            {howItWorks.map((step, idx) => {
              const Icon = step.icon
              return (
                <div
                  key={idx}
                  className="relative group"
                  style={{
                    animationDelay: `${idx * 150}ms`,
                    animation: isVisible ? 'fadeInUp 0.6s ease-out forwards' : 'none'
                  }}
                >
                  <div className="bg-gradient-to-br from-white to-gray-50 rounded-3xl p-8 border-2 border-gray-200 shadow-xl hover:shadow-2xl transform hover:scale-105 transition-all duration-300 h-full">
                    <div className={`inline-flex p-4 rounded-2xl bg-gradient-to-br ${step.color} mb-6 shadow-lg`}>
                      <Icon className="w-8 h-8 text-white" />
                    </div>
                    <div className={`text-5xl font-bold mb-4 bg-gradient-to-r ${step.color} bg-clip-text text-transparent`}>
                      {step.step}
                    </div>
                    <h3 className="text-xl font-bold text-gray-900 dark:text-white mb-3">{step.title}</h3>
                    <p className="text-gray-600 dark:text-gray-400 leading-relaxed">{step.description}</p>
                  </div>
                  {idx < howItWorks.length - 1 && (
                    <div className="hidden lg:block absolute top-1/2 -right-4 z-0">
                      <ArrowRightIcon className="w-8 h-8 text-gray-300" />
                    </div>
                  )}
                </div>
              )
            })}
          </div>
        </div>
      </section>

      {/* Trust & Security Section */}
      <section className="relative py-20 px-4 z-10 bg-gradient-to-br from-gray-50 to-white dark:from-gray-900 dark:to-gray-800">
        <div className="max-w-6xl mx-auto">
          <div className="text-center mb-12">
            <h2 className="text-3xl md:text-4xl font-bold text-gray-900 dark:text-white mb-4">
              Trusted & Secure
            </h2>
            <p className="text-lg text-gray-600 dark:text-gray-400 max-w-2xl mx-auto">
              Your data is protected with enterprise-grade security
            </p>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            <div className="text-center p-6 bg-white dark:bg-gray-800 rounded-2xl shadow-lg border border-gray-200 dark:border-gray-700 hover:shadow-xl transform hover:scale-105 transition-all">
              <div className="inline-flex p-4 bg-gradient-to-br from-emerald-500 to-teal-500 rounded-2xl mb-4">
                <LockClosedIcon className="w-8 h-8 text-white" />
              </div>
              <h3 className="text-xl font-bold text-gray-900 mb-2">Bank-Level Security</h3>
              <p className="text-gray-600">256-bit encryption protects your data</p>
            </div>
            <div className="text-center p-6 bg-white dark:bg-gray-800 rounded-2xl shadow-lg border border-gray-200 dark:border-gray-700 hover:shadow-xl transform hover:scale-105 transition-all">
              <div className="inline-flex p-4 bg-gradient-to-br from-blue-500 to-cyan-500 rounded-2xl mb-4">
                <ShieldCheckIcon className="w-8 h-8 text-white" />
              </div>
              <h3 className="text-xl font-bold text-gray-900 mb-2">Privacy First</h3>
              <p className="text-gray-600">Your data is never sold or shared</p>
            </div>
            <div className="text-center p-6 bg-white dark:bg-gray-800 rounded-2xl shadow-lg border border-gray-200 dark:border-gray-700 hover:shadow-xl transform hover:scale-105 transition-all">
              <div className="inline-flex p-4 bg-gradient-to-br from-purple-500 to-pink-500 rounded-2xl mb-4">
                <AcademicCapIcon className="w-8 h-8 text-white" />
              </div>
              <h3 className="text-xl font-bold text-gray-900 mb-2">AI-Powered</h3>
              <p className="text-gray-600">Advanced machine learning algorithms</p>
            </div>
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="relative py-32 px-4 z-10">
        <div className="max-w-5xl mx-auto">
          <div className="bg-gradient-to-r from-cyan-600 via-blue-600 via-purple-600 to-pink-600 rounded-3xl p-12 md:p-16 text-center text-white shadow-2xl transform hover:scale-[1.02] transition-transform duration-500 relative overflow-hidden">
            <div
              className="absolute inset-0 opacity-20"
              style={{
                backgroundImage: `url("data:image/svg+xml,%3Csvg width='60' height='60' viewBox='0 0 60 60' xmlns='http://www.w3.org/2000/svg'%3E%3Cg fill='none' fill-rule='evenodd'%3E%3Cg fill='%23ffffff' fill-opacity='0.05'%3E%3Cpath d='M36 34v-4h-2v4h-4v2h4v4h2v-4h4v-2h-4zm0-30V0h-2v4h-4v2h4v4h2V6h4V4h-4zM6 34v-4H4v4H0v2h4v4h2v-4h4v-2H6zM6 4V0H4v4H0v2h4v4h2V6h4V4H6z'/%3E%3C/g%3E%3C/g%3E%3C/svg%3E")`
              }}
            ></div>
            <div className="relative z-10">
              <h2 className="text-4xl md:text-5xl font-bold mb-6">
                Ready to Transform Your Driving Experience?
              </h2>
              <p className="text-xl mb-8 opacity-95 max-w-2xl mx-auto">
                Join thousands of drivers who are saving money while becoming safer on the road
              </p>
              <div className="flex flex-col sm:flex-row gap-4 justify-center">
                {isAuthenticated ? (
                  <button
                    onClick={() => navigate('/simulator')}
                    className="px-8 py-4 bg-white text-cyan-600 rounded-full font-semibold text-lg shadow-xl hover:shadow-2xl transform hover:scale-105 transition-all duration-300 flex items-center justify-center gap-2"
                  >
                    <PlayIcon className="w-5 h-5" />
                    Try Drive Simulator
                  </button>
                ) : (
                  <button
                    onClick={() => navigate('/signup')}
                    className="px-8 py-4 bg-white text-cyan-600 rounded-full font-semibold text-lg shadow-xl hover:shadow-2xl transform hover:scale-105 transition-all duration-300 flex items-center justify-center gap-2"
                  >
                    Get Your Quote
                    <ArrowRightIcon className="w-5 h-5" />
                  </button>
                )}
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="relative py-12 px-4 border-t-2 border-gradient-to-r from-cyan-200 via-blue-200 to-purple-200 bg-gradient-to-br from-white via-cyan-50/30 to-blue-50/30 dark:from-gray-900 dark:via-gray-900/30 dark:to-gray-800/30 backdrop-blur-sm z-10">
        <div className="max-w-7xl mx-auto text-center">
          <div className="flex items-center justify-center gap-2 mb-4">
            <div className="w-10 h-10 bg-gradient-to-br from-cyan-600 via-blue-600 to-purple-600 rounded-xl flex items-center justify-center shadow-lg">
              <ShieldCheckIcon className="w-6 h-6 text-white" />
            </div>
            <span className="text-2xl font-bold bg-gradient-to-r from-cyan-700 via-blue-700 to-purple-700 bg-clip-text text-transparent">SmartDrive</span>
          </div>
          <p className="text-gray-700 dark:text-gray-300 font-medium">
            © 2024 SmartDrive Telematics. All rights reserved.
          </p>
          <div className="mt-4 flex justify-center gap-6 text-sm text-gray-600 dark:text-gray-400">
            <span className="hover:text-cyan-600 dark:hover:text-cyan-400 cursor-pointer transition-colors">Privacy Policy</span>
            <span className="hover:text-cyan-600 dark:hover:text-cyan-400 cursor-pointer transition-colors">Terms of Service</span>
            <span className="hover:text-cyan-600 dark:hover:text-cyan-400 cursor-pointer transition-colors">Contact Us</span>
          </div>
        </div>
      </footer>

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
        @keyframes fadeInUp {
          from {
            opacity: 0;
            transform: translateY(30px);
          }
          to {
            opacity: 1;
            transform: translateY(0);
          }
        }
        @keyframes gradient {
          0%, 100% {
            background-position: 0% 50%;
          }
          50% {
            background-position: 100% 50%;
          }
        }
        .animate-gradient {
          background-size: 200% 200%;
          animation: gradient 3s ease infinite;
        }
        .animate-gradient-delay {
          background-size: 200% 200%;
          animation: gradient 3s ease infinite 1.5s;
        }
        @keyframes float {
          0%, 100% {
            transform: translateY(0px) rotate(0deg);
          }
          50% {
            transform: translateY(-20px) rotate(5deg);
          }
        }
        .animate-float {
          animation: float 6s ease-in-out infinite;
        }
        .animate-float-delay {
          animation: float 6s ease-in-out infinite 2s;
        }
        .animate-float-delay-2 {
          animation: float 6s ease-in-out infinite 4s;
        }
      `}</style>
    </div>
  )
}

