import { useState, useEffect } from 'react'
import { useQuery } from 'react-query'
import { authAPI, driverAPI } from '../services/api'
import {
  UserIcon,
  EnvelopeIcon,
  PhoneIcon,
  MapPinIcon,
  IdentificationIcon,
  CalendarIcon,
  ShieldCheckIcon
} from '@heroicons/react/24/outline'

export default function Profile() {
  const { data: currentUser } = useQuery(
    ['currentUser'],
    () => authAPI.getCurrentUser(),
    { retry: false }
  )

  const driverId = currentUser?.data?.driver_id || 'DRV-0001'

  const { data: driverData } = useQuery(
    ['driver', driverId],
    () => driverAPI.getDriver(driverId),
    { 
      retry: false, 
      enabled: !!driverId 
    }
  )

  const driver = driverData?.data || {}

  const formatDate = (dateString) => {
    if (!dateString) return 'N/A'
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'long',
      day: 'numeric'
    })
  }

  const getInitials = (firstName, lastName) => {
    const first = firstName?.charAt(0) || 'U'
    const last = lastName?.charAt(0) || ''
    return `${first}${last}`.toUpperCase()
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold text-gray-900">My Profile</h1>
        <p className="mt-2 text-gray-600">Manage your account information and preferences</p>
      </div>

      {/* Profile Card */}
      <div className="bg-white rounded-xl shadow-md overflow-hidden">
        {/* Profile Header */}
        <div className="bg-gradient-to-r from-blue-600 to-blue-700 px-8 py-12">
          <div className="flex items-center">
            <div className="w-24 h-24 bg-white rounded-full flex items-center justify-center mr-6 shadow-lg">
              <span className="text-3xl font-bold text-blue-600">
                {getInitials(driver.first_name, driver.last_name)}
              </span>
            </div>
            <div className="text-white">
              <h2 className="text-3xl font-bold">
                {driver.first_name || 'User'} {driver.last_name || ''}
              </h2>
              <p className="text-blue-100 mt-1">{driver.email || currentUser?.data?.email || 'No email'}</p>
              {currentUser?.data?.is_admin && (
                <span className="inline-flex items-center mt-2 px-3 py-1 rounded-full text-xs font-semibold bg-blue-500 text-white">
                  <ShieldCheckIcon className="w-4 h-4 mr-1" />
                  Administrator
                </span>
              )}
            </div>
          </div>
        </div>

        {/* Profile Content */}
        <div className="p-8">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
            {/* Personal Information */}
            <div>
              <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
                <UserIcon className="w-5 h-5 mr-2 text-blue-600" />
                Personal Information
              </h3>
              <div className="space-y-4">
                <div className="flex items-start">
                  <div className="w-32 text-gray-500 text-sm">Full Name</div>
                  <div className="flex-1 font-medium text-gray-900">
                    {driver.first_name || 'N/A'} {driver.last_name || ''}
                  </div>
                </div>
                <div className="flex items-start">
                  <div className="w-32 text-gray-500 text-sm">Email</div>
                  <div className="flex-1 font-medium text-gray-900 flex items-center">
                    <EnvelopeIcon className="w-4 h-4 mr-2 text-gray-400" />
                    {driver.email || currentUser?.data?.email || 'N/A'}
                  </div>
                </div>
                <div className="flex items-start">
                  <div className="w-32 text-gray-500 text-sm">Phone</div>
                  <div className="flex-1 font-medium text-gray-900 flex items-center">
                    <PhoneIcon className="w-4 h-4 mr-2 text-gray-400" />
                    {driver.phone || 'N/A'}
                  </div>
                </div>
                <div className="flex items-start">
                  <div className="w-32 text-gray-500 text-sm">Date of Birth</div>
                  <div className="flex-1 font-medium text-gray-900 flex items-center">
                    <CalendarIcon className="w-4 h-4 mr-2 text-gray-400" />
                    {formatDate(driver.date_of_birth)}
                  </div>
                </div>
                <div className="flex items-start">
                  <div className="w-32 text-gray-500 text-sm">Gender</div>
                  <div className="flex-1 font-medium text-gray-900">
                    {driver.gender || 'N/A'}
                  </div>
                </div>
                <div className="flex items-start">
                  <div className="w-32 text-gray-500 text-sm">Marital Status</div>
                  <div className="flex-1 font-medium text-gray-900">
                    {driver.marital_status || 'N/A'}
                  </div>
                </div>
              </div>
            </div>

            {/* License & Address Information */}
            <div>
              <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
                <IdentificationIcon className="w-5 h-5 mr-2 text-blue-600" />
                License & Address
              </h3>
              <div className="space-y-4">
                <div className="flex items-start">
                  <div className="w-32 text-gray-500 text-sm">License Number</div>
                  <div className="flex-1 font-medium text-gray-900">
                    {driver.license_number || 'N/A'}
                  </div>
                </div>
                <div className="flex items-start">
                  <div className="w-32 text-gray-500 text-sm">License State</div>
                  <div className="flex-1 font-medium text-gray-900">
                    {driver.license_state || 'N/A'}
                  </div>
                </div>
                <div className="flex items-start">
                  <div className="w-32 text-gray-500 text-sm">Years Licensed</div>
                  <div className="flex-1 font-medium text-gray-900">
                    {driver.years_licensed || 'N/A'} {driver.years_licensed ? 'years' : ''}
                  </div>
                </div>
                <div className="flex items-start">
                  <div className="w-32 text-gray-500 text-sm">Address</div>
                  <div className="flex-1 font-medium text-gray-900 flex items-start">
                    <MapPinIcon className="w-4 h-4 mr-2 text-gray-400 mt-0.5 flex-shrink-0" />
                    <div>
                      {driver.address && (
                        <div>{driver.address}</div>
                      )}
                      {(driver.city || driver.state || driver.zip_code) && (
                        <div className="text-gray-600">
                          {[driver.city, driver.state, driver.zip_code].filter(Boolean).join(', ')}
                        </div>
                      )}
                      {!driver.address && !driver.city && 'N/A'}
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Account Information */}
          <div className="mt-8 pt-8 border-t border-gray-200">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Account Information</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="flex items-start">
                <div className="w-32 text-gray-500 text-sm">Driver ID</div>
                <div className="flex-1 font-medium text-gray-900 font-mono">
                  {driverId}
                </div>
              </div>
              <div className="flex items-start">
                <div className="w-32 text-gray-500 text-sm">Username</div>
                <div className="flex-1 font-medium text-gray-900">
                  {currentUser?.data?.username || 'N/A'}
                </div>
              </div>
              <div className="flex items-start">
                <div className="w-32 text-gray-500 text-sm">Account Created</div>
                <div className="flex-1 font-medium text-gray-900">
                  {formatDate(driver.created_at)}
                </div>
              </div>
              <div className="flex items-start">
                <div className="w-32 text-gray-500 text-sm">Last Updated</div>
                <div className="flex-1 font-medium text-gray-900">
                  {formatDate(driver.updated_at)}
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

