import os
import logging

LOG = logging.getLogger(__name__)

CLOWDER_ENABLED = True if os.getenv("CLOWDER_ENABLED", default="False").lower() in ["true", "t", "yes", "y"] else False


def kafka_auth_config(connection_object):
    if KAFKA_BROKER:
        if KAFKA_BROKER.cacert:
            connection_object["ssl.ca.location"] = "/tmp/cacert"
        if KAFKA_BROKER.sasl and KAFKA_BROKER.sasl.username:
            connection_object.update({
                "security.protocol": KAFKA_BROKER.sasl.securityProtocol,
                "sasl.mechanisms": KAFKA_BROKER.sasl.saslMechanism,
                "sasl.username": KAFKA_BROKER.sasl.username,
                "sasl.password": KAFKA_BROKER.sasl.password,
            })
    return connection_object


if CLOWDER_ENABLED:
    LOG.info("Using Clowder Operator...")
    from app_common_python import LoadedConfig, KafkaTopics, KafkaServers
    KAFKA_BROKER = LoadedConfig.kafka.brokers[0]
    BOOTSTRAP_SERVERS = KafkaServers
    ANNOUNCE_TOPIC = KafkaTopics["platform.upload.announce"].name
    UPLOAD_TOPIC = KafkaTopics["platform.inventory.host-ingress"].name
    VALIDATION_TOPIC = KafkaTopics["platform.upload.validation"].name
    TRACKER_TOPIC = KafkaTopics["platform.payload-status"].name
    METRICS_PORT = LoadedConfig.metricsPort
else:
    INSIGHTS_KAFKA_HOST = os.getenv('INSIGHTS_KAFKA_HOST', 'localhost')
    INSIGHTS_KAFKA_PORT = os.getenv('INSIGHTS_KAFKA_PORT', '29092')
    BOOTSTRAP_SERVERS = [f'{INSIGHTS_KAFKA_HOST}:{INSIGHTS_KAFKA_PORT}']
    KAFKA_BROKER = None
    ANNOUNCE_TOPIC = os.getenv('ANNOUNCE_TOPIC', 'platform.upload.announce')
    VALIDATION_TOPIC = os.getenv('VALIDATION_TOPIC', 'platform.upload.validation')
    UPLOAD_TOPIC = os.getenv('UPLOAD_TOPIC', 'platform.inventory.host-ingress')
    TRACKER_TOPIC = os.getenv('TRACKER_TOPIC', "platform.payload-status")
    METRICS_PORT = os.getenv("METRICS_PORT", 5005)

LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
KAFKA_AUTO_COMMIT = os.getenv("KAFKA_AUTO_COMMIT", False)
KAFKA_CONSUMER_GROUP_ID = os.getenv("KAFKA_CONSUMER_GROUP_ID", "qpc-group")
MAX_HOSTS_PER_REP = os.getenv('MAX_HOSTS_PER_REP', default=10000)
HOSTS_TRANSFORMATION_ENABLED = os.getenv('HOSTS_TRANSFORMATION_ENABLED', default=True)
KAFKA_PRODUCER_OVERRIDE_MAX_REQUEST_SIZE = os.getenv(
    'KAFKA_PRODUCER_OVERRIDE_MAX_REQUEST_SIZE', 2097152
)
DISCOVERY_HOST_TTL = os.getenv('DISCOVERY_HOST_TTL', '29')
SATELLITE_HOST_TTL = os.getenv('SATELLITE_HOST_TTL', '29')
