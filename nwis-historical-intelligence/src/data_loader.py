import os
import psycopg2
import psycopg2.extras
import time

# In-memory cache: stores (timestamp, events_list)
# TTL = 300 seconds (5 minutes). The database rarely changes during a
# drilling session, so we can safely serve cached data instead of
# hitting PostgreSQL on every single API call.
_events_cache = None
_cache_timestamp = 0
_CACHE_TTL_SECONDS = 300

def load_historical_events(file_path=None):
    """
    Connects to PostgreSQL and loads the normalized historical events.
    Results are cached for 5 minutes to avoid hammering the DB on
    every API request.
    (file_path is ignored, kept for backward compatibility)
    """
    global _events_cache, _cache_timestamp

    now = time.monotonic()
    if _events_cache is not None and (now - _cache_timestamp) < _CACHE_TTL_SECONDS:
        return _events_cache

    try:
        db_host = os.getenv("DB_HOST")
        hosts = [db_host] if db_host else ["127.0.0.1", "localhost", "db"]
        if db_host == "db":
            hosts.extend(["127.0.0.1", "localhost"])

        conn = None
        for h in hosts:
            try:
                conn = psycopg2.connect(
                    dbname="nwis_wells_db",
                    user="postgres",
                    host=h,
                    password="postgres",
                    port=5432,
                    connect_timeout=3,
                )
                break
            except Exception:
                continue

        if not conn:
            raise RuntimeError("Could not connect to PostgreSQL on any candidate host.")

        cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

        cursor.execute("""
            SELECT
                well_id,
                latitude,
                longitude,
                event_depth as depth_m,
                formation,
                event_type,
                cause,
                mitigation,
                outcome,
                id as report_id
            FROM historical_drilling_events;
        """)

        events = [dict(row) for row in cursor.fetchall()]

        # Update cache
        _events_cache = events
        _cache_timestamp = time.monotonic()
        return events

    except Exception as e:
        print(f"CRITICAL ERROR loading from Postgres: {e}")
        # Return stale cache if available rather than empty list
        return _events_cache if _events_cache is not None else []
    finally:
        if "cursor" in locals():
            cursor.close()
        if "conn" in locals():
            conn.close()
