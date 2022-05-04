import uuid
import tarfile
import pytest
from io import BytesIO
from unittest.mock import patch

from tests.utils import create_tar_buffer
from yuptoo.lib.exceptions import FailExtractException
from yuptoo.validators.report_metadata_validator import validate_metadata_file
from yuptoo.lib.config import MAX_HOSTS_PER_REP


def test_metadata_with_missing_keys():
    uuid1 = uuid.uuid4()
    metadata_json = {
            'host_inventory_api_version': '1.0.0',
            'source': 'qpc',
            'source_metadata': {'foo': 'bar'},
            'report_slices': {str(uuid1): {'number_hosts': 1}}
        }
    report_json = {
        'report_slice_id': str(uuid1),
        'hosts': {str(uuid1): {'key': 'value'}}}
    report_files = {
        'metadata.json': metadata_json,
        '%s.json' % str(uuid1): report_json
    }
    request_obj = {}
    request_obj['account'] = 123
    request_obj['request_id'] = 456
    buffer_content = create_tar_buffer(report_files)
    tar = tarfile.open(fileobj=BytesIO(buffer_content), mode='r:*')
    files = tar.getmembers()
    metafile = None
    for file in files:
        if '/metadata.json' in file.name or file.name == 'metadata.json':
            metafile = file
    with pytest.raises(FailExtractException):
        validate_metadata_file(tar, metafile, request_obj)


def test_validate_metadata_file():
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
        'hosts': {str(uuid1): {'key': 'value'}}}
    report_files = {
        'metadata.json': metadata_json,
        '%s.json' % str(uuid1): report_json
    }
    request_obj = {}
    request_obj['account'] = 123
    request_obj['request_id'] = 456
    buffer_content = create_tar_buffer(report_files)
    tar = tarfile.open(fileobj=BytesIO(buffer_content), mode='r:*')
    files = tar.getmembers()
    metafile = None
    for file in files:
        if '/metadata.json' in file.name or file.name == 'metadata.json':
            metafile = file
    result = validate_metadata_file(tar, metafile, request_obj)
    assert {str(uuid1): 1} == result


def test_metadata_with_invalid_slice():
    uuid1 = uuid.uuid4()
    metadata_json = {
            'report_id': 1,
            'host_inventory_api_version': '1.0.0',
            'source': 'qpc',
            'source_metadata': {'foo': 'bar'},
            'report_slices': {str(uuid1): {'number_hosts': MAX_HOSTS_PER_REP+1}}
        }
    report_json = {
        'report_slice_id': str(uuid1),
        'hosts': {str(uuid1): {'key': 'value'}}}
    report_files = {
        'metadata.json': metadata_json,
        '%s.json' % str(uuid1): report_json
    }
    request_obj = {}
    request_obj['account'] = 123
    request_obj['request_id'] = 456
    buffer_content = create_tar_buffer(report_files)
    tar = tarfile.open(fileobj=BytesIO(buffer_content), mode='r:*')
    files = tar.getmembers()
    metafile = None
    for file in files:
        if '/metadata.json' in file.name or file.name == 'metadata.json':
            metafile = file
    with patch('yuptoo.validators.report_metadata_validator.LOG.warning', spec=True) as mock:
        validate_metadata_file(tar, metafile, request_obj)
    mock.assert_called_once
