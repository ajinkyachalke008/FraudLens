'use client';

import { useQuery } from '@tanstack/react-query';

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1';

// ──── Ingestion Sessions ────────────────────────────────────────

export function useIngestionSessions(limit = 20) {
  return useQuery({
    queryKey: ['ingestion-sessions', limit],
    queryFn: async () => {
      const res = await fetch(`${API_BASE}/ingest/sessions?limit=${limit}`);
      if (!res.ok) throw new Error('Failed to fetch ingestion sessions');
      return res.json();
    },
    staleTime: 30_000,
  });
}

export function useSessionDetail(sessionId: string | null) {
  return useQuery({
    queryKey: ['ingestion-session', sessionId],
    queryFn: async () => {
      const res = await fetch(`${API_BASE}/ingest/sessions/${sessionId}`);
      if (!res.ok) throw new Error('Failed to fetch session detail');
      return res.json();
    },
    enabled: !!sessionId,
    staleTime: 10_000,
  });
}

export function useSessionPreview(sessionId: string | null) {
  return useQuery({
    queryKey: ['ingestion-preview', sessionId],
    queryFn: async () => {
      const res = await fetch(`${API_BASE}/ingest/sessions/${sessionId}/preview`);
      if (!res.ok) throw new Error('Failed to fetch preview');
      return res.json();
    },
    enabled: !!sessionId,
    staleTime: 30_000,
  });
}
