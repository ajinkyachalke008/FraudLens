'use client';

import React from 'react';
import { MapPin, Globe } from 'lucide-react';
import dynamic from 'next/dynamic';

// Deck.gl needs to be dynamically imported with SSR disabled
const SpatialMap = dynamic(() => import('@/components/map/SpatialMap'), {
  ssr: false,
  loading: () => (
    <div className="w-full h-full flex items-center justify-center bg-background-base text-primary-500 font-mono animate-pulse">
      Loading Spatial Geometry...
    </div>
  )
});

export default function MapPage() {
  return (
    <div className="flex flex-col h-screen p-4 gap-4 bg-background-base">
      <div className="h-16 bg-background-surface border border-border-default rounded-lg shadow flex items-center justify-between px-6 shrink-0">
        <div>
          <h1 className="font-display text-xl text-primary-400 font-bold tracking-widest flex items-center gap-3">
            <Globe className="w-6 h-6" />
            GEOSPATIAL INTELLIGENCE
            <span className="text-xs px-2 py-0.5 rounded bg-primary-600/20 text-primary-400">
              DECK.GL ENGINE
            </span>
          </h1>
          <p className="text-xs text-text-muted font-mono mt-1">
            Tracking money movement across geographic clusters.
          </p>
        </div>
        <div className="flex gap-4">
          <button className="px-4 py-2 border border-border-default rounded text-sm hover:border-primary-500 transition-colors font-mono">
            Focus: Pune
          </button>
        </div>
      </div>

      <div className="flex-1 relative">
        <SpatialMap />
      </div>
    </div>
  );
}
