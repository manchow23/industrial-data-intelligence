import logging
import json
from datetime import datetime, timezone

from psycopg2 import extras
from src.db.pool import get_pool

logger = logging.getLogger(__name__)


def insert_anomaly(sensor_id, timestamp, score, is_anomaly, raw_data):
    pool = get_pool()
    conn = None

    try:
        conn = pool.getconn()

        # Convert Unix timestamp to UTC datetime
        if isinstance(timestamp, (int, float)):
            timestamp = datetime.fromtimestamp(timestamp, tz=timezone.utc)

        # Convert JSON string into a Python object
        if isinstance(raw_data, str):
            raw_data = json.loads(raw_data)

        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO anomalies
                (sensor_id, timestamp, score, is_anomaly, raw_data)
                VALUES (%s, %s, %s, %s, %s)
                """,
                (
                    sensor_id,
                    timestamp,
                    score,
                    is_anomaly,
                    extras.Json(raw_data),
                ),
            )

        conn.commit()
        logger.info(f"Inserted anomaly for sensor {sensor_id}")

    except Exception as e:
        if conn:
            conn.rollback()
        logger.error(f"Failed to insert anomaly: {e}")
        raise

    finally:
        if conn is not None:
            pool.putconn(conn)