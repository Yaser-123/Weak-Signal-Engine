# merge_existing_clusters.py

"""
Script to merge existing candidate clusters that were created before the improved similarity thresholds.
This re-runs the merging logic on all existing clusters to consolidate similar topics.
"""

import sys
import os
sys.path.append(os.path.dirname(__file__))

from src.embeddings.embedding_model import EmbeddingModel
from src.clustering.cluster_evolution import evolve_clusters
from src.memory.candidate_store import load_candidates, save_candidates

def merge_existing_clusters():
    """Merge existing candidate clusters using improved similarity thresholds"""

    print("=== Merging Existing Candidate Clusters ===\n")

    # Load existing candidates
    existing_candidates = load_candidates()
    print(f"Loaded {len(existing_candidates)} existing candidate clusters")

    if not existing_candidates:
        print("No candidates to merge.")
        return

    # Show current statistics
    signal_counts = [c["signal_count"] for c in existing_candidates]
    total_signals = sum(signal_counts)
    print(f"Current total signals: {total_signals}")
    print(f"Current average signals per cluster: {total_signals / len(existing_candidates):.1f}")
    print(f"Current largest cluster: {max(signal_counts)} signals")
    print(f"Current clusters with ≥3 signals: {len([c for c in existing_candidates if c['signal_count'] >= 3])}")
    print()

    # Initialize embedding model
    print("Initializing embedding model...")
    embedding_model = EmbeddingModel()

    # Merge all existing candidates together
    # Treat existing candidates as "new batch clusters" to merge into empty existing list
    print("Running cluster evolution with improved similarity threshold (0.40)...")

    # Process in smaller batches and save progress
    batch_size = 5  # Even smaller batches
    merged_candidates = []
    total_batches = (len(existing_candidates) + batch_size - 1) // batch_size

    print(f"Processing {len(existing_candidates)} clusters in {total_batches} batches of {batch_size}...")
    print("Progress will be saved after each batch in case of interruption.")

    for i in range(0, len(existing_candidates), batch_size):
        batch = existing_candidates[i:i + batch_size]
        batch_num = i // batch_size + 1
        print(f"  Processing batch {batch_num}/{total_batches} ({len(batch)} clusters)...")

        try:
            # Merge this batch with already merged candidates
            merged_candidates = evolve_clusters(
                merged_candidates,  # existing (already merged)
                batch,              # new batch to merge
                embedding_model,
                0.30                # Even lower threshold for more aggressive merging
            )
            print(f"    Saving progress...")
            save_candidates(merged_candidates)
            print(f"    Progress saved: {len(merged_candidates)} clusters so far")

        except Exception as e:
            print(f"    Error in batch {batch_num}: {e}")
            print(f"    Saving partial progress and stopping...")
            save_candidates(merged_candidates)
            break

    print(f"\nFinal merged result: {len(merged_candidates)} candidate clusters")

    # Show new statistics
    merged_signal_counts = [c["signal_count"] for c in merged_candidates]
    merged_total_signals = sum(merged_signal_counts)
    print(f"Merged total signals: {merged_total_signals}")
    print(f"Merged average signals per cluster: {merged_total_signals / len(merged_candidates):.1f}")
    print(f"Merged largest cluster: {max(merged_signal_counts)} signals")
    print(f"Merged clusters with ≥3 signals: {len([c for c in merged_candidates if c['signal_count'] >= 3])}")

    # Validation
    print("\n=== VALIDATION ===")
    print(f"Signals preserved: {'✓' if merged_total_signals == total_signals else '✗'}")
    print(f"Clusters reduced: {'✓' if len(merged_candidates) < len(existing_candidates) else '✗'}")

    if merged_total_signals == total_signals and len(merged_candidates) < len(existing_candidates):
        print("✓ SUCCESS: Clusters successfully merged!")
    else:
        print("⚠ No merging occurred - clusters may already be optimally separated")

    # Save merged candidates
    print("\nSaving merged candidates...")
    save_candidates(merged_candidates)
    print(f"Saved {len(merged_candidates)} merged candidate clusters to candidate_clusters.json")

    print("\n=== MERGING COMPLETE ===")
    print(f"Reduced from {len(existing_candidates)} to {len(merged_candidates)} clusters")
    print(f"Signals preserved: {merged_total_signals}")

if __name__ == "__main__":
    merge_existing_clusters()