from confluent_kafka import Consumer, KafkaException
import json
from yuptoo.config.base import get_logger, INSIGHTS_KAFKA_ADDRESS, QPC_TOPIC, GROUP_ID
from datetime import datetime, timedelta
from urllib.parse import parse_qs, urlparse


LOG = get_logger(__name__)  # TODO define this func and import here


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
                self.handle_report(msg)
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

    def handle_report(msg):
        print(msg)
