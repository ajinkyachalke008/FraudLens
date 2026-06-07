'use client';

import {
  Zap, Layers, RotateCcw, Box, Moon, Network, Brain, Activity,
  Shield, ShieldCheck, ShieldAlert, ShieldX,
  Clock, Users, UserMinus, Split, Merge, Landmark, Calendar, Timer
} from 'lucide-react';

// ──── Types ──────────────────────────────────────────────────────

interface RiskProfile {
  account_id: string;
  // Behavioral
  velocity_score: number;
  structuring_score: number;
  rapid_succession_score: number;
  amount_anomaly_score: number;
  // Network
  roundtrip_score: number;
  shell_score: number;
  fanout_score: number;
  fanin_score: number;
  centrality_score: number;
  crossbank_score: number;
  // Temporal
  dormancy_score: number;
  time_anomaly_score: number;
  weekend_holiday_score: number;
  // ML
  gnn_score: number;
  isolation_score: number;
  // Composite
  final_risk_score: number;
  risk_tier: 'CLEAN' | 'WATCH' | 'ALERT' | 'CRITICAL';
  tags: string[];
  signals_active: number;
}

interface Props {
  accountId: string;
  profile?: RiskProfile | null;
  loading?: boolean;
  compact?: boolean;
}

// ──── Mock Profiles (15-signal) ──────────────────────────────────

const MOCK_PROFILES: Record<string, RiskProfile> = {
  'ACC-1001': { account_id: 'ACC-1001', velocity_score: 0.82, structuring_score: 0.45, rapid_succession_score: 0.71, amount_anomaly_score: 0.65, roundtrip_score: 0.91, shell_score: 0.74, fanout_score: 0.88, fanin_score: 0.42, centrality_score: 0.88, crossbank_score: 0.72, dormancy_score: 0.10, time_anomaly_score: 0.68, weekend_holiday_score: 0.55, gnn_score: 0.95, isolation_score: 0.87, final_risk_score: 0.89, risk_tier: 'CRITICAL', tags: ['VELOCITY_SPIKE', 'RAPID_FIRE', 'ROUND_TRIP', 'SHELL', 'FAN_OUT', 'CROSS_BANK', 'NIGHT_OPS', 'MULE', 'SYNDICATE_HUB'], signals_active: 13 },
  'ACC-1002': { account_id: 'ACC-1002', velocity_score: 0.55, structuring_score: 0.78, rapid_succession_score: 0.30, amount_anomaly_score: 0.40, roundtrip_score: 0.30, shell_score: 0.88, fanout_score: 0.35, fanin_score: 0.65, centrality_score: 0.42, crossbank_score: 0.55, dormancy_score: 0.05, time_anomaly_score: 0.25, weekend_holiday_score: 0.10, gnn_score: 0.72, isolation_score: 0.65, final_risk_score: 0.58, risk_tier: 'ALERT', tags: ['STRUCTURING', 'SHELL', 'FAN_IN', 'CROSS_BANK', 'MULE', 'LAYERING', 'COLLECTOR'], signals_active: 8 },
  'ACC-1003': { account_id: 'ACC-1003', velocity_score: 0.05, structuring_score: 0.02, rapid_succession_score: 0.0, amount_anomaly_score: 0.10, roundtrip_score: 0.00, shell_score: 0.03, fanout_score: 0.02, fanin_score: 0.04, centrality_score: 0.05, crossbank_score: 0.0, dormancy_score: 0.00, time_anomaly_score: 0.03, weekend_holiday_score: 0.02, gnn_score: 0.08, isolation_score: 0.04, final_risk_score: 0.04, risk_tier: 'CLEAN', tags: [], signals_active: 0 },
  'ACC-1004': { account_id: 'ACC-1004', velocity_score: 0.70, structuring_score: 0.55, rapid_succession_score: 0.62, amount_anomaly_score: 0.58, roundtrip_score: 0.65, shell_score: 0.60, fanout_score: 0.72, fanin_score: 0.48, centrality_score: 0.55, crossbank_score: 0.68, dormancy_score: 0.15, time_anomaly_score: 0.45, weekend_holiday_score: 0.38, gnn_score: 0.80, isolation_score: 0.72, final_risk_score: 0.72, risk_tier: 'ALERT', tags: ['VELOCITY_SPIKE', 'STRUCTURING', 'RAPID_FIRE', 'ROUND_TRIP', 'SHELL', 'FAN_OUT', 'CROSS_BANK', 'MULE', 'LAYERING', 'SYNDICATE_HUB'], signals_active: 12 },
  'ACC-1005': { account_id: 'ACC-1005', velocity_score: 0.40, structuring_score: 0.20, rapid_succession_score: 0.15, amount_anomaly_score: 0.72, roundtrip_score: 0.10, shell_score: 0.35, fanout_score: 0.28, fanin_score: 0.18, centrality_score: 0.18, crossbank_score: 0.12, dormancy_score: 0.85, time_anomaly_score: 0.60, weekend_holiday_score: 0.42, gnn_score: 0.55, isolation_score: 0.48, final_risk_score: 0.42, risk_tier: 'WATCH', tags: ['AMOUNT_SPIKE', 'DORMANCY_BREAK', 'NIGHT_OPS'], signals_active: 5 },
};

// ──── Signal Categories ──────────────────────────────────────────

type SignalDef = { key: string; label: string; icon: typeof Zap; desc: string };

const SIGNAL_CATEGORIES: { name: string; color: string; signals: SignalDef[] }[] = [
  {
    name: 'BEHAVIORAL',
    color: 'text-orange-400',
    signals: [
      { key: 'velocity_score', label: 'Velocity', icon: Zap, desc: 'Txn burst speed' },
      { key: 'structuring_score', label: 'Structuring', icon: Layers, desc: 'Sub-₹50k splits' },
      { key: 'rapid_succession_score', label: 'Rapid Fire', icon: Timer, desc: 'Sub-min bursts' },
      { key: 'amount_anomaly_score', label: 'Amt Anomaly', icon: Activity, desc: 'Z-score deviation' },
    ]
  },
  {
    name: 'NETWORK',
    color: 'text-cyan-400',
    signals: [
      { key: 'roundtrip_score', label: 'Roundtrip', icon: RotateCcw, desc: 'Circular flows' },
      { key: 'shell_score', label: 'Shell', icon: Box, desc: 'Pass-through' },
      { key: 'fanout_score', label: 'Fan-Out', icon: Split, desc: 'Scatter distro' },
      { key: 'fanin_score', label: 'Fan-In', icon: Merge, desc: 'Collection hub' },
      { key: 'centrality_score', label: 'Centrality', icon: Network, desc: 'PageRank' },
      { key: 'crossbank_score', label: 'Cross-Bank', icon: Landmark, desc: 'Bank layering' },
    ]
  },
  {
    name: 'TEMPORAL',
    color: 'text-indigo-400',
    signals: [
      { key: 'dormancy_score', label: 'Dormancy', icon: Moon, desc: 'Sleeper wake-up' },
      { key: 'time_anomaly_score', label: 'Night Ops', icon: Clock, desc: '12AM-5AM activity' },
      { key: 'weekend_holiday_score', label: 'Weekend/Hol', icon: Calendar, desc: 'Off-day activity' },
    ]
  },
  {
    name: 'ML',
    color: 'text-purple-400',
    signals: [
      { key: 'gnn_score', label: 'FraudSAGE', icon: Brain, desc: 'GNN embedding' },
      { key: 'isolation_score', label: 'Isolation', icon: UserMinus, desc: 'Anomaly forest' },
    ]
  }
];

const TIER_CONFIG = {
  CLEAN: { color: 'text-emerald-400', bg: 'bg-emerald-500/10', border: 'border-emerald-500/20', icon: ShieldCheck, glow: '' },
  WATCH: { color: 'text-sky-400', bg: 'bg-sky-500/10', border: 'border-sky-500/20', icon: Shield, glow: '' },
  ALERT: { color: 'text-amber-400', bg: 'bg-amber-400/10', border: 'border-amber-500/20', icon: ShieldAlert, glow: 'shadow-[0_0_15px_rgba(251,191,36,0.1)]' },
  CRITICAL: { color: 'text-red-400', bg: 'bg-red-500/10', border: 'border-red-500/20', icon: ShieldX, glow: 'shadow-[0_0_20px_rgba(248,113,113,0.15)]' },
};

const TAG_COLORS: Record<string, string> = {
  MULE: 'bg-red-500/15 text-red-400',
  SHELL: 'bg-purple-500/15 text-purple-400',
  STRUCTURING: 'bg-amber-400/15 text-amber-400',
  VELOCITY_SPIKE: 'bg-orange-500/15 text-orange-400',
  ROUND_TRIP: 'bg-cyan-500/15 text-cyan-400',
  DORMANCY_BREAK: 'bg-indigo-500/15 text-indigo-400',
  LAYERING: 'bg-pink-500/15 text-pink-400',
  FAN_OUT: 'bg-teal-500/15 text-teal-400',
  FAN_IN: 'bg-lime-500/15 text-lime-400',
  NIGHT_OPS: 'bg-violet-500/15 text-violet-400',
  WEEKEND_OPS: 'bg-fuchsia-500/15 text-fuchsia-400',
  RAPID_FIRE: 'bg-rose-500/15 text-rose-400',
  AMOUNT_SPIKE: 'bg-yellow-500/15 text-yellow-400',
  CROSS_BANK: 'bg-sky-500/15 text-sky-400',
  COLLECTOR: 'bg-emerald-500/15 text-emerald-400',
  AUTOMATED: 'bg-zinc-500/15 text-zinc-400',
  SYNDICATE_HUB: 'bg-red-600/20 text-red-300 font-bold',
};

function getBarColor(score: number): string {
  if (score >= 0.75) return 'bg-red-500';
  if (score >= 0.50) return 'bg-amber-400';
  if (score >= 0.30) return 'bg-sky-400';
  return 'bg-emerald-400';
}

// ──── Component ──────────────────────────────────────────────────

export default function RiskProfileCard({ accountId, profile: propProfile, loading, compact }: Props) {
  const profile = propProfile || MOCK_PROFILES[accountId] || null;
  const tier = profile ? TIER_CONFIG[profile.risk_tier] : TIER_CONFIG.CLEAN;
  const TierIcon = tier.icon;

  if (loading) {
    return (
      <div className="space-y-3 animate-pulse">
        <div className="h-16 rounded-xl bg-white/5" />
        {[...Array(15)].map((_, i) => (
          <div key={i} className="h-3 rounded bg-white/5" style={{ width: `${60 + Math.random() * 40}%` }} />
        ))}
      </div>
    );
  }

  if (!profile) {
    return (
      <div className="text-center py-6">
        <Shield className="w-8 h-8 text-white/10 mx-auto mb-2" />
        <p className="text-xs text-white/20 font-mono">No risk data available</p>
        <p className="text-[9px] text-white/10 font-mono mt-1">15-signal analysis requires transaction data</p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* Risk Score Header */}
      <div className={`rounded-xl ${tier.bg} border ${tier.border} p-4 ${tier.glow}`}>
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <TierIcon className={`w-6 h-6 ${tier.color}`} />
            <div>
              <p className={`text-2xl font-mono font-bold ${tier.color}`}>
                {(profile.final_risk_score * 100).toFixed(0)}
              </p>
              <p className="text-[10px] text-white/30 uppercase tracking-wider">Risk Score</p>
            </div>
          </div>
          <div className="text-right">
            <span className={`text-xs font-mono font-bold px-3 py-1.5 rounded-lg ${tier.bg} ${tier.color} border ${tier.border}`}>
              {profile.risk_tier}
            </span>
            <p className="text-[9px] text-white/20 mt-1 font-mono">
              {profile.signals_active}/15 signals active
            </p>
          </div>
        </div>
      </div>

      {/* Behavioral Tags */}
      {profile.tags.length > 0 && (
        <div className="flex flex-wrap gap-1.5">
          {profile.tags.map(tag => (
            <span
              key={tag}
              className={`text-[8px] font-mono px-2 py-0.5 rounded-full ${TAG_COLORS[tag] || 'bg-white/10 text-white/40'}`}
            >
              {tag.replace(/_/g, ' ')}
            </span>
          ))}
        </div>
      )}

      {/* Signal Categories with Bars */}
      <div className="space-y-3">
        {SIGNAL_CATEGORIES.map(category => (
          <div key={category.name}>
            {/* Category Header */}
            <p className={`text-[9px] font-mono uppercase tracking-[0.15em] mb-1.5 ${category.color}`}>
              {category.name}
            </p>

            {/* Signal Bars */}
            <div className="space-y-1.5">
              {category.signals.map(signal => {
                const score = (profile as any)[signal.key] as number;
                const Icon = signal.icon;

                if (compact && score < 0.1) return null;

                return (
                  <div key={signal.key} className="group">
                    <div className="flex items-center justify-between mb-0.5">
                      <div className="flex items-center gap-1.5">
                        <Icon className="w-3 h-3 text-white/15 group-hover:text-white/35 transition-colors" />
                        <span className="text-[10px] text-white/35 font-mono group-hover:text-white/55 transition-colors">
                          {signal.label}
                        </span>
                      </div>
                      <span className={`text-[10px] font-mono font-bold tabular-nums ${
                        score >= 0.7 ? 'text-red-400' :
                        score >= 0.5 ? 'text-amber-400' :
                        score >= 0.3 ? 'text-sky-400' :
                        'text-white/20'
                      }`}>
                        {(score * 100).toFixed(0)}%
                      </span>
                    </div>
                    <div className="h-1 bg-white/[0.04] rounded-full overflow-hidden">
                      <div
                        className={`h-full rounded-full transition-all duration-700 ease-out ${getBarColor(score)}`}
                        style={{ width: `${Math.max(score * 100, 1)}%` }}
                      />
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
