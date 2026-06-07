'use client';

import React, { useEffect, useRef } from 'react';
import { useAuth } from '@/contexts/AuthContext';
import { toast } from 'sonner';

export default function AlertWebSocketProvider({ children }: { children: React.ReactNode }) {
  const { token } = useAuth();
  const wsRef = useRef<WebSocket | null>(null);

  useEffect(() => {
    if (!token) return;

    // Connect to WebSocket
    // For local dev, we assume backend is on localhost:8001
    const wsUrl = `ws://localhost:8001/api/v1/ws/stream?token=${token}`;
    
    const ws = new WebSocket(wsUrl);
    wsRef.current = ws;

    ws.onopen = () => {
      console.log('Connected to FraudLens Alert Stream');
    };

    ws.onmessage = (event) => {
      try {
        // Handle ping/pong heartbeats
        if (event.data === 'pong') return;
        
        const data = JSON.parse(event.data);
        
        // Ensure it's a fraud alert message
        if (data.type === 'NEW_TRANSACTION' && data.data?.ai_analysis?.is_fraud) {
          toast.error(`High-Risk Transfer Detected: ₹${data.data.amount}`, {
            description: `Origin: ${data.data.source} -> Syndicate: ${data.data.ai_analysis.syndicate_id}`,
            duration: 10000,
            action: {
              label: 'Investigate',
              onClick: () => {
                window.location.href = `/cases`;
              }
            }
          });
        }
        else if (data.id && data.alert_type && data.severity) {
            // Check if it's an escalation
            const isEscalation = data.escalation_level > 0;
            const title = isEscalation ? `[ESCALATION L${data.escalation_level}] ${data.title}` : data.title;
            
            // Format toast based on severity
            if (data.severity === 'CRITICAL') {
              toast.error(title, {
                description: data.message,
                duration: isEscalation ? 10000 : 5000,
                action: {
                  label: 'Acknowledge',
                  onClick: () => {
                    // Send ACK back through socket
                    ws.send(JSON.stringify({
                      type: 'ALERT_ACK',
                      alert_id: data.id
                    }));
                    toast.success('Alert Acknowledged');
                  }
                }
              });
            } else if (data.severity === 'HIGH') {
              toast.warning(title, {
                description: data.message,
              });
            } else {
              toast.info(title, {
                description: data.message,
              });
            }
        }
      } catch (e) {
        console.error('Error parsing websocket message', e);
      }
    };

    ws.onclose = () => {
      console.log('Disconnected from Alert Stream');
    };

    return () => {
      ws.close();
    };
  }, [token]);

  return <>{children}</>;
}
