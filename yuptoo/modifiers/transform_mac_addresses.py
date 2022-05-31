from yuptoo.processor.utils import Modifier
import logging

LOG = logging.getLogger(__name__)


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
                LOG.debug("Mac address is not present in host object")
