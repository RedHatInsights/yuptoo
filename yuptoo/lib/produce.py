from confluent_kafka import Producer, KafkaException
from yuptoo.lib.config import (BOOTSTRAP_SERVERS, KAFKA_PRODUCER_OVERRIDE_MAX_REQUEST_SIZE,
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
        'bootstrap.servers': ",".join(BOOTSTRAP_SERVERS),
        'message.max.bytes': KAFKA_PRODUCER_OVERRIDE_MAX_REQUEST_SIZE
    }
    kafka_auth_config(connection_object)
    producer = Producer(connection_object)
    return producer


def send_message(kafka_topic, msg, request_obj=None):

    def delivery_report(err, msg=None, is_msg_for_hbi=False):
        nonlocal request_obj  # noqa: F824
        if err is not None:
            LOG.error(f"Message delivery for topic {msg.topic()} failed: {err}")
            if is_msg_for_hbi:
                host_upload_failures.inc()
        else:
            if is_msg_for_hbi:
                request_obj['host_inventory_upload_count'] += 1
                host_uploaded.inc()
            LOG.debug(f"Message delivered to {msg.topic()} [{msg.partition()}]")

    try:
        bytes = json.dumps(msg, ensure_ascii=False).encode("utf-8")
        if kafka_topic == UPLOAD_TOPIC:
            org_id = request_obj.get('org_id') if request_obj else None
            key = org_id.encode("utf-8") if org_id else None
            producer.produce(kafka_topic, bytes, key, callback=partial(delivery_report, is_msg_for_hbi=True))
        else:
            producer.produce(kafka_topic, bytes, callback=delivery_report)
        producer.poll(1)
    except KafkaException:
        LOG.error(f"Failed to produce message to [{kafka_topic}] topic.")
