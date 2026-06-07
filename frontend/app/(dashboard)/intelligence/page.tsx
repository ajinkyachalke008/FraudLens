'use client';

import React from 'react';
import { useQuery } from '@tanstack/react-query';
import CrossCaseTable from '@/components/intelligence/CrossCaseTable';
import SyndicateGraph from '@/components/intelligence/SyndicateGraph';
import { Network, Activity, ShieldAlert, Loader2 } from 'lucide-react';
import { useAuth } from '@/contexts/AuthContext';

export default function GlobalIntelligenceDashboard() {
  const { token } = useAuth();

  const { data: linksData, isLoading: linksLoading } = useQuery({
    queryKey: ['cross-case-links'],
    queryFn: async () => {
      const res = await fetch('http://localhost:8001/api/v1/intelligence/cross-case/links', {
        headers: { Authorization: `Bearer ${token}` }
      });
      if (!res.ok) throw new Error('Failed to fetch links');
      return res.json();
    },
    enabled: !!token,
  });

  const { data: graphData, isLoading: graphLoading } = useQuery({
    queryKey: ['cross-case-graph'],
    queryFn: async () => {
      const res = await fetch('http://localhost:8001/api/v1/intelligence/cross-case/graph', {
        headers: { Authorization: `Bearer ${token}` }
      });
      if (!res.ok) throw new Error('Failed to fetch graph');
      return res.json();
    },
    enabled: !!token,
  });

  return (
    <div className="flex flex-col h-[calc(100vh-64px)] overflow-y-auto bg-background-base p-6 gap-6">
      <div className="flex items-center gap-4">
        <div className="p-3 bg-warning-500/10 rounded-xl border border-warning-500/20">
          <Network className="w-8 h-8 text-warning-400" />
        </div>
        <div>
          <h1 className="text-2xl font-bold text-text-primary">Global Criminal Intelligence</h1>
          <p className="text-text-secondary">Detecting multi-case syndicate overlaps and shared money mules.</p>
        </div>
      </div>

      <div className="grid grid-cols-3 gap-6">
        <div className="bg-background-surface border border-border-default rounded-xl p-6">
          <h3 className="text-text-muted font-mono text-sm uppercase tracking-wider mb-2">Syndicates Detected</h3>
          <div className="text-4xl font-bold text-text-primary">
            {linksLoading ? <Loader2 className="animate-spin w-8 h-8" /> : linksData?.total_syndicates_detected || 0}
          </div>
        </div>
        <div className="bg-background-surface border border-border-default rounded-xl p-6">
          <h3 className="text-text-muted font-mono text-sm uppercase tracking-wider mb-2">Total Mules Flagged</h3>
          <div className="text-4xl font-bold text-warning-400">
            {linksLoading ? <Loader2 className="animate-spin w-8 h-8" /> : linksData?.links?.length || 0}
          </div>
        </div>
        <div className="bg-background-surface border border-border-default rounded-xl p-6">
          <h3 className="text-text-muted font-mono text-sm uppercase tracking-wider mb-2">Network Risk Status</h3>
          <div className="flex items-center gap-2 text-error-400">
            <Activity className="w-8 h-8" />
            <span className="text-4xl font-bold">CRITICAL</span>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 xl:grid-cols-3 gap-6">
        <div className="xl:col-span-2 space-y-4">
          <h2 className="text-lg font-bold text-text-primary flex items-center gap-2">
            <Network className="w-5 h-5 text-primary-400" />
            Macro Syndicate Graph
          </h2>
          <p className="text-sm text-text-secondary">Visualizing the shared nodes connecting isolated criminal cases.</p>
          {graphLoading ? (
             <div className="w-full h-[600px] bg-background-surface rounded-xl border border-border-default flex items-center justify-center">
               <Loader2 className="w-8 h-8 animate-spin text-primary-500" />
             </div>
          ) : (
            <SyndicateGraph nodes={graphData?.nodes || []} links={graphData?.links || []} />
          )}
        </div>
        
        <div className="space-y-4 xl:col-span-1">
          <h2 className="text-lg font-bold text-text-primary flex items-center gap-2">
            <ShieldAlert className="w-5 h-5 text-warning-400" />
            Shared Mules
          </h2>
          <p className="text-sm text-text-secondary">Accounts operating across multiple jurisdictions.</p>
          {linksLoading ? (
            <div className="w-full h-64 bg-background-surface rounded-xl border border-border-default flex items-center justify-center">
              <Loader2 className="w-8 h-8 animate-spin text-primary-500" />
            </div>
          ) : (
            <CrossCaseTable links={linksData?.links || []} />
          )}
        </div>
      </div>
    </div>
  );
}
