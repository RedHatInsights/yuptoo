import json

from confluent_kafka import KafkaException

from yuptoo.lib.config import get_logger, KAFKA_AUTO_COMMIT, QPC_TOPIC
from yuptoo.lib.utils import format_message
from yuptoo.lib.exceptions import QPCKafkaMsgException
from yuptoo.validators.qpc_message_validator import validate_qpc_message
from yuptoo.processor.report_processor import process_report
from yuptoo.lib import consume, produce

LOG = get_logger(__name__)
LOG_PREFIX = 'REPORT CONSUMER'

consumer = consume.init_consumer()
producer = produce.init_producer()
LOG.info(f"{LOG_PREFIX} - Started listening on kafka topic - {QPC_TOPIC}.")
while True:
    msg = consumer.poll(1.0)
    if msg is None:
        continue
    if msg.error():
        LOG.error("%s - Kafka error occured : %s.", LOG_PREFIX, msg.error())
        raise KafkaException(msg.error())
    try:
        topic = msg.topic()
        msg = json.loads(msg.value().decode("utf-8"))
        msg['topic'] = topic
        consumed_message = validate_qpc_message(msg)
        process_report(consumed_message, producer)
    except json.decoder.JSONDecodeError:
        consumer.commit()
        LOG.error(
            'Unable to decode kafka message: %s - %s',
            msg.value(), LOG_PREFIX
        )
    except QPCKafkaMsgException as message_error:
        LOG.error(format_message(
                LOG_PREFIX, 'Error processing records.  Message: %s, Error: %s' %
                (msg, message_error)))
        consumer.commit()
    except Exception as err:
        consumer.commit()
        LOG.error(
            'An error occurred during message processing: %s - %s',
            repr(err),
            LOG_PREFIX
        )
    finally:
        if not KAFKA_AUTO_COMMIT:
            consumer.commit()
        consumer.close()
        producer.flush()
