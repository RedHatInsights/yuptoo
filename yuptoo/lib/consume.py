import logging

from confluent_kafka import Consumer
from yuptoo.lib.config import (
        KAFKA_AUTO_COMMIT,
        BOOTSTRAP_SERVERS,
        ANNOUNCE_TOPIC,
        KAFKA_CONSUMER_GROUP_ID,
        KAFKA_CONSUMER_MAXPOLL_INTERVAL,
        kafka_auth_config
    )

LOG = logging.getLogger(__name__)


def init_consumer():
    connection_object = {
        'bootstrap.servers': ",".join(BOOTSTRAP_SERVERS),
        'group.id': KAFKA_CONSUMER_GROUP_ID,
        'enable.auto.commit': KAFKA_AUTO_COMMIT,
        'max.poll.interval.ms': KAFKA_CONSUMER_MAXPOLL_INTERVAL,
    }
    # Note. Log only non-sensitive connection parameters
    LOG.info(f"Init Kafka Consumer with parameters: {connection_object}.")
    kafka_auth_config(connection_object)
    consumer = Consumer(connection_object)
    consumer.subscribe([ANNOUNCE_TOPIC])

    return consumer
