import logging
from datetime import datetime, timedelta
from urllib.parse import parse_qs, urlparse

from yuptoo.lib.config import QPC_TOPIC
from yuptoo.lib.exceptions import QPCKafkaMsgException

LOG = logging.getLogger(__name__)


def validate_qpc_message(upload_message):
    """Handle the JSON report."""

    if upload_message.get('topic') == QPC_TOPIC:
        account = upload_message.get('account')
        LOG.info(f"Received record on {QPC_TOPIC} topic for account {account}.")
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
            raise QPCKafkaMsgException(f"Message missing required field(s): {', '.join(missing_fields)}.")

        check_if_url_expired(url, request_id)
        request_obj = {
            'request_id': request_id,
            'account': account,
            'org_id': upload_message.get('org_id'),
            'b64_identity': upload_message.get('b64_identity')
        }
        return request_obj
    else:
        LOG.error(f"Message not found on topic: {QPC_TOPIC}")


def check_if_url_expired(url, request_id):
    """Validate if url is expired."""
    parsed_url_query = parse_qs(urlparse(url).query)
    creation_timestamp = parsed_url_query['X-Amz-Date']
    expire_time = timedelta(seconds=int(parsed_url_query['X-Amz-Expires'][0]))
    creation_datatime = datetime.strptime(str(creation_timestamp[0]), '%Y%m%dT%H%M%SZ')

    if datetime.now().replace(microsecond=0) > (creation_datatime + expire_time):
        raise QPCKafkaMsgException(
            f"Request_id = {request_id} is already expired and cannot be processed:"
            f"Creation time = {creation_datatime}, Expiry interval = {expire_time}."
        )
