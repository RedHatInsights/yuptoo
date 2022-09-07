from confluent_kafka import Producer
from yuptoo.lib.config import INSIGHTS_KAFKA_ADDRESS, KAFKA_PRODUCER_OVERRIDE_MAX_REQUEST_SIZE, kafka_auth_config


def init_producer():
    connection_object = {
        'bootstrap.servers': INSIGHTS_KAFKA_ADDRESS,
        'message.max.bytes': KAFKA_PRODUCER_OVERRIDE_MAX_REQUEST_SIZE
    }
    kafka_auth_config(connection_object)
    producer = Producer(connection_object)

    return producer
