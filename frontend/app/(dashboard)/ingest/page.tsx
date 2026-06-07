'use client';

import { useState, useCallback, useRef, useEffect } from 'react';
import {
  Upload, FileText, FileSpreadsheet, File, CheckCircle2, XCircle,
  AlertTriangle, Loader2, ArrowRight, History, ChevronDown, Eye, Trash2,
  Edit2, GitCommitHorizontal
} from 'lucide-react';

// ──── Types ──────────────────────────────────────────────────────

interface ParsedTransaction {
  transaction_ref: string;
  timestamp: string;
  amount: number;
  currency: string;
  direction: string;
  from_account: string;
  to_account: string;
  transaction_type: string | null;
  upi_id: string | null;
  narration: string | null;
  source_file: string;
  confidence: number;
}

interface UploadedFile {
  id: string;
  name: string;
  size: number;
  type: string;
  status: 'queued' | 'uploading' | 'parsing' | 'parsed' | 'error';
  progress: number;
  transactions: number;
  error?: string;
}

interface IngestionSession {
  session_id: string;
  status: string;
  files_count: number;
  transactions_extracted: number;
  new_accounts_discovered: number;
  created_at: string;
}

// ──── Mock Data ──────────────────────────────────────────────────

const MOCK_SESSIONS: IngestionSession[] = [
  {
    session_id: 'mock-001', status: 'complete', files_count: 3,
    transactions_extracted: 847, new_accounts_discovered: 42,
    created_at: '2026-06-06T14:30:00Z'
  },
  {
    session_id: 'mock-002', status: 'complete', files_count: 1,
    transactions_extracted: 234, new_accounts_discovered: 18,
    created_at: '2026-06-05T09:15:00Z'
  },
  {
    session_id: 'mock-003', status: 'partial_error', files_count: 5,
    transactions_extracted: 1205, new_accounts_discovered: 67,
    created_at: '2026-06-03T22:00:00Z'
  },
];

const MOCK_PREVIEW: ParsedTransaction[] = [
  { transaction_ref: 'UTR-789456123', timestamp: '2026-06-01T10:30:00Z', amount: 45000, currency: 'INR', direction: 'DEBIT', from_account: 'ACC-1001', to_account: 'ACC-1002', transaction_type: 'UPI', upi_id: 'suspect1@upi', narration: 'UPI/789456123/Payment', source_file: 'HDFC_Statement.pdf', confidence: 0.92 },
  { transaction_ref: 'UTR-789456124', timestamp: '2026-06-01T11:15:00Z', amount: 48500, currency: 'INR', direction: 'DEBIT', from_account: 'ACC-1001', to_account: 'ACC-1004', transaction_type: 'IMPS', upi_id: null, narration: 'IMPS/Transfer to savings', source_file: 'HDFC_Statement.pdf', confidence: 0.88 },
  { transaction_ref: 'TXN-DOCX-001', timestamp: '2026-06-02T08:45:00Z', amount: 125000, currency: 'INR', direction: 'DEBIT', from_account: 'ACC-1003', to_account: 'ACC-1001', transaction_type: 'RTGS', upi_id: null, narration: 'Complaint letter — victim payment', source_file: 'Complaint_Letter.docx', confidence: 0.55 },
  { transaction_ref: 'PDF-L34-49000', timestamp: '2026-06-03T16:20:00Z', amount: 49000, currency: 'INR', direction: 'DEBIT', from_account: 'ACC-1004', to_account: 'ACC-1005', transaction_type: 'UPI', upi_id: 'mule4@ybl', narration: 'UPI/Sub-threshold transfer', source_file: 'SBI_Extract.pdf', confidence: 0.70 },
  { transaction_ref: 'EXCEL-R5-2400000', timestamp: '2026-06-04T09:00:00Z', amount: 2400000, currency: 'INR', direction: 'CREDIT', from_account: 'ACC-1007', to_account: 'ACC-1001', transaction_type: 'NEFT', upi_id: null, narration: 'NEFT/Bulk collection', source_file: 'Transaction_Dump.xlsx', confidence: 1.0 },
];

// ──── Helpers ──────────────────────────────────────────────────

const FILE_ICONS: Record<string, typeof FileText> = {
  pdf: FileText,
  xlsx: FileSpreadsheet,
  xls: FileSpreadsheet,
  csv: FileSpreadsheet,
  docx: File,
};

const FILE_COLORS: Record<string, string> = {
  pdf: 'text-red-400',
  xlsx: 'text-emerald-400',
  xls: 'text-emerald-400',
  csv: 'text-sky-400',
  docx: 'text-blue-400',
};

function getFileExt(name: string): string {
  return name.split('.').pop()?.toLowerCase() || 'unknown';
}

function formatBytes(bytes: number): string {
  if (bytes < 1024) return bytes + ' B';
  if (bytes < 1048576) return (bytes / 1024).toFixed(1) + ' KB';
  return (bytes / 1048576).toFixed(1) + ' MB';
}

function formatAmount(amount: number): string {
  return '₹' + amount.toLocaleString('en-IN');
}

function formatDate(date: string): string {
  return new Date(date).toLocaleString('en-IN', {
    day: '2-digit', month: 'short', year: 'numeric',
    hour: '2-digit', minute: '2-digit', hour12: false
  });
}

function getConfidenceColor(c: number): string {
  if (c >= 0.9) return 'text-emerald-400 bg-emerald-500/10';
  if (c >= 0.7) return 'text-amber-400 bg-amber-400/10';
  return 'text-red-400 bg-red-500/10';
}

// ──── Main Component ──────────────────────────────────────────

export default function IngestPage() {
  const [files, setFiles] = useState<UploadedFile[]>([]);
  const [isDragging, setIsDragging] = useState(false);
  const [preview, setPreview] = useState<ParsedTransaction[]>([]);
  const [showPreview, setShowPreview] = useState(false);
  const [parseLog, setParseLog] = useState<string[]>([]);
  const [isUploading, setIsUploading] = useState(false);
  const [isCommitting, setIsCommitting] = useState(false);
  const [sessions, setSessions] = useState<IngestionSession[]>(MOCK_SESSIONS);
  const [stats, setStats] = useState({ filesProcessed: 0, txnsExtracted: 0, accountsFound: 0 });

  const fileInputRef = useRef<HTMLInputElement>(null);
  const logRef = useRef<HTMLDivElement>(null);

  // Auto-scroll log
  useEffect(() => {
    if (logRef.current) {
      logRef.current.scrollTop = logRef.current.scrollHeight;
    }
  }, [parseLog]);

  const addLog = useCallback((msg: string) => {
    const ts = new Date().toLocaleTimeString('en-IN', { hour12: false, hour: '2-digit', minute: '2-digit', second: '2-digit' });
    setParseLog(prev => [...prev, `[${ts}] ${msg}`]);
  }, []);

  // ──── Drag & Drop ──────────────────────────────────────────

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  }, []);

  const handleDragLeave = useCallback(() => setIsDragging(false), []);

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    const droppedFiles = Array.from(e.dataTransfer.files);
    addFilesToQueue(droppedFiles);
  }, []);

  const handleFileSelect = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files) {
      addFilesToQueue(Array.from(e.target.files));
    }
  }, []);

  const addFilesToQueue = useCallback((newFiles: globalThis.File[]) => {
    const queuedFiles: UploadedFile[] = newFiles.map(f => ({
      id: Math.random().toString(36).substr(2, 9),
      name: f.name,
      size: f.size,
      type: getFileExt(f.name),
      status: 'queued' as const,
      progress: 0,
      transactions: 0,
    }));
    setFiles(prev => [...prev, ...queuedFiles]);
    addLog(`📁 ${newFiles.length} file(s) added to queue`);
  }, [addLog]);

  // ──── Simulated Upload & Parse ──────────────────────────────

  const handleUpload = useCallback(async () => {
    if (files.length === 0) return;
    setIsUploading(true);
    setParseLog([]);

    addLog('🚀 Starting multi-file ingestion...');

    let totalTxns = 0;
    const accounts = new Set<string>();

    for (let i = 0; i < files.length; i++) {
      const file = files[i];

      // Uploading
      setFiles(prev => prev.map(f => f.id === file.id ? { ...f, status: 'uploading', progress: 30 } : f));
      addLog(`⬆️  Uploading ${file.name} (${formatBytes(file.size)})...`);
      await new Promise(r => setTimeout(r, 400));

      // Parsing
      setFiles(prev => prev.map(f => f.id === file.id ? { ...f, status: 'parsing', progress: 60 } : f));
      addLog(`🔍 Parsing ${file.name} — detecting format: ${file.type.toUpperCase()}`);
      await new Promise(r => setTimeout(r, 600));

      // Simulate results
      const txnCount = Math.floor(Math.random() * 200) + 50;
      totalTxns += txnCount;
      const accs = Math.floor(Math.random() * 15) + 5;
      for (let a = 0; a < accs; a++) accounts.add(`ACC-${1000 + Math.floor(Math.random() * 100)}`);

      setFiles(prev => prev.map(f => f.id === file.id ? {
        ...f, status: 'parsed', progress: 100, transactions: txnCount
      } : f));
      addLog(`✅ ${file.name} — extracted ${txnCount} transactions, ${accs} accounts`);
    }

    setStats({ filesProcessed: files.length, txnsExtracted: totalTxns, accountsFound: accounts.size });
    addLog(`\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━`);
    addLog(`📊 TOTAL: ${totalTxns} transactions from ${files.length} files`);
    addLog(`🏦 ${accounts.size} unique accounts discovered`);
    addLog(`⏳ Awaiting your review before graph commit...`);

    setPreview(MOCK_PREVIEW);
    setShowPreview(true);
    setIsUploading(false);
  }, [files, addLog]);

  const handleCommit = useCallback(async () => {
    setIsCommitting(true);
    addLog(`\n🔗 Committing to PostgreSQL + Neo4j graph...`);
    await new Promise(r => setTimeout(r, 1500));
    addLog(`✅ Graph updated: ${stats.accountsFound} nodes, ${stats.txnsExtracted} edges`);
    addLog(`🎯 Risk scoring triggered for ${stats.accountsFound} accounts`);
    setIsCommitting(false);

    // Add to history
    setSessions(prev => [{
      session_id: `session-${Date.now()}`,
      status: 'complete',
      files_count: stats.filesProcessed,
      transactions_extracted: stats.txnsExtracted,
      new_accounts_discovered: stats.accountsFound,
      created_at: new Date().toISOString(),
    }, ...prev]);

    // Reset
    setFiles([]);
    setShowPreview(false);
    setPreview([]);
    setStats({ filesProcessed: 0, txnsExtracted: 0, accountsFound: 0 });
  }, [addLog, stats]);

  const removeFile = useCallback((id: string) => {
    setFiles(prev => prev.filter(f => f.id !== id));
  }, []);

  return (
    <div className="min-h-screen p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-display text-white tracking-wider">
            DATA INGESTION
          </h1>
          <p className="text-sm text-white/40 mt-1 font-mono">
            Drop files · Extract transactions · Build the graph
          </p>
        </div>
        <div className="flex gap-3">
          {stats.filesProcessed > 0 && (
            <div className="flex gap-2">
              {[
                { label: 'Files', value: stats.filesProcessed, color: 'text-sky-400' },
                { label: 'Txns', value: stats.txnsExtracted, color: 'text-emerald-400' },
                { label: 'Accounts', value: stats.accountsFound, color: 'text-amber-400' },
              ].map(s => (
                <div key={s.label} className="px-3 py-2 rounded-lg bg-white/5 border border-white/5">
                  <p className={`text-lg font-mono font-bold ${s.color}`}>{s.value.toLocaleString()}</p>
                  <p className="text-[10px] text-white/30 uppercase tracking-widest">{s.label}</p>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Main Grid */}
      <div className="grid grid-cols-12 gap-6">
        {/* Left: Drop Zone + File Queue */}
        <div className="col-span-5 space-y-4">
          {/* Drop Zone */}
          <div
            onDragOver={handleDragOver}
            onDragLeave={handleDragLeave}
            onDrop={handleDrop}
            onClick={() => fileInputRef.current?.click()}
            className={`
              relative cursor-pointer rounded-2xl border-2 border-dashed p-8 text-center transition-all duration-300
              ${isDragging
                ? 'border-sky-400/60 bg-sky-400/5 shadow-[inset_0_0_30px_rgba(56,189,248,0.1)]'
                : 'border-white/10 bg-white/[0.02] hover:border-white/20 hover:bg-white/[0.04]'
              }
            `}
          >
            <input
              ref={fileInputRef}
              type="file"
              multiple
              accept=".pdf,.xlsx,.xls,.csv,.docx"
              onChange={handleFileSelect}
              className="hidden"
            />
            <Upload className={`w-10 h-10 mx-auto mb-3 transition-colors ${isDragging ? 'text-sky-400' : 'text-white/20'}`} />
            <p className="text-white/60 font-medium">
              {isDragging ? 'Release to upload' : 'Drop files here or click to browse'}
            </p>
            <p className="text-xs text-white/30 mt-2 font-mono">
              PDF · Excel · CSV · Word — up to 50MB each
            </p>
          </div>

          {/* File Queue */}
          {files.length > 0 && (
            <div className="space-y-2">
              <div className="flex items-center justify-between px-1">
                <h3 className="text-xs font-mono text-white/40 uppercase tracking-wider">
                  File Queue ({files.length})
                </h3>
                {!isUploading && (
                  <button
                    onClick={() => { setFiles([]); setPreview([]); setShowPreview(false); }}
                    className="text-xs text-red-400/60 hover:text-red-400 transition-colors"
                  >
                    Clear All
                  </button>
                )}
              </div>

              <div className="space-y-1.5 max-h-[300px] overflow-y-auto pr-1 scrollbar-thin">
                {files.map(file => {
                  const ext = getFileExt(file.name);
                  const Icon = FILE_ICONS[ext] || File;
                  const color = FILE_COLORS[ext] || 'text-white/40';

                  return (
                    <div
                      key={file.id}
                      className="flex items-center gap-3 px-3 py-2.5 rounded-xl bg-white/[0.03] border border-white/5 group"
                    >
                      <Icon className={`w-4 h-4 flex-shrink-0 ${color}`} />
                      <div className="flex-1 min-w-0">
                        <p className="text-sm text-white/80 truncate">{file.name}</p>
                        <div className="flex items-center gap-2 mt-0.5">
                          <span className="text-[10px] text-white/30 font-mono">{formatBytes(file.size)}</span>
                          {file.status === 'parsed' && (
                            <span className="text-[10px] text-emerald-400 font-mono">
                              {file.transactions} txns
                            </span>
                          )}
                        </div>
                        {/* Progress Bar */}
                        {(file.status === 'uploading' || file.status === 'parsing') && (
                          <div className="w-full h-1 bg-white/5 rounded-full mt-1.5 overflow-hidden">
                            <div
                              className="h-full bg-gradient-to-r from-sky-500 to-sky-400 rounded-full transition-all duration-500"
                              style={{ width: `${file.progress}%` }}
                            />
                          </div>
                        )}
                      </div>
                      <div className="flex-shrink-0">
                        {file.status === 'queued' && (
                          <button onClick={() => removeFile(file.id)} className="text-white/20 hover:text-red-400 transition-colors opacity-0 group-hover:opacity-100">
                            <XCircle className="w-4 h-4" />
                          </button>
                        )}
                        {(file.status === 'uploading' || file.status === 'parsing') && (
                          <Loader2 className="w-4 h-4 text-sky-400 animate-spin" />
                        )}
                        {file.status === 'parsed' && (
                          <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                        )}
                        {file.status === 'error' && (
                          <XCircle className="w-4 h-4 text-red-400" />
                        )}
                      </div>
                    </div>
                  );
                })}
              </div>

              {/* Upload Button */}
              {!isUploading && files.some(f => f.status === 'queued') && (
                <button
                  onClick={handleUpload}
                  className="w-full py-3 rounded-xl bg-sky-500/20 border border-sky-500/30 text-sky-400 font-mono text-sm hover:bg-sky-500/30 transition-all flex items-center justify-center gap-2 shadow-[0_0_15px_rgba(56,189,248,0.15)]"
                >
                  <Upload className="w-4 h-4" />
                  Upload & Parse {files.filter(f => f.status === 'queued').length} file(s)
                </button>
              )}
            </div>
          )}
        </div>

        {/* Middle: Parse Log */}
        <div className="col-span-4">
          <div className="rounded-2xl bg-[#0a0e14] border border-white/5 overflow-hidden h-full flex flex-col">
            <div className="px-4 py-3 border-b border-white/5 flex items-center gap-2">
              <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
              <span className="text-xs font-mono text-white/40 uppercase tracking-wider">Parse Log</span>
            </div>
            <div ref={logRef} className="flex-1 p-4 overflow-y-auto max-h-[400px] scrollbar-thin">
              {parseLog.length === 0 ? (
                <p className="text-white/20 text-xs font-mono text-center mt-8">
                  Upload files to see parse output...
                </p>
              ) : (
                <div className="space-y-1">
                  {parseLog.map((line, i) => (
                    <p key={i} className="text-[11px] font-mono leading-relaxed text-white/60">{line}</p>
                  ))}
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Right: Preview or Stats */}
        <div className="col-span-3">
          <div className="rounded-2xl bg-white/[0.02] border border-white/5 p-4 space-y-4">
            <h3 className="text-xs font-mono text-white/40 uppercase tracking-wider">Session Stats</h3>
            {[
              { label: 'Status', value: isUploading ? 'PARSING' : isCommitting ? 'COMMITTING' : showPreview ? 'READY' : 'IDLE', color: isUploading ? 'text-amber-400' : showPreview ? 'text-emerald-400' : 'text-white/30' },
              { label: 'Files', value: files.length.toString(), color: 'text-white/60' },
              { label: 'Transactions', value: stats.txnsExtracted.toLocaleString(), color: 'text-sky-400' },
              { label: 'Accounts', value: stats.accountsFound.toLocaleString(), color: 'text-amber-400' },
            ].map(s => (
              <div key={s.label} className="flex items-center justify-between">
                <span className="text-xs text-white/30 font-mono">{s.label}</span>
                <span className={`text-sm font-mono font-bold ${s.color}`}>{s.value}</span>
              </div>
            ))}

            {showPreview && (
              <button
                onClick={handleCommit}
                disabled={isCommitting}
                className="w-full py-3 rounded-xl bg-emerald-500/20 border border-emerald-500/30 text-emerald-400 font-mono text-sm hover:bg-emerald-500/30 transition-all flex items-center justify-center gap-2 shadow-[0_0_15px_rgba(16,185,129,0.2)] disabled:opacity-50"
              >
                {isCommitting ? (
                  <><Loader2 className="w-4 h-4 animate-spin" /> Committing...</>
                ) : (
                  <><GitCommitHorizontal className="w-4 h-4" /> Commit to Graph</>
                )}
              </button>
            )}
          </div>
        </div>
      </div>

      {/* Preview Table */}
      {showPreview && preview.length > 0 && (
        <div className="rounded-2xl bg-white/[0.02] border border-white/5 overflow-hidden">
          <div className="px-5 py-4 border-b border-white/5 flex items-center justify-between">
            <div className="flex items-center gap-3">
              <Eye className="w-4 h-4 text-sky-400" />
              <h3 className="text-sm font-mono text-white/60">
                Preview — {preview.length} transactions extracted
              </h3>
            </div>
            <span className="text-xs px-2 py-1 rounded bg-amber-400/10 text-amber-400 font-mono">
              {preview.filter(t => t.confidence < 0.8).length} low confidence
            </span>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b border-white/5">
                  {['Date', 'From', 'To', 'Amount', 'Mode', 'Source', 'Confidence'].map(h => (
                    <th key={h} className="px-4 py-3 text-left text-[10px] font-mono text-white/30 uppercase tracking-wider">
                      {h}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {preview.map((txn, i) => (
                  <tr
                    key={i}
                    className={`border-b border-white/[0.03] hover:bg-white/[0.02] transition-colors ${
                      txn.confidence < 0.7 ? 'bg-red-500/[0.03]' : ''
                    }`}
                  >
                    <td className="px-4 py-3 text-xs font-mono text-white/60">
                      {formatDate(txn.timestamp)}
                    </td>
                    <td className="px-4 py-3 text-xs font-mono text-white/70">{txn.from_account}</td>
                    <td className="px-4 py-3 text-xs font-mono text-white/70">{txn.to_account}</td>
                    <td className="px-4 py-3 text-xs font-mono text-white/80 font-bold">
                      {formatAmount(txn.amount)}
                    </td>
                    <td className="px-4 py-3">
                      {txn.transaction_type ? (
                        <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-sky-500/10 text-sky-400">
                          {txn.transaction_type}
                        </span>
                      ) : (
                        <span className="text-[10px] text-white/20">—</span>
                      )}
                    </td>
                    <td className="px-4 py-3 text-[10px] font-mono text-white/30 max-w-[150px] truncate">
                      {txn.source_file}
                    </td>
                    <td className="px-4 py-3">
                      <span className={`text-[10px] font-mono px-2 py-0.5 rounded ${getConfidenceColor(txn.confidence)}`}>
                        {(txn.confidence * 100).toFixed(0)}%
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Ingestion History */}
      <div className="rounded-2xl bg-white/[0.02] border border-white/5 overflow-hidden">
        <div className="px-5 py-4 border-b border-white/5 flex items-center gap-3">
          <History className="w-4 h-4 text-white/30" />
          <h3 className="text-sm font-mono text-white/40">Ingestion History</h3>
        </div>
        <div className="divide-y divide-white/[0.03]">
          {sessions.map(session => (
            <div key={session.session_id} className="px-5 py-3 flex items-center justify-between hover:bg-white/[0.02] transition-colors">
              <div className="flex items-center gap-4">
                <span className={`text-[10px] font-mono px-2 py-0.5 rounded ${
                  session.status === 'complete' ? 'bg-emerald-500/10 text-emerald-400' : 'bg-amber-400/10 text-amber-400'
                }`}>
                  {session.status.toUpperCase()}
                </span>
                <span className="text-xs text-white/30 font-mono">{formatDate(session.created_at)}</span>
              </div>
              <div className="flex items-center gap-6 text-xs font-mono">
                <span className="text-white/40">{session.files_count} files</span>
                <span className="text-sky-400">{session.transactions_extracted.toLocaleString()} txns</span>
                <span className="text-amber-400">{session.new_accounts_discovered} accounts</span>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
