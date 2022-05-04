import pytest
from unittest.mock import patch

from datetime import datetime
from yuptoo.validators.qpc_message_validator import check_if_url_expired, validate_qpc_message
from yuptoo.lib.exceptions import QPCKafkaMsgException
from yuptoo.lib.config import QPC_TOPIC


payload_url = f"http://minio:9000/insights-upload-perma?X-Amz-Date="\
            f"{datetime.now().strftime('%Y%m%dT%H%M%SZ')}&X-Amz-Expires=86400"
b64_identity = ('eyJpZGVudGl0eSI6IHsiYWNjb3VudF9udW1iZXIiOiAic3lzYWNjb3VudCIsICJ0eXBlIjogIlN5c3R'
                'lbSIsICJhdXRoX3R5cGUiOiAiY2VydC1hdXRoIiwgInN5c3RlbSI6IHsiY24iOiAiMWIzNmIyMGYtN2'
                'ZhMC00NDU0LWE2ZDItMDA4Mjk0ZTA2Mzc4IiwgImNlcnRfdHlwZSI6ICJzeXN0ZW0ifSwgImludGVyb'
                'mFsIjogeyJvcmdfaWQiOiAiMzM0MDg1MSIsICJhdXRoX3RpbWUiOiA2MzAwfX19')


def test_validate_qpc_message():
    qpc_msg = {'url': payload_url, 'account': '123', 'request_id': '234332',
               'b64_identity': b64_identity, 'topic': QPC_TOPIC}
    result = validate_qpc_message(qpc_msg)
    qpc_msg == result


def test_validate_qpc_message_without_account():
    qpc_msg = {'url': payload_url, 'request_id': '234332',
               'b64_identity': b64_identity, 'topic': QPC_TOPIC}
    with pytest.raises(QPCKafkaMsgException):
        validate_qpc_message(qpc_msg)


def test_qpc_message_without_topic():
    qpc_msg = {'url': payload_url, 'request_id': '234332',
               'b64_identity': b64_identity}
    with patch('yuptoo.validators.qpc_message_validator.LOG.debug') as mock:
        validate_qpc_message(qpc_msg)
    mock.assert_called_once_with('QPC MESSAGE VALIDATOR', 'Message not found on topic: %s', QPC_TOPIC)


def test_check_if_url_expired():
    """Test expired url(bad case)."""
    url = 'http://minio:9000/insights-upload-perma'\
          '?X-Amz-Date=20200928T063623Z&X-Amz-Expires=86400'
    request_id = '123456'
    with pytest.raises(QPCKafkaMsgException):
        check_if_url_expired(url, request_id)
