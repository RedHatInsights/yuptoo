import logging
from datetime import datetime, timedelta
from urllib.parse import parse_qs, urlparse

from yuptoo.lib.config import ANNOUNCE_TOPIC
from yuptoo.lib.exceptions import QPCKafkaMsgException

LOG = logging.getLogger(__name__)


def validate_qpc_message(upload_message):
    """Handle the JSON report."""

    if upload_message.get('topic') == ANNOUNCE_TOPIC:
        org_id = upload_message.get('org_id')
        LOG.info(f"Received record on {ANNOUNCE_TOPIC} topic for org_id {org_id}.")
        missing_fields = []
        request_id = upload_message.get('request_id')
        url = upload_message.get('url')
        if not org_id:
            missing_fields.append('org_id')
        if not request_id:
            missing_fields.append('request_id')
        if not url:
            missing_fields.append('url')
        if missing_fields:
            raise QPCKafkaMsgException(f"Message missing required field(s): {', '.join(missing_fields)}.")

        check_if_url_expired(url, request_id)
        request_obj = {
            'request_id': request_id,
            'account': upload_message.get('account'),
            'org_id': org_id,
            'b64_identity': upload_message.get('b64_identity')
        }
        return request_obj
    else:
        LOG.error(f"Message not found on topic: {ANNOUNCE_TOPIC}")


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
