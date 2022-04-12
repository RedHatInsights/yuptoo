from confluent_kafka import Consumer
from yuptoo.lib.config import KAFKA_AUTO_COMMIT, INSIGHTS_KAFKA_ADDRESS, QPC_TOPIC


def init_consumer():
    consumer = Consumer({
                'bootstrap.servers': INSIGHTS_KAFKA_ADDRESS,
                'group.id': 'qpc-group',
                'auto.offset.reset': 'earliest',
                'enable.auto.commit': KAFKA_AUTO_COMMIT
                })
    consumer.subscribe([QPC_TOPIC])

    return consumer
