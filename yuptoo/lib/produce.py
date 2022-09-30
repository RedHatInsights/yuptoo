from confluent_kafka import Producer, KafkaException
from yuptoo.lib.config import (INSIGHTS_KAFKA_ADDRESS, KAFKA_PRODUCER_OVERRIDE_MAX_REQUEST_SIZE,
                               kafka_auth_config, UPLOAD_TOPIC)
from functools import partial
from yuptoo.lib.metrics import host_uploaded, host_upload_failures
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


def send_message(kafka_topic, msg, request_obj=None):

    def delivery_report(err, msg=None, is_msg_for_hbi=False):
        nonlocal request_obj
        if err is not None:
            LOG.error(f"Message delivery for topic {msg.topic()} failed: {err}")
            if is_msg_for_hbi:
                host_upload_failures.labels(
                        org_id=request_obj['org_id']
                    ).inc()
        else:
            if is_msg_for_hbi:
                request_obj['host_inventory_upload_count'] += 1
                host_uploaded.labels(
                        org_id=request_obj['org_id']
                    ).inc()
            LOG.debug(f"Message delivered to {msg.topic()} [{msg.partition()}]")

    try:
        bytes = json.dumps(msg, ensure_ascii=False).encode("utf-8")
        if kafka_topic == UPLOAD_TOPIC:
            producer.produce(kafka_topic, bytes, callback=partial(delivery_report, is_msg_for_hbi=True))
        else:
            producer.produce(kafka_topic, bytes, callback=delivery_report)
        producer.poll(1)
    except KafkaException:
        LOG.error(f"Failed to produce message to [{kafka_topic}] topic.")
