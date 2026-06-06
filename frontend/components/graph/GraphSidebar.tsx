import React, { useState } from 'react';
import { GraphNode, GraphEdge } from './TransactionGraph';

interface GraphSidebarProps {
  selectedNode: GraphNode | null;
  selectedEdge: GraphEdge | null;
  onClose: () => void;
}

export default function GraphSidebar({ selectedNode, selectedEdge, onClose }: GraphSidebarProps) {
  const [activeTab, setActiveTab] = useState<'details' | 'ai'>('details');

  if (!selectedNode && !selectedEdge) return null;

  return (
    <div className="w-80 h-full bg-background-card border-l border-border-default shadow-xl flex flex-col">
      <div className="p-4 border-b border-border-default flex justify-between items-center">
        <h2 className="font-display text-primary-400 font-bold tracking-wider">
          {selectedNode ? 'NODE DETAILS' : 'EDGE DETAILS'}
        </h2>
        <button onClick={onClose} className="text-text-muted hover:text-text-primary transition-colors">
          ✕
        </button>
      </div>

      {selectedNode && (
        <div className="flex border-b border-border-default">
          <button 
            className={`flex-1 py-2 text-xs font-mono tracking-wider ${activeTab === 'details' ? 'border-b-2 border-primary-500 text-primary-400' : 'text-text-muted hover:bg-background-surface'}`}
            onClick={() => setActiveTab('details')}
          >
            DETAILS
          </button>
          <button 
            className={`flex-1 py-2 text-xs font-mono tracking-wider ${activeTab === 'ai' ? 'border-b-2 border-primary-500 text-primary-400' : 'text-text-muted hover:bg-background-surface'}`}
            onClick={() => setActiveTab('ai')}
          >
            AI ANALYSIS
          </button>
        </div>
      )}

      <div className="p-4 overflow-y-auto flex-1">
        {selectedNode && activeTab === 'details' && (
          <div className="space-y-6">
            <div>
              <div className="text-xs text-text-muted font-mono mb-1">ACCOUNT NUMBER</div>
              <div className="font-mono text-lg text-text-primary">{selectedNode.accountNumber}</div>
            </div>
            
            <div className="grid grid-cols-2 gap-4">
              <div className="bg-background-surface p-3 rounded border border-border-default">
                <div className="text-xs text-text-muted font-mono mb-1">RISK SCORE</div>
                <div className={`font-display text-xl ${selectedNode.riskScore > 0.7 ? 'text-danger-500' : selectedNode.riskScore > 0.4 ? 'text-warning-500' : 'text-safe-500'}`}>
                  {(selectedNode.riskScore * 100).toFixed(1)}%
                </div>
              </div>
              <div className="bg-background-surface p-3 rounded border border-border-default">
                <div className="text-xs text-text-muted font-mono mb-1">LABEL</div>
                <div className="capitalize text-primary-400 font-semibold">{selectedNode.type}</div>
              </div>
            </div>

            <div>
              <div className="text-xs text-text-muted font-mono mb-1">CENTRALITY METRICS</div>
              <div className="space-y-2 bg-background-surface p-3 rounded border border-border-default text-sm font-mono">
                <div className="flex justify-between">
                  <span className="text-text-secondary">PageRank:</span>
                  <span className="text-text-primary">{selectedNode.centrality.pageRank.toFixed(4)}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-text-secondary">Betweenness:</span>
                  <span className="text-text-primary">{selectedNode.centrality.betweenness.toFixed(4)}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-text-secondary">Degree:</span>
                  <span className="text-text-primary">{selectedNode.centrality.degree}</span>
                </div>
              </div>
            </div>
            
            <button className="w-full py-2 bg-danger-500/10 text-danger-400 border border-danger-500/30 rounded hover:bg-danger-500/20 transition-colors font-mono text-sm uppercase tracking-wide">
              Recommend Freeze
            </button>
          </div>
        )}

        {selectedNode && activeTab === 'ai' && (
          <div className="space-y-6">
            <div>
              <div className="text-xs text-text-muted font-mono mb-1">PREDICTIVE FLAG</div>
              <div className="font-mono text-lg text-text-primary">{selectedNode.accountNumber}</div>
            </div>
            
            {/* Core Risk Score Card */}
            <div className="bg-background-surface p-4 rounded border border-border-default relative overflow-hidden">
              <div className="absolute top-0 right-0 p-2">
                <span className="text-[9px] bg-primary-600/20 text-primary-400 px-1.5 py-0.5 rounded font-mono uppercase">FraudSAGE v1.2</span>
              </div>
              <div className="flex justify-between items-end mb-2 mt-2">
                <span className="text-xs text-text-muted font-mono">GNN Probability</span>
                <span className={`font-display text-3xl font-bold ${selectedNode.riskScore > 0.7 ? 'text-danger-500' : selectedNode.riskScore > 0.4 ? 'text-warning-500' : 'text-safe-500'}`}>
                  {(selectedNode.riskScore * 100).toFixed(1)}%
                </span>
              </div>
              <div className="w-full h-2 bg-background-base rounded-full overflow-hidden mb-3">
                <div 
                  className={`h-full transition-all duration-1000 ${selectedNode.riskScore > 0.7 ? 'bg-danger-500' : selectedNode.riskScore > 0.4 ? 'bg-warning-500' : 'bg-safe-500'}`} 
                  style={{ width: `${selectedNode.riskScore * 100}%` }}
                ></div>
              </div>
              <div className="flex justify-between text-[10px] font-mono text-text-secondary uppercase">
                <span>Safe</span>
                <span>Review</span>
                <span>Flagged</span>
              </div>
            </div>

            {/* AI Confidence & Embeddings */}
            <div className="grid grid-cols-2 gap-3">
              <div className="bg-background-base p-3 rounded border border-border-default">
                <div className="text-[10px] text-text-muted font-mono mb-1">MODEL CONFIDENCE</div>
                <div className="font-mono text-lg text-primary-400">89.4%</div>
                <div className="text-[9px] text-text-secondary mt-1">Based on 16-dim latent vector</div>
              </div>
              <div className="bg-background-base p-3 rounded border border-border-default">
                <div className="text-[10px] text-text-muted font-mono mb-1">NETWORK DEGREE</div>
                <div className="font-mono text-lg text-primary-400">{selectedNode.centrality.degree} Hops</div>
                <div className="text-[9px] text-text-secondary mt-1">Topology complexity</div>
              </div>
            </div>

            {/* Syndicate Assignment */}
            <div className="bg-primary-900/10 border border-primary-500/20 rounded p-3 flex justify-between items-center">
              <div>
                <div className="text-[10px] text-primary-400/80 font-mono mb-1">PREDICTED SYNDICATE</div>
                <div className="text-sm font-mono text-primary-300">SYN-10{Math.floor(Math.random() * 5)}</div>
              </div>
              <div className="bg-primary-500/20 text-primary-300 px-2 py-1 rounded text-xs font-mono">K-Means</div>
            </div>

            {/* SHAP Explanations */}
            <div>
              <div className="text-xs text-text-muted font-mono mb-3 flex items-center justify-between border-b border-border-default pb-2">
                <span>SHAP EXPLANATION (TREE EXPLAINER)</span>
              </div>
              <div className="space-y-4">
                
                {/* Feature 1 */}
                <div className="text-sm">
                  <div className="flex justify-between font-mono mb-1">
                    <span className="text-text-primary text-xs">Degree Centrality</span>
                    <span className="text-danger-400 text-xs">+0.60 SHAP</span>
                  </div>
                  <div className="w-full h-1.5 bg-background-surface rounded-full overflow-hidden mb-1">
                    <div className="h-full bg-danger-500" style={{ width: '60%' }}></div>
                  </div>
                  <div className="text-[10px] text-text-secondary italic">Account is acting as a massive central relay point.</div>
                </div>
                
                {/* Feature 2 */}
                <div className="text-sm">
                  <div className="flex justify-between font-mono mb-1">
                    <span className="text-text-primary text-xs">Velocity (1h)</span>
                    <span className="text-danger-400 text-xs">+0.45 SHAP</span>
                  </div>
                  <div className="w-full h-1.5 bg-background-surface rounded-full overflow-hidden mb-1">
                    <div className="h-full bg-danger-400" style={{ width: '45%' }}></div>
                  </div>
                  <div className="text-[10px] text-text-secondary italic">Rapid burst of 8 transactions in under an hour.</div>
                </div>

                {/* Feature 3 (Safe factor) */}
                <div className="text-sm">
                  <div className="flex justify-between font-mono mb-1">
                    <span className="text-text-primary text-xs">Account Age</span>
                    <span className="text-safe-400 text-xs">-0.10 SHAP</span>
                  </div>
                  <div className="w-full h-1.5 bg-background-surface rounded-full overflow-hidden mb-1 flex justify-end">
                    <div className="h-full bg-safe-500" style={{ width: '10%' }}></div>
                  </div>
                  <div className="text-[10px] text-text-secondary italic">Older account history slightly reduces risk.</div>
                </div>

              </div>
            </div>

            {/* Action Engine */}
            <div className="pt-2 border-t border-border-default space-y-2">
              <div className="text-[10px] text-text-muted font-mono mb-2">AUTOMATED RECOMMENDATIONS</div>
              {selectedNode.riskScore > 0.7 ? (
                <>
                  <button className="w-full py-2 bg-danger-500/10 text-danger-400 border border-danger-500/30 rounded hover:bg-danger-500/20 transition-colors font-mono text-xs uppercase tracking-wide flex items-center justify-center gap-2">
                    <span>⚡</span> Freeze Account
                  </button>
                  <button className="w-full py-2 bg-background-surface text-text-primary border border-border-default rounded hover:border-primary-500/50 transition-colors font-mono text-xs uppercase tracking-wide">
                    Escalate to Cyber Cell
                  </button>
                </>
              ) : selectedNode.riskScore > 0.4 ? (
                <button className="w-full py-2 bg-warning-500/10 text-warning-400 border border-warning-500/30 rounded hover:bg-warning-500/20 transition-colors font-mono text-xs uppercase tracking-wide flex items-center justify-center gap-2">
                  <span>⚠️</span> Request KYC Update
                </button>
              ) : (
                <div className="p-2 bg-safe-500/10 border border-safe-500/30 rounded text-safe-400 text-[10px] font-mono text-center">
                  No automated actions required.
                </div>
              )}
            </div>
          </div>
        )}

        {selectedEdge && (
          <div className="space-y-6">
            <div>
              <div className="text-xs text-text-muted font-mono mb-1">TRANSACTION REF</div>
              <div className="font-mono text-sm text-text-primary break-all">{selectedEdge.id}</div>
            </div>
            
            <div className="bg-background-surface p-4 rounded border border-border-default flex flex-col items-center justify-center space-y-2">
              <div className="text-xs text-text-muted font-mono">AMOUNT</div>
              <div className="font-display text-2xl text-primary-400">₹{selectedEdge.amount.toLocaleString('en-IN')}</div>
            </div>

            <div className="space-y-3">
              <div>
                <div className="text-xs text-text-muted font-mono mb-1">SENDER</div>
                <div className="font-mono text-sm text-text-primary bg-background-surface p-2 rounded border border-border-default">
                  {typeof selectedEdge.source === 'string' ? selectedEdge.source : selectedEdge.source.accountNumber}
                </div>
              </div>
              <div className="flex justify-center text-text-muted">↓</div>
              <div>
                <div className="text-xs text-text-muted font-mono mb-1">RECEIVER</div>
                <div className="font-mono text-sm text-text-primary bg-background-surface p-2 rounded border border-border-default">
                  {typeof selectedEdge.target === 'string' ? selectedEdge.target : selectedEdge.target.accountNumber}
                </div>
              </div>
            </div>

            <div>
              <div className="text-xs text-text-muted font-mono mb-1">METADATA</div>
              <div className="space-y-2 bg-background-surface p-3 rounded border border-border-default text-sm font-mono">
                <div className="flex justify-between">
                  <span className="text-text-secondary">Time:</span>
                  <span className="text-text-primary">{new Date(selectedEdge.timestamp).toLocaleString()}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-text-secondary">Type:</span>
                  <span className="text-text-primary">{selectedEdge.transactionType}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-text-secondary">Risk:</span>
                  <span className={`capitalize ${selectedEdge.riskFlag === 'high' ? 'text-danger-500' : 'text-text-primary'}`}>{selectedEdge.riskFlag}</span>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
