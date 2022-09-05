import copy
import logging
from yuptoo.processor.utils import Modifier

LOG = logging.getLogger(__name__)
TRANSFORMED_DICT = dict({'removed': [], 'modified': [], 'missing_data': []})


def _remove_mac_addrs_for_omitted_nics(
    host: dict, mac_addresses_to_omit: list,
        transformed_obj=copy.deepcopy(TRANSFORMED_DICT)):
    """Remove mac_addresses for omitted nics."""

    mac_addresses = host.get('mac_addresses')
    len_of_mac_addrs_to_omit = len(mac_addresses_to_omit)
    if mac_addresses and len_of_mac_addrs_to_omit > 0:
        host['mac_addresses'] = list(
            set(mac_addresses) - set(mac_addresses_to_omit))
        if not host['mac_addresses']:
            del host['mac_addresses']
        transformed_obj['removed'].append(
            'omit mac_addresses for omitted nics')
    return [host, transformed_obj]


class TransformMacAddresses(Modifier):
    def run(self, host: dict, transformed_obj: dict, **kwargs):
        """Make values unique and remove empty 'mac_addresses' field."""
        mac_addresses = host.get('mac_addresses')
        if mac_addresses:
            host['mac_addresses'] = list(set(mac_addresses))
            transformed_obj['modified'].append(
                'transformed mac_addresses to store unique values')
        else:
            try:
                del host['mac_addresses']
                transformed_obj['removed'].append('empty mac_addresses')
            except KeyError:
                LOG.debug("Mac address is not present in host object.")
