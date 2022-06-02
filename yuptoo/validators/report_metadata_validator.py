import json
import logging
from yuptoo.lib.config import MAX_HOSTS_PER_REP
from yuptoo.lib.exceptions import FailExtractException

LOG = logging.getLogger(__name__)


def validate_metadata_file(tar, metadata, request_obj):
    """Validate the contents of the metadata file.
    :param tar: the tarfile object.
    :param metadata: metadata file object.
    :returns: report_slice_ids
    """

    LOG.info(f"Attempting to decode the file {metadata.name}")
    metadata_file = tar.extractfile(metadata)
    try:
        metadata_str = metadata_file.read().decode('utf-8')
    except UnicodeDecodeError as error:
        LOG.error(
            f"Attempting to decode the file {metadata_file.name} "
            f"the following error occured: {error}. Discarding file."
        )
        return {}

    LOG.info(f"Successfully decoded the file {metadata.name}")
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
        raise FailExtractException(f"Metadata is missing required fields: {missing_keys_str}")

    request_obj['report_platform_id'] = metadata_json.get('report_id')
    # we should save the above information into the report object
    request_obj['source'] = metadata_json.get('source')
    source_metadata = metadata_json.get('source_metadata')
    # if source_metadata exists, we should log it
    if source_metadata:
        LOG.info(f"The following source metadata was uploaded: {source_metadata}")
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
            LOG.warning(
                f"Report {report_slice_id} has {str(num_hosts)} hosts. "
                f"There must be no more than {str(MAX_HOSTS_PER_REP)} hosts per report."
            )

    return valid_slice_ids
