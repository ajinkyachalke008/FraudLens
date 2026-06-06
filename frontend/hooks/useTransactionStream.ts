import { useEffect, useState, useRef, useCallback } from 'react';
import { GraphNode, GraphEdge } from '@/components/graph/TransactionGraph';

interface WebSocketPayload {
  type: string;
  data: any;
}

const MAX_RECONNECT_DELAY = 30000; // 30 seconds max
const INITIAL_RECONNECT_DELAY = 1000; // 1 second

export function useTransactionStream(url: string) {
  const [streamedNodes, setStreamedNodes] = useState<GraphNode[]>([]);
  const [streamedEdges, setStreamedEdges] = useState<GraphEdge[]>([]);
  const [connectionStatus, setConnectionStatus] = useState<'connecting' | 'connected' | 'disconnected'>('connecting');
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectDelay = useRef(INITIAL_RECONNECT_DELAY);
  const reconnectTimer = useRef<NodeJS.Timeout | null>(null);
  const shouldReconnect = useRef(true);

  const connect = useCallback(() => {
    if (!shouldReconnect.current) return;
    if (typeof window === 'undefined') return;

    try {
      const token = localStorage.getItem('fraudlens_token');
      const wsUrl = `${url}${url.includes('?') ? '&' : '?'}token=${token || ''}`;
      const ws = new WebSocket(wsUrl);
      wsRef.current = ws;
      setConnectionStatus('connecting');

      ws.onopen = () => {
        console.log('✅ Connected to FraudLens Live Intelligence Stream');
        setConnectionStatus('connected');
        reconnectDelay.current = INITIAL_RECONNECT_DELAY; // Reset backoff on success
      };

      ws.onmessage = (event) => {
        try {
          const payload: WebSocketPayload = JSON.parse(event.data);
          if (payload.type === 'NEW_TRANSACTION') {
            const tx = payload.data;
            
            const sourceNode: GraphNode = {
              id: tx.source,
              accountNumber: tx.source,
              type: 'unknown',
              riskScore: tx.ai_analysis?.risk_score || 0.1,
              totalVolume: tx.amount || 0,
              transactionCount: 1,
              isCentralNode: false,
              centrality: { pageRank: 0.1, betweenness: 0.1, degree: 1 },
              metadata: { bankName: 'Unknown', accountType: 'savings' }
            };

            const targetNode: GraphNode = {
              id: tx.target,
              accountNumber: tx.target,
              type: 'unknown',
              riskScore: 0.1,
              totalVolume: tx.amount || 0,
              transactionCount: 1,
              isCentralNode: false,
              centrality: { pageRank: 0.1, betweenness: 0.1, degree: 1 },
              metadata: { bankName: 'Unknown', accountType: 'savings' }
            };

            const newEdge: GraphEdge = {
              id: tx.id,
              source: tx.source,
              target: tx.target,
              amount: tx.amount,
              timestamp: new Date().toISOString(),
              transactionType: 'TRANSFER',
              riskFlag: tx.ai_analysis?.is_fraud ? 'high' : 'low'
            };

            setStreamedNodes(prev => {
              const exists = new Set(prev.map(n => n.id));
              const newArray = [...prev];
              if (!exists.has(sourceNode.id)) newArray.push(sourceNode);
              if (!exists.has(targetNode.id)) newArray.push(targetNode);
              return newArray;
            });

            setStreamedEdges(prev => [...prev, newEdge]);
          }
        } catch (err) {
          console.error("Failed to parse websocket message", err);
        }
      };

      ws.onclose = () => {
        setConnectionStatus('disconnected');
        if (shouldReconnect.current) {
          console.warn(`⚠️ WebSocket Disconnected. Reconnecting in ${reconnectDelay.current / 1000}s...`);
          reconnectTimer.current = setTimeout(() => {
            reconnectDelay.current = Math.min(reconnectDelay.current * 2, MAX_RECONNECT_DELAY);
            connect();
          }, reconnectDelay.current);
        }
      };

      ws.onerror = () => {
        ws.close(); // Triggers onclose → reconnect
      };
    } catch {
      // WebSocket constructor can throw if URL is invalid
      setConnectionStatus('disconnected');
    }
  }, [url]);

  useEffect(() => {
    shouldReconnect.current = true;
    connect();

    return () => {
      shouldReconnect.current = false;
      if (reconnectTimer.current) clearTimeout(reconnectTimer.current);
      if (wsRef.current) wsRef.current.close();
    };
  }, [connect]);

  return { streamedNodes, streamedEdges, connectionStatus };
}
