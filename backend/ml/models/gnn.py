import torch
import torch.nn.functional as F
from torch_geometric.nn import SAGEConv

class FraudSAGE(torch.nn.Module):
    """
    GraphSAGE model for detecting fraudulent accounts in transaction networks.
    - Uses node features: total_inflow, total_outflow, balance_ratio, degree_centrality
    - Performs inductive representation learning to output a risk score [0, 1].
    """
    def __init__(self, in_channels: int, hidden_channels: int, out_channels: int = 1):
        super(FraudSAGE, self).__init__()
        # Layer 1: Aggregate 1-hop neighborhood
        self.conv1 = SAGEConv(in_channels, hidden_channels)
        self.bn1 = torch.nn.BatchNorm1d(hidden_channels)
        
        # Layer 2: Aggregate 2-hop neighborhood
        self.conv2 = SAGEConv(hidden_channels, hidden_channels)
        self.bn2 = torch.nn.BatchNorm1d(hidden_channels)
        
        # Final classification layer
        self.lin = torch.nn.Linear(hidden_channels, out_channels)

    def forward(self, x, edge_index):
        """
        Forward pass for the GNN.
        Args:
            x (Tensor): Node feature matrix of shape [num_nodes, in_channels]
            edge_index (Tensor): Graph connectivity matrix of shape [2, num_edges]
        Returns:
            Tensor: Predicted risk probability [0, 1] for each node.
        """
        # First layer
        x = self.conv1(x, edge_index)
        x = self.bn1(x)
        x = F.relu(x)
        x = F.dropout(x, p=0.3, training=self.training)
        
        # Second layer
        x = self.conv2(x, edge_index)
        x = self.bn2(x)
        embeddings = F.relu(x)  # Save the embeddings before dropout for visualization/clustering
        
        x = F.dropout(embeddings, p=0.3, training=self.training)
        
        # Output layer
        out = self.lin(x)
        return torch.sigmoid(out), embeddings

# Mock Inference Utility (Used until Neo4j streaming is fully stable)
def run_mock_gnn_inference(num_nodes: int = 5):
    """
    Runs a mock inference pass to test the model architecture without a DB.
    """
    # 4 features: inflow, outflow, balance, degree
    mock_x = torch.rand((num_nodes, 4), dtype=torch.float)
    
    if num_nodes > 1:
        # Create a simple chain
        src = list(range(num_nodes - 1))
        dst = list(range(1, num_nodes))
        # Add reverse edges for undirected graph
        mock_edge_index = torch.tensor([src + dst, dst + src], dtype=torch.long)
    else:
        # Single node with no edges
        mock_edge_index = torch.empty((2, 0), dtype=torch.long)
    
    model = FraudSAGE(in_channels=4, hidden_channels=16, out_channels=1)
    model.eval()
    
    with torch.no_grad():
        predictions, embeddings = model(mock_x, mock_edge_index)
    
    return predictions.squeeze().tolist(), embeddings.tolist()
