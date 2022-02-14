import uuid
import json
from yuptoo.config.base import get_logger
from .exceptions import FailExtractException, QPCReportException
from yuptoo.config.base import MAX_HOSTS_PER_REP


LOG = get_logger(__name__)
CANONICAL_FACTS = ['insights_client_id', 'bios_uuid', 'ip_addresses', 'mac_addresses',
                   'vm_uuid', 'etc_machine_id', 'subscription_manager_id']


class ReportValidator:
    def __init__(self):
        pass

    def validate_metadata_file(self, tar, metadata):
        """Validate the contents of the metadata file.
        :param tar: the tarfile object.
        :param metadata: metadata file object.
        :returns: report_slice_ids
        """

        prefix = 'VALIDATE METADATA FILE'

        LOG.info(
            '%s - Attempting to decode the file %s for account=%s.',
            prefix, metadata.name, self.account
        )
        metadata_file = tar.extractfile(metadata)
        decode_error_message = '%s - Attempting to decode the file %s' \
            ' for account=%s resulted in' \
            'the following error: %s. Discarding file.',
        try:
            metadata_str = metadata_file.read().decode('utf-8')
        except UnicodeDecodeError as error:
            LOG.exception(
                decode_error_message,
                prefix, metadata_file.name, error, self.account
            )
            return {}

        LOG.info(
            '%s - Successfully decoded the file %s for account=%s.',
            prefix, metadata.name, self.account)
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
                '%s - Metadata is missing required fields: %s for account=%s and report_platform_id=%s.',
                prefix, missing_keys_str, self.account, self.report_platform_id)

        self.report_platform_id = metadata_json.get('report_id')
        host_inventory_api_version = metadata_json.get('host_inventory_api_version')
        self.source = metadata_json.get('source', '')
        # we should save the above information into the report object
        options = {
            'report_platform_id': self.report_platform_id,
            'host_inventory_api_version': host_inventory_api_version,
            'source': self.source
        }
        print("HELLO FROM VALIDATE METADATA FILE....................")
        print(options)

        self.source_metadata = metadata_json.get('source_metadata')
        # if source_metadata exists, we should log it
        if self.source_metadata:
            LOG.info(
                '%s - The following source metadata was uploaded: %s for account=%s and report_platform_id=%s.',
                prefix, self.source_metadata, self.account, self.report_platform_id
            )
            options['source_metadata'] = self.source_metadata
        # self.update_object_state(options)
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
                large_slice_message = '%s - Report %s has %s hosts. '\
                    'There must be no more than %s hosts per'\
                    ' report.'
                LOG.warning(
                    large_slice_message,
                    prefix, report_slice_id, str(num_hosts), str(MAX_HOSTS_PER_REP),
                    self.account, self.report_platform_id)

        return valid_slice_ids, options

    # def validate_report_details(self): returns candidate hosts
    def validate_report_details(self):  # pylint: disable=too-many-locals
        """
        Verify that the report contents are a valid Insights report.
        :returns: tuple contain list of valid and invalid hosts
        """
        prefix = 'VALIDATE REPORT STRUCTURE'
        required_keys = ['report_slice_id',
                         'hosts']

        missing_keys = []
        for key in required_keys:
            required_key = self.report_json.get(key)
            if not required_key:
                missing_keys.append(key)

        if missing_keys:
            missing_keys_str = ', '.join(missing_keys)
            raise QPCReportException(
                '%s - Report is missing required fields: %s for account=%s and report_platform_id=%s.',
                prefix, missing_keys_str, self.account, self.report_platform_id)

        # validate that hosts is an array
        invalid_hosts_message = \
            '%s - Hosts must be a list of dictionaries, account=%s '\
            'and report_platform_id=%s. Source metadata: %s'
        hosts = self.report_json.get('hosts')
        if not hosts or not isinstance(hosts, list):
            LOG.error(invalid_hosts_message, prefix, self.account,
                      self.report_platform_id, self.source_metadata)
            raise QPCReportException()
        invalid_hosts_count = 0
        for host in hosts:
            if not isinstance(host, dict):
                invalid_hosts_count += 1
        if invalid_hosts_count > 0:
            hosts_count_message = \
                '%s invalid host(s) found. '
            invalid_hosts_message = invalid_hosts_message + hosts_count_message
            LOG.error(
                invalid_hosts_message, prefix, self.account, self.report_platform_id,
                self.source_metadata, invalid_hosts_count)
            raise QPCReportException()
        print(";;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;")
        print("Calling validate_hosts method")
        report_slice_id = self.report_json.get('report_slice_id')
        candidate_hosts, hosts_without_facts = \
            self.validate_report_hosts(report_slice_id)

        total_fingerprints = len(candidate_hosts)
        total_valid = total_fingerprints - len(hosts_without_facts)
        LOG.info(
            '%s/%s hosts are valid for account=%s and report_platform_id=%s.',
            total_valid, total_fingerprints, self.account, self.report_platform_id
        )
        if not candidate_hosts:
            LOG.error(
                'Report does not contain any valid hosts for account=%s and report_platform_id=%s.',
                self.account, self.report_platform_id)
            raise QPCReportException()
        return candidate_hosts

    # if candidate hosts: self.status=true else false

    def validate_report_hosts(self, report_slice_id):
        """Verify that report hosts contain canonical facts.
        :returns: tuple containing valid & invalid hosts
        """
        hosts = self.report_json.get('hosts', [])

        prefix = 'VALIDATE HOSTS'
        candidate_hosts = []
        hosts_without_facts = []
        for host in hosts:
            host_uuid = str(uuid.uuid4())
            host['account'] = self.account
            host_facts = host.get('facts', [])
            host_facts.append({'namespace': 'yupana',
                               'facts': {'yupana_host_id': host_uuid,
                                         'report_platform_id': str(self.report_platform_id),
                                         'report_slice_id': str(report_slice_id),
                                         'account': self.account,
                                         'source': self.source}})
            host['stale_timestamp'] = self.get_stale_time()
            host['reporter'] = 'yupana'
            host['facts'] = host_facts
            found_facts = False
            for fact in CANONICAL_FACTS:
                if host.get(fact):
                    found_facts = True
                    break
            if not found_facts:
                hosts_without_facts.append({host_uuid: host})
            candidate_hosts.append({host_uuid: host})
        if hosts_without_facts:
            invalid_hosts_message = \
                '%s - %d host(s) found that contain(s) 0 canonical facts: %s.'\
                'Source metadata: %s'
            LOG.warning(
                invalid_hosts_message, prefix, len(hosts_without_facts),
                hosts_without_facts, self.source_metadata, self.account,
                self.report_platform_id)

        return candidate_hosts, hosts_without_facts
