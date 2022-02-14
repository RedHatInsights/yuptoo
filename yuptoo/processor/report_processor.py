import imp
import json
from os import stat
from xml.dom import VALIDATION_ERR
import requests
from datetime import datetime, timedelta
import tarfile
import uuid
import pytz
from io import BytesIO
from confluent_kafka import Producer, KafkaException
from yuptoo.config.base import (
    get_logger, INSIGHTS_KAFKA_ADDRESS, VALIDATION_TOPIC,
    DISCOVERY_HOST_TTL, SATELLITE_HOST_TTL
)
from .exceptions import FailDownloadException, FailExtractException
from yuptoo.processor.report_validator import ReportValidator
from yuptoo.processor.report_slice_processor import ReportSliceProcessor


LOG = get_logger(__name__)

CANONICAL_FACTS = ['insights_client_id', 'bios_uuid', 'ip_addresses', 'mac_addresses',
                   'vm_uuid', 'etc_machine_id', 'subscription_manager_id']

SUCCESS_CONFIRM_STATUS = 'success'
FAILURE_CONFIRM_STATUS = 'failure'


class ReportProcessor(ReportValidator):
    def __init__(self):
        pass

    def pass_message_to_report_processor(self, consumed_message):
        self.account = consumed_message.get('account')
        """
        Connecting consumer with processor.
        """
        self.request_id = consumed_message.get('request_id')
        report_tar = self.download_report(consumed_message)
        self.extract_and_create_slices(report_tar)

        self.status = FAILURE_CONFIRM_STATUS
        message_hash = self.request_id
        candidate_hosts = self.validate_report_details()
        if candidate_hosts:
            self.status = SUCCESS_CONFIRM_STATUS
        validation_message = {
            'hash': message_hash,
            'request_id': self.request_id,
            'validation': self.status
        }
        self.send_message(
            VALIDATION_TOPIC,
            validation_message
        )
        candidates = {}
        # we want to generate a dictionary of just the id mapped to the data
        # so we iterate the list creating a dictionary of the key: value if
        # the key is not 'cause' or 'status_code'

        candidates = {key: host[key] for host in candidate_hosts
                      for key in host.keys() if key not in ['cause', 'status_code']}

        ReportSliceProcessor().upload_to_host_inventory_via_kafka(candidates)

    def download_report(self, consumed_message):
        """
        Download report. Returns the tar binary content or None if there are errors.
        """
        prefix = 'REPORT DOWNLOAD'
        try:
            report_url = consumed_message.get('url', None)
            if not report_url:
                raise FailDownloadException(
                    '%s - Kafka message has no report url.  Message: %s', 
                    prefix, consumed_message)

            LOG.info(
                '%s - Downloading Report from %s for account=%s.',
                prefix, report_url, consumed_message.get('account'))

            download_response = requests.get(report_url)

            LOG.info(
                '%s - Successfully downloaded TAR from %s for account=%s.',
                prefix, report_url, consumed_message.get('account')
            )
            return download_response.content

        except FailDownloadException as fail_err:
            raise fail_err

        except Exception as err:
            raise FailDownloadException(
                '%s - Unexpected error for URL %s. Error: %s',
                prefix, report_url, err,
                consumed_message.get('account'))

    def extract_and_create_slices(self, report_tar):
        """Extract Insights report from tar file and
        returns Insights report as dict"""

        prefix = 'EXTRACT REPORT FROM TAR'

        try:  # pylint: disable=too-many-nested-blocks
            tar = tarfile.open(fileobj=BytesIO(report_tar), mode='r:*')
            files = tar.getmembers()
            json_files = []
            metadata_file = None
            for file in files:
                # First we need to Find the metadata file
                if '/metadata.json' in file.name or file.name == 'metadata.json':
                    metadata_file = file
                # Next we want to add all .json files to our list
                elif '.json' in file.name:
                    json_files.append(file)
            if json_files and metadata_file:
                try:
                    valid_slice_ids, options = self.validate_metadata_file(tar, metadata_file)
                    report_names = []
                    for report_id, num_hosts in valid_slice_ids.items():
                        for file in json_files:
                            if report_id in file.name:
                                matches_metadata = True
                                mismatch_message = ''
                                report_slice = tar.extractfile(file)
                                LOG.info(
                                    '%s - Attempting to decode the file %s for account=%s and report_platform_id=%s.',
                                    prefix, file.name, self.account, self.report_platform_id)
                                try:
                                    report_slice_string = report_slice.read().decode('utf-8')
                                except UnicodeDecodeError as error:
                                    decode_error_message = '%s - Attempting to decode the file'\
                                        ' %s resulted in the following error: %s '\
                                        'for account=%s and report_platform_id=%s. Discarding file.'
                                    LOG.exception(
                                        decode_error_message,
                                        prefix, file.name, error, self.account, self.report_platform_id
                                    )
                                    continue
                                LOG.info(
                                    '%s - Successfully decoded the file %s for account=%s and report_platform_id=%s.',
                                    prefix, file.name, self.account, self.report_platform_id)
                                # `loads` caused errros earlier. any alternative?
                                # check if json library is python-based or c-based
                                # performance issue
                                report_slice_json = json.loads(report_slice_string)
                                report_slice_id = report_slice_json.get('report_slice_id', '')
                                if report_slice_id != report_id:
                                    matches_metadata = False
                                    invalid_report_id = 'Metadata & filename reported the '\
                                        '"report_slice_id" as %s but the "report_slice_id" '\
                                        'inside the JSON has a value of %s. ' % \
                                        (report_id, report_slice_id)
                                    mismatch_message += invalid_report_id
                                hosts = report_slice_json.get('hosts', {})
                                if len(hosts) != num_hosts:
                                    matches_metadata = False
                                    invalid_hosts = 'Metadata for report slice'\
                                        ' %s reported %d hosts '\
                                        'but report contains %d hosts. ' % \
                                        (report_slice_id, num_hosts, len(hosts))
                                    mismatch_message += invalid_hosts
                                if not matches_metadata:
                                    mismatch_message += '%s - Metadata must match report slice data. '\
                                        'Discarding the report slice as invalid for account=%s '\
                                        'and report_platform_id=%s.'
                                    LOG.warning(
                                        prefix, mismatch_message, self.account, self.report_platform_id)
                                    continue

                                slice_options = {
                                    'report_json': report_slice_json,
                                    'report_slice_id': report_slice_id,
                                    'hosts_count': num_hosts,
                                    'source': options.get('source'),
                                    'source_metadata': options.get('source_metadata', {})
                                }
                                created = self.create_report_slice(
                                    slice_options)
                                if created:
                                    report_names.append(report_id)

                    if not report_names:
                        raise FailExtractException(
                            '%s - Report contained no valid report slices for account=%s.',
                            prefix, self.account)
                    LOG.info(
                        '%s - Successfully extracted & created report slices for account=%s '\
                        'and report_platform_id=%s.',
                        prefix, self.account, self.report_platform_id)
                    return options

                except ValueError as error:
                    raise FailExtractException(
                        '%s - Report is not valid JSON. Error: %s',
                        prefix, str(error), self.account)
            raise FailExtractException(
                '%s - Tar does not contain valid JSON metadata & report files for account=%s.',
                prefix, self.account)
        except FailExtractException as qpc_err:
            raise qpc_err
        except tarfile.ReadError as err:
            raise FailExtractException(
                '%s - Unexpected error reading tar file: %s for account=%s.',
                prefix, str(err), self.account)
        except Exception as err:
            LOG.error(
                '%s - Unexpected error reading tar file: %s for account=%s.',
                prefix, str(err), self.account)

    def create_report_slice(self, options):
        prefix = 'CREATE REPORT SLICE'

        self.report_json = options.get('report_json')
        report_slice_id = options.get('report_slice_id')
        hosts_count = options.get('hosts_count')
        self.source = options.get('source')
        self.source_metadata = options.get('source_metadata')
        LOG.info(
            '%s - Creating report slice %s for account=%s and report_platform_id=%s',
            prefix, report_slice_id, self.account, self.report_platform_id)

        report_slice = {
            'account': self.account,
            'last_update_time': datetime.now(pytz.utc),
            'report_json': json.dumps(self.report_json),  # corresponding dumps
            'report_platform_id': self.report_platform_id,
            'report_slice_id': report_slice_id,
            'hosts_count': hosts_count,
            'source': self.source,
            'source_metadata': json.dumps(self.source_metadata),
            'creation_time': datetime.now(pytz.utc)
        }
        LOG.info(
            '%s - Successfully created report slice %s for account=%s and report_platform_id=%s.',
            prefix, report_slice_id, self.account, self.report_platform_id)
        return True

    # def deduplicate_reports() What to do if report with same id is retried to be uploaded.

    def get_stale_time(self):
        """Compute the stale date based on the host source."""

        ttl = int(DISCOVERY_HOST_TTL)
        if self.source == 'satellite':
            ttl = int(SATELLITE_HOST_TTL)
        current_time = datetime.utcnow()
        stale_time = current_time + timedelta(hours=ttl)

        return stale_time.strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z'

    def delivery_report(self, err, msg=None):
        prefix = 'REPORT VALIDATION STATE ON KAFKA'

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
            })

            bytes = json.dumps(msg, ensure_ascii=False).encode("utf-8")

            self.producer.produce(topic, bytes, callback=self.delivery_report)
            # currently, this msg is successfully going to the validation topic,
            # but, callback `delivery_report` is not getting invoked.
            self.producer.poll(1)
        except KafkaException:
            LOG.exception(
                "Failed to produce message to [%s] topic: %s", topic, self.request_id
            )
