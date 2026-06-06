'use client';

import React, { useEffect, useState } from 'react';
import { Clock, Bell, User, Search, LogOut } from 'lucide-react';
import { useAuth } from '@/contexts/AuthContext';

export default function TopBar() {
  const [currentTime, setCurrentTime] = useState('');
  const { user, logout } = useAuth();

  useEffect(() => {
    const update = () => {
      const now = new Date();
      setCurrentTime(now.toLocaleTimeString('en-IN', { hour: '2-digit', minute: '2-digit', second: '2-digit', hour12: false }));
    };
    update();
    const interval = setInterval(update, 1000);
    return () => clearInterval(interval);
  }, []);

  return (
    <header className="sticky top-0 z-40 flex items-center justify-between h-14 px-6 bg-background-surface/80 backdrop-blur-xl border-b border-white/5">
      {/* Left: Search */}
      <div className="flex items-center gap-3 flex-1 max-w-md">
        <div className="relative w-full">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-white/20" />
          <input
            type="text"
            placeholder="Search accounts, transactions, syndicates..."
            className="w-full bg-white/[0.03] border border-white/5 rounded-lg pl-10 pr-4 py-2 text-sm font-mono text-white/60 placeholder:text-white/20 focus:outline-none focus:border-primary-500/30 focus:ring-1 focus:ring-primary-500/20 transition-all"
          />
          <kbd className="absolute right-3 top-1/2 -translate-y-1/2 text-[9px] text-white/15 font-mono bg-white/5 px-1.5 py-0.5 rounded border border-white/5">⌘K</kbd>
        </div>
      </div>

      {/* Center: Clock */}
      <div className="hidden lg:flex items-center gap-2 text-white/30">
        <Clock className="w-3.5 h-3.5" />
        <span className="text-xs font-mono tabular-nums tracking-wider">{currentTime} IST</span>
      </div>

      {/* Right: Actions */}
      <div className="flex items-center gap-4">
        {/* Alerts Bell */}
        <button className="relative text-white/30 hover:text-white/60 transition-colors">
          <Bell className="w-4.5 h-4.5" />
          <span className="absolute -top-1 -right-1 w-3.5 h-3.5 bg-danger-500 rounded-full flex items-center justify-center text-[8px] font-mono text-white font-bold shadow-[0_0_6px_rgba(239,68,68,0.5)]">3</span>
        </button>

        {/* User Badge */}
        <div className="flex items-center gap-3 bg-white/[0.03] border border-white/5 rounded-lg px-3 py-1.5">
          <div className="flex items-center gap-2">
            <div className="w-6 h-6 rounded-full bg-gradient-to-br from-primary-500 to-primary-600 flex items-center justify-center">
              <User className="w-3.5 h-3.5 text-white" />
            </div>
            <div className="hidden sm:block">
              <div className="text-[11px] font-mono text-white/60 leading-tight">{user?.full_name ?? 'Guest'}</div>
              <div className="text-[9px] font-mono text-primary-400 tracking-wider uppercase">{user?.role ?? 'VIEWER'}</div>
            </div>
          </div>
          <button 
            onClick={logout}
            className="p-1 hover:bg-white/10 rounded-md transition-colors text-white/40 hover:text-danger-400"
            title="Sign out"
          >
            <LogOut className="w-4 h-4" />
          </button>
        </div>
      </div>
    </header>
  );
}
