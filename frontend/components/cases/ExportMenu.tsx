'use client';

import React, { useState } from 'react';
import { Download, FileText, FileBadge, ChevronDown, Loader2 } from 'lucide-react';
import { toast } from 'sonner';

interface Props {
  caseId: string;
}

export default function ExportMenu({ caseId }: Props) {
  const [isOpen, setIsOpen] = useState(false);
  const [isExporting, setIsExporting] = useState(false);

  const handleExport = async (type: 'fir' | 'chargesheet') => {
    setIsOpen(false);
    setIsExporting(true);
    toast.loading(`Compiling official ${type.toUpperCase()} document...`, { id: 'export' });
    
    try {
      const response = await fetch(`http://localhost:8001/api/v1/reports/export/${type}/${caseId}`);
      if (!response.ok) throw new Error('Export failed');
      
      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `${type === 'fir' ? 'FIR' : 'ChargeSheet'}_${caseId}.${type === 'fir' ? 'pdf' : 'docx'}`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
      
      toast.success(`${type.toUpperCase()} exported successfully!`, { id: 'export' });
    } catch (error) {
      toast.error('Failed to generate document.', { id: 'export' });
    } finally {
      setIsExporting(false);
    }
  };

  return (
    <div className="relative">
      <button 
        onClick={() => setIsOpen(!isOpen)}
        disabled={isExporting}
        className="flex items-center gap-2 bg-primary-600 hover:bg-primary-500 disabled:opacity-50 text-white px-4 py-2 rounded-lg transition-colors font-mono text-sm font-bold"
      >
        {isExporting ? <Loader2 className="w-4 h-4 animate-spin" /> : <Download className="w-4 h-4" />}
        EXPORT
        <ChevronDown className="w-4 h-4 opacity-70" />
      </button>

      {isOpen && (
        <>
          <div className="fixed inset-0 z-10" onClick={() => setIsOpen(false)} />
          <div className="absolute right-0 mt-2 w-56 bg-background-card border border-border-default rounded-xl shadow-xl z-20 overflow-hidden animate-in fade-in slide-in-from-top-2">
            <div className="p-2 border-b border-border-default">
              <span className="text-[10px] font-mono text-text-muted uppercase tracking-widest px-2">Official Documents</span>
            </div>
            <div className="p-1">
              <button 
                onClick={() => handleExport('fir')}
                className="w-full text-left flex items-center gap-3 px-3 py-2.5 hover:bg-background-surface rounded-lg text-sm text-text-primary transition-colors group"
              >
                <FileText className="w-4 h-4 text-primary-400 group-hover:scale-110 transition-transform" />
                Draft FIR (PDF)
              </button>
              <button 
                onClick={() => handleExport('chargesheet')}
                className="w-full text-left flex items-center gap-3 px-3 py-2.5 hover:bg-background-surface rounded-lg text-sm text-text-primary transition-colors group"
              >
                <FileBadge className="w-4 h-4 text-warning-400 group-hover:scale-110 transition-transform" />
                Draft Charge Sheet (DOCX)
              </button>
            </div>
          </div>
        </>
      )}
    </div>
  );
}
