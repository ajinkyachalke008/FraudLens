'use client';

import React, { useEffect, useRef, useState } from 'react';
import * as d3 from 'd3';

export interface SyndicateNode extends d3.SimulationNodeDatum {
  id: string;
  label: string;
  type: 'shared_suspect' | 'case_cluster';
  riskScore: number;
}

export interface SyndicateLink extends d3.SimulationLinkDatum<SyndicateNode> {
  source: string | SyndicateNode;
  target: string | SyndicateNode;
  type: string;
}

interface Props {
  nodes: SyndicateNode[];
  links: SyndicateLink[];
}

const colorMap = {
  shared_suspect: 'var(--node-suspect)',
  case_cluster: 'var(--node-victim)'
};

export default function SyndicateGraph({ nodes: initialNodes, links: initialEdges }: Props) {
  const svgRef = useRef<SVGSVGElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const [tooltip, setTooltip] = useState<{ visible: boolean; x: number; y: number; content: string }>({ visible: false, x: 0, y: 0, content: '' });

  useEffect(() => {
    if (!svgRef.current || !containerRef.current || initialNodes.length === 0) return;

    const width = containerRef.current.clientWidth;
    const height = containerRef.current.clientHeight;

    const svg = d3.select(svgRef.current);
    svg.selectAll("*").remove();

    const g = svg.append("g");

    const zoomBehavior = d3.zoom<SVGSVGElement, unknown>()
      .scaleExtent([0.1, 4])
      .on("zoom", (e: d3.D3ZoomEvent<SVGSVGElement, unknown>) => {
        g.attr("transform", e.transform.toString());
      });
      
    svg.call(zoomBehavior);

    const simulationNodes: SyndicateNode[] = initialNodes.map(d => ({ ...d }));
    const simulationEdges: SyndicateLink[] = initialEdges.map(d => ({ ...d }));

    const nodeRadius = (d: SyndicateNode) => d.type === 'case_cluster' ? 25 : 15;

    const simulation = d3.forceSimulation<SyndicateNode>(simulationNodes)
      .force("link", d3.forceLink<SyndicateNode, SyndicateLink>(simulationEdges).id((d) => d.id).distance(150).strength(0.5))
      .force("charge", d3.forceManyBody().strength(-500).distanceMax(800))
      .force("center", d3.forceCenter(width / 2, height / 2))
      .force("collision", d3.forceCollide<SyndicateNode>().radius((d) => nodeRadius(d) + 30))
      .force("x", d3.forceX(width / 2).strength(0.05))
      .force("y", d3.forceY(height / 2).strength(0.05));

    const link = g.append("g")
      .attr("class", "links")
      .selectAll("line")
      .data(simulationEdges)
      .enter().append("line")
      .attr("stroke-width", 2)
      .attr("stroke", "var(--edge-high-value)")
      .attr("stroke-opacity", 0.6)
      .attr("stroke-dasharray", "5,5");

    const node = g.append("g")
      .attr("class", "nodes")
      .selectAll("g")
      .data(simulationNodes)
      .enter().append("g")
      .style("cursor", "pointer")
      .on("mouseover", (e: MouseEvent, d) => {
        setTooltip({ visible: true, x: e.pageX, y: e.pageY, content: d.type === 'case_cluster' ? `Case: ${d.label}` : `Shared Suspect: ${d.label}` });
      })
      .on("mousemove", (e: MouseEvent) => setTooltip(prev => ({ ...prev, x: e.pageX, y: e.pageY })))
      .on("mouseout", () => {
        setTooltip(prev => ({ ...prev, visible: false }));
      });

    const dragBehavior = d3.drag<SVGGElement, SyndicateNode>()
        .on("start", dragstarted)
        .on("drag", dragged)
        .on("end", dragended);

    node.call(dragBehavior);

    node.append("circle")
      .attr("r", (d) => nodeRadius(d))
      .attr("fill", (d) => colorMap[d.type as keyof typeof colorMap] || '#555')
      .attr("stroke", (d) => d.type === 'shared_suspect' ? "var(--warning-400)" : "none")
      .attr("stroke-width", (d) => d.type === 'shared_suspect' ? 3 : 0)
      .attr("filter", "drop-shadow(0px 4px 4px rgba(0,0,0,0.25))");

    node.append("text")
      .text((d) => d.label)
      .attr('x', (d) => nodeRadius(d) + 5)
      .attr('y', 4)
      .attr("fill", "var(--text-primary)")
      .style("font-family", "JetBrains Mono")
      .style("font-size", "12px")
      .style("font-weight", "600")
      .style("text-shadow", "0 1px 3px rgba(0,0,0,0.8)")
      .style("pointer-events", "none");

    simulation.on("tick", () => {
      link
        .attr("x1", (d) => (d.source as SyndicateNode).x ?? 0)
        .attr("y1", (d) => (d.source as SyndicateNode).y ?? 0)
        .attr("x2", (d) => (d.target as SyndicateNode).x ?? 0)
        .attr("y2", (d) => (d.target as SyndicateNode).y ?? 0);

      node.attr("transform", (d) => `translate(${d.x ?? 0},${d.y ?? 0})`);
    });

    function dragstarted(event: d3.D3DragEvent<SVGGElement, SyndicateNode, SyndicateNode>, d: SyndicateNode) {
      if (!event.active) simulation.alphaTarget(0.3).restart();
      d.fx = d.x;
      d.fy = d.y;
    }

    function dragged(event: d3.D3DragEvent<SVGGElement, SyndicateNode, SyndicateNode>, d: SyndicateNode) {
      d.fx = event.x;
      d.fy = event.y;
    }

    function dragended(event: d3.D3DragEvent<SVGGElement, SyndicateNode, SyndicateNode>, d: SyndicateNode) {
      if (!event.active) simulation.alphaTarget(0);
      d.fx = null;
      d.fy = null;
    }

    return () => {
      simulation.stop();
    };
  }, [initialNodes, initialEdges]);

  return (
    <>
      <div ref={containerRef} className="w-full h-[600px] bg-background-surface rounded-xl overflow-hidden border border-border-default shadow-lg">
        <svg ref={svgRef} className="w-full h-full" />
      </div>
      
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
