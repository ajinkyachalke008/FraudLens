'use client';

import React, { useState, useRef, useEffect } from 'react';
import { FileText, Download, Loader2, Sparkles, AlertTriangle, Terminal } from 'lucide-react';
import { toast } from 'sonner';

export default function ReportsPage() {
  const [caseId, setCaseId] = useState('CASE-2026-A8F3');
  const [isGenerating, setIsGenerating] = useState(false);
  const [pdfUrl, setPdfUrl] = useState<string | null>(null);
  
  // Streaming state
  const [streamedText, setStreamedText] = useState('');
  const [isStreaming, setIsStreaming] = useState(false);
  const scrollRef = useRef<HTMLDivElement>(null);

  // Auto-scroll while streaming
  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [streamedText]);

  const handleGenerate = async () => {
    if (!caseId) {
      toast.error('Please enter a Case ID');
      return;
    }

    setIsGenerating(true);
    setIsStreaming(true);
    setStreamedText('');
    setPdfUrl(null);
    toast.info('Establishing secure LLM uplink...');

    try {
      // 1. Start SSE stream for live narrative
      const eventSource = new EventSource(`http://localhost:8001/api/v1/reports/stream/${caseId}`);
      
      eventSource.onmessage = (event) => {
        if (event.data === '[DONE]') {
          eventSource.close();
          setIsStreaming(false);
          generateFinalPdf();
          return;
        }
        
        try {
          const data = JSON.parse(event.data);
          if (data.chunk) {
            setStreamedText((prev) => prev + data.chunk);
          }
        } catch (e) {
          console.error("Error parsing stream chunk", e);
        }
      };

      eventSource.onerror = (error) => {
        console.error("SSE Error", error);
        eventSource.close();
        setIsStreaming(false);
        setIsGenerating(false);
        toast.error('Connection to LLM stream lost.');
      };

    } catch (error) {
      console.error(error);
      toast.error('Failed to initialize stream. Is the backend running?');
      setIsGenerating(false);
      setIsStreaming(false);
    }
  };

  const generateFinalPdf = async () => {
    toast.success('Narrative complete. Generating official PDF...');
    try {
      const response = await fetch(`http://localhost:8001/api/v1/reports/generate/${caseId}`, {
        method: 'POST',
      });

      if (!response.ok) throw new Error('Failed to generate PDF');

      const blob = await response.blob();
      const url = URL.createObjectURL(blob);
      setPdfUrl(url);
      setIsGenerating(false);
    } catch (error) {
      console.error(error);
      toast.error('Failed to generate final PDF.');
      setIsGenerating(false);
    }
  };

  return (
    <div className="flex-1 p-8 overflow-y-auto">
      <div className="max-w-5xl mx-auto space-y-8">
        
        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-display font-bold tracking-tight">AI Case Dossiers</h1>
            <p className="text-text-muted mt-2">Generate official cybercrime narratives using OpenRouter LLM.</p>
          </div>
          <Sparkles className="w-8 h-8 text-primary-500 opacity-50" />
        </div>

        {/* Control Panel */}
        <div className="bg-background-surface border border-border-default rounded-xl p-6 shadow-sm">
          <div className="flex gap-4 items-end">
            <div className="flex-1">
              <label className="block text-sm font-medium text-text-muted mb-2">Target Case ID</label>
              <input
                type="text"
                value={caseId}
                onChange={(e) => setCaseId(e.target.value)}
                className="w-full bg-background-base border border-border-default rounded-lg px-4 py-2 font-mono focus:outline-none focus:border-primary-500"
                placeholder="e.g. CASE-2026-XXXX"
              />
            </div>
            <button
              onClick={handleGenerate}
              disabled={isGenerating}
              className="px-6 py-2 bg-primary-600 hover:bg-primary-500 text-white rounded-lg flex items-center gap-2 transition-colors disabled:opacity-50"
            >
              {isGenerating ? (
                <>
                  <Loader2 className="w-5 h-5 animate-spin" />
                  Synthesizing...
                </>
              ) : (
                <>
                  <FileText className="w-5 h-5" />
                  Generate Dossier
                </>
              )}
            </button>
          </div>
          
          <div className="mt-4 flex items-center gap-2 text-xs text-warning-400 bg-warning-500/10 p-3 rounded border border-warning-500/20">
            <AlertTriangle className="w-4 h-4" />
            <span>AI narratives are for investigative assistance only. Always verify entity connections manually.</span>
          </div>
        </div>

        {/* Live Terminal Stream */}
        {(isStreaming || streamedText) && !pdfUrl && (
          <div className="bg-[#0a0a0a] border border-[#1f2937] rounded-xl flex flex-col h-[500px] shadow-[0_0_30px_rgba(14,165,233,0.1)] overflow-hidden">
            <div className="h-10 bg-[#111827] border-b border-[#1f2937] flex items-center px-4 gap-2 shrink-0">
              <Terminal className="w-4 h-4 text-primary-500" />
              <span className="text-xs font-mono text-primary-500 tracking-widest">
                {isStreaming ? 'STREAMING NARRATIVE...' : 'STREAM COMPLETE'}
              </span>
              {isStreaming && (
                <span className="flex h-2 w-2 ml-auto">
                  <span className="animate-ping absolute inline-flex h-2 w-2 rounded-full bg-primary-400 opacity-75"></span>
                  <span className="relative inline-flex rounded-full h-2 w-2 bg-primary-500"></span>
                </span>
              )}
            </div>
            <div ref={scrollRef} className="flex-1 p-6 overflow-y-auto font-mono text-sm leading-relaxed text-green-400/90 whitespace-pre-wrap">
              {streamedText}
              {isStreaming && <span className="animate-pulse inline-block w-2 h-4 bg-green-400 ml-1 translate-y-1"></span>}
            </div>
          </div>
        )}

        {/* PDF Viewer */}
        {pdfUrl && (
          <div className="bg-background-surface border border-border-default rounded-xl flex flex-col h-[800px] overflow-hidden shadow-lg animate-in fade-in slide-in-from-bottom-4 duration-500">
            <div className="h-14 bg-background-card border-b border-border-default flex items-center justify-between px-6">
              <div className="flex items-center gap-2 text-sm font-medium text-text-primary">
                <FileText className="w-4 h-4 text-primary-400" />
                FraudLens_Dossier_{caseId}.pdf
              </div>
              <a 
                href={pdfUrl} 
                download={`FraudLens_Dossier_${caseId}.pdf`}
                className="flex items-center gap-2 px-3 py-1.5 bg-background-base hover:bg-border-default rounded text-sm transition-colors"
              >
                <Download className="w-4 h-4" />
                Download PDF
              </a>
            </div>
            <iframe 
              src={pdfUrl} 
              className="flex-1 w-full bg-white"
              title="PDF Viewer"
            />
          </div>
        )}

      </div>
    </div>
  );
}
