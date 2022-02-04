from confluent_kafka import Consumer, KafkaException


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

    # Function skeleton based on current functions
    def save_message_and_ack(self, consumer_record)
    def check_if_url_expired(self, url, request_id)
    def unpack_consumer_record(self, consumer_record)
    def listen_for_messages(self, log_message)

