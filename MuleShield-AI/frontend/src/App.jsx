/**
 * MuleShield AI - Main Application Component
 * Banking-Grade AML and Mule Account Detection System
 */

import { Routes, Route, Navigate } from 'react-router-dom'
import { ReactFlowProvider } from 'reactflow'
import Layout from './components/Layout'
import Dashboard from './pages/Dashboard'
import Accounts from './pages/Accounts'
import AccountDetail from './pages/AccountDetail'
import Alerts from './pages/Alerts'
import AlertDetail from './pages/AlertDetail'
import NetworkGraph from './pages/NetworkGraph'
import Cases from './pages/Cases'
import Reports from './pages/Reports'

function App() {
  return (
    <Layout>
      <Routes>
        <Route path="/" element={<Navigate to="/dashboard" replace />} />
        <Route path="/dashboard" element={<Dashboard />} />
        <Route path="/accounts" element={<Accounts />} />
        <Route path="/accounts/:id" element={<AccountDetail />} />
        <Route path="/alerts" element={<Alerts />} />
        <Route path="/alerts/:id" element={<AlertDetail />} />
        <Route path="/network" element={<ReactFlowProvider><NetworkGraph /></ReactFlowProvider>} />
        <Route path="/cases" element={<Cases />} />
        <Route path="/cases/:id" element={<Cases />} />
        <Route path="/reports" element={<Reports />} />
      </Routes>
    </Layout>
  )
}

export default App
