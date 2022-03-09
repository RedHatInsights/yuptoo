from confluent_kafka import Consumer, KafkaException
import json
import pytz
from yuptoo.config.base import get_logger, INSIGHTS_KAFKA_ADDRESS, QPC_TOPIC, GROUP_ID, KAFKA_AUTO_COMMIT
from datetime import datetime, timedelta
from urllib.parse import parse_qs, urlparse
from yuptoo.processor.report_processor import ReportProcessor
from .exceptions import QPCKafkaMsgException


LOG = get_logger(__name__)


class ReportConsumer:
    def __init__(self):
        self.account = None
        self.prefix = 'REPORT CONSUMER'
        self.consumer = Consumer({
            'bootstrap.servers': INSIGHTS_KAFKA_ADDRESS,
            'group.id': GROUP_ID,
            'enable.auto.commit': KAFKA_AUTO_COMMIT
        })
        self.consumer.subscribe([QPC_TOPIC])

    def __iter__(self):
        return self

    def __next__(self):
        msg = self.consumer.poll()
        if msg is None:
            raise StopIteration
        return msg

    def run(self):
        """Initialize Report Consumer."""
        LOG.info(f"{self.prefix} - Report Consumer started.  Waiting for messages...")

        for msg in iter(self):
            if msg.error():
                LOG.error("%s - Kafka error occured : %s.", self.prefix, msg.error())
                raise KafkaException(msg.error())
            try:
                topic = msg.topic()
                msg = json.loads(msg.value().decode("utf-8"))
                msg['topic'] = topic
                self.handle_message(msg)
            except json.decoder.JSONDecodeError:
                self.consumer.commit()
                LOG.error(
                    'Unable to decode kafka message: %s - %s',
                    msg.value(), self.prefix
                )
            except Exception as err:
                LOG.error(
                    'An error occurred during message processing: %s - %s',
                    repr(err),
                    self.prefix
                )
            finally:
                if not KAFKA_AUTO_COMMIT:
                    self.consumer.commit()

    def handle_message(self, upload_message):
        """Handle the JSON report."""

        if upload_message.get('topic') == QPC_TOPIC:
            account = upload_message.get('account')
            LOG.info(
                '%s - Received record on %s topic for account %s.',
                self.prefix, QPC_TOPIC, account)
            try:
                missing_fields = []
                request_id = upload_message.get('request_id')
                url = upload_message.get('url')
                if not account:
                    missing_fields.append('account')
                if not request_id:
                    missing_fields.append('request_id')
                if not url:
                    missing_fields.append('url')
                if missing_fields:
                    raise QPCKafkaMsgException(
                        LOG.error(
                            self.prefix,
                            'Message missing required field(s): %s.' % ', '.join(missing_fields)))

                self.check_if_url_expired(url, request_id)
                upload_message.update(
                    {
                        'last_update_time': datetime.now(pytz.utc),
                        'arrival_time': datetime.now(pytz.utc),
                    }
                )
                ReportProcessor().pass_message_to_report_processor(upload_message)

            except QPCKafkaMsgException as message_error:
                LOG.error(
                    self.prefix,
                    'Error processing records. Error: %s',
                    message_error)
                self.consumer.commit()
        else:
            LOG.debug(
                self.prefix,
                'Message not found on topic: %s', QPC_TOPIC)

    def check_if_url_expired(self, url, request_id):
        """Validate if url is expired."""
        self.prefix = 'NEW REPORT VALIDATION'
        parsed_url_query = parse_qs(urlparse(url).query)
        creation_timestamp = parsed_url_query['X-Amz-Date']
        expire_time = timedelta(seconds=int(parsed_url_query['X-Amz-Expires'][0]))
        creation_datatime = datetime.strptime(str(creation_timestamp[0]), '%Y%m%dT%H%M%SZ')

        if datetime.now().replace(microsecond=0) > (creation_datatime + expire_time):
            raise QPCKafkaMsgException(
                self.prefix,
                'Request_id = %s is already expired and cannot be processed:'
                'Creation time = %s, Expiry interval = %s.',
                request_id, creation_datatime, expire_time)
