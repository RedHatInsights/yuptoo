import requests
from abc import ABC, abstractmethod

from yuptoo.lib.exceptions import FailDownloadException
from yuptoo.lib.config import get_logger

LOG = get_logger(__name__)


def print_transformed_info(request_obj, host_id, transformed_obj):
    """Print transformed logs."""
    prefix = 'Printing Transformed Logs'
    if transformed_obj is None:
        return

    log_sections = []
    for key, value in transformed_obj.items():
        if value:
            log_sections.append('%s: %s' % (key, (',').join(value)))

    if log_sections:
        log_message = (
            '%s - Transformed details host with id %s (request_id: %s) for account=%s and report_platform_id=%s. '
        )
        log_message += '\n'.join(log_sections)
        LOG.info(
            log_message, prefix, host_id, request_obj['request_id'],
            request_obj['account'], request_obj['report_platform_id']
        )


def has_canonical_facts(host):
    CANONICAL_FACTS = ['insights_client_id', 'bios_uuid', 'ip_addresses', 'mac_addresses',
                       'vm_uuid', 'etc_machine_id', 'subscription_manager_id']
    for fact in CANONICAL_FACTS:
        if host.get(fact):
            return True

    return False


def download_report(consumed_message):
    """
    Download report. Returns the tar binary content or None if there are errors.
    """
    prefix = 'REPORT DOWNLOAD'
    try:
        report_url = consumed_message.get('url', None)
        if not report_url:
            raise FailDownloadException(
                '%s - Kafka message has no report url.  Message: %s',
                prefix, consumed_message)

        LOG.info(
            '%s - Downloading Report from %s for account=%s.',
            prefix, report_url, consumed_message.get('account'))

        download_response = requests.get(report_url)

        LOG.info(
            '%s - Successfully downloaded TAR from %s for account=%s.',
            prefix, report_url, consumed_message.get('account')
        )
        return download_response.content

    except FailDownloadException as fail_err:
        raise fail_err

    except Exception as err:
        raise FailDownloadException(
            '%s - Unexpected error for URL %s. Error: %s',
            prefix, report_url, err,
            consumed_message.get('account'))


class Modifier(ABC):

    @abstractmethod
    def run(self):
        pass
