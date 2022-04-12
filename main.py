import json

from confluent_kafka import Consumer, KafkaException

from yuptoo.lib.config import get_logger, KAFKA_AUTO_COMMIT, INSIGHTS_KAFKA_ADDRESS, QPC_TOPIC
from yuptoo.validators.qpc_message_validator import validate_qpc_message
from yuptoo.processor.report_processor import process_report


LOG = get_logger(__name__)
LOG_PREFIX = 'REPORT CONSUMER'

c = Consumer({
    'bootstrap.servers': INSIGHTS_KAFKA_ADDRESS,
    'group.id': 'qpc-group',
    'auto.offset.reset': 'earliest',
    'enable.auto.commit': KAFKA_AUTO_COMMIT
})

c.subscribe([QPC_TOPIC])
while True:
    msg = c.poll()
    if msg is None:
        continue
    if msg.error():
        LOG.error("%s - Kafka error occured : %s.", LOG_PREFIX, msg.error())
        raise KafkaException(msg.error())
    try:
        topic = msg.topic()
        msg = json.loads(msg.value().decode("utf-8"))
        msg['topic'] = topic
        consumed_message = validate_qpc_message(msg, c)
        process_report(consumed_message)
    except json.decoder.JSONDecodeError:
        c.commit()
        LOG.error(
            'Unable to decode kafka message: %s - %s',
            msg.value(), LOG_PREFIX
        )
    except Exception as err:
        LOG.error(
            'An error occurred during message processing: %s - %s',
            repr(err),
            LOG_PREFIX
        )
    finally:
        if not KAFKA_AUTO_COMMIT:
            c.commit()