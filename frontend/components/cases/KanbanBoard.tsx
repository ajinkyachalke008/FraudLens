'use client';

import React from 'react';
import Link from 'next/link';
import { ArrowRight, ShieldAlert, AlertTriangle, IndianRupee, Users } from 'lucide-react';

interface Case {
  id: string;
  case_number: string;
  title: string;
  status: string;
  priority: string;
  total_amount: number;
  victim_count: number;
  created_at: string;
}

interface Props {
  cases: Case[];
  onStatusChange?: (caseId: string, newStatus: string) => void;
}

const COLUMNS = ['open', 'investigating', 'closed', 'archived'];

export default function KanbanBoard({ cases, onStatusChange }: Props) {
  
  const getPriorityIcon = (priority: string) => {
    switch(priority) {
      case 'critical': return <ShieldAlert className="w-4 h-4 text-danger-500" />;
      case 'high': return <AlertTriangle className="w-4 h-4 text-warning-500" />;
      default: return <AlertTriangle className="w-4 h-4 text-primary-500" />;
    }
  };

  return (
    <div className="flex gap-6 overflow-x-auto pb-8 h-[700px]">
      {COLUMNS.map((columnStatus) => {
        const columnCases = cases.filter(c => c.status === columnStatus);
        
        return (
          <div key={columnStatus} className="flex-none w-80 flex flex-col bg-background-surface/50 rounded-xl border border-border-default">
            {/* Column Header */}
            <div className="p-4 border-b border-border-default flex items-center justify-between bg-background-surface rounded-t-xl">
              <h3 className="font-mono text-sm font-bold text-text-primary uppercase tracking-widest">{columnStatus}</h3>
              <span className="bg-background-base text-text-muted px-2 py-0.5 rounded text-xs font-mono">{columnCases.length}</span>
            </div>

            {/* Column Body */}
            <div className="flex-1 p-3 overflow-y-auto space-y-3">
              {columnCases.map((c) => (
                <div key={c.id} className="bg-background-card border border-[#1f2937] hover:border-primary-500/50 rounded-lg p-4 shadow-lg transition-colors group">
                  <div className="flex justify-between items-start mb-3">
                    <span className="text-xs font-mono text-primary-400 font-medium bg-primary-500/10 px-2 py-0.5 rounded">{c.case_number}</span>
                    {getPriorityIcon(c.priority)}
                  </div>
                  
                  <h4 className="text-sm font-medium text-text-primary leading-snug mb-3">{c.title}</h4>
                  
                  <div className="flex items-center gap-4 text-xs font-mono text-text-muted mb-4">
                    <div className="flex items-center gap-1.5"><IndianRupee className="w-3.5 h-3.5" /> {(c.total_amount / 1000).toFixed(1)}k</div>
                    <div className="flex items-center gap-1.5"><Users className="w-3.5 h-3.5" /> {c.victim_count}</div>
                  </div>

                  <div className="flex items-center justify-between pt-3 border-t border-[#1f2937]">
                    <span className="text-[10px] font-mono text-text-muted uppercase tracking-wider">{new Date(c.created_at).toLocaleDateString()}</span>
                    <Link href={`/cases/${c.id}`} className="flex items-center gap-1 text-xs font-medium text-primary-500 hover:text-primary-400 group-hover:translate-x-1 transition-transform">
                      Inspect <ArrowRight className="w-3.5 h-3.5" />
                    </Link>
                  </div>
                </div>
              ))}
              
              {columnCases.length === 0 && (
                <div className="h-24 border-2 border-dashed border-[#1f2937] rounded-lg flex items-center justify-center text-xs font-mono text-text-muted">
                  Drop cases here
                </div>
              )}
            </div>
          </div>
        );
      })}
    </div>
  );
}
