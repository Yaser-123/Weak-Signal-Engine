"""
Setup required indexes on Qdrant Cloud collections
Run this once after creating collections
"""

import os
from dotenv import load_dotenv
from qdrant_client import QdrantClient
from qdrant_client.http.models import PayloadSchemaType

load_dotenv()

def setup_indexes():
    print("[INFO] Setting up Qdrant indexes...")
    
    client = QdrantClient(
        url=os.getenv("QDRANT_URL"),
        api_key=os.getenv("QDRANT_API_KEY"),
        timeout=30
    )
    
    # Create index on signal_id field for fast filtering
    print("[INFO] Creating index on 'signal_id' field in signals_hot collection...")
    try:
        client.create_payload_index(
            collection_name="signals_hot",
            field_name="signal_id",
            field_schema=PayloadSchemaType.KEYWORD
        )
        print("[INFO] ✅ Index on 'signal_id' created")
    except Exception as e:
        if "already exists" in str(e).lower():
            print("[INFO] Index on 'signal_id' already exists")
        else:
            print(f"[ERROR] Failed to create index: {e}")
    
    # Create index on cluster_id field for fast lookups
    print("[INFO] Creating index on 'cluster_id' field in signals_hot collection...")
    try:
        client.create_payload_index(
            collection_name="signals_hot",
            field_name="cluster_id",
            field_schema=PayloadSchemaType.KEYWORD
        )
        print("[INFO] ✅ Index on 'cluster_id' created")
    except Exception as e:
        if "already exists" in str(e).lower():
            print("[INFO] Index on 'cluster_id' already exists")
        else:
            print(f"[ERROR] Failed to create index: {e}")
    
    # Create index on cluster_id in clusters_warm
    print("[INFO] Creating index on 'cluster_id' field in clusters_warm collection...")
    try:
        client.create_payload_index(
            collection_name="clusters_warm",
            field_name="cluster_id",
            field_schema=PayloadSchemaType.KEYWORD
        )
        print("[INFO] ✅ Index on 'cluster_id' created in clusters_warm")
    except Exception as e:
        if "already exists" in str(e).lower():
            print("[INFO] Index on 'cluster_id' already exists")
        else:
            print(f"[ERROR] Failed to create index: {e}")
    
    print("\n" + "="*60)
    print("✅ INDEXES SETUP COMPLETE!")
    print("="*60)

if __name__ == "__main__":
    setup_indexes()
