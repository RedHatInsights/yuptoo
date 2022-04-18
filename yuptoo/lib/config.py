import os
import logging


def get_logger(name):
    logging.basicConfig(
        level='INFO',
        format='%(asctime)s - %(levelname)s  - %(funcName)s - %(message)s'
    )
    return logging.getLogger(name)


INSIGHTS_KAFKA_HOST = os.getenv('INSIGHTS_KAFKA_HOST', 'localhost')
INSIGHTS_KAFKA_PORT = os.getenv('INSIGHTS_KAFKA_PORT', '29092')
INSIGHTS_KAFKA_ADDRESS = f'{INSIGHTS_KAFKA_HOST}:{INSIGHTS_KAFKA_PORT}'
QPC_TOPIC = os.getenv('QPC_TOPIC', 'platform.upload.qpc')
KAFKA_AUTO_COMMIT = os.getenv("KAFKA_AUTO_COMMIT", False)
MAX_HOSTS_PER_REP = os.getenv('MAX_HOSTS_PER_REP', default=10000)
HOSTS_TRANSFORMATION_ENABLED = os.getenv('HOSTS_TRANSFORMATION_ENABLED', default=True)
UPLOAD_TOPIC = os.getenv('UPLOAD_TOPIC', 'platform.inventory.host-ingress')
KAFKA_PRODUCER_OVERRIDE_MAX_REQUEST_SIZE = os.getenv(
    'KAFKA_PRODUCER_OVERRIDE_MAX_REQUEST_SIZE', 2097152
)
HOSTS_UPLOAD_FUTURES_COUNT = os.getenv('HOSTS_UPLOAD_FUTURES_COUNT', default=100)
DISCOVERY_HOST_TTL = os.getenv('DISCOVERY_HOST_TTL', '29')
SATELLITE_HOST_TTL = os.getenv('SATELLITE_HOST_TTL', '29')
VALIDATION_TOPIC = os.getenv('VALIDATION_TOPIC', 'platform.upload.validation')
