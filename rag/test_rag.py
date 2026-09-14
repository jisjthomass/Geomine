import json
from rag_db_module import insert_event_embedding, semantic_search, get_db_connection

print("Testing RAG Database Module...\n")

print("1. Cleaning up previous test data...")
try:
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM historical_event_embeddings WHERE well_id IN ('WELL_001', 'WELL_002', 'WELL_003')")
    conn.commit()
except Exception as e:
    print(f"Cleanup error: {e}")
finally:
    if 'cur' in locals(): cur.close()
    if 'conn' in locals(): conn.close()

print("2. Inserting isolated test data...")
insert_event_embedding(
    event_id=101, 
    content="Drill string got stuck at 2800m due to poor hole cleaning.",
    embedding=[0.1, 0.2, 0.3], 
    well_id="WELL_001", 
    depth_m=2800.0, 
    formation="Formation X", 
    event_type="Stuck Pipe"
)

insert_event_embedding(
    event_id=102, 
    content="Severe mud loss encountered at 2850m.",
    embedding=[0.9, 0.8, 0.7], 
    well_id="WELL_002", 
    depth_m=2850.0, 
    formation="Formation Y", 
    event_type="Mud Loss"
)

insert_event_embedding(
    event_id=103, 
    content="Kick detected at 3000m.",
    embedding=[0.5, 0.5, 0.5], 
    well_id="WELL_003", 
    depth_m=3000.0, 
    formation="Formation X", 
    event_type="Kick"
)

print("Inserted successfully!\n")

print("3. Testing Hybrid Semantic Search Filters...")

# Test A: Basic search
res_a = semantic_search([0.1, 0.25, 0.3], top_k=5)
print("Test A (No filters): found", len(res_a['results']))
assert len(res_a['results']) >= 3

# Test B: Formation filter
res_b = semantic_search([0.1, 0.25, 0.3], formation="Formation X", top_k=5)
print("Test B (Formation='Formation X'): found", len(res_b['results']))
assert all(r['formation'] == "Formation X" for r in res_b['results'])
assert len(res_b['results']) == 2

# Test C: Depth filter (min and max)
res_c = semantic_search([0.1, 0.25, 0.3], min_depth=2820, max_depth=2900, top_k=5)
print("Test C (Depth 2820 - 2900): found", len(res_c['results']))
assert all(2820 <= r['depth_m'] <= 2900 for r in res_c['results'])
assert len(res_c['results']) == 1

# Test D: Empty result filter
res_d = semantic_search([0.1, 0.25, 0.3], formation="Nonexistent", top_k=5)
print("Test D (Formation='Nonexistent'): found", len(res_d['results']))
assert len(res_d['results']) == 0

# Test E: Event type filter
res_e = semantic_search([0.1, 0.25, 0.3], event_type="Kick", top_k=5)
print("Test E (Event Type='Kick'): found", len(res_e['results']))
assert all(r['event_type'] == "Kick" for r in res_e['results'])
assert len(res_e['results']) == 1

# Test F: Nearby well IDs filter
res_f = semantic_search([0.1, 0.25, 0.3], nearby_well_ids=["WELL_001", "WELL_002"], top_k=5)
print("Test F (Nearby Wells): found", len(res_f['results']))
assert all(r['well_id'] in ["WELL_001", "WELL_002"] for r in res_f['results'])
assert len(res_f['results']) == 2

# Test G: Invalid input validation
print("Test G (Invalid Inputs):")
try:
    semantic_search(query_embedding=[], top_k=5)
    print("FAILED: Did not catch empty embedding")
except ValueError:
    print("Caught empty embedding successfully")

try:
    insert_event_embedding(event_id=None, content="test", embedding=[1.0, 2.0])
    print("FAILED: Did not catch missing event_id")
except ValueError:
    print("Caught missing event_id successfully")

print("\nFinal details of Test B (Formation Filter):")
print(json.dumps(res_b, indent=2))
