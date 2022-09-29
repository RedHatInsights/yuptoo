import json

from yuptoo.lib.config import KAFKA_AUTO_COMMIT, ANNOUNCE_TOPIC, METRICS_PORT, KAFKA_BROKER, TRACKER_TOPIC
from yuptoo.lib.logger import initialize_logging, threadctx
import logging
from yuptoo.lib.exceptions import QPCKafkaMsgException, FailExtractException
from yuptoo.lib.metrics import kafka_failures, report_processing_exceptions, extract_report_slices_failures
from yuptoo.validators.qpc_message_validator import validate_qpc_message
from yuptoo.processor.report_processor import process_report
from yuptoo.lib import consume, produce
from prometheus_client import start_http_server
from yuptoo.processor.utils import tracker_message


initialize_logging()
LOG = logging.getLogger(__name__)


# Create cacert for kafka managed kafka config.
if KAFKA_BROKER and KAFKA_BROKER.cacert:
    with open('/tmp/cacert', 'w') as f:
        f.write(KAFKA_BROKER.cacert)


def set_extra_log_data(request_obj):
    threadctx.request_id = request_obj['request_id']
    threadctx.account = request_obj['account']
    threadctx.org_id = request_obj['org_id']


consumer = consume.init_consumer()
producer = produce.init_producer()

LOG.info(f"Started listening on kafka topic - {ANNOUNCE_TOPIC}.")
start_http_server(METRICS_PORT)
LOG.info("Started Yuptoo Prometheus Server.")

while True:
    msg = consumer.poll(1.0)
    if msg is None:
        continue
    if msg.error():
        LOG.error(f"Kafka error occured : {msg.error()}.")
        continue
    try:
        service = dict(msg.headers() or []).get('service')
        if service:
            service = service.decode("utf-8")
            if service == 'qpc':
                topic = msg.topic()
                msg = json.loads(msg.value().decode("utf-8"))
                msg['topic'] = topic
                request_obj = validate_qpc_message(msg)
                produce.send_message(
                    TRACKER_TOPIC,
                    tracker_message(request_obj, "received", "Payload received by yuptoo")
                )
                set_extra_log_data(request_obj)
                consumer.commit()
                process_report(msg, request_obj)
    except json.decoder.JSONDecodeError:
        LOG.error(f"Unable to decode kafka message: {msg.value()}")
    except QPCKafkaMsgException as message_error:
        kafka_failures.labels(
            org_id=msg['org_id']
        ).inc()
        LOG.error(f"Error processing Kafka message.  Message: {msg}, Error: {message_error}")
    except FailExtractException as err:
        extract_report_slices_failures.labels(
                    org_id=request_obj['org_id']
                ).inc()
        LOG.error(f"Error Extracting report.  Message: {msg}, Error: {err}")
    except Exception as err:
        report_processing_exceptions.labels(
            org_id=msg['org_id']
        ).inc()
        LOG.error(f"An error occurred during message processing: {repr(err)}")
    finally:
        if not KAFKA_AUTO_COMMIT:
            consumer.commit()
        producer.flush()
