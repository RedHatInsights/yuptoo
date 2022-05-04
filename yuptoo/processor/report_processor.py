import uuid
import importlib
import inspect
import tarfile
import json
from functools import partial
from io import BytesIO
from confluent_kafka import KafkaException

from yuptoo.lib.config import (get_logger, HOSTS_TRANSFORMATION_ENABLED,
                               UPLOAD_TOPIC, HOSTS_UPLOAD_FUTURES_COUNT,
                               VALIDATION_TOPIC)
from yuptoo.lib.exceptions import FailExtractException, QPCReportException, KafkaMsgHandlerError
from yuptoo.validators.report_metadata_validator import validate_metadata_file
from yuptoo.processor.utils import has_canonical_facts, print_transformed_info, download_report

LOG = get_logger(__name__)

producer = None
SUCCESS_CONFIRM_STATUS = 'success'
FAILURE_CONFIRM_STATUS = 'failure'


def process_report(consumed_message, p):
    global producer
    producer = p
    request_obj = {}
    prefix = 'PROCESS REPORT'
    request_obj['account'] = consumed_message.get('account')
    request_obj['b64_identity'] = consumed_message.get('b64_identity')
    request_obj['request_id'] = consumed_message.get('request_id')
    report_tar = download_report(consumed_message)
    report_json_files = extract_report_slices(report_tar, request_obj)

    status = FAILURE_CONFIRM_STATUS
    for report_slice in report_json_files:
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
                send_message(VALIDATION_TOPIC, validation_message, request_obj['request_id'])
                print_transformed_info(request_obj, host['yupana_host_id'], transformed_obj)
                upload_to_host_inventory_via_kafka(host, request_obj)
                if count % HOSTS_UPLOAD_FUTURES_COUNT == 0 or count == total_hosts:
                    LOG.info(
                        '%s - Sending %s/%s hosts to the inventory service for account=%s and report_platform_id=%s.',
                        prefix, count, total_hosts, request_obj['account'], request_obj['report_platform_id'])
            else:
                hosts_without_facts.append({report_slice.get('report_slice_id'): host})

        if hosts_without_facts:
            invalid_hosts_message = \
                '%s - %d host(s) found that contain(s) 0 canonical facts: %s.'
            LOG.warning(
                invalid_hosts_message, prefix, len(hosts_without_facts),
                hosts_without_facts)

        total_fingerprints = len(candidate_hosts)
        total_valid = total_fingerprints - len(hosts_without_facts)
        LOG.info(
            '%s/%s hosts are valid for account=%s and report_platform_id=%s.',
            total_valid, total_fingerprints, request_obj['account'], request_obj['request_id']
        )
        if not candidate_hosts:
            LOG.error(
                'Report does not contain any valid hosts for account=%s and report_platform_id=%s.',
                request_obj['account'], request_obj['request_id'])
            raise QPCReportException()


def upload_to_host_inventory_via_kafka(host, request_obj):
    prefix = 'UPLOAD TO INVENTORY VIA KAFKA'
    try:  # pylint: disable=too-many-nested-blocks
        upload_msg = {
            'operation': 'add_host',
            'data': host,
            'platform_metadata': {'request_id': host['system_unique_id'],
                                  'b64_identity': request_obj['b64_identity']}
        }
        send_message(UPLOAD_TOPIC, upload_msg, request_obj['request_id'])

    except Exception as err:  # pylint: disable=broad-except
        LOG.error(
            '%s - The following error occurred: %s',
            prefix, err)
        raise KafkaMsgHandlerError(
            '%s - The following exception occurred: %s for account=%s and report_platform_id=%s.',
            prefix, err, host['account'], request_obj['report_platform_id'])


def delivery_report(err, msg=None, request_id=None):
    prefix = 'PUBLISH TO INVENTORY TOPIC ON KAFKA'

    if err is not None:
        LOG.error(
            "Message delivery for topic %s failed for request_id [%s]: %s",
            msg.topic(),
            err,
            request_id,
        )
    else:
        LOG.info(
            "%s - Message delivered to %s [%s] for request_id [%s]",
            prefix,
            msg.topic(),
            msg.partition(),
            request_id
        )


def send_message(kafka_topic, msg, request_id):
    try:
        bytes = json.dumps(msg, ensure_ascii=False).encode("utf-8")
        producer.produce(kafka_topic, bytes, callback=partial(delivery_report, request_id=request_id))
        producer.poll(1)
    except KafkaException:
        LOG.exception(
            "Failed to produce message to [%s] topic: %s", UPLOAD_TOPIC, request_id
        )


def extract_report_slices(report_tar, request_obj):
    """Extract Insights report from tar file and
    returns Insights report as dict"""

    prefix = 'EXTRACT REPORT FROM TAR'

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
                            LOG.info(
                                '%s - Attempting to decode the file %s for account=%s and report_platform_id=%s.',
                                prefix, file.name, request_obj['account'], request_obj['request_id'])
                            try:
                                report_slice_string = report_slice.read().decode('utf-8')
                            except UnicodeDecodeError as error:
                                decode_error_message = '%s - Attempting to decode the file'\
                                    ' %s resulted in the following error: %s '\
                                    'for account=%s and report_platform_id=%s. Discarding file.'
                                LOG.exception(
                                    decode_error_message,
                                    prefix, file.name, error, request_obj['account'], request_obj['request_id']
                                )
                                continue
                            LOG.info(
                                '%s - Successfully decoded the file %s for account=%s and report_platform_id=%s.',
                                prefix, file.name, request_obj['account'], request_obj['request_id'])
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
                                    prefix, mismatch_message, request_obj['account'], request_obj['request_id'])
                                continue

                            # Here performace can be improved by using Async thread
                            report_files.append(report_slice_json)
                return report_files
            except ValueError as error:
                raise FailExtractException(
                    '%s - Report is not valid JSON. Error: %s',
                    prefix, str(error), request_obj['account'])
        raise FailExtractException(
            '%s - Tar does not contain valid JSON metadata & report files for account=%s.',
            prefix, request_obj['account'])
    except FailExtractException as qpc_err:
        raise qpc_err
    except tarfile.ReadError as err:
        raise FailExtractException(
            '%s - Unexpected error reading tar file: %s for account=%s.',
            prefix, str(err), request_obj['account'])
    except Exception as err:
        LOG.error(
            '%s - Unexpected error reading tar file: %s for account=%s.',
            prefix, str(err), request_obj['account'])
