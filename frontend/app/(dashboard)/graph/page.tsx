'use client';

import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import axios from 'axios';
import TransactionGraph, { GraphNode, GraphEdge } from '../../../components/graph/TransactionGraph';
import GraphSidebar from '../../../components/graph/GraphSidebar';

// MOCK DATASET for visual testing while Neo4j is offline
const MOCK_NODES: GraphNode[] = [
  { id: 'ACC-1001', accountNumber: 'ACC-1001', type: 'suspect', riskScore: 0.95, totalVolume: 500000, transactionCount: 15, isCentralNode: true, centrality: { pageRank: 1.2, betweenness: 0.8, degree: 5 }, metadata: { bankName: 'HDFC', accountType: 'Savings' } },
  { id: 'ACC-1002', accountNumber: 'ACC-1002', type: 'relay', riskScore: 0.75, totalVolume: 450000, transactionCount: 8, isCentralNode: false, centrality: { pageRank: 0.5, betweenness: 0.6, degree: 2 }, metadata: { bankName: 'SBI', accountType: 'Current' } },
  { id: 'ACC-1003', accountNumber: 'ACC-1003', type: 'victim', riskScore: 0.1, totalVolume: 100000, transactionCount: 2, isCentralNode: false, centrality: { pageRank: 0.1, betweenness: 0.0, degree: 1 }, metadata: { bankName: 'ICICI', accountType: 'Savings' } },
  { id: 'ACC-1004', accountNumber: 'ACC-1004', type: 'relay', riskScore: 0.82, totalVolume: 350000, transactionCount: 12, isCentralNode: false, centrality: { pageRank: 0.6, betweenness: 0.4, degree: 3 }, metadata: { bankName: 'Axis', accountType: 'Current' } },
  { id: 'ACC-1005', accountNumber: 'ACC-1005', type: 'relay', riskScore: 0.88, totalVolume: 200000, transactionCount: 5, isCentralNode: false, centrality: { pageRank: 0.3, betweenness: 0.1, degree: 1 }, metadata: { bankName: 'PNB', accountType: 'Savings' } },
  { id: 'ACC-1006', accountNumber: 'ACC-1006', type: 'clean', riskScore: 0.05, totalVolume: 10000, transactionCount: 1, isCentralNode: false, centrality: { pageRank: 0.05, betweenness: 0.0, degree: 1 }, metadata: { bankName: 'HDFC', accountType: 'Savings' } },
  { id: 'ACC-1007', accountNumber: 'ACC-1007', type: 'victim', riskScore: 0.15, totalVolume: 50000, transactionCount: 1, isCentralNode: false, centrality: { pageRank: 0.1, betweenness: 0.0, degree: 1 }, metadata: { bankName: 'SBI', accountType: 'Savings' } },
];

const MOCK_EDGES: GraphEdge[] = [
  { id: 'TX-001', source: 'ACC-1003', target: 'ACC-1001', amount: 100000, timestamp: '2025-10-01T10:00:00Z', transactionType: 'IMPS', riskFlag: 'high' },
  { id: 'TX-002', source: 'ACC-1001', target: 'ACC-1002', amount: 50000, timestamp: '2025-10-01T10:15:00Z', transactionType: 'UPI', riskFlag: 'high' },
  { id: 'TX-003', source: 'ACC-1001', target: 'ACC-1004', amount: 45000, timestamp: '2025-10-01T10:20:00Z', transactionType: 'RTGS', riskFlag: 'high' },
  { id: 'TX-004', source: 'ACC-1002', target: 'ACC-1005', amount: 48000, timestamp: '2025-10-01T11:00:00Z', transactionType: 'NEFT', riskFlag: 'medium' },
  { id: 'TX-005', source: 'ACC-1004', target: 'ACC-1005', amount: 40000, timestamp: '2025-10-01T11:05:00Z', transactionType: 'UPI', riskFlag: 'medium' },
  { id: 'TX-006', source: 'ACC-1006', target: 'ACC-1004', amount: 10000, timestamp: '2025-10-01T09:00:00Z', transactionType: 'UPI', riskFlag: 'low' },
  { id: 'TX-007', source: 'ACC-1007', target: 'ACC-1001', amount: 50000, timestamp: '2025-10-01T09:30:00Z', transactionType: 'IMPS', riskFlag: 'high' },
];

export default function GraphPage() {
  const [selectedNode, setSelectedNode] = useState<GraphNode | null>(null);
  const [selectedEdge, setSelectedEdge] = useState<GraphEdge | null>(null);
  const [useLive, setUseLive] = useState(false);
  const [searchAccount, setSearchAccount] = useState('ACC-1001');
  const [hops, setHops] = useState(2);

  const { data: liveData, isLoading, isError, error } = useQuery({
    queryKey: ['subgraph', searchAccount, hops],
    queryFn: async () => {
      const res = await axios.get(`http://localhost:8000/api/v1/graph/subgraph`, {
        params: { account_id: searchAccount, hops }
      });
      return res.data;
    },
    enabled: useLive && !!searchAccount,
  });

  const displayNodes = useLive ? (liveData?.nodes || []) : MOCK_NODES;
  const displayEdges = useLive ? (liveData?.edges || []) : MOCK_EDGES;

  const handleNodeClick = (node: GraphNode) => {
    setSelectedEdge(null);
    setSelectedNode(node);
  };

  const handleEdgeClick = (edge: GraphEdge) => {
    setSelectedNode(null);
    setSelectedEdge(edge);
  };

  const handleCloseSidebar = () => {
    setSelectedNode(null);
    setSelectedEdge(null);
  };

  return (
    <div className="flex h-screen w-full bg-background-base overflow-hidden">
      {/* Main Graph Area */}
      <div className="flex-1 flex flex-col relative p-4 gap-4">
        
        {/* Top Control Bar */}
        <div className="h-16 bg-background-surface border border-border-default rounded-lg shadow flex items-center justify-between px-6 z-10 shrink-0">
          <div>
            <h1 className="font-display text-xl text-primary-400 font-bold tracking-widest flex items-center gap-3">
              NETWORK EXPLORER
              <span className={`text-xs px-2 py-0.5 rounded ${useLive ? 'bg-primary-600/20 text-primary-400' : 'bg-warning-500/20 text-warning-400'}`}>
                {useLive ? 'LIVE DB' : 'MOCK DATA'}
              </span>
            </h1>
            <p className="text-xs text-text-muted font-mono mt-1">
              {useLive && liveData?.stats 
                ? `${liveData.stats.node_count} nodes, ${liveData.stats.edge_count} edges found` 
                : 'Showing 3-hop fraud ring'}
            </p>
          </div>
          
          <div className="flex gap-4 items-center">
            {/* Database Toggle */}
            <label className="flex items-center gap-2 cursor-pointer mr-4">
              <span className="text-sm font-mono text-text-muted">Live DB</span>
              <input 
                type="checkbox" 
                className="toggle toggle-primary"
                checked={useLive}
                onChange={(e) => setUseLive(e.target.checked)}
              />
            </label>

            {useLive && (
              <div className="flex gap-2 mr-4">
                <input 
                  type="text" 
                  value={searchAccount}
                  onChange={(e) => setSearchAccount(e.target.value)}
                  className="bg-background-base border border-border-default rounded px-3 py-1 text-sm font-mono text-text-primary focus:outline-none focus:border-primary-500"
                  placeholder="Target Account..."
                />
                <select 
                  value={hops}
                  onChange={(e) => setHops(Number(e.target.value))}
                  className="bg-background-base border border-border-default rounded px-2 py-1 text-sm font-mono text-text-primary"
                >
                  <option value={1}>1 Hop</option>
                  <option value={2}>2 Hops</option>
                  <option value={3}>3 Hops</option>
                </select>
              </div>
            )}

            <button className="px-4 py-2 bg-background-card border border-border-default rounded text-sm text-text-primary hover:border-primary-500 transition-colors font-mono">
              Filters
            </button>
            <button className="px-4 py-2 bg-primary-600/20 text-primary-400 border border-primary-500/50 rounded text-sm hover:bg-primary-600/30 transition-colors font-mono">
              Export SVG
            </button>
          </div>
        </div>

        {/* The D3 Canvas */}
        <div className="flex-1 relative rounded-xl overflow-hidden border border-border-default shadow-lg">
          {useLive && isLoading && (
            <div className="absolute inset-0 z-20 flex items-center justify-center bg-background-base/80 backdrop-blur-sm">
              <div className="font-mono text-primary-400 animate-pulse">Running Cypher traversal...</div>
            </div>
          )}
          
          {useLive && isError && (
            <div className="absolute inset-0 z-20 flex items-center justify-center bg-background-base/80 backdrop-blur-sm">
              <div className="font-mono text-danger-500 bg-danger-500/10 border border-danger-500/30 p-4 rounded max-w-lg text-center">
                <p className="font-bold mb-2">Neo4j Database Offline</p>
                <p className="text-xs text-text-muted">{error?.message || 'Failed to fetch graph data'}</p>
                <button 
                  onClick={() => setUseLive(false)}
                  className="mt-4 px-4 py-1 border border-danger-500/50 rounded hover:bg-danger-500/20"
                >
                  Return to Mock Data
                </button>
              </div>
            </div>
          )}

          {/* Live Stream Status Widget */}
          <div className="absolute top-4 left-1/2 transform -translate-x-1/2 z-10 flex items-center gap-3 bg-background-card/90 backdrop-blur border border-border-default px-4 py-2 rounded-full shadow-lg">
            <div className="flex items-center gap-2">
              <span className="relative flex h-3 w-3">
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-safe-400 opacity-75"></span>
                <span className="relative inline-flex rounded-full h-3 w-3 bg-safe-500"></span>
              </span>
              <span className="text-xs font-mono font-bold tracking-widest text-safe-400 uppercase">Stream Live</span>
            </div>
            <div className="w-px h-4 bg-border-default"></div>
            <div className="text-[10px] font-mono text-text-muted">Listening for anomalies...</div>
          </div>

          <TransactionGraph 
            nodes={displayNodes} 
            edges={displayEdges} 
            onNodeClick={handleNodeClick}
            onEdgeClick={handleEdgeClick}
          />
          
          {/* Legend Overlay */}
          <div className="absolute bottom-4 left-4 bg-background-surface/80 backdrop-blur border border-border-default p-4 rounded-lg text-xs font-mono">
            <div className="text-text-muted mb-2 font-bold tracking-wider">NODE LEGEND</div>
            <div className="space-y-2">
              <div className="flex items-center gap-2"><div className="w-3 h-3 rounded-full bg-danger-500"></div> <span className="text-text-primary">Suspect / Fraud</span></div>
              <div className="flex items-center gap-2"><div className="w-3 h-3 rounded-full bg-warning-500"></div> <span className="text-text-primary">Victim</span></div>
              <div className="flex items-center gap-2"><div className="w-3 h-3 rounded-full" style={{ backgroundColor: 'var(--node-relay)' }}></div> <span className="text-text-primary">Relay / Mule</span></div>
              <div className="flex items-center gap-2"><div className="w-3 h-3 rounded-full bg-safe-500"></div> <span className="text-text-primary">Clean</span></div>
            </div>
          </div>
        </div>
      </div>

      {/* Slide-out Sidebar */}
      {(selectedNode ?? selectedEdge) && (
        <GraphSidebar 
          selectedNode={selectedNode} 
          selectedEdge={selectedEdge} 
          onClose={handleCloseSidebar} 
        />
      )}
    </div>
  );
}
