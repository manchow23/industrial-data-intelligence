import logging
import time
import json
import random
from kafka import KafkaProducer

from src.settings import KAFKA_BOOTSTRAP

logger = logging.getLogger(__name__)

def get_random_reading():
    return {
        "sensor_id": f"sensor_{random.randint(1, 10)}",
        "timestamp": int(time.time()),
        "value": random.uniform(0, 100)
    }

def run(producer: KafkaProducer, topic: str, interval: float = 1.0):
    while True:
        reading = get_random_reading()
        producer.send(topic, json.dumps(reading).encode("utf-8"))
        producer.flush()
        logger.info(f"Sent reading: {reading}")
        time.sleep(interval)

def main():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s"
    )

    producer = KafkaProducer(
        bootstrap_servers=KAFKA_BOOTSTRAP
    )

    try:
        logger.info("Sensor producer started!")
        run(producer, "sensor_readings", interval=1.0)
    except KeyboardInterrupt:
        logger.info("Producer stopped.")
    finally:
        producer.close()

if __name__ == "__main__":
    main()