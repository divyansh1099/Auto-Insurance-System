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
    CpuChipIcon,
    LockClosedIcon,
    SparklesIcon,
    RocketLaunchIcon,
    StarIcon,
    FireIcon
} from '@heroicons/react/24/outline'

export default function Homepage() {
    const navigate = useNavigate()
    const [isVisible, setIsVisible] = useState(false)
    const heroRef = useRef(null)

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

    // Intersection Observer for scroll animations
    useEffect(() => {
        const observer = new IntersectionObserver(
            (entries) => {
                entries.forEach((entry) => {
                    if (entry.isIntersecting) {
                        setIsVisible(true)
                    }
                })
            },
            { threshold: 0.1 }
        )

        if (heroRef.current) observer.observe(heroRef.current)

        return () => {
            if (heroRef.current) observer.unobserve(heroRef.current)
        }
    }, [])

    return (
        <div className="min-h-screen bg-gradient-to-br from-slate-950 via-blue-950 to-slate-900 text-white overflow-hidden">
            {/* Animated Background Orbs */}
            <div className="fixed inset-0 overflow-hidden pointer-events-none">
                <div className="absolute top-1/4 -left-1/4 w-[800px] h-[800px] bg-cyan-500/20 rounded-full blur-3xl animate-pulse" />
                <div className="absolute bottom-1/4 -right-1/4 w-[800px] h-[800px] bg-purple-500/20 rounded-full blur-3xl animate-pulse delay-1000" />
                <div className="absolute top-1/2 left-1/2 w-[600px] h-[600px] bg-blue-500/10 rounded-full blur-3xl animate-pulse delay-2000" />
            </div>

            {/* Hero Section - Premium Modern Design */}
            <section ref={heroRef} className="relative min-h-screen flex items-center justify-center px-4 py-20">
                <div className="max-w-7xl mx-auto text-center z-10">
                    {/* Premium Badge */}
                    <div className={`inline-flex items-center gap-3 px-6 py-3 rounded-full bg-gradient-to-r from-cyan-500/10 to-blue-500/10 border border-cyan-500/20 backdrop-blur-xl mb-8 transition-all duration-1000 ${isVisible ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-4'}`}>
                        <FireIcon className="w-5 h-5 text-cyan-400" />
                        <span className="text-sm font-semibold text-cyan-300">AI-Powered Insurance Revolution</span>
                        <StarIcon className="w-5 h-5 text-cyan-400" />
                    </div>

                    {/* Main Hero Heading */}
                    <h1 className={`text-6xl md:text-8xl font-black mb-8 transition-all duration-1000 delay-100 ${isVisible ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-8'}`}>
                        <span className="block bg-gradient-to-r from-white via-cyan-200 to-blue-200 bg-clip-text text-transparent">
                            Drive Smart.
                        </span>
                        <span className="block bg-gradient-to-r from-cyan-400 via-blue-400 to-purple-400 bg-clip-text text-transparent mt-4">
                            Pay Less.
                        </span>
                    </h1>

                    {/* Subheading */}
                    <p className={`text-xl md:text-2xl text-gray-300 mb-12 max-w-3xl mx-auto leading-relaxed transition-all duration-1000 delay-200 ${isVisible ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-8'}`}>
                        Revolutionary telematics insurance powered by AI. Get personalized rates based on how you actually drive, not statistics.
                    </p>

                    {/* CTA Buttons */}
                    <div className={`flex flex-col sm:flex-row gap-4 justify-center items-center mb-16 transition-all duration-1000 delay-300 ${isVisible ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-8'}`}>
                        {isAuthenticated ? (
                            <>
                                <button
                                    onClick={() => navigate('/')}
                                    className="group relative px-8 py-5 bg-gradient-to-r from-cyan-500 to-blue-600 rounded-2xl font-bold text-lg shadow-2xl shadow-cyan-500/50 hover:shadow-cyan-500/70 transform hover:scale-105 transition-all duration-300 overflow-hidden"
                                >
                                    <span className="relative z-10 flex items-center gap-2">
                                        <RocketLaunchIcon className="w-6 h-6" />
                                        Go to Dashboard
                                        <ArrowRightIcon className="w-5 h-5 group-hover:translate-x-1 transition-transform" />
                                    </span>
                                    <div className="absolute inset-0 bg-gradient-to-r from-blue-600 to-purple-600 opacity-0 group-hover:opacity-100 transition-opacity duration-300" />
                                </button>
                            </>
                        ) : (
                            <>
                                <button
                                    onClick={() => navigate('/signup')}
                                    className="group relative px-10 py-5 bg-gradient-to-r from-cyan-500 to-blue-600 rounded-2xl font-bold text-xl shadow-2xl shadow-cyan-500/50 hover:shadow-cyan-500/70 transform hover:scale-105 transition-all duration-300"
                                >
                                    <span className="relative z-10 flex items-center gap-3">
                                        Get Started Free
                                        <ArrowRightIcon className="w-6 h-6 group-hover:translate-x-2 transition-transform" />
                                    </span>
                                </button>
                                <button
                                    onClick={() => navigate('/login')}
                                    className="px-10 py-5 bg-white/5 backdrop-blur-xl border-2 border-white/10 hover:border-cyan-500/50 rounded-2xl font-semibold text-xl hover:bg-white/10 transform hover:scale-105 transition-all duration-300"
                                >
                                    Sign In
                                </button>
                            </>
                        )}
                    </div>

                    {/* Stats - Modern Bento Box Style */}
                    {isAuthenticated && summary?.data && (
                        <div className={`grid grid-cols-2 md:grid-cols-4 gap-4 max-w-5xl mx-auto transition-all duration-1000 delay-400 ${isVisible ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-8'}`}>
                            <div className="group relative p-6 bg-gradient-to-br from-cyan-500/10 to-transparent border border-cyan-500/20 rounded-2xl backdrop-blur-xl hover:bg-cyan-500/20 transition-all duration-300">
                                <div className="text-4xl font-black bg-gradient-to-r from-cyan-400 to-blue-400 bg-clip-text text-transparent mb-2">
                                    {Math.round(summary.data.safety_score || 85)}
                                </div>
                                <div className="text-sm font-medium text-cyan-300">Safety Score</div>
                            </div>
                            <div className="group relative p-6 bg-gradient-to-br from-blue-500/10 to-transparent border border-blue-500/20 rounded-2xl backdrop-blur-xl hover:bg-blue-500/20 transition-all duration-300">
                                <div className="text-4xl font-black bg-gradient-to-r from-blue-400 to-purple-400 bg-clip-text text-transparent mb-2">
                                    ${Math.round(summary.data.total_savings || 0)}
                                </div>
                                <div className="text-sm font-medium text-blue-300">Total Savings</div>
                            </div>
                            <div className="group relative p-6 bg-gradient-to-br from-purple-500/10 to-transparent border border-purple-500/20 rounded-2xl backdrop-blur-xl hover:bg-purple-500/20 transition-all duration-300">
                                <div className="text-4xl font-black bg-gradient-to-r from-purple-400 to-pink-400 bg-clip-text text-transparent mb-2">
                                    {summary.data.reward_points || 0}
                                </div>
                                <div className="text-sm font-medium text-purple-300">Reward Points</div>
                            </div>
                            <div className="group relative p-6 bg-gradient-to-br from-pink-500/10 to-transparent border border-pink-500/20 rounded-2xl backdrop-blur-xl hover:bg-pink-500/20 transition-all duration-300">
                                <div className="text-4xl font-black bg-gradient-to-r from-pink-400 to-rose-400 bg-clip-text text-transparent mb-2">
                                    {summary.data.total_trips || 0}
                                </div>
                                <div className="text-sm font-medium text-pink-300">Trips Tracked</div>
                            </div>
                        </div>
                    )}
                </div>

                {/* Scroll Indicator */}
                <div className="absolute bottom-8 left-1/2 transform -translate-x-1/2 animate-bounce">
                    <div className="w-6 h-10 border-2 border-cyan-500/50 rounded-full flex justify-center p-2">
                        <div className="w-1 h-3 bg-cyan-500 rounded-full animate-pulse" />
                    </div>
                </div>
            </section>

            {/* Stats Section - Redesigned Modern Grid */}
            <section className="relative py-24 px-4 z-10">
                <div className="max-w-7xl mx-auto">
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
                        <div className="relative group">
                            <div className="absolute inset-0 bg-gradient-to-r from-cyan-500 to-blue-500 rounded-3xl blur-xl opacity-25 group-hover:opacity-40 transition-opacity" />
                            <div className="relative p-8 bg-slate-900/50 backdrop-blur-xl border border-cyan-500/20 rounded-3xl hover:border-cyan-500/40 transition-all duration-300">
                                <div className="text-5xl font-black bg-gradient-to-r from-cyan-400 to-blue-400 bg-clip-text text-transparent mb-2">
                                    50K+
                                </div>
                                <div className="text-sm font-semibold text-gray-400">Active Drivers</div>
                            </div>
                        </div>
                        <div className="relative group">
                            <div className="absolute inset-0 bg-gradient-to-r from-blue-500 to-purple-500 rounded-3xl blur-xl opacity-25 group-hover:opacity-40 transition-opacity" />
                            <div className="relative p-8 bg-slate-900/50 backdrop-blur-xl border border-blue-500/20 rounded-3xl hover:border-blue-500/40 transition-all duration-300">
                                <div className="text-5xl font-black bg-gradient-to-r from-blue-400 to-purple-400 bg-clip-text text-transparent mb-2">
                                    $2.5M+
                                </div>
                                <div className="text-sm font-semibold text-gray-400">Total Savings</div>
                            </div>
                        </div>
                        <div className="relative group">
                            <div className="absolute inset-0 bg-gradient-to-r from-purple-500 to-pink-500 rounded-3xl blur-xl opacity-25 group-hover:opacity-40 transition-opacity" />
                            <div className="relative p-8 bg-slate-900/50 backdrop-blur-xl border border-purple-500/20 rounded-3xl hover:border-purple-500/40 transition-all duration-300">
                                <div className="text-5xl font-black bg-gradient-to-r from-purple-400 to-pink-400 bg-clip-text text-transparent mb-2">
                                    1M+
                                </div>
                                <div className="text-sm font-semibold text-gray-400">Trips Analyzed</div>
                            </div>
                        </div>
                        <div className="relative group">
                            <div className="absolute inset-0 bg-gradient-to-r from-pink-500 to-rose-500 rounded-3xl blur-xl opacity-25 group-hover:opacity-40 transition-opacity" />
                            <div className="relative p-8 bg-slate-900/50 backdrop-blur-xl border border-pink-500/20 rounded-3xl hover:border-pink-500/40 transition-all duration-300">
                                <div className="text-5xl font-black bg-gradient-to-r from-pink-400 to-rose-400 bg-clip-text text-transparent mb-2">
                                    95%
                                </div>
                                <div className="text-sm font-semibold text-gray-400">Avg Safety Score</div>
                            </div>
                        </div>
                    </div>
                </div>
            </section>

            {/* Features Section - Modern Bento Box Layout */}
            <section className="relative py-24 px-4 z-10">
                <div className="max-w-7xl mx-auto">
                    {/* Section Header */}
                    <div className="text-center mb-20">
                        <div className="inline-flex items-center gap-2 px-6 py-3 rounded-full bg-cyan-500/10 border border-cyan-500/20 backdrop-blur-xl mb-6">
                            <SparklesIcon className="w-5 h-5 text-cyan-400" />
                            <span className="text-sm font-semibold text-cyan-300">Powerful Features</span>
                        </div>
                        <h2 className="text-5xl md:text-6xl font-black mb-6">
                            <span className="bg-gradient-to-r from-white to-gray-300 bg-clip-text text-transparent">
                                Everything You Need
                            </span>
                        </h2>
                        <p className="text-xl text-gray-400 max-w-2xl mx-auto">
                            Advanced technology meets simple, transparent insurance
                        </p>
                    </div>

                    {/* Bento Grid */}
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                        {/* Large Feature Card */}
                        <div className="md:col-span-2 md:row-span-2 relative group">
                            <div className="absolute inset-0 bg-gradient-to-r from-cyan-500 to-blue-500 rounded-3xl blur-2xl opacity-20 group-hover:opacity-30 transition-opacity" />
                            <div className="relative h-full p-10 bg-slate-900/50 backdrop-blur-xl border border-cyan-500/20 rounded-3xl hover:border-cyan-500/40 transition-all duration-300">
                                <div className="flex items-start justify-between mb-6">
                                    <div className="p-4 bg-gradient-to-br from-cyan-500 to-blue-600 rounded-2xl">
                                        <CpuChipIcon className="w-10 h-10 text-white" />
                                    </div>
                                </div>
                                <h3 className="text-4xl font-black mb-4 bg-gradient-to-r from-white to-cyan-200 bg-clip-text text-transparent">
                                    AI-Powered Risk Analysis
                                </h3>
                                <p className="text-lg text-gray-400 mb-8 leading-relaxed">
                                    Our advanced machine learning algorithms analyze millions of data points in real-time to give you the most accurate risk assessment and personalized rates.
                                </p>
                                <div className="flex flex-wrap gap-2">
                                    <span className="px-4 py-2 bg-cyan-500/10 border border-cyan-500/20 rounded-full text-sm text-cyan-300">Real-time Analysis</span>
                                    <span className="px-4 py-2 bg-cyan-500/10 border border-cyan-500/20 rounded-full text-sm text-cyan-300">99.9% Accurate</span>
                                    <span className="px-4 py-2 bg-cyan-500/10 border border-cyan-500/20 rounded-full text-sm text-cyan-300">Privacy First</span>
                                </div>
                            </div>
                        </div>

                        {/* Small Feature Cards */}
                        <div className="relative group">
                            <div className="absolute inset-0 bg-gradient-to-r from-blue-500 to-purple-500 rounded-3xl blur-2xl opacity-20 group-hover:opacity-30 transition-opacity" />
                            <div className="relative h-full p-8 bg-slate-900/50 backdrop-blur-xl border border-blue-500/20 rounded-3xl hover:border-blue-500/40 transition-all duration-300">
                                <div className="p-3 bg-gradient-to-br from-blue-500 to-purple-600 rounded-xl w-fit mb-4">
                                    <BoltIcon className="w-8 h-8 text-white" />
                                </div>
                                <h3 className="text-2xl font-bold mb-3 text-white">
                                    Instant Feedback
                                </h3>
                                <p className="text-gray-400">
                                    Get real-time alerts and safety recommendations during every drive
                                </p>
                            </div>
                        </div>

                        <div className="relative group">
                            <div className="absolute inset-0 bg-gradient-to-r from-purple-500 to-pink-500 rounded-3xl blur-2xl opacity-20 group-hover:opacity-30 transition-opacity" />
                            <div className="relative h-full p-8 bg-slate-900/50 backdrop-blur-xl border border-purple-500/20 rounded-3xl hover:border-purple-500/40 transition-all duration-300">
                                <div className="p-3 bg-gradient-to-br from-purple-500 to-pink-600 rounded-xl w-fit mb-4">
                                    <ChartBarIcon className="w-8 h-8 text-white" />
                                </div>
                                <h3 className="text-2xl font-bold mb-3 text-white">
                                    Smart Analytics
                                </h3>
                                <p className="text-gray-400">
                                    Comprehensive insights into your driving patterns and safety
                                </p>
                            </div>
                        </div>

                        <div className="relative group">
                            <div className="absolute inset-0 bg-gradient-to-r from-emerald-500 to-teal-500 rounded-3xl blur-2xl opacity-20 group-hover:opacity-30 transition-opacity" />
                            <div className="relative h-full p-8 bg-slate-900/50 backdrop-blur-xl border border-emerald-500/20 rounded-3xl hover:border-emerald-500/40 transition-all duration-300">
                                <div className="p-3 bg-gradient-to-br from-emerald-500 to-teal-600 rounded-xl w-fit mb-4">
                                    <CurrencyDollarIcon className="w-8 h-8 text-white" />
                                </div>
                                <h3 className="text-2xl font-bold mb-3 text-white">
                                    Save up to 40%
                                </h3>
                                <p className="text-gray-400">
                                    Dynamic pricing rewards safe driving with lower premiums
                                </p>
                            </div>
                        </div>

                        <div className="relative group">
                            <div className="absolute inset-0 bg-gradient-to-r from-amber-500 to-orange-500 rounded-3xl blur-2xl opacity-20 group-hover:opacity-30 transition-opacity" />
                            <div className="relative h-full p-8 bg-slate-900/50 backdrop-blur-xl border border-amber-500/20 rounded-3xl hover:border-amber-500/40 transition-all duration-300">
                                <div className="p-3 bg-gradient-to-br from-amber-500 to-orange-600 rounded-xl w-fit mb-4">
                                    <TrophyIcon className="w-8 h-8 text-white" />
                                </div>
                                <h3 className="text-2xl font-bold mb-3 text-white">
                                    Earn Rewards
                                </h3>
                                <p className="text-gray-400">
                                    Unlock exclusive rewards for safe driving habits
                                </p>
                            </div>
                        </div>
                    </div>
                </div>
            </section>

            {/* How It Works - Sleek Timeline */}
            <section className="relative py-24 px-4 z-10">
                <div className="max-w-7xl mx-auto">
                    <div className="text-center mb-20">
                        <div className="inline-flex items-center gap-2 px-6 py-3 rounded-full bg-blue-500/10 border border-blue-500/20 backdrop-blur-xl mb-6">
                            <RocketLaunchIcon className="w-5 h-5 text-blue-400" />
                            <span className="text-sm font-semibold text-blue-300">Simple Process</span>
                        </div>
                        <h2 className="text-5xl md:text-6xl font-black mb-6">
                            <span className="bg-gradient-to-r from-white to-gray-300 bg-clip-text text-transparent">
                                Get Started in Minutes
                            </span>
                        </h2>
                    </div>

                    <div className="relative">
                        {/* Connection Line */}
                        <div className="absolute top-16 left-0 right-0 h-0.5 bg-gradient-to-r from-cyan-500 via-blue-500 to-purple-500 hidden lg:block" />

                        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-8">
                            {[
                                { num: '01', title: 'Sign Up', desc: 'Create your account in 60 seconds', icon: CpuChipIcon, color: 'cyan' },
                                { num: '02', title: 'Connect Device', desc: 'Link your telematics device or app', icon: BoltIcon, color: 'blue' },
                                { num: '03', title: 'Start Driving', desc: 'Our AI tracks and analyzes your trips', icon: ChartBarIcon, color: 'purple' },
                                { num: '04', title: 'Save Money', desc: 'Watch your premiums drop month by month', icon: TrophyIcon, color: 'pink' }
                            ].map((step, idx) => (
                                <div key={idx} className="relative">
                                    {/* Step Number Circle */}
                                    <div className={`relative z-10 w-16 h-16 mx-auto mb-6 bg-gradient-to-br from-${step.color}-500 to-${step.color}-600 rounded-full flex items-center justify-center text-2xl font-black shadow-lg shadow-${step.color}-500/50`}>
                                        {step.num}
                                    </div>

                                    <div className="relative group">
                                        <div className={`absolute inset-0 bg-gradient-to-r from-${step.color}-500 to-${step.color}-600 rounded-3xl blur-xl opacity-0 group-hover:opacity-30 transition-opacity`} />
                                        <div className={`relative p-8 bg-slate-900/50 backdrop-blur-xl border border-${step.color}-500/20 rounded-3xl hover:border-${step.color}-500/40 transition-all duration-300 text-center`}>
                                            <step.icon className="w-12 h-12 mx-auto mb-4 text-cyan-400" />
                                            <h3 className="text-2xl font-bold mb-3 text-white">{step.title}</h3>
                                            <p className="text-gray-400">{step.desc}</p>
                                        </div>
                                    </div>
                                </div>
                            ))}
                        </div>
                    </div>
                </div>
            </section>

            {/* CTA Section - Bold and Modern */}
            <section className="relative py-32 px-4 z-10">
                <div className="max-w-5xl mx-auto">
                    <div className="relative group">
                        <div className="absolute inset-0 bg-gradient-to-r from-cyan-500 via-blue-500 to-purple-500 rounded-[3rem] blur-3xl opacity-30 group-hover:opacity-40 transition-opacity" />
                        <div className="relative p-16 bg-gradient-to-r from-cyan-600 via-blue-600 to-purple-600 rounded-[3rem] text-center overflow-hidden">
                            <div className="absolute inset-0 bg-[url('data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iNjAiIGhlaWdodD0iNjAiIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyI+PGRlZnM+PHBhdHRlcm4gaWQ9ImdyaWQiIHdpZHRoPSI2MCIgaGVpZ2h0PSI2MCIgcGF0dGVyblVuaXRzPSJ1c2VyU3BhY2VPblVzZSI+PHBhdGggZD0iTSAxMCAwIEwgMCAwIDAgMTAiIGZpbGw9Im5vbmUiIHN0cm9rZT0id2hpdGUiIHN0cm9rZS1vcGFjaXR5PSIwLjA1IiBzdHJva2Utd2lkdGg9IjEiLz48L3BhdHRlcm4+PC9kZWZzPjxyZWN0IHdpZHRoPSIxMDAlIiBoZWlnaHQ9IjEwMCUiIGZpbGw9InVybCgjZ3JpZCkiLz48L3N2Zz4=')] opacity-20" />
                            <div className="relative z-10">
                                <h2 className="text-5xl md:text-6xl font-black mb-6 text-white">
                                    Ready to Drive Smarter?
                                </h2>
                                <p className="text-xl text-white/90 mb-10 max-w-2xl mx-auto">
                                    Join thousands of drivers saving money while improving their safety
                                </p>
                                {isAuthenticated ? (
                                    <button
                                        onClick={() => navigate('/simulator')}
                                        className="px-12 py-6 bg-white text-blue-600 rounded-2xl font-bold text-xl shadow-2xl hover:shadow-white/50 transform hover:scale-105 transition-all duration-300 inline-flex items-center gap-3"
                                    >
                                        <RocketLaunchIcon className="w-6 h-6" />
                                        Try Drive Simulator
                                    </button>
                                ) : (
                                    <button
                                        onClick={() => navigate('/signup')}
                                        className="px-12 py-6 bg-white text-blue-600 rounded-2xl font-bold text-xl shadow-2xl hover:shadow-white/50 transform hover:scale-105 transition-all duration-300 inline-flex items-center gap-3"
                                    >
                                        Get Started Free
                                        <ArrowRightIcon className="w-6 h-6" />
                                    </button>
                                )}
                            </div>
                        </div>
                    </div>
                </div>
            </section>

            {/* Footer - Clean and Minimal */}
            <footer className="relative py-16 px-4 border-t border-white/5 z-10">
                <div className="max-w-7xl mx-auto text-center">
                    <div className="flex items-center justify-center gap-3 mb-6">
                        <div className="w-12 h-12 bg-gradient-to-br from-cyan-500 to-blue-600 rounded-2xl flex items-center justify-center">
                            <ShieldCheckIcon className="w-7 h-7 text-white" />
                        </div>
                        <span className="text-3xl font-black bg-gradient-to-r from-white to-cyan-200 bg-clip-text text-transparent">
                            SmartDrive
                        </span>
                    </div>
                    <p className="text-gray-400 font-medium mb-6">
                        © 2024 SmartDrive Telematics. All rights reserved.
                    </p>
                    <div className="flex justify-center gap-8 text-sm text-gray-500">
                        <span className="hover:text-cyan-400 cursor-pointer transition-colors">Privacy Policy</span>
                        <span className="hover:text-cyan-400 cursor-pointer transition-colors">Terms of Service</span>
                        <span className="hover:text-cyan-400 cursor-pointer transition-colors">Contact Us</span>
                    </div>
                </div>
            </footer>

            <style>{`
        @keyframes blob {
          0%, 100% { transform: translate(0px, 0px) scale(1); }
          33% { transform: translate(30px, -50px) scale(1.1); }
          66% { transform: translate(-20px, 20px) scale(0.9); }
        }
        .animate-blob {
          animation: blob 15s infinite;
        }
        .delay-1000 {
          animation-delay: 5s;
        }
        .delay-2000 {
          animation-delay: 10s;
        }
      `}</style>
        </div>
    )
}
