'use client';

import React, { useState, useEffect } from 'react';
import { LayoutGrid, List, Search, Loader2 } from 'lucide-react';
import CaseTable from '@/components/cases/CaseTable';
import KanbanBoard from '@/components/cases/KanbanBoard';

export default function CaseExplorerPage() {
  const [view, setView] = useState<'table' | 'kanban'>('table');
  const [cases, setCases] = useState([]);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    fetchCases();
  }, []);

  const fetchCases = async () => {
    setIsLoading(true);
    try {
      // Hardcoded API endpoint or you could use a shared config
      const response = await fetch('http://localhost:8001/api/v1/cases/?limit=50');
      if (response.ok) {
        const data = await response.json();
        setCases(data.cases);
      }
    } catch (error) {
      console.error('Failed to fetch cases:', error);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="flex-1 p-8 overflow-y-auto">
      <div className="max-w-7xl mx-auto space-y-8">
        
        {/* Header & Controls */}
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <h1 className="text-3xl font-display font-bold tracking-tight">Case Explorer</h1>
            <p className="text-text-muted mt-2">Manage active investigations, track evidence, and assign workflows.</p>
          </div>
          
          <div className="flex items-center gap-4">
            <div className="relative">
              <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-text-muted" />
              <input 
                type="text" 
                placeholder="Search case # or suspect..."
                className="bg-background-surface border border-border-default rounded-lg pl-9 pr-4 py-2 font-mono text-sm focus:border-primary-500 focus:outline-none w-64"
              />
            </div>
            
            <div className="flex bg-background-surface rounded-lg p-1 border border-border-default">
              <button 
                onClick={() => setView('table')}
                className={`p-2 rounded-md transition-colors ${view === 'table' ? 'bg-background-card text-primary-400 shadow' : 'text-text-muted hover:text-text-primary'}`}
                title="Table View"
              >
                <List className="w-4 h-4" />
              </button>
              <button 
                onClick={() => setView('kanban')}
                className={`p-2 rounded-md transition-colors ${view === 'kanban' ? 'bg-background-card text-primary-400 shadow' : 'text-text-muted hover:text-text-primary'}`}
                title="Kanban View"
              >
                <LayoutGrid className="w-4 h-4" />
              </button>
            </div>
          </div>
        </div>

        {/* Content Area */}
        {isLoading ? (
          <div className="flex justify-center items-center h-64">
            <Loader2 className="w-8 h-8 text-primary-500 animate-spin" />
          </div>
        ) : view === 'table' ? (
          <div className="animate-in fade-in zoom-in-95 duration-300">
             <CaseTable cases={cases} />
          </div>
        ) : (
          <div className="animate-in fade-in slide-in-from-bottom-4 duration-300">
            <KanbanBoard cases={cases} />
          </div>
        )}

      </div>
    </div>
  );
}
