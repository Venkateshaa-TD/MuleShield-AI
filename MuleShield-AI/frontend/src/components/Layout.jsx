/**
 * MuleShield AI - Layout Component
 * Main application layout with sidebar navigation
 */

import { NavLink, useLocation } from 'react-router-dom'
import { useState, useEffect } from 'react'
import { systemApi } from '../api'
import {
  HomeIcon,
  UserGroupIcon,
  ExclamationTriangleIcon,
  ShareIcon,
  FolderIcon,
  DocumentTextIcon,
  Cog6ToothIcon,
  ShieldCheckIcon,
  SignalIcon,
} from '@heroicons/react/24/outline'

const navigation = [
  { name: 'Dashboard', href: '/dashboard', icon: HomeIcon },
  { name: 'Transaction Stream', href: '/stream', icon: SignalIcon },
  { name: 'Accounts', href: '/accounts', icon: UserGroupIcon },
  { name: 'Alerts', href: '/alerts', icon: ExclamationTriangleIcon },
  { name: 'Network Graph', href: '/network', icon: ShareIcon },
  { name: 'Cases', href: '/cases', icon: FolderIcon },
  { name: 'Reports', href: '/reports', icon: DocumentTextIcon },
]

export default function Layout({ children }) {
  const location = useLocation()
  const [systemStatus, setSystemStatus] = useState('checking')

  useEffect(() => {
    checkSystemHealth()
  }, [])

  const checkSystemHealth = async () => {
    try {
      const response = await systemApi.health()
      setSystemStatus(response.data.initialized ? 'healthy' : 'initializing')
    } catch (error) {
      setSystemStatus('error')
    }
  }

  return (
    <div className="min-h-screen flex">
      {/* Sidebar */}
      <aside className="sidebar">
        <div className="flex flex-col h-full">
          {/* Logo */}
          <div className="flex items-center gap-3 px-4 py-5 border-b border-gray-800">
            <ShieldCheckIcon className="h-8 w-8 text-mule-500" />
            <div>
              <h1 className="text-lg font-bold text-white">MuleShield AI</h1>
              <p className="text-xs text-gray-400">AML Detection System</p>
            </div>
          </div>

          {/* Navigation */}
          <nav className="flex-1 py-4 space-y-1">
            {navigation.map((item) => {
              const isActive = location.pathname.startsWith(item.href)
              return (
                <NavLink
                  key={item.name}
                  to={item.href}
                  className={`sidebar-link ${isActive ? 'active' : ''}`}
                >
                  <item.icon className="mr-3 h-5 w-5" />
                  {item.name}
                </NavLink>
              )
            })}
          </nav>

          {/* System Status */}
          <div className="p-4 border-t border-gray-800">
            <div className="flex items-center gap-2">
              <div className={`status-dot ${
                systemStatus === 'healthy' ? 'status-dot-active' :
                systemStatus === 'error' ? 'status-dot-error' :
                'status-dot-warning'
              }`} />
              <span className="text-sm text-gray-400">
                {systemStatus === 'healthy' ? 'System Online' :
                 systemStatus === 'error' ? 'System Error' :
                 'Initializing...'}
              </span>
            </div>
            <p className="text-xs text-gray-500 mt-1">v1.0.0</p>
          </div>
        </div>
      </aside>

      {/* Main Content */}
      <main className="flex-1 ml-64">
        {/* Top Bar */}
        <header className="bg-white border-b border-gray-200 px-6 py-4">
          <div className="flex items-center justify-between">
            <h2 className="text-xl font-semibold text-gray-900">
              {navigation.find(n => location.pathname.startsWith(n.href))?.name || 'MuleShield AI'}
            </h2>
            <div className="flex items-center gap-4">
              <span className="text-sm text-gray-500">
                {new Date().toLocaleDateString('en-US', { 
                  weekday: 'long', 
                  year: 'numeric', 
                  month: 'long', 
                  day: 'numeric' 
                })}
              </span>
              <button className="btn btn-secondary text-sm">
                <Cog6ToothIcon className="h-4 w-4 mr-2" />
                Settings
              </button>
            </div>
          </div>
        </header>

        {/* Page Content */}
        <div className="p-6">
          {children}
        </div>
      </main>
    </div>
  )
}
