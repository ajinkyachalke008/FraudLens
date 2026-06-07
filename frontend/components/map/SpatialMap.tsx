'use client';

import React, { useState, useMemo } from 'react';
import DeckGL from '@deck.gl/react';
import { Map } from 'react-map-gl/maplibre';
import { ArcLayer, ScatterplotLayer } from '@deck.gl/layers';
import { HexagonLayer, HeatmapLayer } from '@deck.gl/aggregation-layers';
import { Layers } from 'lucide-react';

const MAP_STYLE = 'https://basemaps.cartocdn.com/gl/dark-matter-gl-style/style.json';

const INITIAL_VIEW_STATE = {
  longitude: 73.8567,
  latitude: 18.5204,
  zoom: 11,
  pitch: 45,
  bearing: 0
};

interface Props {
  locations?: any[];
  connections?: any[];
}

export default function SpatialMap({ locations = [], connections = [] }: Props) {
  const [viewState, setViewState] = useState(INITIAL_VIEW_STATE);

  
  // Layer Toggles
  const [showArcs, setShowArcs] = useState(true);
  const [showScatter, setShowScatter] = useState(false);
  const [showHexagon, setShowHexagon] = useState(true);
  const [showHeatmap, setShowHeatmap] = useState(false);

  const layers = useMemo(() => {
    const activeLayers = [];

    if (showHeatmap) {
      activeLayers.push(
        new HeatmapLayer({
          id: 'fraud-heatmap',
          data: locations,
          getPosition: (d: any) => d.coordinates,
          getWeight: (d: any) => d.amount,
          radiusPixels: 50,
          intensity: 1,
          threshold: 0.05
        })
      );
    }

    if (showHexagon) {
      activeLayers.push(
        new HexagonLayer({
          id: 'fraud-hexagons',
          data: locations,
          getPosition: (d: any) => d.coordinates,
          getElevationWeight: (d: any) => d.amount,
          elevationScale: 50,
          extruded: true,
          radius: 400,
          opacity: 0.8,
          coverage: 0.9,
          lowerPercentile: 0,
          upperPercentile: 100,
          colorRange: [
            [14, 165, 233],   // Sky 500
            [56, 189, 248],   // Sky 400
            [250, 204, 21],   // Yellow 400
            [234, 179, 8],    // Yellow 500
            [248, 113, 113],  // Red 400
            [239, 68, 68]     // Red 500
          ],
          pickable: true,
          autoHighlight: true,
        })
      );
    }

    if (showArcs) {
      activeLayers.push(
        new ArcLayer({
          id: 'transaction-arcs',
          data: connections,
          getSourcePosition: (d: any) => d.source,
          getTargetPosition: (d: any) => d.target,
          getSourceColor: [234, 179, 8, 200],
          getTargetColor: [239, 68, 68, 200],
          getWidth: (d: any) => Math.max(2, d.amount / 20000),
          pickable: true,
          autoHighlight: true,
        })
      );
    }

    if (showScatter) {
      activeLayers.push(
        new ScatterplotLayer({
          id: 'node-locations',
          data: locations,
          getPosition: (d: any) => d.coordinates,
          getFillColor: (d: any) => d.type === 'suspect' ? [239, 68, 68, 200] : [14, 165, 233, 150],
          getRadius: 100,
          radiusMinPixels: 3,
          radiusMaxPixels: 10,
          pickable: true,
          autoHighlight: true,
        })
      );
    }

    return activeLayers;
  }, [showArcs, showScatter, showHexagon, showHeatmap]);

  return (
    <div className="relative w-full h-full rounded-xl overflow-hidden border border-border-default shadow-lg">
      <DeckGL
        initialViewState={viewState}
        controller={true}
        layers={layers}
        onViewStateChange={(e) => setViewState(e.viewState as any)}
        getTooltip={({object}) => object && (object.amount ? `Volume: ₹${Math.round(object.amount).toLocaleString()}` : object.elevationValue ? `Total Volume: ₹${Math.round(object.elevationValue).toLocaleString()}` : null)}
      >
        <Map
          mapStyle={MAP_STYLE}
          reuseMaps
        />
      </DeckGL>

      {/* Map Control Panel */}
      <div className="absolute top-4 left-4 z-10 w-64">
        <div className="bg-background-surface/90 backdrop-blur border border-border-default rounded-xl p-4 shadow-xl">
          <h3 className="text-primary-400 font-mono font-bold tracking-widest text-sm mb-4 flex items-center gap-2">
            <Layers className="w-4 h-4" />
            LAYER CONTROLS
          </h3>
          
          <div className="space-y-3">
            <label className="flex items-center justify-between cursor-pointer group">
              <span className="text-xs font-mono text-text-primary group-hover:text-primary-400 transition-colors">3D Hexagon Volume</span>
              <input type="checkbox" className="toggle toggle-primary toggle-sm" checked={showHexagon} onChange={(e) => setShowHexagon(e.target.checked)} />
            </label>
            <label className="flex items-center justify-between cursor-pointer group">
              <span className="text-xs font-mono text-text-primary group-hover:text-primary-400 transition-colors">Density Heatmap</span>
              <input type="checkbox" className="toggle toggle-primary toggle-sm" checked={showHeatmap} onChange={(e) => setShowHeatmap(e.target.checked)} />
            </label>
            <div className="h-px bg-border-default my-2"></div>
            <label className="flex items-center justify-between cursor-pointer group">
              <span className="text-xs font-mono text-text-primary group-hover:text-primary-400 transition-colors">Transaction Arcs</span>
              <input type="checkbox" className="toggle toggle-primary toggle-sm" checked={showArcs} onChange={(e) => setShowArcs(e.target.checked)} />
            </label>
            <label className="flex items-center justify-between cursor-pointer group">
              <span className="text-xs font-mono text-text-primary group-hover:text-primary-400 transition-colors">Node Scatterplot</span>
              <input type="checkbox" className="toggle toggle-primary toggle-sm" checked={showScatter} onChange={(e) => setShowScatter(e.target.checked)} />
            </label>
          </div>
        </div>
      </div>
    </div>
  );
}
