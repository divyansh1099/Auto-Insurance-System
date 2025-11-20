import { useEffect, useRef } from 'react'
import { MapContainer, TileLayer, Marker, Popup, Polyline, useMap } from 'react-leaflet'
import 'leaflet/dist/leaflet.css'
import L from 'leaflet'
import { useTheme } from '../contexts/ThemeContext'

// Fix for default marker icon
delete L.Icon.Default.prototype._getIconUrl
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon-2x.png',
  iconUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon.png',
  shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-shadow.png',
})

// Component to update map center
function MapUpdater({ center }) {
  const map = useMap()
  useEffect(() => {
    if (center) {
      map.setView(center, map.getZoom())
    }
  }, [center, map])
  return null
}

export default function LiveMap({ currentLocation, pathHistory }) {
  const { theme } = useTheme()
  const defaultCenter = [37.7749, -122.4194] // San Francisco
  const center = currentLocation
    ? [currentLocation.latitude, currentLocation.longitude]
    : defaultCenter

  // Choose tile layer based on theme
  // Light: OpenStreetMap Standard
  // Dark: CartoDB Dark Matter
  const tileLayerUrl = theme === 'dark'
    ? 'https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png'
    : 'https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png'

  const attribution = theme === 'dark'
    ? '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/attributions">CARTO</a>'
    : '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'

  return (
    <div className="h-[400px] w-full rounded-xl overflow-hidden shadow-lg border border-gray-200 dark:border-gray-700 z-0 transition-colors duration-200">
      <MapContainer
        center={center}
        zoom={15}
        style={{ height: '100%', width: '100%' }}
      >
        <TileLayer
          key={theme} // Force re-render when theme changes
          attribution={attribution}
          url={tileLayerUrl}
        />

        <MapUpdater center={center} />

        {/* Path History */}
        {pathHistory && pathHistory.length > 0 && (
          <Polyline
            positions={pathHistory.map(loc => [loc.latitude, loc.longitude])}
            color={theme === 'dark' ? '#60A5FA' : 'blue'} // Lighter blue in dark mode
            weight={4}
            opacity={0.6}
          />
        )}

        {/* Current Location Marker */}
        {currentLocation && (
          <Marker position={[currentLocation.latitude, currentLocation.longitude]}>
            <Popup className={theme === 'dark' ? 'dark-popup' : ''}>
              <div className="text-sm font-semibold">Current Location</div>
              <div className="text-xs">
                Lat: {currentLocation.latitude.toFixed(4)}<br />
                Lon: {currentLocation.longitude.toFixed(4)}
              </div>
            </Popup>
          </Marker>
        )}
      </MapContainer>
    </div>
  )
}
