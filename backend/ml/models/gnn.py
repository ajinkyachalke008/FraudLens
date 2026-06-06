import random

# Mock Inference Utility (Used until Neo4j streaming is fully stable)
# PyTorch and torch-geometric removed for free-tier Render deployment.
def run_mock_gnn_inference(num_nodes: int = 5):
    """
    Runs a mock inference pass to test the pipeline without crashing the free tier.
    """
    predictions = [random.uniform(0.1, 0.9) for _ in range(num_nodes)]
    # Mock 16-dimensional embedding
    embeddings = [[random.uniform(-1, 1) for _ in range(16)] for _ in range(num_nodes)]
    
    if num_nodes == 1:
        return predictions, embeddings
    
    return predictions, embeddings
