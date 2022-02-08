from confluent_kafka import Consumer, KafkaException
import json
import pytz
from yuptoo.config.base import get_logger, INSIGHTS_KAFKA_ADDRESS, QPC_TOPIC, GROUP_ID
from datetime import datetime, timedelta
from urllib.parse import parse_qs, urlparse
from .report_processor import ReportProcessor
from .exceptions import QPCReportException, QPCKafkaMsgException


LOG = get_logger(__name__)


class ReportConsumer:
    def __init__(self):
        self.account_number = None
        self.upload_message = None
        self.prefix = 'REPORT CONSUMER'
        self.consumer = Consumer({
            'bootstrap.servers': INSIGHTS_KAFKA_ADDRESS,
            'group.id': GROUP_ID,
            'enable.auto.commit': False
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
        """Intialize Report Consumer."""
        LOG.info(f"{self.prefix} - Report Consumer started.  Waiting for messages...")
        for msg in iter(self):
            if msg.error():
                LOG.error("%s - Kafka error occured : %s.", self.prefix, msg.error())
                raise KafkaException(msg.error())
            try:
                print("Hello World")
                msg = json.loads(msg.value().decode("utf-8"))
                self.handle_message(msg)
                # add listen_for_messages() func inside run() func
            except json.decoder.JSONDecodeError:
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
                self.consumer.commit()

    def handle_message(self, msg):
        """Handle the JSON report."""
        # This msg is the message we are getting
        # from QPC topic. We are fetching it here directly
        # and later unpacking it in a different method.
        if msg.topic == QPC_TOPIC:
            try:
                # since we are not saving anything to db,
                # we are only trying to consume the incoming message
                missing_fields = []
                self.upload_message = self.unpack_consumer_record(msg)
                rh_account = self.upload_message.get('rh_account')
                request_id = self.upload_message.get('request_id')
                url = self.upload_message.get('url')
                self.account_number = self.upload_message.get('account', rh_account)
                if not self.account_number:
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
                # we want to construct the incoming message properly
                # to send it to the report processor directly, instead
                # of saving it to the database.
                self.upload_qpc_kafka_msg = self.upload_message
                self.upload_qpc_kafka_msg.update(
                    {
                        'account': self.account_number,
                        'request_id': request_id,
                        'last_update_time': datetime.now(pytz.utc),
                        'arrival_time': datetime.now(pytz.utc),
                    }
                )
                print(self.upload_qpc_kafka_msg)
                received_message_dump = json.dumps(self.upload_qpc_kafka_msg)
                # sending this msg to report_processor
                ReportProcessor.pass_message_to_report_processor(received_message_dump)

            except QPCKafkaMsgException as message_error:
                LOG.error(
                    self.prefix,
                    'Error processing records.  Message: %s, Error: %s' %
                    (msg, message_error))
                self.consumer.commit()
        else:
            LOG.debug(
                self.prefix,
                'Message not found on %s topic: %s' % (QPC_TOPIC, msg))

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
                'Creation time = %s, Expiry interval = %s.'
                % (request_id, creation_datatime, expire_time))

    def unpack_consumer_record(self, consumer_record):
        """Decode uploaded message and return it in JSON format."""
        self.prefix = 'DECODE NEW REPORT'
        try:
            json_message = json.loads(consumer_record.value.decode('utf-8'))
            message = 'received on %s topic' % consumer_record.topic
            rh_account = json_message.get('rh_account')
            self.account_number = json_message.get('account', rh_account)
            LOG.info(
                self.prefix,
                message,
                account_number=self.account_number)
            LOG.debug(
                self.prefix,
                'Message: %s' % str(consumer_record),
                account_number=self.account_number)
            return json_message
        except ValueError:
            raise QPCKafkaMsgException(
                LOG.error(self.prefix, 'Upload service message not JSON.'))
