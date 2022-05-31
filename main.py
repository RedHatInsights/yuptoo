import json

from confluent_kafka import KafkaException

from yuptoo.lib.config import KAFKA_AUTO_COMMIT, QPC_TOPIC
from yuptoo.lib.logger import initialize_logging
import logging
from yuptoo.lib.exceptions import QPCKafkaMsgException
from yuptoo.validators.qpc_message_validator import validate_qpc_message
from yuptoo.processor.report_processor import process_report
from yuptoo.lib import consume, produce
from yuptoo.lib.logger import threadctx


initialize_logging()
LOG = logging.getLogger(__name__)


def set_extra_log_data(request_obj):
    threadctx.request_id = request_obj['request_id']
    threadctx.account = request_obj['account']
    threadctx.org_id = request_obj['org_id']


consumer = consume.init_consumer()
producer = produce.init_producer()
LOG.info(f"Started listening on kafka topic - {QPC_TOPIC}.")
while True:
    msg = consumer.poll(1.0)
    if msg is None:
        continue
    if msg.error():
        LOG.error(f"Kafka error occured : {msg.error()}.")
        raise KafkaException(msg.error())
    try:
        topic = msg.topic()
        msg = json.loads(msg.value().decode("utf-8"))
        msg['topic'] = topic
        request_obj = validate_qpc_message(msg)
        set_extra_log_data(request_obj)
        process_report(msg, producer, request_obj)
    except json.decoder.JSONDecodeError:
        consumer.commit()
        LOG.error(f"Unable to decode kafka message: {msg.value()}")
    except QPCKafkaMsgException as message_error:
        LOG.error(f"Error processing records.  Message: {msg}, Error: {message_error}")
        consumer.commit()
    except Exception as err:
        consumer.commit()
        LOG.error(f"An error occurred during message processing: {repr(err)}")
    finally:
        if not KAFKA_AUTO_COMMIT:
            consumer.commit()
        producer.flush()
