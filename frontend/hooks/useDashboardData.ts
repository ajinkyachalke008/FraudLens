import { useQuery } from '@tanstack/react-query';

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1';

const getHeaders = (): Record<string, string> => {
  if (typeof window === 'undefined') return {};
  const token = localStorage.getItem('fraudlens_token');
  return token ? { 'Authorization': `Bearer ${token}` } : {};
};

interface TelemetryData {
  telemetry: {
    threat_level: string;
    total_protected_value: number;
    active_cases: number;
  };
  recent_alerts: CaseAlert[];
}

interface CaseAlert {
  id: string;
  case_number: string;
  title: string;
  status: string;
  priority: string;
  amount: number;
  created_at: string | null;
}

interface StreamMetrics {
  active_websocket_clients: number;
  messages_processed: number;
  high_risk_flags: number;
  last_processed_time: string | null;
}

export function useDashboardTelemetry() {
  return useQuery<TelemetryData>({
    queryKey: ['dashboard', 'telemetry'],
    queryFn: async () => {
      const res = await fetch(`${API_BASE}/dashboard/telemetry`, { headers: getHeaders() });
      if (!res.ok) throw new Error('Failed to fetch telemetry');
      return res.json();
    },
    refetchInterval: 10000, // Refresh every 10 seconds
  });
}

export function useStreamMetrics() {
  return useQuery<StreamMetrics>({
    queryKey: ['stream', 'metrics'],
    queryFn: async () => {
      const res = await fetch(`${API_BASE}/ws/metrics`, { headers: getHeaders() });
      if (!res.ok) throw new Error('Failed to fetch stream metrics');
      return res.json();
    },
    refetchInterval: 5000, // Refresh every 5 seconds
  });
}

export function useCases(status?: string, priority?: string) {
  return useQuery({
    queryKey: ['cases', status, priority],
    queryFn: async () => {
      const params = new URLSearchParams();
      if (status) params.set('status', status);
      if (priority) params.set('priority', priority);
      params.set('limit', '10');
      const res = await fetch(`${API_BASE}/cases/?${params.toString()}`, { headers: getHeaders() });
      if (!res.ok) throw new Error('Failed to fetch cases');
      return res.json();
    },
    refetchInterval: 15000,
  });
}
