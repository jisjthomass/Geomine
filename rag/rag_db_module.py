import psycopg2
import os
import json

def get_db_connection():
    db_host = os.getenv("DB_HOST")
    # If not explicitly specified, try localhost first on host machines, fallback to db
    if not db_host:
        db_host = "localhost"

    return psycopg2.connect(
        dbname=os.getenv("DB_NAME", "nwis_wells_db"),
        user=os.getenv("DB_USER", "postgres"),
        password=os.getenv("DB_PASSWORD", "postgres"),
        host=db_host,
        port=os.getenv("DB_PORT", "5432"),
        connect_timeout=3,
    )

def insert_event_embedding(event_id, content, embedding, well_id=None, depth_m=None, formation=None, event_type=None, report_id=None, document_type=None):
    if not embedding or not isinstance(embedding, (list, tuple)):
        raise ValueError("Embedding must be a non-empty list or tuple of numbers.")
    if event_id is None or content is None:
        raise ValueError("event_id and content are required.")

    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        embedding_str = f"[{','.join(map(str, embedding))}]"
        query = """
            INSERT INTO historical_event_embeddings 
            (event_id, content, embedding, well_id, depth_m, formation, event_type, report_id, document_type)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id;
        """
        cursor.execute(query, (event_id, content, embedding_str, well_id, depth_m, formation, event_type, report_id, document_type))
        new_id = cursor.fetchone()[0]
        conn.commit()
        return new_id
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        cursor.close()
        conn.close()

def semantic_search(query_embedding, formation=None, min_depth=None, max_depth=None, event_type=None, nearby_well_ids=None, top_k=5):
    if not query_embedding or not isinstance(query_embedding, (list, tuple)):
        raise ValueError("query_embedding must be a non-empty list or tuple of numbers.")
    if top_k is None or top_k < 1:
        top_k = 5

    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        embedding_str = f"[{','.join(map(str, query_embedding))}]"
        query = """
            SELECT 
                event_id, content, well_id, depth_m, formation, event_type, report_id, document_type,
                (embedding <=> %s::vector) AS distance
            FROM historical_event_embeddings
            WHERE 1=1
        """
        params = [embedding_str]
        
        if formation and str(formation).strip():
            query += " AND LOWER(formation) = LOWER(%s)"
            params.append(str(formation).strip())
        if min_depth is not None:
            query += " AND depth_m >= %s"
            params.append(float(min_depth))
        if max_depth is not None:
            query += " AND depth_m <= %s"
            params.append(float(max_depth))
        if event_type and str(event_type).strip():
            query += " AND LOWER(event_type) = LOWER(%s)"
            params.append(str(event_type).strip())
        if nearby_well_ids and len(nearby_well_ids) > 0:
            query += " AND well_id = ANY(%s)"
            params.append(list(nearby_well_ids))
            
        query += " ORDER BY distance ASC LIMIT %s;"
        params.append(top_k)
        
        cursor.execute(query, tuple(params))
        rows = cursor.fetchall()
        
        results = []
        for row in rows:
            results.append({
                "event_id": row[0],
                "content": row[1],
                "well_id": row[2],
                "depth_m": row[3],
                "formation": row[4],
                "event_type": row[5],
                "report_id": row[6],
                "document_type": row[7],
                "distance": float(row[8])
            })
        return {"results": results}
    finally:
        cursor.close()
        conn.close()
