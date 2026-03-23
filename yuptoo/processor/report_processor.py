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
    import time
    slice_start_time = time.time()

    status = FAILURE_CONFIRM_STATUS
    slice_id = report_slice.get('report_slice_id')
    LOG.info(f"Processing hosts in slice with id - {slice_id}")
    hosts = report_slice.get('hosts', [])
    num_hosts = len(hosts)
    request_obj['total_host_count'] += num_hosts
    LOG.info(f"Slice {slice_id} contains {num_hosts} hosts")

    host_loop_start = time.time()
    for host_idx, host in enumerate(hosts):
        host_start_time = time.time()

        yupana_host_id = str(uuid.uuid4())
        host['yupana_host_id'] = yupana_host_id
        if has_canonical_facts(host):
            host['report_slice_id'] = report_slice.get('report_slice_id')
            request_obj['candidate_hosts'] += 1
            # Run modifier below
            transformed_obj = {'removed': [], 'modified': [], 'missing_data': []}
            if HOSTS_TRANSFORMATION_ENABLED:
                modifiers_start = time.time()
                from yuptoo.modifiers import get_modifiers
                for modifier in get_modifiers():
                    i = importlib.import_module('yuptoo.modifiers.' + modifier)
                    for m in inspect.getmembers(i, inspect.isclass):
                        if m[1].__module__ == i.__name__:
                            m[1]().run(host, transformed_obj, request_obj=request_obj)
                modifiers_elapsed = time.time() - modifiers_start
                if modifiers_elapsed > 1.0:  # Log if modifiers take >1 second
                    LOG.warning(f"Modifiers took {modifiers_elapsed:.2f}s for host {host_idx+1}/{num_hosts}")

            # We will need to contact storage broker team and confirm below behaviour.
            status = SUCCESS_CONFIRM_STATUS
            validation_message = {
                'hash': request_obj['request_id'],
                'request_id': request_obj['request_id'],
                'validation': status
            }

            # Time Kafka operations separately
            kafka_start = time.time()
            send_message(VALIDATION_TOPIC, validation_message)
            validation_elapsed = time.time() - kafka_start

            print_transformed_info(request_obj, host['yupana_host_id'], transformed_obj)

            upload_start = time.time()
            upload_to_host_inventory_via_kafka(host, request_obj)
            upload_elapsed = time.time() - upload_start

            # Log if Kafka operations are slow
            if validation_elapsed > 0.5:
                LOG.warning(f"Validation message send took {validation_elapsed:.2f}s for host {host_idx+1}/{num_hosts}")
            if upload_elapsed > 0.5:
                LOG.warning(f"Upload message send took {upload_elapsed:.2f}s for host {host_idx+1}/{num_hosts}")
        else:
            request_obj['hosts_without_facts'].append({report_slice.get('report_slice_id'): host['fqdn']})
            host_upload_failures.inc()

        # Log progress every 100 hosts
        if (host_idx + 1) % 100 == 0:
            elapsed_so_far = time.time() - host_loop_start
            avg_per_host = elapsed_so_far / (host_idx + 1)
            remaining = num_hosts - (host_idx + 1)
            eta_seconds = avg_per_host * remaining
            LOG.info(f"Slice {slice_id} progress: {host_idx+1}/{num_hosts} hosts "
                    f"({elapsed_so_far:.1f}s elapsed, {avg_per_host:.3f}s/host, "
                    f"ETA: {eta_seconds:.0f}s)")

    # Log slice completion summary
    slice_total_time = time.time() - slice_start_time
    avg_per_host = slice_total_time / num_hosts if num_hosts > 0 else 0
    LOG.info(f"Completed slice {slice_id}: {num_hosts} hosts in {slice_total_time:.2f}s "
            f"(avg {avg_per_host:.3f}s/host)")

    # Log warning if slice took too long
    if slice_total_time > 600:  # 10 minutes
        LOG.warning(f"PERFORMANCE WARNING: Slice {slice_id} took {slice_total_time/60:.1f} minutes to process! "
                   f"This may cause Kafka consumer timeout.")


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
        send_message(UPLOAD_TOPIC, upload_msg, request_obj)
    except Exception as err:
        LOG.error(f"The following error occurred: {err}")


def process_report(consumed_message, request_obj):
    """Extract, Validate and Process report"""
    import time
    report_start_time = time.time()

    request_obj.update({
        "candidate_hosts": 0,
        "hosts_without_facts": [],
        "total_host_count": 0,
        "host_inventory_upload_count": 0
    })

    # Time the download
    download_start = time.time()
    report_tar = download_report(consumed_message)
    download_time = time.time() - download_start
    LOG.info(f"Download completed in {download_time:.2f}s, size: {len(report_tar)/1024/1024:.2f} MB")

    send_message(
        TRACKER_TOPIC,
        tracker_message(request_obj, "processing", "Report Downloaded")
    )

    try:  # pylint: disable=too-many-nested-blocks
        # Time tar extraction
        extract_start = time.time()
        tar = tarfile.open(fileobj=BytesIO(report_tar), mode='r:*')
        extract_time = time.time() - extract_start
        LOG.info(f"Tar extraction completed in {extract_time:.2f}s")
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

                # Time the producer flush
                flush_start = time.time()
                from yuptoo.lib.produce import producer
                producer.flush()
                flush_time = time.time() - flush_start
                LOG.info(f"Producer flush completed in {flush_time:.2f}s")

                # Log total report processing time
                total_time = time.time() - report_start_time
                LOG.info(f"Total report processing time: {total_time:.2f}s ({total_time/60:.1f} min)")

                log_report_summary(request_obj)
            except ValueError as error:
                raise FailExtractException(
                    f"Report is not valid JSON. Error: {str(error)}"
                )
    except tarfile.ReadError as err:
        raise FailExtractException(
            f"Unexpected error reading tar file: {str(err),}")
