import React, { useEffect } from 'react'
import {
  CheckCircleIcon,
  XCircleIcon,
  InformationCircleIcon,
  ExclamationTriangleIcon,
  XMarkIcon,
} from '@heroicons/react/24/outline'

const toastIcons = {
  success: CheckCircleIcon,
  error: XCircleIcon,
  info: InformationCircleIcon,
  warning: ExclamationTriangleIcon,
}

const toastStyles = {
  success: 'bg-green-50 border-green-200 text-green-800',
  error: 'bg-red-50 border-red-200 text-red-800',
  info: 'bg-blue-50 border-blue-200 text-blue-800',
  warning: 'bg-yellow-50 border-yellow-200 text-yellow-800',
}

const iconStyles = {
  success: 'text-green-400',
  error: 'text-red-400',
  info: 'text-blue-400',
  warning: 'text-yellow-400',
}

export default function Toast({ message, type = 'info', duration = 3000, onClose }) {
  const Icon = toastIcons[type]

  useEffect(() => {
    if (duration && onClose) {
      const timer = setTimeout(onClose, duration)
      return () => clearTimeout(timer)
    }
  }, [duration, onClose])

  return (
    <div
      className={`fixed top-4 right-4 z-50 min-w-[320px] max-w-md rounded-lg border shadow-lg p-4 transition-all duration-300 ease-in-out ${toastStyles[type]}`}
      role="alert"
    >
      <div className="flex items-start">
        <div className="flex-shrink-0">
          <Icon className={`h-6 w-6 ${iconStyles[type]}`} />
        </div>
        <div className="ml-3 flex-1">
          <p className="text-sm font-medium">{message}</p>
        </div>
        {onClose && (
          <div className="ml-auto pl-3">
            <button
              onClick={onClose}
              className={`inline-flex rounded-md focus:outline-none focus:ring-2 focus:ring-offset-2 ${iconStyles[type]} hover:opacity-75`}
            >
              <span className="sr-only">Close</span>
              <XMarkIcon className="h-5 w-5" />
            </button>
          </div>
        )}
      </div>
    </div>
  )
}

export function useToast() {
  const [toast, setToast] = React.useState(null)

  const showToast = React.useCallback((message, type = 'info', duration = 3000) => {
    setToast({ message, type, duration })
  }, [])

  const hideToast = React.useCallback(() => {
    setToast(null)
  }, [])

  const ToastComponent = toast ? (
    <Toast
      message={toast.message}
      type={toast.type}
      duration={toast.duration}
      onClose={hideToast}
    />
  ) : null

  return { showToast, ToastComponent }
}
