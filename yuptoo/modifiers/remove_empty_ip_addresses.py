from yuptoo.processor.utils import Modifier
import logging

LOG = logging.getLogger(__name__)


class RemoveEmptyIpAddress(Modifier):
    def run(self, host: dict, transformed_obj: dict, **kwargs):
        """Remove 'ip_addresses' field."""
        ip_addresses = host.get('ip_addresses')
        if ip_addresses is None or ip_addresses == []:
            try:
                del host['ip_addresses']
                transformed_obj['removed'].append('empty ip_addresses')
            except KeyError:
                LOG.debug("ipaddress field is not present in host object.")
