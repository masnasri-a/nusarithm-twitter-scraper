
from confluent_kafka import Producer
import json
import logging

logger = logging.getLogger(__name__)

def produce(topic: str, key: str, value: dict):

    conf = {
        'bootstrap.servers': 'localhost:9092',  # ganti dengan alamat broker kamu
        'client.id': 'python-producer'
    }

    producer = Producer(conf)

    def delivery_report(err, msg):
        if err is not None:
            logger.error(f"Message delivery failed: {err}")
        else:
            logger.info(f"Message delivered to {msg.topic()} [{msg.partition()}] @ offset {msg.offset()}")

    # kirim pesan
    producer.produce(
        topic=topic,
        key=key,
        value=json.dumps(value),
        callback=delivery_report
    )

    # flush untuk memastikan semua pesan terkirim
    producer.flush()