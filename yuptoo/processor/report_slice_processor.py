#
# Copyright 2019 Red Hat, Inc.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
"""Report Slice Processor."""

import asyncio
import base64
import copy
import json
import logging
from processor.report_consumer import (KAFKA_ERRORS,
                                       KafkaMsgHandlerError,
                                       QPCReportException)

from config.base import (
    HOSTS_TRANSFORMATION_ENABLED, KAFKA_PRODUCER_OVERRIDE_MAX_REQUEST_SIZE,
    UPLOAD_TOPIC
)

from yuptoo.processor.host_transformation import (
    transform_tags, remove_display_name, remove_empty_ip_addresses,
    transform_mac_addresses, remove_invalid_bios_uuid,
    transform_os_release, transform_os_kernel_version,
    transform_network_interfaces, remove_installed_packages,
    TRANSFORMED_DICT
)

LOG = logging.getLogger(__name__)


class RetryUploadTimeException(Exception):
    """Use to report upload errors that should be retried on time."""

    pass


class RetryUploadCommitException(Exception):
    """Use to report upload errors that should be retried on commit."""

    pass


class ReportSliceProcessor:  # pylint: disable=too-many-instance-attributes
    """Class for processing report slices that have been created."""

    def __init__(self):
        self.producer = AIOKafkaProducer(
            loop=SLICE_PROCESSING_LOOP, bootstrap_servers=INSIGHTS_KAFKA_ADDRESS,
            max_request_size=KAFKA_PRODUCER_OVERRIDE_MAX_REQUEST_SIZE
        )

    def pass_to_report_slice_processor(self, options):
        pass

    def transform_single_host(self, request_id, host_id, host: dict):
        """Transform 'system_profile' fields."""
        transformed_obj = copy.deepcopy(TRANSFORMED_DICT)
        if 'system_profile' in host:
            host, transformed_obj = transform_os_release(
                host, transformed_obj)
            host, transformed_obj = transform_os_kernel_version(
                host, transformed_obj)
            host, transformed_obj = transform_network_interfaces(
                host, transformed_obj)

        host, transformed_obj = remove_empty_ip_addresses(
            host, transformed_obj)
        host, transformed_obj = transform_mac_addresses(
            host, transformed_obj)
        host, transformed_obj = remove_display_name(
            host, transformed_obj)
        host, transformed_obj = remove_invalid_bios_uuid(
            host, transformed_obj)
        host, transformed_obj = transform_tags(host, transformed_obj)
        host_request_size = bytes(json.dumps(host), 'utf-8')
        if len(host_request_size) >= KAFKA_PRODUCER_OVERRIDE_MAX_REQUEST_SIZE:
            host, transformed_obj = remove_installed_packages(
                host, transformed_obj)

        self.print_transformed_info(request_id, host_id, transformed_obj)
        return host

    def print_transformed_info(self, request_id, host_id, transformed_obj):
        """Print transformed logs."""
        if transformed_obj is None:
            return

        log_sections = []
        for key, value in transformed_obj.items():
            if value:
                log_sections.append('%s: %s' % (key, (',').join(value)))

        if log_sections:
            log_message = (
                'Transformed details host with id %s (request_id: %s):\n'
                % (host_id, request_id)
            )
            log_message += '\n'.join(log_sections)
            LOG.info(
                    prefix,
                    log_message,
                    account_number=self.account_number,
                    report_platform_id=self.report_platform_id
            )

    # pylint:disable=too-many-locals
    # pylint: disable=too-many-statements
    def upload_to_host_inventory_via_kafka(self, hosts):
        """
        Upload to the host inventory via kafka.

        :param: hosts <list> the hosts to upload.
        """
        self.prefix = 'UPLOAD TO INVENTORY VIA KAFKA'
        await self.producer.stop()
        self.producer = AIOKafkaProducer(
            loop=SLICE_PROCESSING_LOOP, bootstrap_servers=INSIGHTS_KAFKA_ADDRESS,
            max_request_size=KAFKA_PRODUCER_OVERRIDE_MAX_REQUEST_SIZE
        )
        try:
            await self.producer.start()
        except (KafkaConnectionError, TimeoutError):
            KAFKA_ERRORS.inc()
            self.should_run = False
            print_error_loop_event()
            raise KafkaMsgHandlerError(
                format_message(
                    self.prefix,
                    'Unable to connect to kafka server.',
                    account_number=self.account_number,
                    report_platform_id=self.report_platform_id))
        total_hosts = len(hosts)
        count = 0
        send_futures = []
        associated_msg = []
        report = self.report_or_slice.report
        cert_cn = None
        try:
            b64_identity = json.loads(report.upload_srv_kafka_msg)['b64_identity']
            raw_b64_identity = base64.b64decode(b64_identity).decode('utf-8')
            identity = json.loads(raw_b64_identity)
            cert_cn = identity['identity']['system']['cn']
        except KeyError as err:
            LOG.error(
                prefix, 'Invalid identity. Key not found: %s', err)

        unique_id_base = '{}:{}:{}:'.format(report.request_id,
                                            report.report_platform_id,
                                            self.report_or_slice.report_slice_id)
        try:  # pylint: disable=too-many-nested-blocks
            for host_id, host in hosts.items():
                if HOSTS_TRANSFORMATION_ENABLED:
                    host = self._transform_single_host(
                        report.request_id, host_id, host)
                    if cert_cn and ('system_profile' in host):
                        host['system_profile']['owner_id'] = cert_cn
                system_unique_id = unique_id_base + host_id
                count += 1
                upload_msg = {
                    'operation': 'add_host',
                    'data': host,
                    'platform_metadata': {'request_id': system_unique_id,
                                          'b64_identity': b64_identity}
                }
                msg = bytes(json.dumps(upload_msg), 'utf-8')
                future = await self.producer.send(UPLOAD_TOPIC, msg)
                send_futures.append(future)
                associated_msg.append(upload_msg)
                if count % HOSTS_UPLOAD_FUTURES_COUNT == 0 or count == total_hosts:
                    LOG.info(
                        format_message(
                            self.prefix,
                            'Sending %s/%s hosts to the inventory service.' % (count, total_hosts),
                            account_number=self.account_number,
                            report_platform_id=self.report_platform_id))
                    try:
                        await asyncio.wait(send_futures, timeout=HOSTS_UPLOAD_TIMEOUT)
                        future_index = 0
                        for future_res in send_futures:
                            if future_res.exception():
                                LOG.error(
                                    'An exception occurred %s when trying to upload '
                                    'the following message: %s',
                                    future_res.exception(),
                                    associated_msg[future_index])
                            future_index += 1
                    except Exception as error:  # pylint: disable=broad-except
                        LOG.error('An exception occurred: %s', error)
                    send_futures = []
        except Exception as err:  # pylint: disable=broad-except
            LOG.error(format_message(
                self.prefix, 'The following error occurred: %s' % err))
            KAFKA_ERRORS.inc()
            self.should_run = False
            print_error_loop_event()
            raise KafkaMsgHandlerError(
                format_message(
                    self.prefix,
                    'The following exception occurred: %s' % err,
                    account_number=self.account_number,
                    report_platform_id=self.report_platform_id))
        finally:
            await self.producer.stop()
