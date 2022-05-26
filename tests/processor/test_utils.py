import pytest
from unittest.mock import patch, Mock
from yuptoo.processor.utils import has_canonical_facts, print_transformed_info, download_report
from yuptoo.lib.exceptions import FailDownloadException


def test_print_transformed_info():
    request_obj = {'request_id': '123', 'account': '456', 'report_platform_id': '789'}
    host_id = 123
    transformed_obj = {'removed': [], 'modified': ['test'], 'missing_data': []}
    with patch('yuptoo.processor.utils.LOG.info') as mock:
        print_transformed_info(request_obj, host_id, transformed_obj)
    log_sections = ['modified: test']
    log_message = f"Transformed details host with id {host_id} "
    log_message += '\n'.join(log_sections)
    mock.assert_called_once_with(
            log_message
        )


def test_download_report():
    consumed_message = {'url': 'https://redhat.com'}
    download_response = Mock()
    download_response.content = 'test_content'
    with patch('yuptoo.processor.utils.requests.get', return_value=download_response):
        result = download_report(consumed_message)
        assert result == 'test_content'


def test_download_report_without_url():
    consumed_message = {}
    with pytest.raises(FailDownloadException):
        download_report(consumed_message)


def test_has_canonical_facts_true():
    host = {'insights_client_id': '123'}
    result = has_canonical_facts(host)
    assert result is True


def test_has_canonical_facts_false():
    host = {}
    result = has_canonical_facts(host)
    assert result is False
