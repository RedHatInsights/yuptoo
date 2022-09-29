from confluent_kafka import Producer, KafkaException
from yuptoo.lib.config import INSIGHTS_KAFKA_ADDRESS, KAFKA_PRODUCER_OVERRIDE_MAX_REQUEST_SIZE, kafka_auth_config
import logging
import json

LOG = logging.getLogger(__name__)
producer = None


def init_producer():
    global producer
    connection_object = {
        'bootstrap.servers': INSIGHTS_KAFKA_ADDRESS,
        'message.max.bytes': KAFKA_PRODUCER_OVERRIDE_MAX_REQUEST_SIZE
    }
    kafka_auth_config(connection_object)
    producer = Producer(connection_object)
    return producer


def send_message(kafka_topic, msg):

    msg_sent = False

    def delivery_report(err, msg=None):
        if err is not None:
            LOG.error(f"Message delivery for topic {msg.topic()} failed: {err}")
        else:
            nonlocal msg_sent
            msg_sent = True
            LOG.debug(f"Message delivered to {msg.topic()} [{msg.partition()}]")

    try:
        bytes = json.dumps(msg, ensure_ascii=False).encode("utf-8")
        producer.produce(kafka_topic, bytes, callback=delivery_report)
        producer.poll(1)
        return msg_sent
    except KafkaException:
        LOG.error(f"Failed to produce message to [{kafka_topic}] topic.")
