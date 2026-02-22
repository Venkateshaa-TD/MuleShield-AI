/**
 * MuleShield AI - Transaction Stream
 * Real-time transaction monitoring with Kafka-style streaming
 * 
 * Features:
 * - Live transaction feed with WebSocket
 * - Real-time alerts
 * - Stream statistics
 * - Visual transaction flow
 */

import React, { useState, useEffect, useRef, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  PlayIcon,
  StopIcon,
  SignalIcon,
  ExclamationTriangleIcon,
  ArrowTrendingUpIcon,
  CurrencyDollarIcon,
  ClockIcon,
  MapPinIcon,
  DevicePhoneMobileIcon,
  BanknotesIcon,
  ArrowsRightLeftIcon,
  ChartBarIcon,
  Cog6ToothIcon,
  ArrowPathIcon,
} from '@heroicons/react/24/outline';
import {
  SignalIcon as SignalSolidIcon,
  ExclamationTriangleIcon as ExclamationSolidIcon,
} from '@heroicons/react/24/solid';

const API_URL = 'http://localhost:8000';
const WS_URL = 'ws://localhost:8000';

// Transaction type colors and icons
const TRANSACTION_TYPES = {
  wire_domestic: { color: 'blue', label: 'Wire Transfer', icon: ArrowsRightLeftIcon },
  wire_international: { color: 'purple', label: 'Int\'l Wire', icon: ArrowsRightLeftIcon },
  ach_credit: { color: 'green', label: 'ACH Credit', icon: BanknotesIcon },
  ach_debit: { color: 'orange', label: 'ACH Debit', icon: BanknotesIcon },
  card_purchase: { color: 'cyan', label: 'Card Purchase', icon: CurrencyDollarIcon },
  card_atm: { color: 'yellow', label: 'ATM', icon: BanknotesIcon },
  p2p_transfer: { color: 'pink', label: 'P2P Transfer', icon: DevicePhoneMobileIcon },
  cash_deposit: { color: 'emerald', label: 'Cash Deposit', icon: BanknotesIcon },
  cash_withdrawal: { color: 'red', label: 'Cash Withdrawal', icon: BanknotesIcon },
  bill_payment: { color: 'indigo', label: 'Bill Payment', icon: CurrencyDollarIcon },
  check_deposit: { color: 'teal', label: 'Check Deposit', icon: BanknotesIcon },
};

// Risk level styling
const RISK_STYLES = {
  low: 'bg-green-500/20 text-green-400 border-green-500/30',
  medium: 'bg-yellow-500/20 text-yellow-400 border-yellow-500/30',
  high: 'bg-red-500/20 text-red-400 border-red-500/30',
};

export default function TransactionStream() {
  // State
  const [isStreaming, setIsStreaming] = useState(false);
  const [isConnecting, setIsConnecting] = useState(false);
  const [transactions, setTransactions] = useState([]);
  const [alerts, setAlerts] = useState([]);
  const [stats, setStats] = useState(null);
  const [config, setConfig] = useState({ tps: 3, suspiciousRate: 0.15 });
  const [showConfig, setShowConfig] = useState(false);
  const [connectionStatus, setConnectionStatus] = useState('disconnected');
  
  // Refs
  const transactionWsRef = useRef(null);
  const alertWsRef = useRef(null);
  const statsWsRef = useRef(null);
  const transactionListRef = useRef(null);
  
  // Computed stats
  const recentSuspicious = transactions.filter(t => t.is_suspicious).slice(0, 10);
  const totalVolume = transactions.reduce((sum, t) => sum + (t.amount || 0), 0);
  const suspiciousCount = transactions.filter(t => t.is_suspicious).length;
  
  // Connect to WebSocket
  const connectWebSocket = useCallback((endpoint, ref, onMessage) => {
    try {
      const ws = new WebSocket(`${WS_URL}${endpoint}`);
      
      ws.onopen = () => {
        console.log(`Connected to ${endpoint}`);
        setConnectionStatus('connected');
      };
      
      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          onMessage(data);
        } catch (e) {
          console.error('Failed to parse message:', e);
        }
      };
      
      ws.onclose = () => {
        console.log(`Disconnected from ${endpoint}`);
        if (ref.current === ws) {
          ref.current = null;
        }
      };
      
      ws.onerror = (error) => {
        console.error(`WebSocket error (${endpoint}):`, error);
      };
      
      ref.current = ws;
      return ws;
    } catch (e) {
      console.error('Failed to connect WebSocket:', e);
      return null;
    }
  }, []);
  
  // Start streaming
  const startStream = async () => {
    setIsConnecting(true);
    try {
      const response = await fetch(
        `${API_URL}/api/stream/start?tps=${config.tps}&suspicious_rate=${config.suspiciousRate}`,
        { method: 'POST' }
      );
      const data = await response.json();
      
      if (data.status === 'started' || data.status === 'already_running') {
        setIsStreaming(true);
        
        // Connect to WebSocket endpoints
        connectWebSocket('/ws/transactions', transactionWsRef, (msg) => {
          if (msg.type === 'transaction') {
            setTransactions(prev => [msg.data, ...prev].slice(0, 500));
          }
        });
        
        connectWebSocket('/ws/alerts', alertWsRef, (msg) => {
          if (msg.type === 'alert') {
            setAlerts(prev => [msg.data, ...prev].slice(0, 100));
          }
        });
        
        connectWebSocket('/ws/stats', statsWsRef, (msg) => {
          if (msg.type === 'stats_update') {
            setStats(msg);
          }
        });
      }
    } catch (error) {
      console.error('Failed to start stream:', error);
    } finally {
      setIsConnecting(false);
    }
  };
  
  // Stop streaming
  const stopStream = async () => {
    try {
      await fetch(`${API_URL}/api/stream/stop`, { method: 'POST' });
      
      // Close WebSocket connections
      [transactionWsRef, alertWsRef, statsWsRef].forEach(ref => {
        if (ref.current) {
          ref.current.close();
          ref.current = null;
        }
      });
      
      setIsStreaming(false);
      setConnectionStatus('disconnected');
    } catch (error) {
      console.error('Failed to stop stream:', error);
    }
  };
  
  // Check stream status on mount
  useEffect(() => {
    const checkStatus = async () => {
      try {
        const response = await fetch(`${API_URL}/api/stream/status`);
        const data = await response.json();
        if (data.running) {
          setIsStreaming(true);
          // Reconnect to WebSockets if stream is running
          startStream();
        }
      } catch (e) {
        console.error('Failed to check stream status:', e);
      }
    };
    checkStatus();
    
    return () => {
      // Clean up WebSocket connections
      [transactionWsRef, alertWsRef, statsWsRef].forEach(ref => {
        if (ref.current) {
          ref.current.close();
        }
      });
    };
  }, []);
  
  // Format currency
  const formatCurrency = (amount) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 2,
    }).format(amount || 0);
  };
  
  // Get risk level from score
  const getRiskLevel = (score) => {
    if (score >= 70) return 'high';
    if (score >= 40) return 'medium';
    return 'low';
  };
  
  // Transaction card component
  const TransactionCard = ({ transaction, index }) => {
    const typeInfo = TRANSACTION_TYPES[transaction.type] || { 
      color: 'gray', 
      label: transaction.type,
      icon: CurrencyDollarIcon 
    };
    const Icon = typeInfo.icon;
    const riskLevel = getRiskLevel(transaction.aml_score || 0);
    
    return (
      <motion.div
        initial={{ opacity: 0, x: -50, scale: 0.95 }}
        animate={{ opacity: 1, x: 0, scale: 1 }}
        exit={{ opacity: 0, x: 50, scale: 0.95 }}
        transition={{ duration: 0.3, delay: index * 0.02 }}
        className={`p-4 rounded-lg border ${
          transaction.is_suspicious 
            ? 'bg-red-500/10 border-red-500/30' 
            : 'bg-gray-800/50 border-gray-700/50'
        } hover:border-gray-600 transition-all`}
      >
        <div className="flex items-start justify-between">
          <div className="flex items-start gap-3">
            <div className={`p-2 rounded-lg bg-${typeInfo.color}-500/20`}>
              <Icon className={`w-5 h-5 text-${typeInfo.color}-400`} />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <span className="font-medium text-white">
                  {formatCurrency(transaction.amount)}
                </span>
                <span className={`px-2 py-0.5 rounded text-xs bg-${typeInfo.color}-500/20 text-${typeInfo.color}-400`}>
                  {typeInfo.label}
                </span>
                {transaction.is_suspicious && (
                  <ExclamationSolidIcon className="w-4 h-4 text-red-400" />
                )}
              </div>
              <p className="text-sm text-gray-400 mt-1">
                {transaction.account_name || 'Unknown Account'}
              </p>
              {transaction.merchant?.name && (
                <p className="text-xs text-gray-500 mt-0.5">
                  {transaction.merchant.name}
                </p>
              )}
            </div>
          </div>
          
          <div className="text-right">
            <span className={`px-2 py-0.5 rounded text-xs border ${RISK_STYLES[riskLevel]}`}>
              Score: {transaction.aml_score || 0}
            </span>
            <div className="flex items-center gap-1 mt-1 text-xs text-gray-500">
              <ClockIcon className="w-3 h-3" />
              {new Date(transaction.timestamp).toLocaleTimeString()}
            </div>
            {transaction.location?.city && (
              <div className="flex items-center gap-1 mt-0.5 text-xs text-gray-500">
                <MapPinIcon className="w-3 h-3" />
                {transaction.location.city}
              </div>
            )}
          </div>
        </div>
        
        {transaction.risk_indicators?.length > 0 && (
          <div className="mt-2 pt-2 border-t border-gray-700/50">
            <div className="flex flex-wrap gap-1">
              {transaction.risk_indicators.slice(0, 2).map((indicator, i) => (
                <span key={i} className="px-2 py-0.5 text-xs bg-red-500/10 text-red-400 rounded">
                  {indicator}
                </span>
              ))}
            </div>
          </div>
        )}
      </motion.div>
    );
  };
  
  // Alert card component
  const AlertCard = ({ alert, index }) => (
    <motion.div
      initial={{ opacity: 0, y: -20 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: 20 }}
      transition={{ duration: 0.3, delay: index * 0.05 }}
      className="p-3 rounded-lg bg-red-500/10 border border-red-500/30"
    >
      <div className="flex items-start gap-2">
        <ExclamationSolidIcon className="w-5 h-5 text-red-400 flex-shrink-0 mt-0.5" />
        <div className="flex-1 min-w-0">
          <p className="font-medium text-red-300 truncate">
            {alert.rule_name || alert.alert_type}
          </p>
          <p className="text-sm text-gray-400 mt-0.5 line-clamp-2">
            {alert.description}
          </p>
          <div className="flex items-center gap-2 mt-2">
            <span className={`px-2 py-0.5 text-xs rounded ${
              alert.severity === 'high' 
                ? 'bg-red-500/20 text-red-400' 
                : 'bg-yellow-500/20 text-yellow-400'
            }`}>
              {alert.severity?.toUpperCase()}
            </span>
            <span className="text-xs text-gray-500">
              {formatCurrency(alert.amount)}
            </span>
          </div>
        </div>
      </div>
    </motion.div>
  );
  
  return (
    <div className="min-h-screen bg-gray-900 p-6">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-white flex items-center gap-2">
            <SignalIcon className="w-7 h-7 text-blue-400" />
            Transaction Stream
          </h1>
          <p className="text-gray-400 mt-1">
            Real-time transaction monitoring with Kafka-style message streaming
          </p>
        </div>
        
        <div className="flex items-center gap-3">
          {/* Connection Status */}
          <div className={`flex items-center gap-2 px-3 py-1.5 rounded-full ${
            connectionStatus === 'connected' 
              ? 'bg-green-500/20 text-green-400' 
              : 'bg-gray-700/50 text-gray-400'
          }`}>
            <div className={`w-2 h-2 rounded-full ${
              connectionStatus === 'connected' ? 'bg-green-400 animate-pulse' : 'bg-gray-500'
            }`} />
            {connectionStatus === 'connected' ? 'Connected' : 'Disconnected'}
          </div>
          
          {/* Config Button */}
          <button
            onClick={() => setShowConfig(!showConfig)}
            className="p-2 rounded-lg bg-gray-800 hover:bg-gray-700 text-gray-400 transition-colors"
          >
            <Cog6ToothIcon className="w-5 h-5" />
          </button>
          
          {/* Start/Stop Button */}
          {isStreaming ? (
            <button
              onClick={stopStream}
              className="flex items-center gap-2 px-4 py-2 rounded-lg bg-red-500/20 hover:bg-red-500/30 text-red-400 transition-colors"
            >
              <StopIcon className="w-5 h-5" />
              Stop Stream
            </button>
          ) : (
            <button
              onClick={startStream}
              disabled={isConnecting}
              className="flex items-center gap-2 px-4 py-2 rounded-lg bg-green-500/20 hover:bg-green-500/30 text-green-400 transition-colors disabled:opacity-50"
            >
              {isConnecting ? (
                <ArrowPathIcon className="w-5 h-5 animate-spin" />
              ) : (
                <PlayIcon className="w-5 h-5" />
              )}
              Start Stream
            </button>
          )}
        </div>
      </div>
      
      {/* Config Panel */}
      <AnimatePresence>
        {showConfig && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            exit={{ opacity: 0, height: 0 }}
            className="mb-6 overflow-hidden"
          >
            <div className="p-4 rounded-lg bg-gray-800/50 border border-gray-700/50">
              <h3 className="font-medium text-white mb-4">Stream Configuration</h3>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm text-gray-400 mb-1">
                    Transactions per Second (TPS)
                  </label>
                  <input
                    type="range"
                    min="1"
                    max="20"
                    value={config.tps}
                    onChange={(e) => setConfig({ ...config, tps: Number(e.target.value) })}
                    className="w-full"
                    disabled={isStreaming}
                  />
                  <span className="text-sm text-gray-500">{config.tps} TPS</span>
                </div>
                <div>
                  <label className="block text-sm text-gray-400 mb-1">
                    Suspicious Rate
                  </label>
                  <input
                    type="range"
                    min="0.05"
                    max="0.50"
                    step="0.05"
                    value={config.suspiciousRate}
                    onChange={(e) => setConfig({ ...config, suspiciousRate: Number(e.target.value) })}
                    className="w-full"
                    disabled={isStreaming}
                  />
                  <span className="text-sm text-gray-500">{(config.suspiciousRate * 100).toFixed(0)}%</span>
                </div>
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
      
      {/* Stats Bar */}
      <div className="grid grid-cols-5 gap-4 mb-6">
        <div className="p-4 rounded-lg bg-gray-800/50 border border-gray-700/50">
          <div className="flex items-center gap-2 text-gray-400 text-sm mb-1">
            <ChartBarIcon className="w-4 h-4" />
            Total Transactions
          </div>
          <p className="text-2xl font-bold text-white">{transactions.length}</p>
        </div>
        <div className="p-4 rounded-lg bg-gray-800/50 border border-gray-700/50">
          <div className="flex items-center gap-2 text-gray-400 text-sm mb-1">
            <CurrencyDollarIcon className="w-4 h-4" />
            Total Volume
          </div>
          <p className="text-2xl font-bold text-white">{formatCurrency(totalVolume)}</p>
        </div>
        <div className="p-4 rounded-lg bg-gray-800/50 border border-gray-700/50">
          <div className="flex items-center gap-2 text-gray-400 text-sm mb-1">
            <ExclamationTriangleIcon className="w-4 h-4 text-red-400" />
            Suspicious
          </div>
          <p className="text-2xl font-bold text-red-400">{suspiciousCount}</p>
        </div>
        <div className="p-4 rounded-lg bg-gray-800/50 border border-gray-700/50">
          <div className="flex items-center gap-2 text-gray-400 text-sm mb-1">
            <ArrowTrendingUpIcon className="w-4 h-4" />
            Actual TPS
          </div>
          <p className="text-2xl font-bold text-blue-400">
            {stats?.generator?.tps_actual?.toFixed(1) || '0.0'}
          </p>
        </div>
        <div className="p-4 rounded-lg bg-gray-800/50 border border-gray-700/50">
          <div className="flex items-center gap-2 text-gray-400 text-sm mb-1">
            <SignalSolidIcon className="w-4 h-4 text-green-400" />
            Alerts
          </div>
          <p className="text-2xl font-bold text-yellow-400">{alerts.length}</p>
        </div>
      </div>
      
      {/* Main Content */}
      <div className="grid grid-cols-3 gap-6">
        {/* Transaction Feed */}
        <div className="col-span-2">
          <div className="bg-gray-800/30 rounded-lg border border-gray-700/50 h-[calc(100vh-300px)] flex flex-col">
            <div className="p-4 border-b border-gray-700/50">
              <h2 className="font-medium text-white flex items-center gap-2">
                <ArrowsRightLeftIcon className="w-5 h-5 text-blue-400" />
                Live Transaction Feed
                {isStreaming && (
                  <span className="w-2 h-2 rounded-full bg-green-400 animate-pulse" />
                )}
              </h2>
            </div>
            
            <div 
              ref={transactionListRef}
              className="flex-1 overflow-y-auto p-4 space-y-3"
            >
              {transactions.length === 0 ? (
                <div className="flex flex-col items-center justify-center h-full text-gray-500">
                  <SignalIcon className="w-12 h-12 mb-2" />
                  <p>No transactions yet</p>
                  <p className="text-sm">Start the stream to see live data</p>
                </div>
              ) : (
                <AnimatePresence mode="popLayout">
                  {transactions.slice(0, 50).map((txn, index) => (
                    <TransactionCard 
                      key={txn.id} 
                      transaction={txn}
                      index={index}
                    />
                  ))}
                </AnimatePresence>
              )}
            </div>
          </div>
        </div>
        
        {/* Alerts Panel */}
        <div className="col-span-1">
          <div className="bg-gray-800/30 rounded-lg border border-gray-700/50 h-[calc(100vh-300px)] flex flex-col">
            <div className="p-4 border-b border-gray-700/50">
              <h2 className="font-medium text-white flex items-center gap-2">
                <ExclamationTriangleIcon className="w-5 h-5 text-red-400" />
                Real-time Alerts
                {alerts.length > 0 && (
                  <span className="px-2 py-0.5 text-xs bg-red-500/20 text-red-400 rounded-full">
                    {alerts.length}
                  </span>
                )}
              </h2>
            </div>
            
            <div className="flex-1 overflow-y-auto p-4 space-y-3">
              {alerts.length === 0 ? (
                <div className="flex flex-col items-center justify-center h-full text-gray-500">
                  <ExclamationTriangleIcon className="w-12 h-12 mb-2" />
                  <p>No alerts yet</p>
                  <p className="text-sm text-center">
                    Alerts will appear when suspicious activity is detected
                  </p>
                </div>
              ) : (
                <AnimatePresence mode="popLayout">
                  {alerts.slice(0, 20).map((alert, index) => (
                    <AlertCard 
                      key={alert.id} 
                      alert={alert}
                      index={index}
                    />
                  ))}
                </AnimatePresence>
              )}
            </div>
          </div>
        </div>
      </div>
      
      {/* Stream Info Footer */}
      {stats && isStreaming && (
        <div className="mt-6 p-4 rounded-lg bg-gray-800/30 border border-gray-700/50">
          <div className="flex items-center justify-between text-sm">
            <div className="flex items-center gap-6">
              <span className="text-gray-400">
                Generator: <span className="text-white">{stats.generator?.generated_count || 0} txns</span>
              </span>
              <span className="text-gray-400">
                Processed: <span className="text-white">{stats.processor?.processed_count || 0}</span>
              </span>
              <span className="text-gray-400">
                Alert Rate: <span className="text-yellow-400">
                  {((stats.processor?.alert_rate || 0) * 100).toFixed(1)}%
                </span>
              </span>
            </div>
            <div className="text-gray-500">
              Uptime: {Math.floor(stats.generator?.uptime_seconds || 0)}s
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
