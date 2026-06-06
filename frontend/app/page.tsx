'use client';

import React, { useEffect, useState } from 'react';
import { Shield, AlertTriangle, Activity, Zap, Radio, ChevronRight, Wifi, WifiOff } from 'lucide-react';
import Link from 'next/link';
import type { Route } from 'next';
import { useTransactionStream } from '@/hooks/useTransactionStream';
import { useDashboardTelemetry, useStreamMetrics, useCases } from '@/hooks/useDashboardData';

// Fallback data when backend is offline
const FALLBACK_TELEMETRY = {
  threat_level: 'NOMINAL',
  total_protected_value: 0,
  active_cases: 0,
};

interface CaseAlert {
  id: string;
  case_number: string;
  title: string;
  status: string;
  priority: string;
  amount: number;
  total_amount?: number;
  created_at: string;
}

const FALLBACK_ALERTS: CaseAlert[] = [
  { id: '1', case_number: 'ALERT-8A3F02C1', title: 'High-Risk Transfer in SYN-102', status: 'open', priority: 'critical', amount: 250000, created_at: '2026-06-05T07:55:00Z' },
  { id: '2', case_number: 'ALERT-1B7E94D2', title: 'Phishing Shell Network in SYN-101', status: 'open', priority: 'critical', amount: 890000, created_at: '2026-06-05T07:50:00Z' },
  { id: '3', case_number: 'ALERT-5C2F88A3', title: 'Cross-border Mule Activity in SYN-103', status: 'open', priority: 'high', amount: 1250000, created_at: '2026-06-05T07:45:00Z' },
  { id: '4', case_number: 'ALERT-9D4A11B4', title: 'Crypto Layering Pattern in SYN-104', status: 'open', priority: 'medium', amount: 450000, created_at: '2026-06-05T07:30:00Z' },
  { id: '5', case_number: 'ALERT-3E6C77F5', title: 'Velocity Anomaly Burst Detected', status: 'closed', priority: 'low', amount: 75000, created_at: '2026-06-05T06:00:00Z' },
];

export default function MissionControlDashboard() {
  const [counter, setCounter] = useState(0);

  // Live data hooks
  const { data: telemetryData, isError: telemetryError } = useDashboardTelemetry();
  const { data: streamData } = useStreamMetrics();
  const { data: casesData, isError: casesError } = useCases();
  const { streamedNodes, connectionStatus } = useTransactionStream('ws://localhost:8000/api/v1/ws/stream');

  // Resolve live vs fallback
  const telemetry = telemetryData?.telemetry ?? FALLBACK_TELEMETRY;
  const alerts = casesError || !casesData?.cases?.length
    ? FALLBACK_ALERTS
    : casesData.cases.map((c: CaseAlert) => ({ ...c, amount: c.total_amount }));

  const [streamLog, setStreamLog] = useState<string[]>([
    '[SYS] ✅ Stream Pipeline initialized (Fallback Queue Mode)',
    '[SYS] 🧠 FraudSAGE GNN loaded (16-dim embeddings)',
    '[SYS] 🌲 IsolationForest loaded (4 features)',
    '[SYS] 📡 WebSocket Manager ready',
  ]);

  // Animated counter effect
  useEffect(() => {
    const target = telemetry.total_protected_value;
    if (target === 0) return;
    const duration = 2000;
    const step = target / (duration / 16);
    let current = 0;
    const timer = setInterval(() => {
      current += step;
      if (current >= target) {
        current = target;
        clearInterval(timer);
      }
      setCounter(current);
    }, 16);
    return () => clearInterval(timer);
  }, [telemetry.total_protected_value]);

  // Stream log updates from WebSocket
  useEffect(() => {
    if (streamedNodes.length > 0) {
      const last = streamedNodes[streamedNodes.length - 1];
      setStreamLog(prev => [
        ...prev.slice(-20),
        `[${new Date().toLocaleTimeString('en-IN', { hour12: false })}] 🔴 INGESTED ${last.id} → Risk: ${(last.riskScore * 100).toFixed(0)}%`
      ]);
    }
  }, [streamedNodes]);

  // Connection status log
  useEffect(() => {
    if (connectionStatus === 'connected') {
      setStreamLog(prev => [...prev.slice(-20), `[${new Date().toLocaleTimeString('en-IN', { hour12: false })}] ✅ WebSocket CONNECTED`]);
    } else if (connectionStatus === 'disconnected') {
      setStreamLog(prev => [...prev.slice(-20), `[${new Date().toLocaleTimeString('en-IN', { hour12: false })}] ⚠️ WebSocket DISCONNECTED — reconnecting...`]);
    }
  }, [connectionStatus]);

  const threatColor = telemetry.threat_level === 'CRITICAL' ? 'text-danger-500' :
                       telemetry.threat_level === 'ELEVATED' ? 'text-warning-400' : 'text-safe-400';
  const threatBg = telemetry.threat_level === 'CRITICAL' ? 'bg-danger-500/10 border-danger-500/30' :
                    telemetry.threat_level === 'ELEVATED' ? 'bg-warning-400/10 border-warning-400/30' : 'bg-safe-400/10 border-safe-400/30';

  const wsColor = connectionStatus === 'connected' ? 'text-safe-400' :
                  connectionStatus === 'connecting' ? 'text-warning-400' : 'text-danger-400';
  const wsLabel = connectionStatus === 'connected' ? 'STREAM LIVE' :
                  connectionStatus === 'connecting' ? 'CONNECTING...' : 'RECONNECTING...';

  return (
    <div className="min-h-screen p-6 lg:p-8 space-y-6">
      {/* Header */}
      <div className="flex justify-between items-end">
        <div>
          <h1 className="text-3xl lg:text-4xl font-display font-bold tracking-tight">
            <span className="text-primary-400">MISSION</span>{' '}
            <span className="text-white/80">CONTROL</span>
          </h1>
          <p className="text-sm text-white/40 font-mono mt-1">Pune Police Cybercrime Cell — Real-Time Intelligence</p>
        </div>
        <div className="flex items-center gap-3">
          {/* Data Source Indicator */}
          <div className={`flex items-center gap-2 bg-background-card border border-white/5 rounded-full px-4 py-2`}>
            {connectionStatus === 'connected' ? (
              <Wifi className="w-3.5 h-3.5 text-safe-400" />
            ) : (
              <WifiOff className="w-3.5 h-3.5 text-danger-400" />
            )}
            <span className={`text-xs font-mono ${wsColor}`}>{wsLabel}</span>
          </div>
          {/* Backend Status */}
          <div className="flex items-center gap-2 bg-background-card border border-white/5 rounded-full px-4 py-2">
            <span className="relative flex h-2 w-2">
              <span className={`animate-ping absolute inline-flex h-full w-full rounded-full ${telemetryError ? 'bg-danger-400' : 'bg-safe-400'} opacity-75`}></span>
              <span className={`relative inline-flex rounded-full h-2 w-2 ${telemetryError ? 'bg-danger-500' : 'bg-safe-500'}`}></span>
            </span>
            <span className={`text-xs font-mono ${telemetryError ? 'text-danger-400' : 'text-safe-400'}`}>
              {telemetryError ? 'API OFFLINE' : 'API ONLINE'}
            </span>
          </div>
        </div>
      </div>

      {/* ═══ TIER 1: Global Telemetry ═══ */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Threat Level */}
        <div className={`relative overflow-hidden rounded-2xl border p-5 ${threatBg} group hover:scale-[1.02] transition-transform`}>
          <div className="absolute -right-4 -top-4 w-24 h-24 rounded-full bg-warning-400/5 blur-2xl group-hover:bg-warning-400/10 transition-colors" />
          <div className="relative">
            <div className="flex items-center gap-2 mb-3">
              <AlertTriangle className={`w-4 h-4 ${threatColor}`} />
              <span className="text-[10px] font-mono text-white/40 tracking-widest">THREAT LEVEL</span>
            </div>
            <div className={`text-2xl font-display font-bold tracking-wider ${threatColor}`}>
              {telemetry.threat_level}
            </div>
            <div className="text-[10px] text-white/30 font-mono mt-2">{telemetry.active_cases} active cases generating signal</div>
          </div>
        </div>

        {/* Protected Capital */}
        <div className="relative overflow-hidden rounded-2xl border border-safe-400/20 bg-safe-400/5 p-5 group hover:scale-[1.02] transition-transform">
          <div className="absolute -right-4 -top-4 w-24 h-24 rounded-full bg-safe-400/5 blur-2xl" />
          <div className="relative">
            <div className="flex items-center gap-2 mb-3">
              <Shield className="w-4 h-4 text-safe-400" />
              <span className="text-[10px] font-mono text-white/40 tracking-widest">PROTECTED CAPITAL</span>
            </div>
            <div className="text-2xl font-display font-bold text-safe-400 tabular-nums">
              ₹{counter.toLocaleString('en-IN', { maximumFractionDigits: 0 })}
            </div>
            <div className="text-[10px] text-white/30 font-mono mt-2">Total value intercepted by AI</div>
          </div>
        </div>

        {/* ML Engines */}
        <div className="relative overflow-hidden rounded-2xl border border-primary-400/20 bg-primary-400/5 p-5 group hover:scale-[1.02] transition-transform">
          <div className="absolute -right-4 -top-4 w-24 h-24 rounded-full bg-primary-400/5 blur-2xl" />
          <div className="relative">
            <div className="flex items-center gap-2 mb-3">
              <Zap className="w-4 h-4 text-primary-400" />
              <span className="text-[10px] font-mono text-white/40 tracking-widest">ML ENGINES</span>
            </div>
            <div className="text-2xl font-display font-bold text-primary-400">3/3</div>
            <div className="flex gap-2 mt-3">
              <span className="text-[9px] font-mono bg-safe-500/10 text-safe-400 px-2 py-0.5 rounded border border-safe-500/20">GNN</span>
              <span className="text-[9px] font-mono bg-safe-500/10 text-safe-400 px-2 py-0.5 rounded border border-safe-500/20">IF</span>
              <span className="text-[9px] font-mono bg-safe-500/10 text-safe-400 px-2 py-0.5 rounded border border-safe-500/20">K-M</span>
            </div>
          </div>
        </div>

        {/* Stream Throughput */}
        <div className="relative overflow-hidden rounded-2xl border border-white/10 bg-white/[0.02] p-5 group hover:scale-[1.02] transition-transform">
          <div className="absolute -right-4 -top-4 w-24 h-24 rounded-full bg-white/5 blur-2xl" />
          <div className="relative">
            <div className="flex items-center gap-2 mb-3">
              <Activity className="w-4 h-4 text-white/50" />
              <span className="text-[10px] font-mono text-white/40 tracking-widest">STREAM I/O</span>
            </div>
            <div className="text-2xl font-display font-bold text-white/80 tabular-nums">
              {streamData?.messages_processed ?? 0}
            </div>
            <div className="text-[10px] text-white/30 font-mono mt-2">
              {streamData?.high_risk_flags ?? 0} flagged · {streamData?.active_websocket_clients ?? 0} clients
            </div>
          </div>
        </div>
      </div>

      {/* ═══ TIER 2 & 3: Stream Matrix + Case Ledger ═══ */}
      <div className="grid grid-cols-1 lg:grid-cols-5 gap-6">
        {/* Stream Matrix Terminal */}
        <div className="lg:col-span-2 rounded-2xl border border-white/5 bg-background-card overflow-hidden">
          <div className="flex items-center justify-between px-4 py-3 border-b border-white/5 bg-background-surface">
            <div className="flex items-center gap-2">
              <Radio className={`w-3.5 h-3.5 ${connectionStatus === 'connected' ? 'text-safe-400' : 'text-danger-400'} animate-pulse`} />
              <span className="text-xs font-mono text-white/60 tracking-wider">STREAM MATRIX</span>
            </div>
            <div className="flex items-center gap-2">
              <span className={`text-[9px] font-mono ${wsColor} bg-white/5 px-2 py-0.5 rounded`}>{wsLabel}</span>
              <div className="flex gap-1.5">
                <span className="w-2.5 h-2.5 rounded-full bg-danger-500/60" />
                <span className="w-2.5 h-2.5 rounded-full bg-warning-400/60" />
                <span className="w-2.5 h-2.5 rounded-full bg-safe-500/60" />
              </div>
            </div>
          </div>
          <div className="p-4 h-[340px] overflow-y-auto font-mono text-[11px] leading-relaxed space-y-1 scrollbar-thin scrollbar-thumb-white/10">
            {streamLog.map((line, i) => (
              <div
                key={i}
                className={`${
                  line.includes('🔴') ? 'text-danger-400' :
                  line.includes('✅') ? 'text-safe-400' :
                  line.includes('⚠️') ? 'text-warning-400' :
                  line.includes('🧠') ? 'text-primary-400' :
                  'text-white/40'
                } ${i === streamLog.length - 1 ? 'animate-pulse' : ''}`}
              >
                {line}
              </div>
            ))}
            <div className="text-white/20 animate-pulse">█</div>
          </div>
        </div>

        {/* Case Ledger */}
        <div className="lg:col-span-3 rounded-2xl border border-white/5 bg-background-card overflow-hidden">
          <div className="flex items-center justify-between px-5 py-3 border-b border-white/5 bg-background-surface">
            <div className="flex items-center gap-2">
              <AlertTriangle className="w-3.5 h-3.5 text-warning-400" />
              <span className="text-xs font-mono text-white/60 tracking-wider">AUTOMATED CASE LEDGER</span>
            </div>
            <span className="text-[10px] font-mono text-white/30">
              {casesData?.total ?? alerts.length} total alerts
            </span>
          </div>

          <div className="divide-y divide-white/5">
            {alerts.map((alert: CaseAlert) => {
              const priorityStyle = alert.priority === 'critical'
                ? 'bg-danger-500/10 text-danger-400 border-danger-500/30'
                : alert.priority === 'high'
                ? 'bg-warning-400/10 text-warning-400 border-warning-400/30'
                : alert.priority === 'medium'
                ? 'bg-primary-400/10 text-primary-400 border-primary-400/30'
                : 'bg-white/5 text-white/40 border-white/10';

              return (
                <div key={alert.id} className="flex items-center justify-between px-5 py-4 hover:bg-white/[0.02] transition-colors group">
                  <div className="flex items-center gap-4 min-w-0">
                    <div className={`px-2 py-1 rounded text-[9px] font-mono uppercase tracking-wider border ${priorityStyle}`}>
                      {alert.priority}
                    </div>
                    <div className="min-w-0">
                      <div className="text-sm text-white/80 font-mono truncate">{alert.case_number}</div>
                      <div className="text-xs text-white/30 truncate">{alert.title}</div>
                    </div>
                  </div>
                  <div className="flex items-center gap-4 flex-shrink-0">
                    <div className="text-right hidden sm:block">
                      <div className="text-sm font-mono text-white/60">₹{(alert.amount || 0).toLocaleString('en-IN')}</div>
                      <div className="text-[10px] text-white/20 font-mono">
                        {alert.status === 'open' ? '🔴 OPEN' : alert.status === 'investigating' ? '🟡 INVESTIGATING' : '🟢 CLOSED'}
                      </div>
                    </div>
                    <Link
                      href={'/graph' as Route}
                      className="flex items-center gap-1 bg-primary-500/10 hover:bg-primary-500/20 text-primary-400 px-3 py-1.5 rounded-lg text-xs font-mono tracking-wider transition-colors opacity-0 group-hover:opacity-100"
                    >
                      Investigate <ChevronRight className="w-3 h-3" />
                    </Link>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      </div>

      {/* Footer Ticker */}
      <div className="flex items-center justify-between py-3 border-t border-white/5 text-[10px] font-mono text-white/20">
        <span>FraudLens v2.0 — Pune Police Cybercrime Cell</span>
        <span>
          {streamData?.last_processed_time
            ? `Last stream: ${new Date(streamData.last_processed_time).toLocaleTimeString('en-IN', { hour12: false })}`
            : 'Awaiting stream data...'}
        </span>
      </div>
    </div>
  );
}
