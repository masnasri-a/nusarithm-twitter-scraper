import json
import logging
from confluent_kafka import Consumer, KafkaError, KafkaException
from src.queue.sendmongo import send_to_mongo
import requests

def annotations(post_text: dict) -> str:
    """Simulate text annotation."""
    logger = logging.getLogger(__name__)
    logger.info(f"📝 Annotating text: {post_text.get('text', '')[:30]}...")
    # Simulated annotation process
    base_url = "http://43.157.243.30:8000/v1"
    post_text['annotation'] = {}
    
    response = requests.post(f"{base_url}/sentiment", json={"text": post_text['content'].get('text', '')})
    if response.status_code == 200:
        post_text['annotation']['sentiment'] = response.json()['result'].get("sentiment", "-")
    else:
        logger.error(f"❌ Annotation failed: {response.text}")
    
    # emotion
    response = requests.post(f"{base_url}/emotion", json={"text": post_text['content'].get('text', '')})
    if response.status_code == 200:
        post_text['annotation']['emotion'] = response.json()['result'].get("emotion", "-")
    else:
        logger.error(f"❌ Annotation failed: {response.text}")

    return post_text

def create_kafka_consumer():
    """Create and run Kafka consumer for post enrichment."""
    logger = logging.getLogger(__name__)

    # Configuration for the Kafka consumer
    conf = {
        'bootstrap.servers': 'localhost:9092',  # Replace with your Kafka broker address
        'group.id': 'twitter-post-analysis',  # Consumer group ID
        'auto.offset.reset': 'earliest'  # Start from the beginning if no offset is stored
    }

    logger.info("🚀 Starting Kafka consumer for post enrichment")
    logger.info(f"📍 Bootstrap servers: {conf['bootstrap.servers']}")
    logger.info(f"👥 Consumer group: {conf['group.id']}")

    # Create Consumer instance
    consumer = Consumer(conf)
    logger.info("✅ Kafka consumer created successfully")

    # Subscribe to a topic
    topic = 'twitter_data_raw'  # Replace with your topic name
    consumer.subscribe([topic])
    logger.info(f"📡 Subscribed to topic: {topic}")

    try:
        message_count = 0
        while True:
            # Poll for messages
            msg = consumer.poll(timeout=1.0)
            if msg is None:
                continue

            if msg.error():
                if msg.error().code() == KafkaError._PARTITION_EOF:
                    # End of partition event
                    logger.info(f'🏁 End of partition reached {msg.topic()} [{msg.partition()}] at offset {msg.offset()}')
                elif msg.error():
                    logger.error(f"❌ Kafka error: {msg.error()}")
                    raise KafkaException(msg.error())
            else:
                # Process the message
                message_count += 1
                logger.info(f"📨 Processing message #{message_count}")

                try:
                    content = msg.value().decode("utf-8")
                    data = json.loads(content)
                    post_id = data['content']['id']

                    logger.info(f"🔍 Extracted post ID: {post_id}")
                    # logger.info(f"📊 Message metadata: topic={msg.topic()}, partition={msg.partition()}, offset={msg.offset()}")

                    # Enrich the post details
                    annotations_data = annotations(data)
                    logger.info(annotations_data)
                    send_to_mongo(annotations_data)
                    # enrichment_url = detail(post_id)
                    logger.info(f"✅ Enrichment completed for post ID: {post_id}")

                except json.JSONDecodeError as e:
                    logger.error(f"❌ Failed to parse message JSON: {e}")
                    logger.debug(f"Raw message content: {msg.value()}")
                except KeyError as e:
                    logger.error(f"❌ Missing required field in message: {e}")
                except Exception as e:
                    logger.error(f"❌ Error processing message: {e}")

    except KeyboardInterrupt:
        logger.info("⏹️ Consumer stopped by user interrupt")
    except Exception as e:
        logger.error(f"❌ Unexpected error in consumer: {e}")
    finally:
        # Close the consumer
        logger.info("🧹 Closing Kafka consumer...")
        consumer.close()
        logger.info("✅ Kafka consumer closed successfully")


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    create_kafka_consumer()