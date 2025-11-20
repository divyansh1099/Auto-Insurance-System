import { useQuery } from 'react-query'
import { rewardsAPI, authAPI, driverAPI, dashboardAPI } from '../services/api'
import {
  TrophyIcon,
  CheckCircleIcon,
  StarIcon,
  BoltIcon,
  AcademicCapIcon,
  SparklesIcon,
  MapPinIcon,
  ChartBarIcon
} from '@heroicons/react/24/outline'
import { CheckCircleIcon as CheckCircleSolid, StarIcon as StarSolid } from '@heroicons/react/24/solid'

export default function Rewards() {
  // Get current user to determine driver_id
  const { data: currentUser, isLoading: isLoadingUser } = useQuery(
    ['currentUser'],
    () => authAPI.getCurrentUser(),
    { retry: false }
  )
  
  // Only use driver_id if user is logged in and has one
  // Don't default to DRV-0001 - wait for user data
  const driverId = currentUser?.data?.driver_id
  
  // Fetch rewards data - only if driverId is available
  // ALL HOOKS MUST BE CALLED BEFORE ANY CONDITIONAL RETURNS
  const { data: rewardsSummary } = useQuery(
    ['rewardsSummary', driverId],
    () => rewardsAPI.getRewardsSummary(driverId),
    { 
      retry: false,
      enabled: !!driverId && !!currentUser?.data, // Only fetch if user is logged in and has driver_id
      // Fallback data if endpoint doesn't exist
      onError: () => {
        // Will use fallback data
      }
    }
  )

  const { data: milestones } = useQuery(
    ['milestones', driverId],
    () => rewardsAPI.getMilestones(driverId),
    { retry: false, enabled: !!driverId && !!currentUser?.data }
  )

  const { data: achievements } = useQuery(
    ['achievements', driverId],
    () => rewardsAPI.getAchievements(driverId),
    { retry: false, enabled: !!driverId && !!currentUser?.data }
  )

  const { data: pointsRules } = useQuery(
    ['pointsRules'],
    () => rewardsAPI.getPointsRules(),
    { retry: false }
  )

  // Fetch dashboard summary for consistent trip totals
  const { data: dashboardSummary } = useQuery(
    ['dashboardSummaryForRewards', driverId],
    () => dashboardAPI.getSummary(driverId),
    { retry: false, enabled: !!driverId && !!currentUser?.data }
  )

  // Fetch trip data for detailed metrics (perfect/excellent/good trips)
  const { data: tripsData } = useQuery(
    ['tripsForRewards', driverId],
    () => driverAPI.getTrips(driverId, 1, 100),
    { retry: false, enabled: !!driverId && !!currentUser?.data }
  )
  
  // Show loading or error state if user not logged in or doesn't have driver_id
  // THIS MUST COME AFTER ALL HOOKS
  if (isLoadingUser) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-gray-500">Loading...</div>
      </div>
    )
  }
  
  if (!currentUser?.data || !driverId) {
    return (
      <div className="space-y-6">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white">Rewards & Achievements</h1>
          <p className="text-gray-600 dark:text-gray-400 mt-1">Earn points and unlock rewards through safe driving</p>
        </div>
        <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-6">
          <p className="text-yellow-800">
            Please log in as a driver to view your rewards and achievements.
          </p>
        </div>
      </div>
    )
  }
  
  // Calculate trip metrics - use summary for totals, trips list for breakdowns
  const trips = tripsData?.data?.trips || tripsData?.trips || []
  const tripMetrics = {
    totalTrips: dashboardSummary?.data?.total_trips || trips?.length || 0,
    totalMiles: dashboardSummary?.data?.miles_driven || trips?.reduce((sum, t) => sum + (t?.distance_miles || 0), 0) || 0,
    avgTripScore: dashboardSummary?.data?.avg_trip_score || (trips?.length > 0 
      ? Math.round(trips.reduce((sum, t) => sum + (t?.trip_score || 70), 0) / trips.length)
      : 0),
    perfectTrips: trips?.filter(t => (t?.trip_score || 70) >= 95).length || 0,
    excellentTrips: trips?.filter(t => (t?.trip_score || 70) >= 80).length || 0,
    goodTrips: trips?.filter(t => (t?.trip_score || 70) >= 60 && (t?.trip_score || 70) < 80).length || 0
  }

  // Extract data with fallbacks
  const summary = rewardsSummary?.data || {
    current_points: 450,
    next_milestone: {
      points_threshold: 500,
      reward_description: '10% Extra Discount',
      points_needed: 50,
      progress_percentage: 90.0
    }
  }

  const milestonesList = milestones?.data || milestones || [
    { milestone_id: 1, points_threshold: 100, reward_name: '100 Points', reward_description: '5% Extra Discount', status: 'unlocked' },
    { milestone_id: 2, points_threshold: 250, reward_name: '250 Points', reward_description: 'Free Roadside Assistance', status: 'unlocked' },
    { milestone_id: 3, points_threshold: 500, reward_name: '500 Points', reward_description: '10% Extra Discount', status: 'pending' },
    { milestone_id: 4, points_threshold: 1000, reward_name: '1000 Points', reward_description: 'Premium Upgrade', status: 'pending' }
  ]

  const achievementsList = achievements?.data || achievements || [
    { achievement_id: 1, achievement_name: 'Safe Week', achievement_description: '7 consecutive days with no safety events', status: 'achieved' },
    { achievement_id: 2, achievement_name: 'Speed Demon Reformed', achievement_description: 'No speeding incidents in 30 days', status: 'pending' },
    { achievement_id: 3, achievement_name: 'Smooth Operator', achievement_description: '50 trips with perfect acceleration/braking', status: 'achieved' },
    { achievement_id: 4, achievement_name: 'Century Club', achievement_description: 'Complete 100 trips', status: 'pending' },
    { achievement_id: 5, achievement_name: 'Perfect Score', achievement_description: 'Achieve a trip score of 100', status: 'pending' }
  ]

  const rulesList = pointsRules?.data || pointsRules || [
    { rule_id: 1, rule_name: 'Excellent Trips', rule_description: 'Earn 10 points for trips scored 80+', min_score: 80, max_score: 100, points_awarded: 10 },
    { rule_id: 2, rule_name: 'Good Trips', rule_description: 'Earn 5 points for trips scored 60-79', min_score: 60, max_score: 79, points_awarded: 5 }
  ]

  // Get achievement icon based on status and type
  const getAchievementIcon = (achievement, status) => {
    if (status === 'achieved') {
      if (achievement.achievement_name === 'Safe Week') {
        return <CheckCircleSolid className="w-6 h-6 text-white" />
      } else if (achievement.achievement_name === 'Smooth Operator') {
        return <AcademicCapIcon className="w-6 h-6 text-white" />
      }
      return <CheckCircleSolid className="w-6 h-6 text-white" />
    } else {
      if (achievement.achievement_name.includes('Speed')) {
        return <BoltIcon className="w-6 h-6 text-gray-400" />
      } else if (achievement.achievement_name.includes('Century')) {
        return <TrophyIcon className="w-6 h-6 text-gray-400" />
      } else if (achievement.achievement_name.includes('Perfect')) {
        return <StarIcon className="w-6 h-6 text-gray-400" />
      }
      return <StarIcon className="w-6 h-6 text-gray-400" />
    }
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-cyan-50 via-blue-50 via-indigo-50 to-purple-50 dark:from-gray-900 dark:via-gray-900 dark:to-gray-800 transition-colors duration-200 relative overflow-hidden">
      {/* Animated Background Elements */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        <div className="absolute top-1/4 left-1/4 w-96 h-96 bg-cyan-200 dark:bg-cyan-900 rounded-full mix-blend-multiply dark:mix-blend-screen filter blur-3xl opacity-20 animate-blob" />
        <div className="absolute top-1/3 right-1/4 w-96 h-96 bg-violet-200 dark:bg-violet-900 rounded-full mix-blend-multiply dark:mix-blend-screen filter blur-3xl opacity-20 animate-blob animation-delay-2000" />
        <div className="absolute bottom-1/4 left-1/3 w-96 h-96 bg-fuchsia-200 dark:bg-fuchsia-900 rounded-full mix-blend-multiply dark:mix-blend-screen filter blur-3xl opacity-20 animate-blob animation-delay-4000" />
      </div>

      <div className="relative z-10 space-y-6 p-6">
        {/* Header */}
        <div className="bg-white/80 dark:bg-gray-800/80 backdrop-blur-xl rounded-2xl shadow-lg border border-white/30 dark:border-gray-700/30 transition-colors duration-200 p-6">
          <h1 className="text-3xl md:text-4xl font-bold bg-gradient-to-r from-cyan-600 via-blue-600 to-purple-600 dark:from-cyan-400 dark:via-blue-400 dark:to-purple-400 bg-clip-text text-transparent">Rewards & Achievements</h1>
          <p className="text-gray-600 dark:text-gray-400 mt-1 text-lg">Earn points and unlock rewards through safe driving</p>
        </div>

      {/* Current Reward Points Card */}
      <div className="bg-gradient-to-r from-orange-500 to-orange-600 rounded-xl shadow-lg p-8 text-white">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-6">
            <div className="w-16 h-16 bg-white/20 rounded-xl flex items-center justify-center backdrop-blur-sm">
              <TrophyIcon className="w-10 h-10 text-white" />
            </div>
            <div>
              <p className="text-sm font-medium text-orange-100 mb-2">Your Reward Points</p>
              <p className="text-6xl font-bold mb-3">{summary.current_points}</p>
              <div className="w-64 bg-white/20 rounded-full h-2 mb-2">
                <div 
                  className="bg-white dark:bg-gray-800 h-2 rounded-full transition-all"
                  style={{ width: `${summary.next_milestone?.progress_percentage || 90}%` }}
                />
              </div>
              <p className="text-sm text-orange-100">
                {summary.next_milestone?.points_needed || 50} points to next reward
              </p>
            </div>
          </div>
          <div className="text-right">
            <p className="text-sm font-medium text-orange-100 mb-2">Next Milestone</p>
            <p className="text-2xl font-bold mb-1">{summary.next_milestone?.points_threshold || 500} points</p>
            <p className="text-sm text-orange-100">{summary.next_milestone?.reward_description || '10% Extra Discount'}</p>
          </div>
        </div>
      </div>

      {/* Trip Performance Metrics */}
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
        <div className="flex items-center gap-2 mb-4">
          <MapPinIcon className="w-6 h-6 text-gray-400" />
          <h2 className="text-2xl font-bold text-gray-900 dark:text-white">Trip Performance</h2>
        </div>
        <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
          <div className="bg-gray-50 dark:bg-gray-700 rounded-lg p-4">
            <div className="text-sm text-gray-600 dark:text-gray-400 mb-1">Total Trips</div>
            <div className="text-2xl font-bold text-gray-900 dark:text-white">{Math.round(tripMetrics.totalTrips || 0)}</div>
          </div>
          <div className="bg-gray-50 dark:bg-gray-700 rounded-lg p-4">
            <div className="text-sm text-gray-600 dark:text-gray-400 mb-1">Total Miles</div>
            <div className="text-2xl font-bold text-gray-900 dark:text-white">{Math.round(tripMetrics.totalMiles || 0)}</div>
          </div>
          <div className="bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 rounded-lg p-4">
            <div className="text-sm text-gray-600 dark:text-gray-400 mb-1">Perfect Trips</div>
            <div className="text-2xl font-bold text-green-600">{Math.round(tripMetrics.perfectTrips || 0)}</div>
            <div className="text-xs text-gray-500">Score ≥ 95</div>
          </div>
          <div className="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg p-4">
            <div className="text-sm text-gray-600 dark:text-gray-400 mb-1">Excellent Trips</div>
            <div className="text-2xl font-bold text-blue-600">{Math.round(tripMetrics.excellentTrips || 0)}</div>
            <div className="text-xs text-gray-500">Score ≥ 80</div>
          </div>
          <div className="bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-800 rounded-lg p-4">
            <div className="text-sm text-gray-600 dark:text-gray-400 mb-1">Avg Score</div>
            <div className="text-2xl font-bold text-yellow-600">{Math.round(tripMetrics.avgTripScore || 0)}</div>
          </div>
        </div>
      </div>

      {/* Reward Milestones Section */}
      <div>
        <div className="flex items-center gap-2 mb-4">
          <SparklesIcon className="w-6 h-6 text-gray-400" />
          <h2 className="text-2xl font-bold text-gray-900 dark:text-white">Reward Milestones</h2>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {milestonesList.map((milestone) => {
            const isUnlocked = milestone.status === 'unlocked'
            return (
              <div
                key={milestone.milestone_id}
                className={`rounded-xl shadow-lg p-6 ${
                  isUnlocked ? 'bg-green-500 text-white' : 'bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300'
                }`}
              >
                <div className="flex items-center justify-between mb-4">
                  {isUnlocked ? (
                    <div className="w-12 h-12 bg-white/20 rounded-full flex items-center justify-center">
                      <CheckCircleSolid className="w-7 h-7 text-white" />
                    </div>
                  ) : (
                    <div className="w-12 h-12 bg-gray-200 dark:bg-gray-700 rounded-full flex items-center justify-center">
                      {milestone.points_threshold >= 1000 ? (
                        <TrophyIcon className="w-7 h-7 text-gray-400" />
                      ) : (
                        <StarIcon className="w-7 h-7 text-gray-400" />
                      )}
                    </div>
                  )}
                  {isUnlocked && (
                    <span className="px-2 py-1 bg-white/20 rounded text-xs font-semibold">Unlocked</span>
                  )}
                </div>
                <p className={`text-2xl font-bold mb-2 ${isUnlocked ? 'text-white' : 'text-gray-900 dark:text-white'}`}>
                  {milestone.points_threshold} Points
                </p>
                <p className={`text-sm ${isUnlocked ? 'text-green-100' : 'text-gray-600 dark:text-gray-400'}`}>
                  {milestone.reward_description}
                </p>
              </div>
            )
          })}
        </div>
      </div>

      {/* Achievements Section */}
      <div>
        <div className="flex items-center gap-2 mb-4">
          <AcademicCapIcon className="w-6 h-6 text-gray-400" />
          <h2 className="text-2xl font-bold text-gray-900 dark:text-white">Achievements</h2>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
          {achievementsList.map((achievement) => {
            const isAchieved = achievement.status === 'achieved'
            const bgColor = isAchieved 
              ? (achievement.achievement_name === 'Smooth Operator' ? 'bg-blue-500' : 'bg-emerald-500')
              : 'bg-gray-100 dark:bg-gray-700'
            const textColor = isAchieved ? 'text-white' : 'text-gray-700 dark:text-gray-300'
            
            return (
              <div
                key={achievement.achievement_id}
                className={`${bgColor} ${textColor} rounded-lg shadow-md p-4`}
              >
                <div className="flex items-start justify-between mb-2">
                  <div className={`w-10 h-10 ${isAchieved ? 'bg-white/20' : 'bg-gray-200'} rounded-full flex items-center justify-center flex-shrink-0`}>
                    {getAchievementIcon(achievement, achievement.status)}
                  </div>
                  {isAchieved && (
                    <CheckCircleSolid className={`w-5 h-5 ${isAchieved ? 'text-white' : 'text-gray-400'} flex-shrink-0`} />
                  )}
                </div>
                <p className={`text-base font-bold mb-1 ${isAchieved ? 'text-white' : 'text-gray-900 dark:text-white'}`}>
                  {achievement.achievement_name}
                </p>
                <p className={`text-xs leading-tight ${isAchieved ? 'text-white/90' : 'text-gray-600 dark:text-gray-400'}`}>
                  {achievement.achievement_description}
                </p>
              </div>
            )
          })}
        </div>
      </div>

      {/* How to Earn Points Section */}
      <div>
        <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-4">How to Earn Points</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {rulesList.map((rule) => (
            <div key={rule.rule_id} className="bg-white dark:bg-gray-800 rounded-xl shadow-lg p-6">
              <div className="flex items-center gap-3 mb-4">
                {rule.rule_name === 'Excellent Trips' ? (
                  <StarIcon className="w-8 h-8 text-blue-500" />
                ) : rule.rule_name === 'Good Trips' ? (
                  <CheckCircleIcon className="w-8 h-8 text-green-500" />
                ) : (
                  <TrophyIcon className="w-8 h-8 text-purple-500" />
                )}
              </div>
              <p className="text-lg font-bold text-gray-900 dark:text-white mb-2">{rule.rule_name}</p>
              <p className="text-sm text-gray-600 dark:text-gray-400">{rule.rule_description}</p>
            </div>
          ))}
          {/* Achievements Card */}
          <div className="bg-white dark:bg-gray-800 rounded-xl shadow-lg p-6">
            <div className="flex items-center gap-3 mb-4">
              <TrophyIcon className="w-8 h-8 text-purple-500" />
            </div>
            <p className="text-lg font-bold text-gray-900 dark:text-white mb-2">Achievements</p>
            <p className="text-sm text-gray-600 dark:text-gray-400">Unlock special achievements for bonus points</p>
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
      `}</style>
    </div>
  )
}
