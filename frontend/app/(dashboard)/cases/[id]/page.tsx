'use client';

import React, { useState, useEffect } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { ShieldAlert, IndianRupee, Users, ArrowLeft, Loader2, Link as LinkIcon, Download } from 'lucide-react';
import Link from 'next/link';
import CaseTimeline from '@/components/cases/CaseTimeline';
import ExportMenu from '@/components/cases/ExportMenu';

// Import maps and graph
import SpatialMap from '@/components/map/SpatialMap';
import TransactionGraph from '@/components/graph/TransactionGraph';

export default function CaseDashboard() {
  const params = useParams();
  const router = useRouter();
  const caseId = params.id as string;

  const [caseData, setCaseData] = useState<any>(null);
  const [timeline, setTimeline] = useState<any[]>([]);
  const [spatialData, setSpatialData] = useState({ locations: [], connections: [] });
  const [graphData, setGraphData] = useState({ nodes: [], links: [] });
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    if (caseId) fetchCaseData();
  }, [caseId]);

  const fetchCaseData = async () => {
    setIsLoading(true);
    try {
      const [caseRes, timelineRes, spatialRes, graphRes] = await Promise.all([
        fetch(`http://localhost:8001/api/v1/cases/${caseId}`),
        fetch(`http://localhost:8001/api/v1/cases/${caseId}/timeline`),
        fetch(`http://localhost:8001/api/v1/cases/${caseId}/spatial`),
        fetch(`http://localhost:8001/api/v1/cases/${caseId}/graph`)
      ]);
      
      if (caseRes.ok) {
        const cData = await caseRes.json();
        setCaseData(cData.case);
      }
      if (timelineRes.ok) {
        const tData = await timelineRes.json();
        setTimeline(tData.timeline);
      }
      if (spatialRes.ok) {
        setSpatialData(await spatialRes.json());
      }
      if (graphRes.ok) {
        setGraphData(await graphRes.json());
      }
    } catch (error) {
      console.error(error);
    } finally {
      setIsLoading(false);
    }
  };

  if (isLoading) {
    return <div className="flex-1 flex items-center justify-center"><Loader2 className="w-8 h-8 animate-spin text-primary-500" /></div>;
  }

  if (!caseData) return <div className="p-8 text-center">Case not found</div>;

  return (
    <div className="flex-1 p-6 h-screen flex flex-col overflow-hidden">
      {/* Top Header */}
      <div className="flex items-center justify-between mb-6 shrink-0">
        <div className="flex items-center gap-4">
          <button onClick={() => router.back()} className="p-2 bg-background-surface hover:bg-border-default rounded-lg transition-colors">
            <ArrowLeft className="w-5 h-5 text-text-primary" />
          </button>
          <div>
            <div className="flex items-center gap-3">
              <h1 className="text-2xl font-display font-bold">{caseData.title}</h1>
              <span className="px-2 py-0.5 rounded text-xs font-mono font-bold bg-primary-500/10 text-primary-400 border border-primary-500/20">
                {caseData.case_number}
              </span>
            </div>
            <p className="text-sm text-text-muted mt-1">{caseData.description}</p>
          </div>
        </div>
        
        <div className="flex items-center gap-6 bg-background-surface px-6 py-3 rounded-xl border border-border-default shadow-sm">
          <div className="flex flex-col">
            <span className="text-[10px] font-mono text-text-muted uppercase tracking-wider">Status</span>
            <select 
              value={caseData.status} 
              onChange={() => {}} 
              className="bg-transparent text-sm font-bold text-text-primary focus:outline-none appearance-none"
            >
              <option value="open">OPEN</option>
              <option value="investigating">INVESTIGATING</option>
              <option value="closed">CLOSED</option>
            </select>
          </div>
          <div className="w-px h-8 bg-border-default"></div>
          <div className="flex flex-col">
            <span className="text-[10px] font-mono text-text-muted uppercase tracking-wider">Volume</span>
            <div className="flex items-center gap-1 text-sm font-bold text-danger-400">
              <IndianRupee className="w-4 h-4" />
              {(caseData.total_amount / 1000).toFixed(1)}k
            </div>
          </div>
          <div className="w-px h-8 bg-border-default"></div>
          <div className="flex flex-col">
            <span className="text-[10px] font-mono text-text-muted uppercase tracking-wider">Victims</span>
            <div className="flex items-center gap-1 text-sm font-bold text-warning-400">
              <Users className="w-4 h-4" />
              {caseData.victim_count}
            </div>
          </div>
          <div className="w-px h-8 bg-border-default"></div>
          <ExportMenu caseId={caseId} />
        </div>
      </div>

      {/* Main Grid */}
      <div className="flex-1 grid grid-cols-12 gap-6 min-h-0">
        
        {/* Left Column: Timeline */}
        <div className="col-span-4 h-full flex flex-col min-h-0">
          <CaseTimeline caseId={caseId} initialEvents={timeline} />
        </div>

        {/* Right Column: Visualization Twin */}
        <div className="col-span-8 flex flex-col gap-6 h-full min-h-0">
          
          {/* Top Right: Spatial Map (Half Height) */}
          <div className="flex-1 relative bg-background-surface border border-border-default rounded-xl overflow-hidden shadow-lg group">
            <div className="absolute top-4 left-4 z-10 flex items-center gap-2 bg-background-surface/80 backdrop-blur px-3 py-1.5 rounded-lg border border-border-default">
              <ShieldAlert className="w-4 h-4 text-primary-400" />
              <span className="text-xs font-mono font-bold tracking-widest text-text-primary">SPATIAL TWIN</span>
            </div>
            <div className="absolute inset-0 pointer-events-auto">
              <SpatialMap locations={spatialData.locations} connections={spatialData.connections} />
            </div>
          </div>

          {/* Bottom Right: Network Graph (Half Height) */}
          <div className="flex-1 relative bg-background-surface border border-border-default rounded-xl overflow-hidden shadow-lg group">
             <div className="absolute top-4 left-4 z-10 flex items-center gap-2 bg-background-surface/80 backdrop-blur px-3 py-1.5 rounded-lg border border-border-default">
              <LinkIcon className="w-4 h-4 text-warning-400" />
              <span className="text-xs font-mono font-bold tracking-widest text-text-primary">NETWORK TWIN</span>
            </div>
            <div className="absolute inset-0 pointer-events-auto bg-[#0a0a0a]">
              <TransactionGraph 
                nodes={graphData.nodes} 
                edges={graphData.links} 
                onNodeClick={() => {}} 
                onEdgeClick={() => {}} 
              />
            </div>
          </div>

        </div>
      </div>
    </div>
  );
}
