import json
import requests
import tarfile
import pytz
from io import BytesIO
from confluent_kafka import Producer, KafkaException
from yuptoo.config.base import (
    get_logger, INSIGHTS_KAFKA_ADDRESS, QPC_TOPIC, GROUP_ID, MAX_HOSTS_PER_REP, VALIDATION_TOPIC
)
from .exceptions import QPCReportException, FailDownloadException, FailExtractException


LOG = get_logger(__name__)


class ReportProcessor:
    def __init__(self):
        pass

    def pass_message_to_report_processor(self, consumed_message):
        print("Hello!! I came to Report Processor!!")
        print("**************************************************")
        print(consumed_message)
        """
        Connecting consumer with processor.
        """
        print("I am doing good!!!")
        request_id = consumed_message.get('request_id')
        print(request_id)
        report_tar = self.download_report(consumed_message)
        print("Report Tar.......................")
        options = self.extract_and_create_slices(report_tar)

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
                                    self.prefix,
                                    'Attempting to decode the file %s' % file.name,
                                    account_number=self.account_number,
                                    report_platform_id=self.report_platform_id)
                                try:
                                    report_slice_string = report_slice.read().decode('utf-8')
                                except UnicodeDecodeError as error:
                                    decode_error_message = 'Attempting to decode the file'\
                                        ' %s resulted in the following error: %s. '\
                                        'Discarding file.' % (file.name, error)
                                    LOG.exception(
                                        self.prefix, decode_error_message,
                                        account_number=self.account_number,
                                        report_platform_id=self.report_platform_id
                                    )
                                    continue
                                LOG.info(
                                    self.prefix,
                                    'Successfully decoded the file %s' % file.name,
                                    account_number=self.account_number,
                                    report_platform_id=self.report_platform_id)

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
                                    mismatch_message += 'Metadata must match report slice data. '\
                                        'Discarding the report slice as invalid. '
                                    LOG.warning(
                                        self.prefix, mismatch_message,
                                        account_number=self.account_number,
                                        report_platform_id=self.report_platform_id)
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
                            self.prefix,
                            'Report contained no valid report slices.',
                            account_number=self.account_number)
                    LOG.info(
                        self.prefix,
                        'successfully extracted & created report slices',
                        account_number=self.account_number,
                        report_platform_id=self.report_platform_id)
                    return options

                except ValueError as error:
                    raise FailExtractException(
                        self.prefix,
                        'Report is not valid JSON. Error: %s' % str(error),
                        account_number=self.account_number)
            raise FailExtractException(
                self.prefix,
                'Tar does not contain valid JSON metadata & report files.',
                account_number=self.account_number)
        except FailExtractException as qpc_err:
            raise qpc_err
        except tarfile.ReadError as err:
            raise FailExtractException(
                self.prefix,
                'Unexpected error reading tar file: %s' % str(err),
                account_number=self.account_number)
        except Exception as err:
            LOG.error(
                self.prefix,
                'Unexpected error reading tar file: %s' % str(err),
                account_number=self.account_number)

    def create_report_slice(self, options):
        report_json = options.get('report_json')
        report_slice_id = options.get('report_slice_id')
        hosts_count = options.get('hosts_count')
        source = options.get('source')
        source_metadata = options.get('source_metadata')
        LOG.info(
            self.prefix, 'Creating report slice %s' % report_slice_id,
            account_number=self.account_number, report_platform_id=self.report_platform_id)

        # TODO first we should see if any slices exist with this slice id & report_platform_id
        # if they exist we will not create the slice

        report_slice = {
            'account': self.account_number,
            'last_update_time': datetime.now(pytz.utc),
            'report_json': json.dumps(report_json),
            'report_platform_id': self.report_platform_id,
            'report_slice_id': report_slice_id,
            'hosts_count': hosts_count,
            'source': source,
            'source_metadata': json.dumps(source_metadata),
            'creation_time': datetime.now(pytz.utc)
        }  # 'report': self.report_or_slice.id,
        LOG.info(
            self.prefix,
            'Successfully created report slice %s' % report_slice_id,
            account_number=self.account_number,
            report_platform_id=self.report_platform_id)
        return True

    # def deduplicate_reports() What to do if report with same id is retried to be uploaded.

    def validate_metadata_file(self, tar, metadata):
        """Validate the contents of the metadata file.
        :param tar: the tarfile object.
        :param metadata: metadata file object.
        :returns: report_slice_ids
        """
        LOG.info(
            self.prefix,
            'Attempting to decode the file %s' % metadata.name,
            account_number=self.account_number,
            report_platform_id=self.report_platform_id
        )
        metadata_file = tar.extractfile(metadata)
        try:
            metadata_str = metadata_file.read().decode('utf-8')
        except UnicodeDecodeError as error:
            decode_error_message = 'Attempting to decode the file'\
                ' %s resulted in the following error: %s. Discarding file.' % \
                (metadata_file.name, error)
            LOG.exception(
                self.prefix, decode_error_message,
                account_number=self.account_number,
                report_platform_id=self.report_platform_id
            )
            return {}

        LOG.info(
            self.prefix,
            'Successfully decoded the file %s' % metadata.name,
            account_number=self.account_number,
            report_platform_id=self.report_platform_id)
        metadata_json = json.loads(metadata_str)
        required_keys = ['report_id', 'host_inventory_api_version',
                         'source', 'report_slices']
        missing_keys = []
        for key in required_keys:
            required_key = metadata_json.get(key)
            if not required_key:
                missing_keys.append(key)

        if missing_keys:
            missing_keys_str = ', '.join(missing_keys)
            raise FailExtractException(
                self.prefix,
                'Metadata is missing required fields: %s.' % missing_keys_str,
                account_number=self.account_number,
                report_platform_id=self.report_platform_id)

        self.report_platform_id = metadata_json.get('report_id')
        host_inventory_api_version = metadata_json.get('host_inventory_api_version')
        source = metadata_json.get('source', '')
        # we should save the above information into the report object
        options = {
            'report_platform_id': self.report_platform_id,
            'host_inventory_api_version': host_inventory_api_version,
            'source': source
        }

        source_metadata = metadata_json.get('source_metadata')
        # if source_metadata exists, we should log it
        if source_metadata:
            LOG.info(
                self.prefix,
                'The following source metadata was uploaded: %s' % source_metadata,
                account_number=self.account_number,
                report_platform_id=self.report_platform_id
            )
            options['source_metadata'] = source_metadata
        self.update_object_state(options)
        invalid_slice_ids = {}
        valid_slice_ids = {}
        report_slices = metadata_json.get('report_slices', {})

        # we need to verify that the report slices have the appropriate number of hosts
        total_hosts_in_report = 0
        for report_slice_id, report_info in report_slices.items():
            num_hosts = int(report_info.get('number_hosts', MAX_HOSTS_PER_REP + 1))
            if num_hosts <= MAX_HOSTS_PER_REP:
                total_hosts_in_report += num_hosts
                valid_slice_ids[report_slice_id] = num_hosts
            else:
                invalid_slice_ids[report_slice_id] = num_hosts

        # if any reports were over the max number of hosts, we need to log
        if invalid_slice_ids:
            for report_slice_id, num_hosts in invalid_slice_ids.items():
                large_slice_message = 'Report %s has %s hosts. '\
                    'There must be no more than %s hosts per'\
                    ' report.' % \
                    (report_slice_id, str(num_hosts),
                     str(MAX_HOSTS_PER_REP))
                LOG.warning(
                    self.prefix, large_slice_message,
                    account_number=self.account_number,
                    report_platform_id=self.report_platform_id)

        return valid_slice_ids, options

    def send_confirmation(self, file_hash):
        self.prefix = 'REPORT VALIDATION STATE ON KAFKA'
        
        self.producer = Producer({
            'bootstrap.servers': INSIGHTS_KAFKA_ADDRESS,
        })
        try:
            self.producer.start()
        except (KafkaException, TimeoutError, Exception):
            raise KafkaMsgHandlerError(
                self.prefix,
                'Unable to connect to kafka server.',
                account_number=self.account_number,
                report_platform_id=self.report_platform_id)
        try:
            validation = {
                'hash': file_hash,
                'request_id': self.report_or_slice.request_id,
                'validation': self.status
            }
            msg = bytes(json.dumps(validation), 'utf-8')
            self.producer.produce(VALIDATION_TOPIC, msg)
            LOG.info(
                self.prefix,
                'Send %s validation status to file upload on kafka' % self.status,
                account_number=self.account_number,
                report_platform_id=self.report_platform_id)
        except Exception as err:  # pylint: disable=broad-except
            LOG.error(
                self.prefix, 'The following error occurred: %s' % err)

        finally:
            self.producer.stop()
