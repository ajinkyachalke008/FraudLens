// Web Worker for processing massive GeoJSON or Transaction Data 
// off the main thread to prevent UI freezing during Map/Graph rendering.

self.onmessage = async (e: MessageEvent) => {
  const { type, payload } = e.data;

  try {
    if (type === 'PARSE_SPATIAL_DATA') {
      // Simulate heavy data parsing (e.g., millions of transaction rows to ArcLayer format)
      // In production, this might use Apache Arrow or Supercluster.
      
      const arcs = payload.data.map((tx: any) => ({
        source: [tx.src_lng, tx.src_lat],
        target: [tx.dst_lng, tx.dst_lat],
        amount: tx.amount,
        riskScore: tx.risk_score
      }));

      // Return processed array buffer to main thread
      self.postMessage({ type: 'SPATIAL_DATA_PARSED', data: arcs });
    }
  } catch (error: any) {
    self.postMessage({ type: 'ERROR', error: error.message });
  }
};
