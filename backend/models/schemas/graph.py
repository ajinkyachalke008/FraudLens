from pydantic import BaseModel
from typing import List, Dict, Any, Optional

class GraphNode(BaseModel):
    id: str
    accountNumber: str
    type: str
    riskScore: float
    totalVolume: float
    transactionCount: int
    isCentralNode: bool
    centrality: Dict[str, float]
    metadata: Dict[str, Any]

class GraphEdge(BaseModel):
    id: str
    source: str
    target: str
    amount: float
    timestamp: str
    transactionType: str
    upiId: Optional[str] = None
    riskFlag: str

class SubgraphResponse(BaseModel):
    nodes: List[GraphNode]
    edges: List[GraphEdge]
    stats: Dict[str, Any]
