
import logging
import json
import numpy as np

from kafka import KafkaConsumer, TopicPartition, OffsetAndMetadata

from src.settings import KAFKA_BOOTSTRAP
from src.db.postgres import insert_anomaly
from src.processing.anomaly import predict

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

TOPIC = "sensor_readings"


def consume():
    consumer = KafkaConsumer(
        TOPIC,
        bootstrap_servers=KAFKA_BOOTSTRAP,
        auto_offset_reset="earliest",
        enable_auto_commit=False,
        group_id="anomaly-consumer",
        value_deserializer=lambda x: json.loads(x.decode("utf-8"))
    )

    logging.info("Kafka consumer started!")

    try:
        for message in consumer:
            try:
                data = message.value

                sensor_id = data["sensor_id"]
                timestamp = data["timestamp"]
                value = float(data["value"])

                # Run the trained Isolation Forest model
                is_anomaly, score = predict(
                    np.array([[value]], dtype=float)
                )

                # Save the actual prediction to PostgreSQL
                insert_anomaly(
                    sensor_id=sensor_id,
                    timestamp=timestamp,
                    score=score,
                    is_anomaly=is_anomaly,
                    raw_data=data
                )

                logging.info(
                    f"Prediction: sensor={sensor_id}, "
                    f"value={value:.2f}, "
                    f"anomaly={is_anomaly}, score={score:.4f}"
                )

                # Commit Kafka offset only after successful DB insertion
                tp = TopicPartition(message.topic, message.partition)
                offset = OffsetAndMetadata(message.offset + 1, "")
                consumer.commit({tp: offset})

            except Exception as e:
                logging.error(f"Error processing message: {e}")

    except KeyboardInterrupt:
        logging.info("Consumer stopped.")

    finally:
        consumer.close()


if __name__ == "__main__":
    consume()
