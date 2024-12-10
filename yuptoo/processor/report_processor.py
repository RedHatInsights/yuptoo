import uuid
import importlib
import inspect
import tarfile
import json
import logging
from io import BytesIO


from yuptoo.lib.config import (HOSTS_TRANSFORMATION_ENABLED,
                               UPLOAD_TOPIC, VALIDATION_TOPIC, TRACKER_TOPIC)
from yuptoo.lib.exceptions import FailExtractException, QPCReportException
from yuptoo.validators.report_metadata_validator import validate_metadata_file
from yuptoo.processor.utils import (has_canonical_facts, print_transformed_info,
                                    download_report, tracker_message)
from yuptoo.lib.metrics import host_upload_failures
from yuptoo.lib.produce import send_message

LOG = logging.getLogger(__name__)

SUCCESS_CONFIRM_STATUS = 'success'
FAILURE_CONFIRM_STATUS = 'failure'


def process_report_slice(report_slice, request_obj):
    """
    Run all the modifiers on report slice and send modified host
    to host-inventory
    Args:
        report_slice (dict): Contains hosts array
        request_obj (dict): Object containing metadata of incoming request/report
    """
    status = FAILURE_CONFIRM_STATUS
    LOG.info(f"Processing hosts in slice with id - {report_slice.get('report_slice_id')}")
    hosts = report_slice.get('hosts', [])
    request_obj['total_host_count'] += len(hosts)
    for host in hosts:
        yupana_host_id = str(uuid.uuid4())
        host['yupana_host_id'] = yupana_host_id
        if has_canonical_facts(host):
            host['report_slice_id'] = report_slice.get('report_slice_id')
            request_obj['candidate_hosts'] += 1
            # Run modifier below
            transformed_obj = {'removed': [], 'modified': [], 'missing_data': []}
            if HOSTS_TRANSFORMATION_ENABLED:
                from yuptoo.modifiers import get_modifiers
                for modifier in get_modifiers():
                    i = importlib.import_module('yuptoo.modifiers.' + modifier)
                    for m in inspect.getmembers(i, inspect.isclass):
                        if m[1].__module__ == i.__name__:
                            m[1]().run(host, transformed_obj, request_obj=request_obj)

            # We will need to contact storage broker team and confirm below behaviour.
            status = SUCCESS_CONFIRM_STATUS
            validation_message = {
                'hash': request_obj['request_id'],
                'request_id': request_obj['request_id'],
                'validation': status
            }
            send_message(VALIDATION_TOPIC, validation_message)
            print_transformed_info(request_obj, host['yupana_host_id'], transformed_obj)
            upload_to_host_inventory_via_kafka(host, request_obj)
        else:
            request_obj['hosts_without_facts'].append({report_slice.get('report_slice_id'): host['fqdn']})
            host_upload_failures.inc()


def log_report_summary(request_obj):
    total_fingerprints = request_obj['candidate_hosts']
    total_valid = total_fingerprints - len(request_obj['hosts_without_facts'])
    LOG.info(f"{total_valid}/{total_fingerprints} hosts are valid.")
    host_upload_msg = f"{request_obj['host_inventory_upload_count']}/{request_obj['total_host_count']}" \
                      " hosts has been send to the inventory service."
    LOG.info(host_upload_msg)
    if request_obj['hosts_without_facts']:
        LOG.warning(
            f"{len(request_obj['hosts_without_facts'])} host(s) found that contain(s) 0 canonical facts:"
            f"{request_obj['hosts_without_facts']}."
        )
    if total_fingerprints == 0:
        LOG.error('Report does not contain any valid hosts.')
        raise QPCReportException()
    send_message(
        TRACKER_TOPIC,
        tracker_message(request_obj, "success", host_upload_msg)
    )


def upload_to_host_inventory_via_kafka(host, request_obj):
    try:
        upload_msg = {
            'operation': 'add_host',
            'data': host,
            'platform_metadata': {'request_id': host['system_unique_id'],
                                  'b64_identity': request_obj['b64_identity']}
        }
        send_message(UPLOAD_TOPIC, upload_msg, host.org_id, request_obj)
    except Exception as err:
        LOG.error(f"The following error occurred: {err}")


def process_report(consumed_message, request_obj):
    """Extract, Validate and Process report"""
    request_obj.update({
        "candidate_hosts": 0,
        "hosts_without_facts": [],
        "total_host_count": 0,
        "host_inventory_upload_count": 0
    })
    report_tar = download_report(consumed_message)
    send_message(
        TRACKER_TOPIC,
        tracker_message(request_obj, "processing", "Report Downloaded")
    )
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
                valid_slice_ids = validate_metadata_file(tar, metadata_file, request_obj)
                for report_id, num_hosts in valid_slice_ids.items():
                    for file in json_files:
                        if report_id in file.name:
                            matches_metadata = True
                            mismatch_message = ''
                            report_slice = tar.extractfile(file)
                            LOG.info(f"Attempting to decode the file {file.name}")
                            try:
                                report_slice_string = report_slice.read().decode('utf-8')
                            except UnicodeDecodeError as error:
                                LOG.error(
                                    f"Attempting to decode the file {file.name} "
                                    f"resulted in the following error: {error}. "
                                    "Discarding file."
                                )
                                continue
                            LOG.info(f"Successfully decoded the file {file.name}")
                            report_slice_json = json.loads(report_slice_string)
                            report_slice_id = report_slice_json.get('report_slice_id', '')
                            if report_slice_id != report_id:
                                matches_metadata = False
                                invalid_report_id = "Metadata & filename reported the "\
                                    f"'report_slice_id' as {report_id} but the 'report_slice_id' "\
                                    f"inside the JSON has a value of {report_slice_id}. "
                                mismatch_message += invalid_report_id
                            hosts = report_slice_json.get('hosts', {})

                            if len(hosts) != num_hosts:
                                matches_metadata = False
                                invalid_hosts = 'Metadata for report slice'\
                                    f" {report_slice_id} reported {num_hosts} hosts "\
                                    f"but report contains {len(hosts)} hosts. "
                                mismatch_message += invalid_hosts
                            if not matches_metadata:
                                mismatch_message += 'Metadata must match report slice data. '\
                                    'Discarding the report slice as invalid.'
                                LOG.warning(mismatch_message)
                                continue

                            # FIXME - performance can be improved by using Async thread
                            process_report_slice(report_slice_json, request_obj)

                from yuptoo.lib.produce import producer
                producer.flush()
                log_report_summary(request_obj)
            except ValueError as error:
                raise FailExtractException(
                    f"Report is not valid JSON. Error: {str(error)}"
                )
    except tarfile.ReadError as err:
        raise FailExtractException(
            f"Unexpected error reading tar file: {str(err),}")
