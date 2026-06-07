'use client';

import React, { useState, useEffect, useRef } from 'react';
import { Search, MapPin, Building, Loader2 } from 'lucide-react';

interface BankResult {
  ifsc: string;
  bank: string;
  branch: string;
  city: string;
  state: string;
}

interface Props {
  onSelect: (ifsc: string) => void;
  className?: string;
}

export default function IFSCAutocomplete({ onSelect, className = '' }: Props) {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState<BankResult[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [isOpen, setIsOpen] = useState(false);
  const wrapperRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (wrapperRef.current && !wrapperRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  useEffect(() => {
    if (query.length < 2) {
      setResults([]);
      return;
    }

    const fetchResults = async () => {
      setIsLoading(true);
      try {
        const response = await fetch(`http://localhost:8001/api/v1/enrichment/ifsc/search?query=${encodeURIComponent(query)}`);
        if (response.ok) {
          const data = await response.json();
          setResults(data);
          setIsOpen(true);
        }
      } catch (error) {
        console.error('Failed to fetch IFSC data:', error);
      } finally {
        setIsLoading(false);
      }
    };

    const timer = setTimeout(fetchResults, 300);
    return () => clearTimeout(timer);
  }, [query]);

  const handleSelect = (result: BankResult) => {
    setQuery(result.ifsc);
    setIsOpen(false);
    onSelect(result.ifsc);
  };

  return (
    <div ref={wrapperRef} className={`relative ${className}`}>
      <div className="relative">
        <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
          {isLoading ? (
            <Loader2 className="h-4 w-4 text-primary-400 animate-spin" />
          ) : (
            <Search className="h-4 w-4 text-text-muted" />
          )}
        </div>
        <input
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onFocus={() => { if (results.length > 0) setIsOpen(true); }}
          placeholder="Search Bank, Branch or IFSC..."
          className="w-full bg-background-base border border-border-default rounded-lg pl-10 pr-4 py-2 font-mono text-sm focus:outline-none focus:border-primary-500 transition-colors"
        />
      </div>

      {isOpen && results.length > 0 && (
        <div className="absolute z-50 w-full mt-1 bg-background-surface border border-border-default rounded-lg shadow-xl overflow-hidden max-h-60 overflow-y-auto">
          {results.map((result) => (
            <button
              key={result.ifsc}
              onClick={() => handleSelect(result)}
              className="w-full text-left px-4 py-3 hover:bg-white/5 border-b border-border-default last:border-b-0 transition-colors flex items-start gap-3"
            >
              <div className="mt-0.5">
                <Building className="w-4 h-4 text-primary-500" />
              </div>
              <div>
                <div className="flex items-baseline justify-between gap-4">
                  <span className="font-bold text-sm text-text-primary">{result.bank}</span>
                  <span className="font-mono text-xs text-primary-400">{result.ifsc}</span>
                </div>
                <div className="flex items-center gap-1 text-xs text-text-muted mt-1">
                  <MapPin className="w-3 h-3" />
                  {result.branch}, {result.city}
                </div>
              </div>
            </button>
          ))}
        </div>
      )}
    </div>
  );
}
