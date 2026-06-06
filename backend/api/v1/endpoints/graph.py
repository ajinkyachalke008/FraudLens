from fastapi import APIRouter, HTTPException, Query, Depends
from neo4j import AsyncGraphDatabase
from typing import Optional

from core.neo4j import get_neo4j_credentials
from models.schemas.graph import SubgraphResponse, GraphNode, GraphEdge
from models.sql.user import User
from api.deps import get_current_user
from fastapi_cache.decorator import cache

router = APIRouter()

@router.get("/subgraph", response_model=SubgraphResponse)
@cache(expire=60)
async def get_subgraph(
    account_id: str,
    hops: int = Query(2, ge=1, le=4),
    min_amount: Optional[float] = 0.0,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    current_user: User = Depends(get_current_user)
):
    uri, user, password = get_neo4j_credentials()
    driver = None
    try:
        driver = AsyncGraphDatabase.driver(uri, auth=(user, password))
        async with driver.session() as session:
            # Cypher query to fetch N-hop subgraph
            query = """
            MATCH path = (start:Account {accountNumber: $account_id})-[:SENT|RECEIVED*1..%d]-(neighbor:Account)
            WITH collect(distinct start) + collect(distinct neighbor) AS all_nodes, collect(distinct relationships(path)) AS all_rels
            
            // Unwind relationships to filter by amount and distinct them
            UNWIND all_rels AS path_rels
            UNWIND path_rels AS rel
            WITH all_nodes, collect(distinct rel) AS distinct_rels
            
            RETURN all_nodes, distinct_rels
            """ % hops
            
            result = await session.run(query, account_id=account_id)
            record = await result.single()
            
            if not record:
                return SubgraphResponse(nodes=[], edges=[], stats={"message": "No data found."})
                
            raw_nodes = record["all_nodes"]
            raw_edges = record["distinct_rels"]
            
            nodes = []
            for n in raw_nodes:
                nodes.append(GraphNode(
                    id=n.get("accountNumber", "unknown"),
                    accountNumber=n.get("accountNumber", "unknown"),
                    type=n.get("label", "unknown"),
                    riskScore=n.get("riskScore", 0.0),
                    totalVolume=n.get("totalInflow", 0.0) + n.get("totalOutflow", 0.0),
                    transactionCount=n.get("transactionCount", 0),
                    isCentralNode=n.get("pageRankScore", 0.0) > 0.8,
                    centrality={
                        "pageRank": n.get("pageRankScore", 0.0),
                        "betweenness": n.get("betweennessScore", 0.0),
                        "degree": 0.0
                    },
                    metadata={
                        "bankName": n.get("bankName", ""),
                        "accountType": n.get("accountType", ""),
                        "registeredName": n.get("registeredName", ""),
                    }
                ))
                
            edges = []
            for r in raw_edges:
                amt = r.get("amount", 0.0)
                if min_amount and amt < min_amount:
                    continue
                    
                edges.append(GraphEdge(
                    id=r.get("transactionRef", f"rel_{r.id}"),
                    source=r.nodes[0].get("accountNumber", ""),
                    target=r.nodes[1].get("accountNumber", ""),
                    amount=amt,
                    timestamp=str(r.get("timestamp", "")),
                    transactionType=r.get("transactionType", "UNKNOWN"),
                    upiId=r.get("upiId", None),
                    riskFlag=r.get("riskFlag", "unknown")
                ))
                
            stats = {
                "node_count": len(nodes),
                "edge_count": len(edges),
                "high_risk_nodes": sum(1 for n in nodes if n.riskScore > 0.7)
            }
            
            return SubgraphResponse(nodes=nodes, edges=edges, stats=stats)
            
    except Exception as e:
        print(f"Neo4j Error: {e} - Returning mock graph for Native Mode.")
        # Return a rich mock graph for Native Demo Mode
        mock_nodes = [
            GraphNode(id=account_id, accountNumber=account_id, type="Account", riskScore=0.95, totalVolume=500000, transactionCount=12, isCentralNode=True, centrality={"pageRank": 0.9, "betweenness": 0.8, "degree": 5}, metadata={"bankName": "HDFC", "accountType": "Savings", "registeredName": "John Doe"}),
            GraphNode(id="ACC-002", accountNumber="ACC-002", type="Account", riskScore=0.1, totalVolume=10000, transactionCount=3, isCentralNode=False, centrality={"pageRank": 0.1, "betweenness": 0.1, "degree": 1}, metadata={"bankName": "SBI", "accountType": "Current", "registeredName": "Jane Smith"}),
            GraphNode(id="ACC-003", accountNumber="ACC-003", type="Account", riskScore=0.85, totalVolume=250000, transactionCount=8, isCentralNode=False, centrality={"pageRank": 0.5, "betweenness": 0.4, "degree": 3}, metadata={"bankName": "ICICI", "accountType": "Savings", "registeredName": "Syndicate A"}),
            GraphNode(id="ACC-004", accountNumber="ACC-004", type="Account", riskScore=0.9, totalVolume=300000, transactionCount=10, isCentralNode=False, centrality={"pageRank": 0.6, "betweenness": 0.5, "degree": 4}, metadata={"bankName": "Axis", "accountType": "Current", "registeredName": "Syndicate B"}),
        ]
        mock_edges = [
            GraphEdge(id="rel_1", source=account_id, target="ACC-002", amount=5000, timestamp="2026-06-05T10:00:00Z", transactionType="IMPS", upiId=None, riskFlag="low"),
            GraphEdge(id="rel_2", source="ACC-003", target=account_id, amount=150000, timestamp="2026-06-05T11:00:00Z", transactionType="RTGS", upiId=None, riskFlag="high"),
            GraphEdge(id="rel_3", source="ACC-004", target=account_id, amount=200000, timestamp="2026-06-05T12:00:00Z", transactionType="NEFT", upiId=None, riskFlag="critical"),
            GraphEdge(id="rel_4", source="ACC-003", target="ACC-004", amount=50000, timestamp="2026-06-05T13:00:00Z", transactionType="UPI", upiId="syndicate@ybl", riskFlag="high"),
        ]
        return SubgraphResponse(nodes=mock_nodes, edges=mock_edges, stats={"node_count": 4, "edge_count": 4, "high_risk_nodes": 3, "message": "Native Mock Mode (Neo4j Offline)"})
    finally:
        if driver:
            await driver.close()
