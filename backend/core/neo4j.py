import os
from neo4j import AsyncGraphDatabase

def get_neo4j_credentials():
    uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
    user = os.getenv("NEO4J_USER", "neo4j")
    password = os.getenv("NEO4J_PASSWORD", "fraudlens2025")
    return uri, user, password

async def init_neo4j():
    # Verify connection on startup
    uri, user, password = get_neo4j_credentials()
    try:
        driver = AsyncGraphDatabase.driver(uri, auth=(user, password))
        await driver.verify_connectivity()
        await driver.close()
        print("Neo4j connection verified.")
    except Exception as e:
        print(f"Warning: Could not connect to Neo4j. Is the container running? {e}")
