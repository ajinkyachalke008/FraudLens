'use client';

import React, { useState } from 'react';
import { Shield, Lock, Mail, Loader2, AlertTriangle } from 'lucide-react';
import { useAuth } from '@/contexts/AuthContext';

export default function LoginPage() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const { login, user } = useAuth();

  React.useEffect(() => {
    if (user) {
      window.location.href = '/';
    }
  }, [user]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setIsLoading(true);

    try {
      let API_BASE = process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8000/api/v1';
      if (!API_BASE.endsWith('/api/v1')) {
        API_BASE = `${API_BASE}/api/v1`;
      }
      
      // 1. Get Token
      const tokenRes = await fetch(`${API_BASE}/auth/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
        body: new URLSearchParams({
          username: email,
          password: password,
        }),
      });

      if (!tokenRes.ok) {
        throw new Error('Invalid credentials');
      }

      const tokenData = await tokenRes.json();
      const token = tokenData.access_token;

      // 2. Get User Profile
      const userRes = await fetch(`${API_BASE}/auth/me`, {
        headers: { Authorization: `Bearer ${token}` }
      });

      if (!userRes.ok) {
        throw new Error('Failed to fetch user profile');
      }

      const user = await userRes.json();
      login(token, user);

    } catch (err: unknown) {
      if (err instanceof Error) {
        setError(err.message ?? 'Login failed');
      } else {
        setError('Login failed');
      }
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-background-base flex items-center justify-center p-4 relative overflow-hidden">
      {/* Background glow effects */}
      <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[800px] h-[800px] bg-primary-500/10 rounded-full blur-[120px] pointer-events-none" />
      
      <div className="w-full max-w-md relative z-10">
        <div className="bg-background-surface/80 backdrop-blur-xl border border-white/10 rounded-2xl p-8 shadow-2xl">
          
          <div className="flex flex-col items-center mb-8">
            <div className="w-16 h-16 rounded-2xl bg-gradient-to-br from-primary-500/20 to-primary-600/20 border border-primary-500/30 flex items-center justify-center mb-4">
              <Shield className="w-8 h-8 text-primary-400" />
            </div>
            <h1 className="text-2xl font-display font-bold tracking-tight text-white">
              FraudLens <span className="text-primary-400">HQ</span>
            </h1>
            <p className="text-sm text-white/40 font-mono mt-2">Cybercrime Intelligence Platform</p>
          </div>

          {error && (
            <div className="mb-6 p-3 rounded-lg bg-danger-500/10 border border-danger-500/30 flex items-center gap-3">
              <AlertTriangle className="w-5 h-5 text-danger-400 flex-shrink-0" />
              <p className="text-sm font-mono text-danger-400">{error}</p>
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-5">
            <div className="space-y-1.5">
              <label className="text-xs font-mono text-white/60 uppercase tracking-wider pl-1">Email</label>
              <div className="relative">
                <Mail className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-white/30" />
                <input
                  type="email"
                  required
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  className="w-full bg-white/5 border border-white/10 rounded-xl py-3 pl-10 pr-4 text-sm text-white placeholder:text-white/20 focus:outline-none focus:border-primary-500/50 focus:ring-1 focus:ring-primary-500/50 transition-all"
                  placeholder="agent@fraudlens.gov"
                />
              </div>
            </div>

            <div className="space-y-1.5">
              <label className="text-xs font-mono text-white/60 uppercase tracking-wider pl-1">Password</label>
              <div className="relative">
                <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-white/30" />
                <input
                  type="password"
                  required
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="w-full bg-white/5 border border-white/10 rounded-xl py-3 pl-10 pr-4 text-sm text-white placeholder:text-white/20 focus:outline-none focus:border-primary-500/50 focus:ring-1 focus:ring-primary-500/50 transition-all"
                  placeholder="••••••••"
                />
              </div>
            </div>

            <button
              type="submit"
              disabled={isLoading}
              className="w-full bg-primary-500 hover:bg-primary-600 text-white font-bold py-3 px-4 rounded-xl transition-all disabled:opacity-50 flex items-center justify-center gap-2 mt-2"
            >
              {isLoading ? <Loader2 className="w-5 h-5 animate-spin" /> : 'Authenticate'}
            </button>
          </form>
          
          <div className="mt-8 text-center text-xs font-mono text-white/20">
            Secure Access — Authorized Personnel Only
          </div>
        </div>
      </div>
    </div>
  );
}
