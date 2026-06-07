'use client';

import { useMutation, useQueryClient } from '@tanstack/react-query';

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1';

// ──── Blacklist Mutations ────────────────────────────────────────

export function useAddToBlacklist() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (data: { account_id: string; reason: string; case_id?: string; propagate?: boolean }) => {
      const res = await fetch(`${API_BASE}/watchlist/blacklist`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data),
      });
      if (!res.ok) throw new Error('Failed to add to blacklist');
      return res.json();
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['blacklist'] });
      queryClient.invalidateQueries({ queryKey: ['watchlist'] });
    },
  });
}

export function useRemoveFromBlacklist() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (accountId: string) => {
      const res = await fetch(`${API_BASE}/watchlist/blacklist/${accountId}`, {
        method: 'DELETE',
      });
      if (!res.ok) throw new Error('Failed to remove from blacklist');
      return res.json();
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['blacklist'] });
    },
  });
}

// ──── Watchlist Mutations ────────────────────────────────────────

export function useAddToWatchlist() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (data: { account_id: string; reason: string; watch_level?: string }) => {
      const res = await fetch(`${API_BASE}/watchlist/watch`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data),
      });
      if (!res.ok) throw new Error('Failed to add to watchlist');
      return res.json();
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['watchlist'] });
    },
  });
}

export function useUpdateWatchlist() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({ accountId, ...data }: { accountId: string; watch_level?: string; notes?: string }) => {
      const res = await fetch(`${API_BASE}/watchlist/watch/${accountId}`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data),
      });
      if (!res.ok) throw new Error('Failed to update watchlist entry');
      return res.json();
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['watchlist'] });
    },
  });
}
