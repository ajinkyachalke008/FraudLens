'use client';

import { useQuery } from '@tanstack/react-query';

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1';

// ──── Risk Profile ──────────────────────────────────────────────

export function useRiskProfile(accountId: string | null) {
  return useQuery({
    queryKey: ['risk-profile', accountId],
    queryFn: async () => {
      const res = await fetch(`${API_BASE}/intelligence/risk-profile/${accountId}`);
      if (!res.ok) throw new Error('Failed to fetch risk profile');
      return res.json();
    },
    enabled: !!accountId,
    staleTime: 30_000,
    retry: 1,
  });
}

export function useHighRiskAccounts(tier?: string, limit = 50) {
  return useQuery({
    queryKey: ['high-risk-accounts', tier, limit],
    queryFn: async () => {
      const params = new URLSearchParams();
      if (tier) params.set('tier', tier);
      params.set('limit', String(limit));
      const res = await fetch(`${API_BASE}/intelligence/high-risk-accounts?${params}`);
      if (!res.ok) throw new Error('Failed to fetch high-risk accounts');
      return res.json();
    },
    staleTime: 60_000,
  });
}
