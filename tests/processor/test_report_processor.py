from unittest.mock import patch, Mock
import uuid
import pytest

from datetime import datetime
from yuptoo.processor.report_processor import process_report
from yuptoo.lib.exceptions import QPCReportException
from tests.utils import create_tar_buffer


def test_process_report_without_facts():
    uuid1 = uuid.uuid4()
    metadata_json = {
            'report_id': 1,
            'host_inventory_api_version': '1.0.0',
            'source': 'qpc',
            'source_metadata': {'foo': 'bar'},
            'report_slices': {str(uuid1): {'number_hosts': 1}}
        }
    report_json = {
        'report_slice_id': str(uuid1),
        'hosts': [{'key': 'value', 'fqdn': "test.example.com"}]
    }
    report_files = {
        'metadata.json': metadata_json,
        '%s.json' % str(uuid1): report_json
    }
    consumed_message = {
        "account": "12345",
        "org_id": "123",
        "category": "sample",
        "metadata": {"reporter": ""},
        "request_id": "32bcf6e59d03/IhactaBNbg-000001",
        "principal": "54321",
        "service": "qpc",
        "size": 877,
        "url": f"http://minio:9000/insights-upload-perma?X-Amz-Date=\
                {datetime.now().strftime('%Y%m%dT%H%M%SZ')}&X-Amz-Expires=86400"
    }
    request_object = {'org_id': consumed_message['org_id']}
    buffer_content = create_tar_buffer(report_files)
    producer = Mock()
    with patch('yuptoo.processor.report_processor.download_report', return_value=buffer_content):
        with patch('yuptoo.processor.report_processor.HOSTS_TRANSFORMATION_ENABLED', 0):
            with patch('yuptoo.processor.report_processor.has_canonical_facts', return_value=0):
                with pytest.raises(QPCReportException):
                    process_report(consumed_message, producer, request_object)


def test_process_report():
    uuid1 = uuid.uuid4()
    metadata_json = {
            'report_id': 1,
            'host_inventory_api_version': '1.0.0',
            'source': 'qpc',
            'source_metadata': {'foo': 'bar'},
            'report_slices': {str(uuid1): {'number_hosts': 1}}
        }
    report_json = {
        'report_slice_id': str(uuid1),
        'hosts': [{str(uuid1): {'key': 'value'}, 'ip_addresses': '127.0.0.1'}]}
    report_files = {
        'metadata.json': metadata_json,
        '%s.json' % str(uuid1): report_json
    }
    consumed_message = {
        "account": "12345",
        "org_id": "123",
        "category": "sample",
        "metadata": {"reporter": ""},
        "request_id": "32bcf6e59d03/IhactaBNbg-000001",
        "principal": "54321",
        "service": "qpc",
        "size": 877,
        "url": f"http://minio:9000/insights-upload-perma?X-Amz-Date=\
                {datetime.now().strftime('%Y%m%dT%H%M%SZ')}&X-Amz-Expires=86400"
    }
    request_object = {'request_id': consumed_message['request_id'], 'org_id': consumed_message['org_id']}
    buffer_content = create_tar_buffer(report_files)
    producer = Mock()
    with patch('yuptoo.processor.report_processor.upload_to_host_inventory_via_kafka', return_value=None) as mock:
        with patch('yuptoo.processor.report_processor.download_report', return_value=buffer_content):
            with patch('yuptoo.processor.report_processor.HOSTS_TRANSFORMATION_ENABLED', 0):
                process_report(consumed_message, producer, request_object)
    mock.assert_called_once
