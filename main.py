import json

from confluent_kafka import KafkaException

from yuptoo.lib.config import get_logger, KAFKA_AUTO_COMMIT
from yuptoo.validators.qpc_message_validator import validate_qpc_message
from yuptoo.processor.report_processor import process_report
from yuptoo.lib import consume, produce

LOG = get_logger(__name__)
LOG_PREFIX = 'REPORT CONSUMER'

consumer = consume.init_consumer()
producer = produce.init_producer()
while True:
    msg = consumer.poll()
    if msg is None:
        continue
    if msg.error():
        LOG.error("%s - Kafka error occured : %s.", LOG_PREFIX, msg.error())
        raise KafkaException(msg.error())
    try:
        topic = msg.topic()
        msg = json.loads(msg.value().decode("utf-8"))
        msg['topic'] = topic
        consumed_message = validate_qpc_message(msg, consumer)
        process_report(consumed_message, producer)
    except json.decoder.JSONDecodeError:
        consumer.commit()
        LOG.error(
            'Unable to decode kafka message: %s - %s',
            msg.value(), LOG_PREFIX
        )
    except Exception as err:
        consumer.commit()
        LOG.error(
            'An error occurred during message processing: %s - %s',
            repr(err),
            LOG_PREFIX
        )
    finally:
        producer.flush()
        if not KAFKA_AUTO_COMMIT:
            consumer.commit()
