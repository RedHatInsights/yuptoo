import uuid
import importlib
import inspect
import tarfile
import json
import logging
from io import BytesIO
from confluent_kafka import KafkaException

from yuptoo.lib.config import (HOSTS_TRANSFORMATION_ENABLED,
                               UPLOAD_TOPIC, VALIDATION_TOPIC)
from yuptoo.lib.exceptions import FailExtractException, QPCReportException
from yuptoo.validators.report_metadata_validator import validate_metadata_file
from yuptoo.processor.utils import has_canonical_facts, print_transformed_info, download_report
from yuptoo.lib.metrics import report_extract_failures

LOG = logging.getLogger(__name__)

producer = None
SUCCESS_CONFIRM_STATUS = 'success'
FAILURE_CONFIRM_STATUS = 'failure'


def process_report(consumed_message, p, request_obj):
    global producer
    producer = p
    report_tar = download_report(consumed_message)
    report_json_files = extract_report_slices(report_tar, request_obj)

    status = FAILURE_CONFIRM_STATUS
    for report_slice in report_json_files:
        LOG.info(f"Processing hosts in slice with id - {report_slice.get('report_slice_id')}")
        hosts = report_slice.get('hosts', [])
        total_hosts = len(hosts)
        count = 0
        candidate_hosts = []
        hosts_without_facts = []
        for host in hosts:
            yupana_host_id = str(uuid.uuid4())
            host['yupana_host_id'] = yupana_host_id
            if has_canonical_facts(host):
                host['report_slice_id'] = report_slice.get('report_slice_id')
                candidate_hosts.append({yupana_host_id: host})
                # Run modifier below
                transformed_obj = {'removed': [], 'modified': [], 'missing_data': []}
                if HOSTS_TRANSFORMATION_ENABLED:
                    from yuptoo.modifiers import get_modifiers
                    for modifier in get_modifiers():
                        i = importlib.import_module('yuptoo.modifiers.' + modifier)
                        for m in inspect.getmembers(i, inspect.isclass):
                            if m[1].__module__ == i.__name__:
                                m[1]().run(host, transformed_obj, request_obj=request_obj)

                count += 1
                if candidate_hosts:
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
                hosts_without_facts.append({report_slice.get('report_slice_id'): host})

        total_fingerprints = len(candidate_hosts)
        total_valid = total_fingerprints - len(hosts_without_facts)
        LOG.info(f"{total_valid}/{total_fingerprints} hosts are valid.")
        LOG.info(f"{count}/{total_hosts} hosts has been send to the inventory service.")
        if hosts_without_facts:
            LOG.warning(
                f"{len(hosts_without_facts)} host(s) found that contain(s) 0 canonical facts:"
                f"{hosts_without_facts}."
            )
        if not candidate_hosts:
            LOG.error('Report does not contain any valid hosts.')
            raise QPCReportException()


def upload_to_host_inventory_via_kafka(host, request_obj):
    try:
        upload_msg = {
            'operation': 'add_host',
            'data': host,
            'platform_metadata': {'request_id': host['system_unique_id'],
                                  'b64_identity': request_obj['b64_identity']}
        }
        send_message(UPLOAD_TOPIC, upload_msg)

    except Exception as err:
        LOG.error(f"The following error occurred: {err}")


def delivery_report(err, msg=None):
    if err is not None:
        LOG.error(f"Message delivery for topic {msg.topic()} failed: {err}")
    else:
        LOG.debug(f"Message delivered to {msg.topic()} [{msg.partition()}]")


def send_message(kafka_topic, msg):
    try:
        bytes = json.dumps(msg, ensure_ascii=False).encode("utf-8")
        producer.produce(kafka_topic, bytes, callback=delivery_report)
        producer.poll(1)
    except KafkaException:
        LOG.error(f"Failed to produce message to [{UPLOAD_TOPIC}] topic.")


def extract_report_slices(report_tar, request_obj):
    """Extract Insights report from tar file and
    returns Insights report as dict"""

    try:  # pylint: disable=too-many-nested-blocks
        tar = tarfile.open(fileobj=BytesIO(report_tar), mode='r:*')
        files = tar.getmembers()
        json_files = []
        report_files = []
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

                            # Here performace can be improved by using Async thread
                            report_files.append(report_slice_json)
                return report_files
            except ValueError as error:
                raise FailExtractException(
                    f"Report is not valid JSON. Error: {str(error)}"
                )
        raise FailExtractException(
            'Tar does not contain valid JSON metadata & report files'
        )
    except FailExtractException as qpc_err:
        report_extract_failures.labels(
                    account_number=request_obj['account']
                ).inc()
        raise qpc_err
    except tarfile.ReadError as err:
        raise FailExtractException(
            f"Unexpected error reading tar file: {str(err),}")
    except Exception as err:
        report_extract_failures.labels(
                    account_number=request_obj['account']
                ).inc()
        LOG.error(
            f"Unexpected error reading tar file: {str(err)}",
        )
