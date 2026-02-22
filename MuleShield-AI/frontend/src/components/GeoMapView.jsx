/**
 * MuleShield AI - Geographic Map Visualization
 * Shows account locations and transaction flows on an interactive map
 */

import { useEffect, useMemo, useRef } from 'react'
import { MapContainer, TileLayer, CircleMarker, Polyline, Popup, useMap } from 'react-leaflet'
import 'leaflet/dist/leaflet.css'

// Fix for marker icons in React-Leaflet
import L from 'leaflet'
delete L.Icon.Default.prototype._getIconUrl
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon-2x.png',
  iconUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon.png',
  shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-shadow.png',
})

// Auto-fit map to markers
function FitBounds({ bounds }) {
  const map = useMap()
  useEffect(() => {
    if (bounds && bounds.length > 0) {
      map.fitBounds(bounds, { padding: [50, 50], maxZoom: 6 })
    }
  }, [map, bounds])
  return null
}

// Location marker component
function LocationMarker({ location, onClick }) {
  const { latitude, longitude, city, account_count, avg_risk, mule_count } = location
  
  // Validate coordinates
  if (!latitude || !longitude) {
    return null
  }
  
  // Color based on risk level
  const getColor = () => {
    if (mule_count > 0) return '#ef4444' // Red for locations with mules
    if (avg_risk >= 70) return '#f97316' // Orange for high risk
    if (avg_risk >= 40) return '#eab308' // Yellow for medium risk
    return '#22c55e' // Green for low risk
  }
  
  // Size based on account count
  const getRadius = () => {
    return Math.min(8 + account_count * 3, 30)
  }

  return (
    <CircleMarker
      center={[latitude, longitude]}
      radius={getRadius()}
      pathOptions={{
        fillColor: getColor(),
        fillOpacity: 0.8,
        color: '#ffffff',
        weight: 2,
        opacity: 1,
      }}
      eventHandlers={{
        click: () => onClick && onClick(location),
      }}
    >
      <Popup>
        <div className="min-w-[180px] p-2">
          <h3 className="font-bold text-lg text-gray-900 border-b pb-1 mb-2">{city}</h3>
          <div className="space-y-1 text-sm">
            <div className="flex justify-between">
              <span className="text-gray-600">Accounts:</span>
              <span className="font-bold text-blue-600">{account_count}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-600">Avg Risk:</span>
              <span className={`font-bold ${avg_risk >= 70 ? 'text-red-600' : avg_risk >= 40 ? 'text-yellow-600' : 'text-green-600'}`}>
                {(avg_risk || 0).toFixed(1)}
              </span>
            </div>
            {mule_count > 0 && (
              <div className="flex justify-between">
                <span className="text-gray-600">Mule Accounts:</span>
                <span className="font-bold text-red-600">{mule_count} ⚠️</span>
              </div>
            )}
          </div>
        </div>
      </Popup>
    </CircleMarker>
  )
}

// Transaction flow line component
function TransactionFlow({ connection }) {
  const { from, to, suspicious } = connection
  
  // Validate coordinates
  if (!from?.lat || !from?.lng || !to?.lat || !to?.lng) {
    return null
  }
  
  // Curved line effect using midpoint offset
  const midLat = (from.lat + to.lat) / 2
  const midLng = (from.lng + to.lng) / 2
  const offset = Math.abs(from.lat - to.lat) * 0.2 + Math.abs(from.lng - to.lng) * 0.1
  
  const curvedPositions = [
    [from.lat, from.lng],
    [midLat + offset, midLng],
    [to.lat, to.lng]
  ]

  return (
    <Polyline
      positions={curvedPositions}
      pathOptions={{
        color: suspicious ? '#ef4444' : '#3b82f6',
        weight: suspicious ? 3 : 2,
        opacity: suspicious ? 0.9 : 0.6,
        dashArray: suspicious ? null : '5, 10',
      }}
    >
      <Popup>
        <div className="text-sm p-2">
          <p className="font-bold text-gray-900">{from.city || 'Unknown'} → {to.city || 'Unknown'}</p>
          {suspicious && <p className="text-red-600 font-bold">⚠️ Suspicious Flow</p>}
        </div>
      </Popup>
    </Polyline>
  )
}

export default function GeoMapView({ geoData, onLocationClick }) {
  const mapRef = useRef(null)
  
  // Calculate bounds for auto-fit
  const bounds = useMemo(() => {
    if (!geoData?.nodes?.length) return null
    return geoData.nodes.map(n => [n.latitude, n.longitude])
  }, [geoData])

  // Default center (US)
  const defaultCenter = [39.8283, -98.5795]
  const defaultZoom = 4

  // Stats summary
  const stats = useMemo(() => {
    if (!geoData?.nodes) return null
    return {
      totalLocations: geoData.nodes.length,
      totalAccounts: geoData.nodes.reduce((sum, n) => sum + n.account_count, 0),
      totalMules: geoData.nodes.reduce((sum, n) => sum + n.mule_count, 0),
      connections: geoData.connections?.length || 0,
      suspiciousFlows: geoData.connections?.filter(c => c.suspicious).length || 0,
    }
  }, [geoData])

  if (!geoData || !geoData.nodes || geoData.nodes.length === 0) {
    return (
      <div className="h-full flex items-center justify-center bg-slate-900 text-white">
        <div className="text-center">
          <p className="text-2xl mb-2">🗺️</p>
          <p className="text-gray-400">No geographic data available</p>
          <p className="text-sm text-gray-500">Location data will appear here</p>
        </div>
      </div>
    )
  }

  return (
    <div className="h-full relative">
      {/* Map Container */}
      <MapContainer
        ref={mapRef}
        center={defaultCenter}
        zoom={defaultZoom}
        style={{ height: '100%', width: '100%' }}
        className="rounded-xl"
      >
        <TileLayer
          url="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png"
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/attributions">CARTO</a>'
        />
        
        {/* Auto-fit to data bounds */}
        {bounds && <FitBounds bounds={bounds} />}
        
        {/* Transaction flow lines */}
        {geoData.connections?.map((connection, idx) => (
          <TransactionFlow key={`flow-${idx}`} connection={connection} />
        ))}
        
        {/* Location markers */}
        {geoData.nodes.map((location, idx) => (
          <LocationMarker
            key={`loc-${idx}`}
            location={location}
            onClick={onLocationClick}
          />
        ))}
      </MapContainer>
      
      {/* Stats Overlay */}
      {stats && (
        <div className="absolute top-4 left-4 z-[1000] bg-slate-900/95 backdrop-blur-sm rounded-xl p-4 border border-slate-700 shadow-2xl">
          <h3 className="text-white font-bold text-lg mb-3 flex items-center gap-2">
            <span>🗺️</span> Geographic Distribution
          </h3>
          <div className="grid grid-cols-2 gap-3 text-sm">
            <div className="bg-slate-800/50 rounded-lg p-2">
              <div className="text-2xl font-black text-blue-400">{stats.totalLocations}</div>
              <div className="text-gray-400 text-xs">Locations</div>
            </div>
            <div className="bg-slate-800/50 rounded-lg p-2">
              <div className="text-2xl font-black text-cyan-400">{stats.totalAccounts}</div>
              <div className="text-gray-400 text-xs">Accounts</div>
            </div>
            <div className="bg-slate-800/50 rounded-lg p-2">
              <div className="text-2xl font-black text-red-400">{stats.totalMules}</div>
              <div className="text-gray-400 text-xs">Mule Accounts</div>
            </div>
            <div className="bg-slate-800/50 rounded-lg p-2">
              <div className="text-2xl font-black text-purple-400">{stats.connections}</div>
              <div className="text-gray-400 text-xs">Connections</div>
            </div>
          </div>
          {stats.suspiciousFlows > 0 && (
            <div className="mt-3 p-2 bg-red-900/50 rounded-lg border border-red-700">
              <span className="text-red-400 text-sm font-bold">
                ⚠️ {stats.suspiciousFlows} Suspicious Flows Detected
              </span>
            </div>
          )}
        </div>
      )}
      
      {/* Legend */}
      <div className="absolute bottom-4 right-4 z-[1000] bg-slate-900/95 backdrop-blur-sm rounded-xl p-3 border border-slate-700 shadow-2xl">
        <h4 className="text-white font-bold text-sm mb-2">Legend</h4>
        <div className="space-y-2 text-xs">
          <div className="flex items-center gap-2">
            <div className="w-4 h-4 rounded-full bg-red-500 border-2 border-white"></div>
            <span className="text-gray-300">Mule Location</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-4 h-4 rounded-full bg-orange-500 border-2 border-white"></div>
            <span className="text-gray-300">High Risk</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-4 h-4 rounded-full bg-yellow-500 border-2 border-white"></div>
            <span className="text-gray-300">Medium Risk</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-4 h-4 rounded-full bg-green-500 border-2 border-white"></div>
            <span className="text-gray-300">Low Risk</span>
          </div>
          <hr className="border-slate-700 my-2" />
          <div className="flex items-center gap-2">
            <div className="w-6 h-0.5 bg-red-500"></div>
            <span className="text-gray-300">Suspicious</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-6 h-0.5 bg-blue-500" style={{ borderStyle: 'dashed' }}></div>
            <span className="text-gray-300">Normal Flow</span>
          </div>
        </div>
      </div>
    </div>
  )
}
