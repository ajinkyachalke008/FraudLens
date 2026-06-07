'use client';

import React, { useState } from 'react';
import { ShieldAlert, FileText, Send, User, CircleDot } from 'lucide-react';
import { toast } from 'sonner';

interface TimelineEvent {
  id: string;
  type: 'note' | 'audit';
  content?: string;
  action?: string;
  metadata?: any;
  author: string;
  timestamp: string;
  note_type?: string;
}

interface Props {
  caseId: string;
  initialEvents: TimelineEvent[];
}

export default function CaseTimeline({ caseId, initialEvents }: Props) {
  const [events, setEvents] = useState<TimelineEvent[]>(initialEvents);
  const [newNote, setNewNote] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newNote.trim()) return;

    setIsSubmitting(true);
    try {
      const response = await fetch(`http://localhost:8001/api/v1/cases/${caseId}/notes`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ content: newNote, note_type: 'general' })
      });

      if (response.ok) {
        toast.success('Note added to timeline');
        setNewNote('');
        // Optimistic update
        setEvents(prev => [...prev, {
          id: Math.random().toString(),
          type: 'note' as const,
          content: newNote,
          note_type: 'general',
          author: 'Current Investigator', // Mock
          timestamp: new Date().toISOString()
        }].sort((a, b) => new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime()));
      }
    } catch (error) {
      toast.error('Failed to append note');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="flex flex-col h-full bg-background-surface border border-border-default rounded-xl shadow-lg">
      <div className="p-4 border-b border-border-default flex items-center justify-between bg-[#111827] rounded-t-xl">
        <h3 className="font-mono text-sm font-bold tracking-widest text-primary-400">INVESTIGATION TIMELINE</h3>
      </div>

      <div className="flex-1 overflow-y-auto p-6 space-y-6">
        {events.map((evt, idx) => (
          <div key={evt.id} className="relative pl-6">
            {/* Timeline line */}
            {idx !== events.length - 1 && (
              <div className="absolute left-2.5 top-6 bottom-[-24px] w-px bg-border-default" />
            )}
            
            {/* Dot */}
            <div className="absolute left-1.5 top-1.5 w-2.5 h-2.5 rounded-full bg-border-default ring-4 ring-background-surface" />

            <div className="flex gap-4 items-start">
              <div className="flex-1 space-y-2">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-mono font-medium text-text-muted flex items-center gap-1.5">
                    {evt.type === 'audit' ? <ShieldAlert className="w-3.5 h-3.5 text-warning-400" /> : <FileText className="w-3.5 h-3.5 text-primary-400" />}
                    {evt.author}
                  </span>
                  <span className="text-[10px] font-mono text-text-muted">
                    {new Date(evt.timestamp).toLocaleString()}
                  </span>
                </div>
                
                <div className={`p-3 rounded-lg text-sm border ${
                  evt.type === 'audit' 
                    ? 'bg-warning-500/5 border-warning-500/20 text-warning-200' 
                    : 'bg-background-card border-border-default text-text-primary'
                }`}>
                  {evt.type === 'audit' ? (
                    <div className="font-mono">
                      SYSTEM LOG: <span className="text-warning-400">{evt.action}</span>
                      {evt.metadata && evt.metadata.new_status && (
                        <span className="ml-2">→ {evt.metadata.old_status} to {evt.metadata.new_status}</span>
                      )}
                    </div>
                  ) : (
                    <p className="leading-relaxed">{evt.content}</p>
                  )}
                </div>
              </div>
            </div>
          </div>
        ))}

        {events.length === 0 && (
          <div className="text-center text-text-muted font-mono text-sm py-8">No events in timeline yet.</div>
        )}
      </div>

      <div className="p-4 border-t border-border-default bg-[#111827] rounded-b-xl">
        <form onSubmit={handleSubmit} className="flex gap-3">
          <input
            type="text"
            value={newNote}
            onChange={(e) => setNewNote(e.target.value)}
            placeholder="Append case note or evidence link..."
            className="flex-1 bg-background-base border border-border-default rounded-lg px-4 py-2 text-sm focus:outline-none focus:border-primary-500 transition-colors"
          />
          <button 
            type="submit" 
            disabled={isSubmitting || !newNote.trim()}
            className="bg-primary-600 hover:bg-primary-500 disabled:opacity-50 text-white rounded-lg px-4 py-2 flex items-center justify-center transition-colors"
          >
            <Send className="w-4 h-4" />
          </button>
        </form>
      </div>
    </div>
  );
}
