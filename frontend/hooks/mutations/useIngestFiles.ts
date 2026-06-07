'use client';

import { useMutation, useQueryClient } from '@tanstack/react-query';

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1';

export function useIngestFiles() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({ files, caseId }: { files: File[]; caseId?: string }) => {
      const formData = new FormData();
      files.forEach(file => formData.append('files', file));

      const params = caseId ? `?case_id=${caseId}` : '';
      const res = await fetch(`${API_BASE}/ingest/upload-multi${params}`, {
        method: 'POST',
        body: formData,
      });
      if (!res.ok) throw new Error('Upload failed');
      return res.json();
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['ingestion-sessions'] });
    },
  });
}

export function useCommitSession() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (sessionId: string) => {
      const res = await fetch(`${API_BASE}/ingest/sessions/${sessionId}/commit`, {
        method: 'POST',
      });
      if (!res.ok) throw new Error('Commit failed');
      return res.json();
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['ingestion-sessions'] });
      queryClient.invalidateQueries({ queryKey: ['graph'] });
    },
  });
}
