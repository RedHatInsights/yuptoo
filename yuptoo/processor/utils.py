import requests
from abc import ABC, abstractmethod
from yuptoo.lib.metrics import archive_downloaded_success, archive_failed_to_download
from yuptoo.lib.exceptions import FailDownloadException
import logging
import datetime

LOG = logging.getLogger(__name__)


def print_transformed_info(request_obj, host_id, transformed_obj):
    """Print transformed logs."""
    if transformed_obj is None:
        return

    log_sections = []
    for key, value in transformed_obj.items():
        if value:
            log_sections.append('%s: %s' % (key, (',').join(value)))

    if log_sections:
        log_message = f"Transformed details host with id {host_id}."
        log_message += '\n'.join(log_sections)
        LOG.info(log_message)


def has_canonical_facts(host):
    CANONICAL_FACTS = ['insights_id', 'bios_uuid', 'ip_addresses', 'mac_addresses',
                       'vm_uuid', 'etc_machine_id', 'subscription_manager_id']
    for fact in CANONICAL_FACTS:
        if host.get(fact):
            return True

    return False


def download_report(consumed_message):
    """
    Download report. Returns the tar binary content or None if there are errors.
    """
    try:
        report_url = consumed_message.get('url', None)
        if not report_url:
            raise FailDownloadException(
                f"Kafka message has no report url.  Message: {consumed_message}"
            )

        LOG.info(f"Downloading Report from {report_url}")

        download_response = requests.get(report_url)

        LOG.info(f"Successfully downloaded TAR from {report_url}")
        archive_downloaded_success.inc()
        return download_response.content
    except Exception as err:
        archive_failed_to_download.inc()
        raise FailDownloadException(
            f"Unexpected error for URL {report_url}. Error: {err}"
        )


def tracker_message(request_obj, status, status_msg):

    return {
        "account": request_obj.get("account"),
        "org_id": request_obj.get("org_id"),
        "request_id": request_obj.get("request_id"),
        "payload_id": request_obj.get("request_id"),
        "service": "yuptoo",
        "status": status,
        "status_msg": status_msg,
        "date": datetime.datetime.now().isoformat(),
    }


class Modifier(ABC):

    @abstractmethod
    def run(self):
        pass
