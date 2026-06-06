'use client';

import React, { useEffect, useRef, useState, useMemo } from 'react';
import * as d3 from 'd3';
import { useTransactionStream } from '@/hooks/useTransactionStream';

export interface GraphNode extends d3.SimulationNodeDatum {
  id: string;
  accountNumber: string;
  type: 'suspect' | 'victim' | 'relay' | 'clean' | 'unknown';
  riskScore: number;
  totalVolume: number;
  transactionCount: number;
  isCentralNode: boolean;
  centrality: {
    pageRank: number;
    betweenness: number;
    degree: number;
  };
  metadata: {
    bankName: string;
    accountType: string;
    registeredName?: string;
  };
}

export interface GraphEdge extends d3.SimulationLinkDatum<GraphNode> {
  id: string;
  source: string | GraphNode;
  target: string | GraphNode;
  amount: number;
  timestamp: string;
  transactionType: string;
  upiId?: string;
  riskFlag: 'high' | 'medium' | 'low' | 'unknown';
}

interface TransactionGraphProps {
  nodes: GraphNode[];
  edges: GraphEdge[];
  onNodeClick: (node: GraphNode) => void;
  onEdgeClick: (edge: GraphEdge) => void;
}

const colorMap = {
  suspect: 'var(--node-suspect)',
  victim: 'var(--node-victim)',
  relay: 'var(--node-relay)',
  clean: 'var(--node-clean)',
  unknown: 'var(--node-unknown)'
};

const edgeColorMap = {
  high: 'var(--edge-high-value)',
  medium: 'var(--edge-medium)',
  low: 'var(--edge-low)',
  unknown: 'var(--edge-low)'
};

export default function TransactionGraph({ nodes: initialNodes, edges: initialEdges, onNodeClick, onEdgeClick }: TransactionGraphProps) {
  const svgRef = useRef<SVGSVGElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const [tooltip, setTooltip] = useState<{ visible: boolean; x: number; y: number; content: string }>({ visible: false, x: 0, y: 0, content: '' });

  // Consume Live WebSocket Stream
  const { streamedNodes, streamedEdges } = useTransactionStream('ws://localhost:8000/api/v1/ws/stream');

  // Merge static query data with live streamed data
  const mergedNodes = useMemo(() => {
    const all = [...initialNodes, ...streamedNodes];
    // Deduplicate by ID
    const unique = new Map(all.map(n => [n.id, n]));
    return Array.from(unique.values());
  }, [initialNodes, streamedNodes]);

  const mergedEdges = useMemo(() => {
    return [...initialEdges, ...streamedEdges];
  }, [initialEdges, streamedEdges]);

  useEffect(() => {
    if (!svgRef.current || !containerRef.current || mergedNodes.length === 0) return;

    const width = containerRef.current.clientWidth;
    const height = containerRef.current.clientHeight;

    const svg = d3.select(svgRef.current);
    svg.selectAll("*").remove(); // Clear previous render

    // Define Arrow Markers
    const defs = svg.append("defs");
    Object.keys(edgeColorMap).forEach(key => {
      defs.append("marker")
        .attr("id", `arrow-${key}`)
        .attr("viewBox", "0 -5 10 10")
        .attr("refX", 25) // Offset to account for node radius
        .attr("refY", 0)
        .attr("markerWidth", 6)
        .attr("markerHeight", 6)
        .attr("orient", "auto")
        .append("path")
        .attr("d", "M0,-5L10,0L0,5")
        .attr("fill", edgeColorMap[key as keyof typeof edgeColorMap]);
    });

    // Setup zoom
    const g = svg.append("g");
    
    // Create zoom behavior
    const zoomBehavior = d3.zoom<SVGSVGElement, unknown>()
      .scaleExtent([0.1, 4])
      .on("zoom", (e: d3.D3ZoomEvent<SVGSVGElement, unknown>) => {
        g.attr("transform", e.transform.toString());
      });
      
    svg.call(zoomBehavior);

    // Clone merged nodes and edges to avoid mutating props
    const simulationNodes: GraphNode[] = mergedNodes.map(d => ({ ...d }));
    const simulationEdges: GraphEdge[] = mergedEdges.map(d => ({ ...d }));

    const nodeRadius = (d: GraphNode) => 15 + ((d.riskScore || 0) * 10);

    // Setup Simulation
    const simulation = d3.forceSimulation<GraphNode>(simulationNodes)
      .force("link", d3.forceLink<GraphNode, GraphEdge>(simulationEdges).id((d) => d.id).distance((d) => 120 + (d.riskFlag === 'high' ? 0 : 40)).strength(0.5))
      .force("charge", d3.forceManyBody().strength(-400).distanceMax(500))
      .force("center", d3.forceCenter(width / 2, height / 2))
      .force("collision", d3.forceCollide<GraphNode>().radius((d) => nodeRadius(d) + 20))
      .force("x", d3.forceX(width / 2).strength(0.05))
      .force("y", d3.forceY(height / 2).strength(0.05));

    // Draw Edges as curved paths
    const link = g.append("g")
      .attr("class", "links")
      .selectAll("path")
      .data(simulationEdges)
      .enter().append("path")
      .attr("fill", "none")
      .attr("stroke-width", (d) => Math.max(1.5, Math.log10(d.amount || 10)))
      .attr("stroke", (d) => edgeColorMap[d.riskFlag as keyof typeof edgeColorMap] || edgeColorMap.unknown)
      .attr("stroke-opacity", 0.6)
      .attr("marker-end", (d) => `url(#arrow-${d.riskFlag})`)
      .style("cursor", "pointer")
      .on("click", (e: MouseEvent, d) => onEdgeClick(d))
      .on("mouseover", (e: MouseEvent, d) => {
        d3.select(e.currentTarget as SVGPathElement).attr("stroke-opacity", 1).attr("stroke-width", Math.max(3, Math.log10(d.amount || 10)) * 1.5);
        setTooltip({ visible: true, x: e.pageX, y: e.pageY, content: `₹${d.amount.toLocaleString()} via ${d.transactionType}` });
      })
      .on("mousemove", (e: MouseEvent) => setTooltip(prev => ({ ...prev, x: e.pageX, y: e.pageY })))
      .on("mouseout", (e: MouseEvent, d) => {
        d3.select(e.currentTarget as SVGPathElement).attr("stroke-opacity", 0.6).attr("stroke-width", Math.max(1.5, Math.log10(d.amount || 10)));
        setTooltip(prev => ({ ...prev, visible: false }));
      });

    // Draw Nodes
    const node = g.append("g")
      .attr("class", "nodes")
      .selectAll("g")
      .data(simulationNodes)
      .enter().append("g")
      .style("cursor", "pointer")
      .on("click", (e: MouseEvent, d) => onNodeClick(d))
      .on("mouseover", (e: MouseEvent, d) => {
        setTooltip({ visible: true, x: e.pageX, y: e.pageY, content: `${d.accountNumber} (${d.type})` });
        // Highlight connected links
        link.attr("stroke-opacity", (l) => {
            const sourceNode = l.source as GraphNode;
            const targetNode = l.target as GraphNode;
            return (sourceNode.id === d.id || targetNode.id === d.id) ? 1 : 0.1;
        });
        node.attr("opacity", (n) => {
          const isConnected = simulationEdges.some((l) => {
            const s = l.source as GraphNode;
            const t = l.target as GraphNode;
            return (s.id === d.id && t.id === n.id) || (t.id === d.id && s.id === n.id);
          });
          return isConnected || n.id === d.id ? 1 : 0.3;
        });
      })
      .on("mousemove", (e: MouseEvent) => setTooltip(prev => ({ ...prev, x: e.pageX, y: e.pageY })))
      .on("mouseout", () => {
        setTooltip(prev => ({ ...prev, visible: false }));
        link.attr("stroke-opacity", 0.6);
        node.attr("opacity", 1);
      });

    const dragBehavior = d3.drag<SVGGElement, GraphNode>()
        .on("start", dragstarted)
        .on("drag", dragged)
        .on("end", dragended);

    node.call(dragBehavior);

    node.append("circle")
      .attr("r", (d) => nodeRadius(d))
      .attr("fill", (d) => colorMap[d.type as keyof typeof colorMap] || colorMap.unknown)
      .attr("stroke", (d) => d.isCentralNode ? "white" : "none")
      .attr("stroke-width", (d) => d.isCentralNode ? 3 : 0)
      .attr("filter", "drop-shadow(0px 4px 4px rgba(0,0,0,0.25))");

    node.append("text")
      .text((d) => d.accountNumber)
      .attr('x', (d) => nodeRadius(d) + 5)
      .attr('y', 4)
      .attr("fill", "var(--text-primary)")
      .style("font-family", "JetBrains Mono")
      .style("font-size", "11px")
      .style("font-weight", "600")
      .style("text-shadow", "0 1px 3px rgba(0,0,0,0.8)")
      .style("pointer-events", "none");

    // Simulation tick updates
    simulation.on("tick", () => {
      link.attr("d", (d) => {
        const sourceNode = d.source as GraphNode;
        const targetNode = d.target as GraphNode;
        if (!sourceNode || !targetNode) return null;
        const dx = (targetNode.x ?? 0) - (sourceNode.x ?? 0);
        const dy = (targetNode.y ?? 0) - (sourceNode.y ?? 0);
        const dr = Math.sqrt(dx * dx + dy * dy); // Curve radius
        return `M${sourceNode.x ?? 0},${sourceNode.y ?? 0}A${dr},${dr} 0 0,1 ${targetNode.x ?? 0},${targetNode.y ?? 0}`;
      });

      node.attr("transform", (d) => `translate(${d.x ?? 0},${d.y ?? 0})`);
    });

    // Drag handlers
    function dragstarted(event: d3.D3DragEvent<SVGGElement, GraphNode, GraphNode>, d: GraphNode) {
      if (!event.active) simulation.alphaTarget(0.3).restart();
      d.fx = d.x;
      d.fy = d.y;
    }

    function dragged(event: d3.D3DragEvent<SVGGElement, GraphNode, GraphNode>, d: GraphNode) {
      d.fx = event.x;
      d.fy = event.y;
    }

    function dragended(event: d3.D3DragEvent<SVGGElement, GraphNode, GraphNode>, d: GraphNode) {
      if (!event.active) simulation.alphaTarget(0);
      d.fx = null;
      d.fy = null;
    }

    return () => {
      simulation.stop();
    };
  }, [mergedNodes, mergedEdges, onNodeClick, onEdgeClick]);

  return (
    <>
      <div ref={containerRef} className="w-full h-full bg-background-surface rounded-xl overflow-hidden border border-border-default shadow-lg">
        <svg ref={svgRef} className="w-full h-full" />
      </div>
      
      {/* Tooltip */}
      {tooltip.visible && (
        <div 
          className="fixed z-50 pointer-events-none bg-background-card/90 backdrop-blur border border-border-default px-3 py-2 rounded text-sm font-mono text-text-primary shadow-xl"
          style={{ top: tooltip.y + 15, left: tooltip.x + 15 }}
        >
          {tooltip.content}
        </div>
      )}
    </>
  );
}
