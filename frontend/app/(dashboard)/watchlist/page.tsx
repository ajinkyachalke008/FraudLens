'use client';

import { useState, useMemo } from 'react';
import {
  Eye, Ban, Shield, Plus, Search, X, AlertTriangle, Clock, User, ChevronDown,
  ExternalLink, CheckCircle2, XCircle, Loader2, Filter
} from 'lucide-react';

// ──── Types ──────────────────────────────────────────────────────

interface BlacklistEntry {
  id: string;
  account_id: string;
  reason: string;
  added_by_name: string;
  case_ref: string | null;
  bank_notified: boolean;
  court_order_ref: string | null;
  propagation_complete: boolean;
  added_at: string;
}

interface WatchlistEntry {
  id: string;
  account_id: string;
  reason: string;
  watch_level: 'PASSIVE' | 'ACTIVE' | 'URGENT';
  assigned_to: string | null;
  review_date: string | null;
  notes: string | null;
  source: 'manual' | 'propagation' | 'alert';
  source_account: string | null;
  added_at: string;
}

// ──── Mock Data ──────────────────────────────────────────────────

const MOCK_BLACKLIST: BlacklistEntry[] = [
  { id: '1', account_id: 'ACC-1001', reason: 'Primary mule account — hub of Syndicate SYN-001. 47 victims routed through this account.', added_by_name: 'DI Sharma', case_ref: 'CASE-2026-A8F3', bank_notified: true, court_order_ref: 'HC/2026/CYB/4421', propagation_complete: true, added_at: '2026-05-28T10:00:00Z' },
  { id: '2', account_id: 'ACC-1004', reason: 'Secondary relay node in layering chain. Sub-threshold ₹49k structuring pattern detected.', added_by_name: 'SI Patil', case_ref: 'CASE-2026-A8F3', bank_notified: false, court_order_ref: null, propagation_complete: true, added_at: '2026-06-01T14:30:00Z' },
  { id: '3', account_id: 'ACC-2078', reason: 'Job scam collection account — collected ₹12.5L from 23 victims via UPI.', added_by_name: 'DI Sharma', case_ref: 'CASE-2026-B1D7', bank_notified: true, court_order_ref: 'MC/2026/FRD/891', propagation_complete: false, added_at: '2026-06-03T09:15:00Z' },
];

const MOCK_WATCHLIST: WatchlistEntry[] = [
  { id: '1', account_id: 'ACC-1002', reason: '1st-degree link to blacklisted ACC-1001', watch_level: 'URGENT', assigned_to: 'SI Patil', review_date: '2026-06-08', notes: 'Monitor for outbound transfers', source: 'propagation', source_account: 'ACC-1001', added_at: '2026-05-28T10:05:00Z' },
  { id: '2', account_id: 'ACC-1005', reason: '1st-degree link to blacklisted ACC-1001; Cash-out activity detected', watch_level: 'URGENT', assigned_to: 'ASI Kumar', review_date: '2026-06-07', notes: 'ATM withdrawals in Nashik cluster', source: 'propagation', source_account: 'ACC-1001', added_at: '2026-05-28T10:05:00Z' },
  { id: '3', account_id: 'ACC-1007', reason: '2nd-degree link to ACC-1001 via ACC-1002', watch_level: 'PASSIVE', assigned_to: null, review_date: '2026-06-15', notes: null, source: 'propagation', source_account: 'ACC-1001', added_at: '2026-05-29T16:00:00Z' },
  { id: '4', account_id: 'ACC-3091', reason: 'Dormancy break — 120 days inactive, sudden ₹8L inflow', watch_level: 'ACTIVE', assigned_to: 'DI Sharma', review_date: '2026-06-10', notes: 'New SIM registration linked', source: 'alert', source_account: null, added_at: '2026-06-05T11:30:00Z' },
  { id: '5', account_id: 'ACC-4455', reason: 'Velocity spike — 18 txns in 1 hour', watch_level: 'ACTIVE', assigned_to: null, review_date: null, notes: 'Possible mule onboarding', source: 'alert', source_account: null, added_at: '2026-06-06T22:00:00Z' },
];

// ──── Helpers ──────────────────────────────────────────────────

function formatDate(d: string): string {
  return new Date(d).toLocaleDateString('en-IN', { day: '2-digit', month: 'short', year: 'numeric' });
}

function isOverdue(date: string | null): boolean {
  if (!date) return false;
  return new Date(date) < new Date();
}

const LEVEL_STYLES: Record<string, string> = {
  URGENT: 'bg-red-500/15 text-red-400 border-red-500/30',
  ACTIVE: 'bg-amber-400/15 text-amber-400 border-amber-500/30',
  PASSIVE: 'bg-sky-500/15 text-sky-400 border-sky-500/30',
};

const SOURCE_STYLES: Record<string, string> = {
  manual: 'bg-white/10 text-white/50',
  propagation: 'bg-purple-500/15 text-purple-400',
  alert: 'bg-amber-400/15 text-amber-400',
};

// ──── Main Component ──────────────────────────────────────────

export default function WatchlistPage() {
  const [activeTab, setActiveTab] = useState<'blacklist' | 'watchlist'>('blacklist');
  const [searchQuery, setSearchQuery] = useState('');
  const [showAddModal, setShowAddModal] = useState(false);
  const [levelFilter, setLevelFilter] = useState<string>('ALL');

  // Filter data
  const filteredBlacklist = useMemo(() => {
    if (!searchQuery) return MOCK_BLACKLIST;
    const q = searchQuery.toLowerCase();
    return MOCK_BLACKLIST.filter(e =>
      e.account_id.toLowerCase().includes(q) ||
      e.reason.toLowerCase().includes(q)
    );
  }, [searchQuery]);

  const filteredWatchlist = useMemo(() => {
    let entries = MOCK_WATCHLIST;
    if (searchQuery) {
      const q = searchQuery.toLowerCase();
      entries = entries.filter(e =>
        e.account_id.toLowerCase().includes(q) ||
        e.reason.toLowerCase().includes(q)
      );
    }
    if (levelFilter !== 'ALL') {
      entries = entries.filter(e => e.watch_level === levelFilter);
    }
    return entries;
  }, [searchQuery, levelFilter]);

  return (
    <div className="min-h-screen p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-display text-white tracking-wider">
            {activeTab === 'blacklist' ? 'BLACKLIST' : 'WATCHLIST'}
          </h1>
          <p className="text-sm text-white/40 mt-1 font-mono">
            {activeTab === 'blacklist'
              ? 'Confirmed fraud accounts — institutional memory'
              : 'Accounts under surveillance — review & monitor'
            }
          </p>
        </div>

        <div className="flex items-center gap-3">
          {/* Tab Toggle */}
          <div className="flex rounded-xl bg-white/5 border border-white/5 p-1">
            <button
              onClick={() => setActiveTab('blacklist')}
              className={`px-4 py-2 rounded-lg text-xs font-mono transition-all ${
                activeTab === 'blacklist'
                  ? 'bg-red-500/20 text-red-400 shadow-[0_0_10px_rgba(248,113,113,0.15)]'
                  : 'text-white/30 hover:text-white/60'
              }`}
            >
              <Ban className="w-3.5 h-3.5 inline mr-1.5" />
              Blacklist ({MOCK_BLACKLIST.length})
            </button>
            <button
              onClick={() => setActiveTab('watchlist')}
              className={`px-4 py-2 rounded-lg text-xs font-mono transition-all ${
                activeTab === 'watchlist'
                  ? 'bg-amber-400/20 text-amber-400 shadow-[0_0_10px_rgba(251,191,36,0.15)]'
                  : 'text-white/30 hover:text-white/60'
              }`}
            >
              <Eye className="w-3.5 h-3.5 inline mr-1.5" />
              Watchlist ({MOCK_WATCHLIST.length})
            </button>
          </div>

          {/* Add Button */}
          <button
            onClick={() => setShowAddModal(true)}
            className="px-4 py-2.5 rounded-xl bg-white/5 border border-white/10 text-white/60 text-xs font-mono hover:bg-white/10 hover:text-white transition-all flex items-center gap-2"
          >
            <Plus className="w-3.5 h-3.5" />
            Add
          </button>
        </div>
      </div>

      {/* Search + Filters */}
      <div className="flex items-center gap-3">
        <div className="relative flex-1 max-w-md">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-white/20" />
          <input
            type="text"
            placeholder="Search by account ID or reason..."
            value={searchQuery}
            onChange={e => setSearchQuery(e.target.value)}
            className="w-full pl-10 pr-4 py-2.5 rounded-xl bg-white/5 border border-white/5 text-sm text-white/80 placeholder:text-white/20 focus:outline-none focus:border-sky-500/30 font-mono"
          />
          {searchQuery && (
            <button onClick={() => setSearchQuery('')} className="absolute right-3 top-1/2 -translate-y-1/2 text-white/20 hover:text-white/40">
              <X className="w-3.5 h-3.5" />
            </button>
          )}
        </div>

        {activeTab === 'watchlist' && (
          <div className="flex gap-1.5">
            {['ALL', 'URGENT', 'ACTIVE', 'PASSIVE'].map(level => (
              <button
                key={level}
                onClick={() => setLevelFilter(level)}
                className={`px-3 py-2 rounded-lg text-[10px] font-mono transition-all ${
                  levelFilter === level
                    ? level === 'ALL' ? 'bg-white/10 text-white/70' : LEVEL_STYLES[level]
                    : 'text-white/20 hover:text-white/40'
                }`}
              >
                {level}
              </button>
            ))}
          </div>
        )}
      </div>

      {/* Blacklist Table */}
      {activeTab === 'blacklist' && (
        <div className="rounded-2xl bg-white/[0.02] border border-white/5 overflow-hidden">
          <table className="w-full">
            <thead>
              <tr className="border-b border-white/5">
                {['Account', 'Reason', 'Added By', 'Date', 'Case', 'Bank Notified', 'Court Order', 'Propagated'].map(h => (
                  <th key={h} className="px-4 py-3 text-left text-[10px] font-mono text-white/30 uppercase tracking-wider">{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {filteredBlacklist.map(entry => (
                <tr key={entry.id} className="border-b border-white/[0.03] hover:bg-red-500/[0.02] transition-colors">
                  <td className="px-4 py-3">
                    <span className="text-sm font-mono text-red-400 font-bold flex items-center gap-1.5">
                      <span className="text-[10px]">⛔</span> {entry.account_id}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-xs text-white/50 max-w-[250px]">
                    <p className="line-clamp-2">{entry.reason}</p>
                  </td>
                  <td className="px-4 py-3 text-xs text-white/40 font-mono">{entry.added_by_name}</td>
                  <td className="px-4 py-3 text-xs text-white/30 font-mono">{formatDate(entry.added_at)}</td>
                  <td className="px-4 py-3">
                    {entry.case_ref ? (
                      <span className="text-[10px] font-mono text-sky-400 hover:underline cursor-pointer">{entry.case_ref}</span>
                    ) : <span className="text-white/10">—</span>}
                  </td>
                  <td className="px-4 py-3 text-center">
                    {entry.bank_notified
                      ? <CheckCircle2 className="w-4 h-4 text-emerald-400 mx-auto" />
                      : <XCircle className="w-4 h-4 text-white/10 mx-auto" />
                    }
                  </td>
                  <td className="px-4 py-3">
                    {entry.court_order_ref
                      ? <span className="text-[10px] font-mono text-amber-400">{entry.court_order_ref}</span>
                      : <span className="text-white/10 text-[10px]">—</span>
                    }
                  </td>
                  <td className="px-4 py-3 text-center">
                    {entry.propagation_complete
                      ? <CheckCircle2 className="w-4 h-4 text-emerald-400 mx-auto" />
                      : <Loader2 className="w-4 h-4 text-amber-400 animate-spin mx-auto" />
                    }
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Watchlist Table */}
      {activeTab === 'watchlist' && (
        <div className="rounded-2xl bg-white/[0.02] border border-white/5 overflow-hidden">
          <table className="w-full">
            <thead>
              <tr className="border-b border-white/5">
                {['Account', 'Level', 'Reason', 'Source', 'Assigned To', 'Review Date', 'Notes'].map(h => (
                  <th key={h} className="px-4 py-3 text-left text-[10px] font-mono text-white/30 uppercase tracking-wider">{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {filteredWatchlist.map(entry => (
                <tr key={entry.id} className={`border-b border-white/[0.03] hover:bg-white/[0.02] transition-colors ${
                  isOverdue(entry.review_date) ? 'bg-amber-500/[0.03]' : ''
                }`}>
                  <td className="px-4 py-3">
                    <span className="text-sm font-mono text-white/70 font-bold flex items-center gap-1.5">
                      <span className="text-[10px]">👁</span> {entry.account_id}
                    </span>
                  </td>
                  <td className="px-4 py-3">
                    <span className={`text-[10px] font-mono px-2.5 py-1 rounded-full border ${LEVEL_STYLES[entry.watch_level]}`}>
                      {entry.watch_level}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-xs text-white/50 max-w-[200px]">
                    <p className="line-clamp-2">{entry.reason}</p>
                  </td>
                  <td className="px-4 py-3">
                    <span className={`text-[10px] font-mono px-2 py-0.5 rounded ${SOURCE_STYLES[entry.source]}`}>
                      {entry.source.toUpperCase()}
                    </span>
                    {entry.source_account && (
                      <p className="text-[9px] text-white/20 mt-0.5 font-mono">← {entry.source_account}</p>
                    )}
                  </td>
                  <td className="px-4 py-3 text-xs text-white/40 font-mono">
                    {entry.assigned_to || <span className="text-white/10">Unassigned</span>}
                  </td>
                  <td className="px-4 py-3">
                    {entry.review_date ? (
                      <span className={`text-xs font-mono flex items-center gap-1 ${
                        isOverdue(entry.review_date) ? 'text-amber-400' : 'text-white/30'
                      }`}>
                        <Clock className="w-3 h-3" />
                        {formatDate(entry.review_date)}
                        {isOverdue(entry.review_date) && <span className="text-[9px]">OVERDUE</span>}
                      </span>
                    ) : <span className="text-white/10 text-[10px]">—</span>}
                  </td>
                  <td className="px-4 py-3 text-xs text-white/30 max-w-[150px]">
                    <p className="line-clamp-1">{entry.notes || '—'}</p>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Add Modal (simplified) */}
      {showAddModal && (
        <div className="fixed inset-0 bg-black/60 backdrop-blur-sm z-50 flex items-center justify-center">
          <div className="w-full max-w-md rounded-2xl bg-[#0c1017] border border-white/10 p-6 space-y-4">
            <div className="flex items-center justify-between">
              <h2 className="text-lg font-display text-white tracking-wider">
                Add to {activeTab === 'blacklist' ? 'Blacklist' : 'Watchlist'}
              </h2>
              <button onClick={() => setShowAddModal(false)} className="text-white/30 hover:text-white/60">
                <X className="w-5 h-5" />
              </button>
            </div>

            <div className="space-y-3">
              <div>
                <label className="text-xs text-white/30 font-mono block mb-1">Account ID</label>
                <input
                  type="text"
                  placeholder="ACC-XXXX"
                  className="w-full px-3 py-2.5 rounded-xl bg-white/5 border border-white/5 text-sm text-white/80 placeholder:text-white/20 focus:outline-none focus:border-sky-500/30 font-mono"
                />
              </div>
              <div>
                <label className="text-xs text-white/30 font-mono block mb-1">Reason</label>
                <textarea
                  placeholder="Describe why this account should be flagged..."
                  rows={3}
                  className="w-full px-3 py-2.5 rounded-xl bg-white/5 border border-white/5 text-sm text-white/80 placeholder:text-white/20 focus:outline-none focus:border-sky-500/30 font-mono resize-none"
                />
              </div>

              {activeTab === 'watchlist' && (
                <div>
                  <label className="text-xs text-white/30 font-mono block mb-1">Watch Level</label>
                  <div className="flex gap-2">
                    {['PASSIVE', 'ACTIVE', 'URGENT'].map(level => (
                      <button
                        key={level}
                        className={`flex-1 py-2 rounded-lg text-[10px] font-mono border transition-all ${LEVEL_STYLES[level]}`}
                      >
                        {level}
                      </button>
                    ))}
                  </div>
                </div>
              )}

              {activeTab === 'blacklist' && (
                <label className="flex items-center gap-2 text-xs text-white/40 font-mono cursor-pointer">
                  <input type="checkbox" defaultChecked className="rounded bg-white/5 border-white/10 text-sky-400 focus:ring-sky-500/30" />
                  Auto-propagate to linked accounts
                </label>
              )}
            </div>

            <div className="flex gap-2 pt-2">
              <button
                onClick={() => setShowAddModal(false)}
                className="flex-1 py-2.5 rounded-xl bg-white/5 text-white/40 text-xs font-mono hover:bg-white/10 transition-all"
              >
                Cancel
              </button>
              <button
                onClick={() => setShowAddModal(false)}
                className={`flex-1 py-2.5 rounded-xl text-xs font-mono transition-all flex items-center justify-center gap-2 ${
                  activeTab === 'blacklist'
                    ? 'bg-red-500/20 border border-red-500/30 text-red-400 hover:bg-red-500/30 shadow-[0_0_10px_rgba(248,113,113,0.15)]'
                    : 'bg-amber-400/20 border border-amber-500/30 text-amber-400 hover:bg-amber-400/30 shadow-[0_0_10px_rgba(251,191,36,0.15)]'
                }`}
              >
                <Shield className="w-3.5 h-3.5" />
                {activeTab === 'blacklist' ? 'Blacklist Account' : 'Add to Watchlist'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
