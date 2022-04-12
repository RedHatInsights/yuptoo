from confluent_kafka import Producer
from yuptoo.lib.config import INSIGHTS_KAFKA_ADDRESS, KAFKA_PRODUCER_OVERRIDE_MAX_REQUEST_SIZE


def init_producer():
    producer = Producer({
        'bootstrap.servers': INSIGHTS_KAFKA_ADDRESS,
        'message.max.bytes': KAFKA_PRODUCER_OVERRIDE_MAX_REQUEST_SIZE
    })

    return producer
