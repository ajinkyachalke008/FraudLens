'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { Shield, Network, Brain, Settings, Upload, Eye, Fingerprint, Users, Bell, FileText, Map as MapIcon, Lightbulb, ShieldAlert, Globe } from 'lucide-react';
import type { Route } from 'next';

const navItems: { href: Route; label: string; icon: any; shortLabel: string }[] = [
  { href: '/' as Route, label: 'Mission Control', icon: Shield, shortLabel: 'HQ' },
  { href: '/graph' as Route, label: 'Graph Intel', icon: Network, shortLabel: 'GRAPH' },
  { href: '/ingest' as Route, label: 'Data Ingest', icon: Upload, shortLabel: 'DATA' },
  { href: '/watchlist' as Route, label: 'Watchlist', icon: Eye, shortLabel: 'WATCH' },
  { href: '/map' as Route, label: 'Map', icon: MapIcon, shortLabel: 'MAP' },
  { href: '/patterns' as Route, label: 'Patterns', icon: Fingerprint, shortLabel: 'PTNS' },
  { href: '/reports' as Route, label: 'Reports', icon: FileText, shortLabel: 'RPRT' },
  { href: '/entities' as Route, label: 'Entities', icon: Users, shortLabel: 'LINK' },
  { href: '/osint' as Route, label: 'OSINT Enrichment', icon: Globe, shortLabel: 'OSINT' },
  { href: '/intelligence' as Route, label: 'Intelligence', icon: Lightbulb, shortLabel: 'INTEL' },
  { href: '/alerts' as Route, label: 'Alerts', icon: ShieldAlert, shortLabel: 'ALRT' },
  { href: '/ml' as Route, label: 'ML Core', icon: Brain, shortLabel: 'ML' },
];

export default function GlobalSidebar() {
  const pathname = usePathname();

  return (
    <aside className="fixed left-0 top-0 h-screen w-[72px] bg-background-surface border-r border-white/5 flex flex-col items-center py-6 z-50 transition-all">
      {/* Logo */}
      <div className="mb-8 flex flex-col items-center">
        <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-primary-500 to-primary-600 flex items-center justify-center shadow-[0_0_20px_rgba(14,165,233,0.3)]">
          <Shield className="w-5 h-5 text-white" />
        </div>
        <span className="text-[8px] font-display text-primary-400 tracking-[0.2em] mt-2">FRAUDLENS</span>
      </div>

      {/* Navigation Links */}
      <nav className="flex-1 flex flex-col gap-2 w-full px-3">
        {navItems.map((item) => {
          const isActive = pathname === item.href;
          const Icon = item.icon;
          return (
            <Link
              key={item.href}
              href={item.href}
              className={`
                group relative flex flex-col items-center gap-1 py-3 rounded-xl transition-all duration-200
                ${isActive
                  ? 'bg-primary-500/15 text-primary-400 shadow-[inset_0_0_12px_rgba(56,189,248,0.1)]'
                  : 'text-white/30 hover:text-white/60 hover:bg-white/5'
                }
              `}
            >
              <Icon className={`w-5 h-5 transition-transform ${isActive ? 'scale-110' : 'group-hover:scale-105'}`} />
              <span className="text-[9px] font-mono tracking-wider">{item.shortLabel}</span>
              
              {/* Active Indicator Bar */}
              {isActive && (
                <span className="absolute left-0 top-1/2 -translate-y-1/2 w-[3px] h-8 bg-primary-400 rounded-r-full shadow-[0_0_8px_rgba(56,189,248,0.6)]" />
              )}
            </Link>
          );
        })}
      </nav>

      {/* Bottom Status */}
      <div className="flex flex-col items-center gap-3 mb-2">
        <div className="flex items-center gap-1">
          <span className="relative flex h-2 w-2">
            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-safe-400 opacity-75"></span>
            <span className="relative inline-flex rounded-full h-2 w-2 bg-safe-500"></span>
          </span>
          <span className="text-[8px] font-mono text-safe-400">LIVE</span>
        </div>
        <button className="text-white/20 hover:text-white/40 transition-colors">
          <Settings className="w-4 h-4" />
        </button>
      </div>
    </aside>
  );
}
