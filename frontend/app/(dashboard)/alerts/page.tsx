'use client';

import { useState, useMemo } from 'react';
import {
  Bell, BellRing, Search, X, Filter, Shield, AlertTriangle, CheckCircle2,
  XCircle, Clock, ChevronRight, Eye, UserCheck, Volume2, VolumeX
} from 'lucide-react';

// ──── Types ──────────────────────────────────────────────────

interface AlertData {
  alert_id: string;
  alert_type: string;
  severity: string;
  title: string;
  message: string;
  account_id: string | null;
  case_id: string | null;
  status: string;
  acknowledged: boolean;
  acknowledged_at: string | null;
  assigned_to: string | null;
  escalation_level: number;
  created_at: string;
  age_minutes: number;
}

// ──── Mock Data ──────────────────────────────────────────────

const MOCK_ALERTS: AlertData[] = [
  { alert_id: 'a1', alert_type: 'BLACKLIST_HIT', severity: 'EMERGENCY', title: '⛔ Blacklist hit: ACC-1001 → ACC-BL-007', message: 'Transaction of ₹4,50,000 to BLACKLISTED account ACC-BL-007 detected. Immediate freeze recommended.', account_id: 'ACC-1001', case_id: 'CASE-2026-A8F3', status: 'active', acknowledged: false, acknowledged_at: null, assigned_to: null, escalation_level: 0, created_at: new Date(Date.now() - 2 * 60000).toISOString(), age_minutes: 2 },
  { alert_id: 'a2', alert_type: 'RISK_THRESHOLD', severity: 'CRITICAL', title: '🔴 ACC-1001 risk 89% (13/15 signals)', message: '15-signal risk engine scored ACC-1001 at 0.89. Active tags: MULE, HIGH_VELOCITY, KNOWN_SYNDICATE, LARGE_TXN, DORMANCY_BREAK.', account_id: 'ACC-1001', case_id: 'CASE-2026-A8F3', status: 'active', acknowledged: false, acknowledged_at: null, assigned_to: 'DI Sharma', escalation_level: 0, created_at: new Date(Date.now() - 5 * 60000).toISOString(), age_minutes: 5 },
  { alert_id: 'a3', alert_type: 'PATTERN_DETECTED', severity: 'CRITICAL', title: '🎯 INVESTMENT_SCAM: 2 accounts, ₹24,50,000', message: 'Investment scam pattern: victim ACC-V001 sent 5 escalating payments to ACC-1001 over 75 days. Amounts grew 3.2x.', account_id: 'ACC-1001', case_id: 'CASE-2026-A8F3', status: 'active', acknowledged: false, acknowledged_at: null, assigned_to: 'DI Sharma', escalation_level: 0, created_at: new Date(Date.now() - 8 * 60000).toISOString(), age_minutes: 8 },
  { alert_id: 'a4', alert_type: 'PATTERN_DETECTED', severity: 'HIGH', title: '📱 OTP_FRAUD: ₹2 test → ₹3,85,000 drain', message: 'OTP fraud pattern detected: ₹2 test transaction at 3:15 AM followed by ₹3,85,000 drained in 13 minutes from ACC-1002.', account_id: 'ACC-1002', case_id: 'CASE-2026-A8F3', status: 'acknowledged', acknowledged: true, acknowledged_at: new Date(Date.now() - 10 * 60000).toISOString(), assigned_to: 'DI Sharma', escalation_level: 0, created_at: new Date(Date.now() - 15 * 60000).toISOString(), age_minutes: 15 },
  { alert_id: 'a5', alert_type: 'SHARED_ENTITY', severity: 'HIGH', title: '🔗 Shared PHONE: 9876543210 across 2 cases', message: 'Accounts ACC-1001, ACC-1002, ACC-3091 share phone number 9876543210 across CASE-2026-A8F3 and CASE-2026-B1D7.', account_id: null, case_id: null, status: 'active', acknowledged: false, acknowledged_at: null, assigned_to: null, escalation_level: 1, created_at: new Date(Date.now() - 20 * 60000).toISOString(), age_minutes: 20 },
  { alert_id: 'a6', alert_type: 'VELOCITY_SPIKE', severity: 'HIGH', title: '⚡ Velocity spike on ACC-1004: 15 txns/hr', message: 'Account ACC-1004 processed 15 transactions totaling ₹7,50,000 in under 1 hour. Velocity score: 0.93.', account_id: 'ACC-1004', case_id: 'CASE-2026-A8F3', status: 'investigating', acknowledged: true, acknowledged_at: new Date(Date.now() - 25 * 60000).toISOString(), assigned_to: 'SI Patil', escalation_level: 0, created_at: new Date(Date.now() - 30 * 60000).toISOString(), age_minutes: 30 },
  { alert_id: 'a7', alert_type: 'SYNDICATE_JOIN', severity: 'CRITICAL', title: '🕸 ACC-3091 linked to Syndicate SYN-001', message: 'Account ACC-3091 joined known fraud syndicate SYN-001 via shared beneficiary. 47 known victims in cluster.', account_id: 'ACC-3091', case_id: 'CASE-2026-B1D7', status: 'active', acknowledged: false, acknowledged_at: null, assigned_to: null, escalation_level: 2, created_at: new Date(Date.now() - 35 * 60000).toISOString(), age_minutes: 35 },
  { alert_id: 'a8', alert_type: 'WATCHLIST_ACTIVITY', severity: 'MEDIUM', title: '👁 Watchlist account ACC-3091 active', message: 'Watchlisted account ACC-3091 received ₹25,000 from ACC-V009. Monitor for further activity.', account_id: 'ACC-3091', case_id: 'CASE-2026-B1D7', status: 'active', acknowledged: false, acknowledged_at: null, assigned_to: null, escalation_level: 0, created_at: new Date(Date.now() - 45 * 60000).toISOString(), age_minutes: 45 },
  { alert_id: 'a9', alert_type: 'PATTERN_DETECTED', severity: 'MEDIUM', title: '📅 WEEKEND_RUSH: ACC-1004', message: '73% of transactions on weekends (expected ~29%). Suspicious automated activity on non-business days.', account_id: 'ACC-1004', case_id: 'CASE-2026-A8F3', status: 'active', acknowledged: false, acknowledged_at: null, assigned_to: null, escalation_level: 0, created_at: new Date(Date.now() - 120 * 60000).toISOString(), age_minutes: 120 },
];

const SEVERITY_STYLES: Record<string, { bg: string; text: string; border: string; glow: string }> = {
  EMERGENCY: { bg: 'bg-red-500/20', text: 'text-red-300', border: 'border-red-500/40', glow: 'shadow-[0_0_20px_rgba(248,113,113,0.2)]' },
  CRITICAL: { bg: 'bg-red-500/10', text: 'text-red-400', border: 'border-red-500/20', glow: '' },
  HIGH: { bg: 'bg-orange-500/10', text: 'text-orange-400', border: 'border-orange-500/20', glow: '' },
  MEDIUM: { bg: 'bg-amber-400/10', text: 'text-amber-400', border: 'border-amber-500/20', glow: '' },
  LOW: { bg: 'bg-sky-500/10', text: 'text-sky-400', border: 'border-sky-500/20', glow: '' },
};

function timeAgo(minutes: number): string {
  if (minutes < 1) return 'just now';
  if (minutes < 60) return `${Math.floor(minutes)}m ago`;
  if (minutes < 1440) return `${Math.floor(minutes / 60)}h ago`;
  return `${Math.floor(minutes / 1440)}d ago`;
}

// ──── Component ──────────────────────────────────────────────

export default function AlertsPage() {
  const [severityFilter, setSeverityFilter] = useState<string>('ALL');
  const [statusFilter, setStatusFilter] = useState<string>('ALL');
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedAlert, setSelectedAlert] = useState<AlertData | null>(null);

  const filtered = useMemo(() => {
    let data = MOCK_ALERTS;
    if (severityFilter !== 'ALL') data = data.filter(a => a.severity === severityFilter);
    if (statusFilter !== 'ALL') data = data.filter(a => a.status === statusFilter);
    if (searchQuery) {
      const q = searchQuery.toLowerCase();
      data = data.filter(a => a.title.toLowerCase().includes(q) || a.message.toLowerCase().includes(q) || (a.account_id && a.account_id.toLowerCase().includes(q)));
    }
    return data;
  }, [severityFilter, statusFilter, searchQuery]);

  const stats = useMemo(() => ({
    total: MOCK_ALERTS.length,
    unacked: MOCK_ALERTS.filter(a => !a.acknowledged).length,
    emergency: MOCK_ALERTS.filter(a => a.severity === 'EMERGENCY').length,
    critical: MOCK_ALERTS.filter(a => a.severity === 'CRITICAL').length,
    escalated: MOCK_ALERTS.filter(a => a.escalation_level > 0).length,
  }), []);

  return (
    <div className="min-h-screen p-6 space-y-6">
      {/* Emergency Banner */}
      {stats.emergency > 0 && (
        <div className="rounded-2xl bg-red-500/10 border border-red-500/30 p-4 animate-pulse">
          <div className="flex items-center gap-3">
            <div className="w-3 h-3 rounded-full bg-red-500 shadow-[0_0_12px_rgba(239,68,68,0.8)]" />
            <span className="text-sm font-mono text-red-300">
              {stats.emergency} EMERGENCY ALERT{stats.emergency > 1 ? 'S' : ''} — Requires immediate acknowledgment
            </span>
          </div>
        </div>
      )}

      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-display text-white tracking-wider flex items-center gap-3">
            <BellRing className="w-6 h-6 text-primary-400" />
            FRAUD ALERTS
          </h1>
          <p className="text-sm text-white/40 mt-1 font-mono">
            Real-time alert center • 8 trigger types • Auto-escalation
          </p>
        </div>
      </div>

      {/* Stats Bar */}
      <div className="grid grid-cols-5 gap-3">
        {[
          { label: 'TOTAL', value: stats.total, icon: Bell, color: 'white' },
          { label: 'UNACKED', value: stats.unacked, icon: AlertTriangle, color: 'red' },
          { label: 'EMERGENCY', value: stats.emergency, icon: Shield, color: 'red' },
          { label: 'CRITICAL', value: stats.critical, icon: AlertTriangle, color: 'orange' },
          { label: 'ESCALATED', value: stats.escalated, icon: ChevronRight, color: 'amber' },
        ].map(s => (
          <div key={s.label} className="rounded-xl bg-white/[0.02] border border-white/5 p-3 flex items-center gap-3">
            <s.icon className={`w-4 h-4 text-${s.color}-400`} />
            <div>
              <p className="text-xl font-display text-white">{s.value}</p>
              <p className="text-[8px] font-mono text-white/30 tracking-wider">{s.label}</p>
            </div>
          </div>
        ))}
      </div>

      {/* Filters */}
      <div className="flex items-center gap-3 flex-wrap">
        <div className="flex rounded-xl bg-white/5 border border-white/5 p-1">
          {['ALL', 'EMERGENCY', 'CRITICAL', 'HIGH', 'MEDIUM'].map(sev => (
            <button key={sev} onClick={() => setSeverityFilter(sev)}
              className={`px-3 py-2 rounded-lg text-[10px] font-mono transition-all ${
                severityFilter === sev ? 'bg-white/10 text-white/70' : 'text-white/20 hover:text-white/40'
              }`}>
              {sev}
            </button>
          ))}
        </div>
        <div className="flex gap-1.5">
          {['ALL', 'active', 'acknowledged', 'investigating', 'resolved'].map(s => (
            <button key={s} onClick={() => setStatusFilter(s)}
              className={`px-3 py-2 rounded-lg text-[10px] font-mono transition-all ${
                statusFilter === s ? 'bg-white/10 text-white/70' : 'text-white/20 hover:text-white/40'
              }`}>
              {s.charAt(0).toUpperCase() + s.slice(1)}
            </button>
          ))}
        </div>
        <div className="relative flex-1 max-w-sm ml-auto">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-white/20" />
          <input type="text" placeholder="Search alerts..."
            value={searchQuery} onChange={e => setSearchQuery(e.target.value)}
            className="w-full pl-10 pr-4 py-2.5 rounded-xl bg-white/5 border border-white/5 text-sm text-white/80 placeholder:text-white/20 focus:outline-none focus:border-primary-500/30 font-mono" />
        </div>
      </div>

      {/* Alert Feed */}
      <div className="space-y-3">
        {filtered.map(alert => {
          const style = SEVERITY_STYLES[alert.severity] || SEVERITY_STYLES.MEDIUM;
          return (
            <div key={alert.alert_id}
              onClick={() => setSelectedAlert(alert)}
              className={`rounded-2xl ${style.bg} border ${style.border} ${style.glow} p-5 hover:bg-white/[0.06] transition-all cursor-pointer group ${
                selectedAlert?.alert_id === alert.alert_id ? 'ring-1 ring-white/20' : ''
              } ${alert.severity === 'EMERGENCY' && !alert.acknowledged ? 'animate-pulse' : ''}`}>
              <div className="flex items-start justify-between">
                <div className="flex items-start gap-3 flex-1">
                  {/* Severity Indicator */}
                  <div className={`mt-0.5 w-2.5 h-2.5 rounded-full flex-shrink-0 ${
                    alert.severity === 'EMERGENCY' ? 'bg-red-500 shadow-[0_0_8px_rgba(239,68,68,0.8)]' :
                    alert.severity === 'CRITICAL' ? 'bg-red-400' :
                    alert.severity === 'HIGH' ? 'bg-orange-400' :
                    'bg-amber-400'
                  }`} />

                  <div className="flex-1">
                    {/* Title */}
                    <h3 className={`text-sm font-mono ${style.text} font-bold mb-1`}>{alert.title}</h3>
                    <p className="text-xs text-white/40 mb-2">{alert.message}</p>

                    {/* Meta */}
                    <div className="flex items-center gap-3 flex-wrap">
                      <span className={`text-[10px] font-mono px-2 py-0.5 rounded ${style.bg} ${style.text} border ${style.border}`}>
                        {alert.severity}
                      </span>
                      <span className="text-[10px] font-mono text-white/20 bg-white/5 px-2 py-0.5 rounded">{alert.alert_type}</span>
                      {alert.account_id && <span className="text-[10px] font-mono text-white/40">{alert.account_id}</span>}
                      {alert.assigned_to && (
                        <span className="text-[10px] font-mono text-primary-400 flex items-center gap-1">
                          <UserCheck className="w-3 h-3" /> {alert.assigned_to}
                        </span>
                      )}
                      {alert.escalation_level > 0 && (
                        <span className="text-[10px] font-mono text-red-400 bg-red-500/10 px-2 py-0.5 rounded animate-pulse">
                          ⚡ L{alert.escalation_level} ESCALATED
                        </span>
                      )}
                    </div>
                  </div>
                </div>

                {/* Time + Status */}
                <div className="flex flex-col items-end gap-2">
                  <span className="text-[10px] font-mono text-white/20 flex items-center gap-1">
                    <Clock className="w-3 h-3" /> {timeAgo(alert.age_minutes)}
                  </span>
                  {alert.acknowledged ? (
                    <span className="text-[10px] font-mono text-emerald-400 flex items-center gap-1">
                      <CheckCircle2 className="w-3 h-3" /> ACK
                    </span>
                  ) : (
                    <button className="text-[10px] font-mono text-red-400 bg-red-500/10 px-3 py-1 rounded hover:bg-red-500/20 transition-all opacity-0 group-hover:opacity-100" onClick={e => { e.stopPropagation(); }}>
                      ACK
                    </button>
                  )}
                </div>
              </div>
            </div>
          );
        })}
      </div>

      {/* Detail Drawer */}
      {selectedAlert && (
        <div className="fixed inset-y-0 right-0 w-[420px] bg-[#0a0e14] border-l border-white/5 z-50 overflow-y-auto shadow-2xl">
          <div className="p-6 space-y-5">
            <div className="flex items-center justify-between">
              <h2 className="text-lg font-display text-white tracking-wider">Alert Detail</h2>
              <button onClick={() => setSelectedAlert(null)} className="text-white/30 hover:text-white/60">
                <X className="w-5 h-5" />
              </button>
            </div>

            {/* Severity Badge */}
            <div className={`rounded-xl ${SEVERITY_STYLES[selectedAlert.severity].bg} border ${SEVERITY_STYLES[selectedAlert.severity].border} p-4`}>
              <span className={`text-lg font-display ${SEVERITY_STYLES[selectedAlert.severity].text}`}>
                {selectedAlert.severity}
              </span>
              <p className="text-xs text-white/40 mt-1">{selectedAlert.alert_type}</p>
            </div>

            {/* Title & Message */}
            <div>
              <h3 className="text-sm font-mono text-white/80 mb-2">{selectedAlert.title}</h3>
              <p className="text-sm text-white/50 leading-relaxed">{selectedAlert.message}</p>
            </div>

            {/* Details Grid */}
            <div className="space-y-2">
              {[
                { label: 'Account', value: selectedAlert.account_id || '—' },
                { label: 'Case', value: selectedAlert.case_id || '—' },
                { label: 'Assigned', value: selectedAlert.assigned_to || 'Unassigned' },
                { label: 'Escalation', value: `Level ${selectedAlert.escalation_level}` },
                { label: 'Status', value: selectedAlert.status },
                { label: 'Created', value: new Date(selectedAlert.created_at).toLocaleString('en-IN') },
              ].map(item => (
                <div key={item.label} className="flex items-center justify-between py-2 border-b border-white/[0.03]">
                  <span className="text-[10px] font-mono text-white/30">{item.label}</span>
                  <span className="text-xs font-mono text-white/60">{item.value}</span>
                </div>
              ))}
            </div>

            {/* Actions */}
            <div className="space-y-2 pt-4">
              {!selectedAlert.acknowledged && (
                <button className="w-full py-3 rounded-xl bg-primary-500/20 border border-primary-500/30 text-primary-400 text-sm font-mono hover:bg-primary-500/30 transition-all flex items-center justify-center gap-2">
                  <CheckCircle2 className="w-4 h-4" /> Acknowledge Alert
                </button>
              )}
              <div className="flex gap-2">
                <button className="flex-1 py-2.5 rounded-xl bg-amber-400/20 border border-amber-500/30 text-amber-400 text-xs font-mono hover:bg-amber-400/30 transition-all flex items-center justify-center gap-2">
                  <Eye className="w-3.5 h-3.5" /> Investigate
                </button>
                <button className="flex-1 py-2.5 rounded-xl bg-emerald-500/20 border border-emerald-500/30 text-emerald-400 text-xs font-mono hover:bg-emerald-500/30 transition-all flex items-center justify-center gap-2">
                  <CheckCircle2 className="w-3.5 h-3.5" /> Resolve
                </button>
                <button className="flex-1 py-2.5 rounded-xl bg-white/5 border border-white/5 text-white/40 text-xs font-mono hover:bg-white/10 transition-all flex items-center justify-center gap-2">
                  <XCircle className="w-3.5 h-3.5" /> Dismiss
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
