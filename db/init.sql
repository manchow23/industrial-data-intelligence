CREATE TABLE IF NOT EXISTS anomalies (
    id SERIAL PRIMARY KEY,
    sensor_id VARCHAR(255) NOT NULL,
    timestamp TIMESTAMPTZ NOT NULL,
    score FLOAT NOT NULL,
    is_anomaly BOOLEAN NOT NULL,
    raw_data JSONB
);