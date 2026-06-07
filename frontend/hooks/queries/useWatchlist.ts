'use client';

import { useQuery } from '@tanstack/react-query';

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1';

// ──── Blacklist ──────────────────────────────────────────────────

export function useBlacklist(activeOnly = true, limit = 100) {
  return useQuery({
    queryKey: ['blacklist', activeOnly, limit],
    queryFn: async () => {
      const res = await fetch(`${API_BASE}/watchlist/blacklist?active_only=${activeOnly}&limit=${limit}`);
      if (!res.ok) throw new Error('Failed to fetch blacklist');
      return res.json();
    },
    staleTime: 30_000,
  });
}

// ──── Watchlist ──────────────────────────────────────────────────

export function useWatchlist(watchLevel?: string, limit = 100) {
  return useQuery({
    queryKey: ['watchlist', watchLevel, limit],
    queryFn: async () => {
      const params = new URLSearchParams({ limit: String(limit) });
      if (watchLevel) params.set('watch_level', watchLevel);
      const res = await fetch(`${API_BASE}/watchlist/watch?${params}`);
      if (!res.ok) throw new Error('Failed to fetch watchlist');
      return res.json();
    },
    staleTime: 30_000,
  });
}

// ──── Account Check ──────────────────────────────────────────────

export function useAccountCheck(accountId: string | null) {
  return useQuery({
    queryKey: ['account-check', accountId],
    queryFn: async () => {
      const res = await fetch(`${API_BASE}/watchlist/check/${accountId}`);
      if (!res.ok) throw new Error('Failed to check account');
      return res.json();
    },
    enabled: !!accountId,
    staleTime: 15_000,
  });
}
