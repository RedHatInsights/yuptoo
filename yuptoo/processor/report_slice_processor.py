import base64
import copy
import json
import re
from confluent_kafka import Producer, KafkaException

from yuptoo.processor.exceptions import KafkaMsgHandlerError
from yuptoo.processor.host_transform_processor import HostTransformProcessor
from yuptoo.config.base import (
    HOSTS_TRANSFORMATION_ENABLED, KAFKA_PRODUCER_OVERRIDE_MAX_REQUEST_SIZE,
    UPLOAD_TOPIC, INSIGHTS_KAFKA_ADDRESS, HOSTS_UPLOAD_FUTURES_COUNT, get_logger
)

LOG = get_logger(__name__)
TRANSFORMED_DICT = dict({'removed': [], 'modified': [], 'missing_data': []})


class ReportSliceProcessor(HostTransformProcessor):  # pylint: disable=too-many-instance-attributes
    """Class for processing report slices that have been created."""

    def __init__(self, report_platform_id):
        self.report_platform_id = report_platform_id

    def transform_single_host(self, request_id, host_id, host: dict):
        """Transform 'system_profile' fields."""
        transformed_obj = copy.deepcopy(TRANSFORMED_DICT)
        if 'system_profile' in host:
            host, transformed_obj = self.transform_os_release(
                host, transformed_obj)
            host, transformed_obj = self.transform_os_kernel_version(
                host, transformed_obj)
            host, transformed_obj = self.transform_network_interfaces(
                host, transformed_obj)

        host, transformed_obj = self.remove_empty_ip_addresses(
            host, transformed_obj)
        host, transformed_obj = self.transform_mac_addresses(
            host, transformed_obj)
        host, transformed_obj = self.remove_display_name(
            host, transformed_obj)
        host, transformed_obj = self.remove_invalid_bios_uuid(
            host, transformed_obj)
        host, transformed_obj = self.transform_tags(host, transformed_obj)

        host_request_size = bytes(json.dumps(host), 'utf-8')
        if len(host_request_size) >= KAFKA_PRODUCER_OVERRIDE_MAX_REQUEST_SIZE:
            host, transformed_obj = self.remove_installed_packages(
                host, transformed_obj)

        self.print_transformed_info(request_id, host_id, transformed_obj)
        return host

    def print_transformed_info(self, request_id, host_id, transformed_obj):
        """Print transformed logs."""
        prefix = 'Printing Transformed Logs'
        if transformed_obj is None:
            return

        log_sections = []
        for key, value in transformed_obj.items():
            if value:
                log_sections.append('%s: %s' % (key, (',').join(value)))

        if log_sections:
            log_message = (
                '%s - Transformed details host with id %s (request_id: %s) for account=%s and report_platform_id=%s.'
            )
            log_message += '\n'.join(log_sections)
            LOG.info(
                log_message, prefix, host_id, request_id, self.account, self.report_platform_id
            )

    def delivery_report(self, err, msg=None):
        prefix = 'PUBLISH TO INVENTORY TOPIC ON KAFKA'

        if err is not None:
            LOG.error(
                "Message delivery for topic %s failed for request_id [%s]: %s",
                msg.topic(),
                err,
                self.request_id,
            )
        else:
            LOG.info(
                "%s - Message delivered to %s [%s] for request_id [%s]",
                prefix,
                msg.topic(),
                msg.partition(),
                self.request_id
            )

    def send_message(self, topic, msg):
        try:

            self.producer = Producer({
                'bootstrap.servers': INSIGHTS_KAFKA_ADDRESS,
                'message.max.bytes': KAFKA_PRODUCER_OVERRIDE_MAX_REQUEST_SIZE
            })

            bytes = json.dumps(msg, ensure_ascii=False).encode("utf-8")

            self.producer.produce(topic, bytes, callback=self.delivery_report)
            self.producer.poll(1)
        except KafkaException:
            LOG.exception(
                "Failed to produce message to [%s] topic: %s", topic, self.request_id
            )
        finally:
            self.producer.flush()

    # pylint:disable=too-many-locals
    # pylint: disable=too-many-statements
    def upload_to_host_inventory_via_kafka(self, hosts, b64_identity, request_id):
        self.request_id = request_id
        prefix = 'UPLOAD TO INVENTORY VIA KAFKA'
        total_hosts = len(hosts)
        count = 0
        cert_cn = None

        try:
            raw_b64_identity = base64.b64decode(b64_identity).decode('utf-8')
            identity = json.loads(raw_b64_identity)
            self.account = identity['identity']['account_number']
            cert_cn = identity['identity']['system']['cn']
        except KeyError as err:
            LOG.error(
                prefix, 'Invalid identity. Key not found: %s', err)

        unique_id_base = '{}:{}:'.format(self.request_id,
                                         self.report_platform_id)
        try:  # pylint: disable=too-many-nested-blocks
            for host_id, host in hosts.items():
                if HOSTS_TRANSFORMATION_ENABLED:
                    host = self.transform_single_host(
                        self.request_id, host_id, host)
                    if cert_cn and ('system_profile' in host):
                        host['system_profile']['owner_id'] = cert_cn

                report_slice_id = host.get('report_slice_id')
                system_unique_id = unique_id_base + report_slice_id + host_id

                count += 1
                upload_msg = {
                    'operation': 'add_host',
                    'data': host,
                    'platform_metadata': {'request_id': system_unique_id,
                                          'b64_identity': b64_identity}
                }

                self.send_message(UPLOAD_TOPIC, upload_msg)
                if count % HOSTS_UPLOAD_FUTURES_COUNT == 0 or count == total_hosts:
                    LOG.info(
                        '%s - Sending %s/%s hosts to the inventory service for account=%s and report_platform_id=%s.',
                        prefix, count, total_hosts, self.account, self.report_platform_id)

        except Exception as err:  # pylint: disable=broad-except
            LOG.error(
                '%s - The following error occurred: %s',
                prefix, err)
            raise KafkaMsgHandlerError(
                '%s - The following exception occurred: %s for account=%s and report_platform_id=%s.',
                prefix, err, self.account, self.report_platform_id)
