import json
import random
import math
import logging
import time
import requests
from datetime import datetime
from confluent_kafka import Consumer, KafkaError, KafkaException
from src.queue.producer import produce as send_post_ids_to_kafka

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)


def generate_token():
    """Generate a random token for tweet enrichment."""
    logger = logging.getLogger(__name__)
    ids = random.sample(range(1, 1000000), 10)
    token = sum(int(id) * 1e15 * math.pi for id in ids)
    token_str = format(int(token), 'x').replace('0', '').replace('.', '')
    logger.debug(f"Generated token: {token_str[:20]}...")
    return token_str

def detail(post_id: str):
    """Simulate enriching tweet details."""
    logger = logging.getLogger(__name__)
    logger.info(f"🔍 Enriching details for post ID: {post_id}")

    token = generate_token()
    url = f"https://cdn.syndication.twimg.com/tweet-result?id={post_id}&token={token}"

    logger.info(f"📡 Enrichment URL: {url}")
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        try:
            tweet_details = {
                "id": data.get("id_str"),
                "text": data.get("text"),
                "created_at": data.get("created_at"),
                "created_at_timestamp": int(datetime.strptime(data.get("created_at"), "%Y-%m-%dT%H:%M:%S.%fZ").timestamp()) if data.get("created_at") else None,
                "lang": data.get("lang"),
                "user": {
                    "id": data["user"].get("id_str"),
                    "name": data["user"].get("name"),
                    "screen_name": data["user"].get("screen_name"),
                    "verified": data["user"].get("verified"),
                    "profile_image_url": data["user"].get("profile_image_url_https"),
                },
                "media": [
                    {
                        "type": media.get("type"),
                        "url": media.get("media_url_https"),
                        "video_info": media.get("video_info", {})
                    }
                for media in data.get("mediaDetails", [])
                ],
                "favorite_count": data.get("favorite_count"),
                "possibly_sensitive": data.get("possibly_sensitive"),
                "cleaned_data": False,
                "analysed_data": False
            }
            logger.info(f"✅ Successfully enriched post ID: {post_id}")
            send_post_ids_to_kafka(
                key=post_id,
                value={
                    'content':tweet_details,
                    'scraped_at': int(time.time())
                },
                topic='twitter_data_raw'
            )
            return tweet_details
        except KeyError as e:
            logger.error(f"KeyError: {e} in tweet {post_id}")
            return None
    else:
        logger.error(f"Failed to fetch details for tweet {post_id}, status code: {response.status_code}")
        return None

    # Here you would typically make an HTTP request to get tweet details
    # For now, we'll just log the URL

    return url
    

def create_kafka_consumer():
    """Create and run Kafka consumer for post enrichment."""
    logger = logging.getLogger(__name__)

    # Configuration for the Kafka consumer
    conf = {
        'bootstrap.servers': 'localhost:9092',  # Replace with your Kafka broker address
        'group.id': 'twitter-post-id',  # Consumer group ID
        'auto.offset.reset': 'earliest'  # Start from the beginning if no offset is stored
    }

    logger.info("🚀 Starting Kafka consumer for post enrichment")
    logger.info(f"📍 Bootstrap servers: {conf['bootstrap.servers']}")
    logger.info(f"👥 Consumer group: {conf['group.id']}")

    # Create Consumer instance
    consumer = Consumer(conf)
    logger.info("✅ Kafka consumer created successfully")

    # Subscribe to a topic
    topic = 'twitter_post_id'  # Replace with your topic name
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
                    post_id = data['post_id']

                    logger.info(f"🔍 Extracted post ID: {post_id}")
                    logger.info(f"📊 Message metadata: topic={msg.topic()}, partition={msg.partition()}, offset={msg.offset()}")

                    # Enrich the post details
                    enrichment_url = detail(post_id)
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

def start_enrich_detail():
    """Start the post enrichment process."""
    logger = logging.getLogger(__name__)
    logger.info("🎯 Starting Twitter post enrichment service")
    logger.info("═" * 60)

    try:
        create_kafka_consumer()
    except Exception as e:
        logger.error(f"❌ Failed to start enrichment service: {e}")
        raise
    finally:
        logger.info("🏁 Post enrichment service stopped")
        logger.info("═" * 60)