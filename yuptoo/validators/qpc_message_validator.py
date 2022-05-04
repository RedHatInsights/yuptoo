from datetime import datetime, timedelta
from urllib.parse import parse_qs, urlparse

from yuptoo.lib.config import get_logger, QPC_TOPIC
from yuptoo.lib.exceptions import QPCKafkaMsgException
from yuptoo.lib.utils import format_message

LOG = get_logger(__name__)
LOG_PREFIX = 'QPC MESSAGE VALIDATOR'


def validate_qpc_message(upload_message):
    """Handle the JSON report."""

    if upload_message.get('topic') == QPC_TOPIC:
        account = upload_message.get('account')
        LOG.info(
            '%s - Received record on %s topic for account %s.',
            LOG_PREFIX, QPC_TOPIC, account)

        missing_fields = []
        request_id = upload_message.get('request_id')
        url = upload_message.get('url')
        if not account:
            missing_fields.append('account')
        if not request_id:
            missing_fields.append('request_id')
        if not url:
            missing_fields.append('url')
        if missing_fields:
            raise QPCKafkaMsgException(
                format_message(
                    LOG_PREFIX,
                    'Message missing required field(s): %s.' % ', '.join(missing_fields)))

        check_if_url_expired(url, request_id)
        return upload_message
    else:
        LOG.debug(
            LOG_PREFIX,
            'Message not found on topic: %s', QPC_TOPIC)


def check_if_url_expired(url, request_id):
    """Validate if url is expired."""
    LOG_PREFIX = 'NEW REPORT VALIDATION'
    parsed_url_query = parse_qs(urlparse(url).query)
    creation_timestamp = parsed_url_query['X-Amz-Date']
    expire_time = timedelta(seconds=int(parsed_url_query['X-Amz-Expires'][0]))
    creation_datatime = datetime.strptime(str(creation_timestamp[0]), '%Y%m%dT%H%M%SZ')

    if datetime.now().replace(microsecond=0) > (creation_datatime + expire_time):
        raise QPCKafkaMsgException(
            LOG_PREFIX,
            'Request_id = %s is already expired and cannot be processed:'
            'Creation time = %s, Expiry interval = %s.',
            request_id, creation_datatime, expire_time)
