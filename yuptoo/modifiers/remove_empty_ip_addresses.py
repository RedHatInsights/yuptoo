from yuptoo.processor.utils import Modifier
from yuptoo.lib.config import get_logger

LOG = get_logger(__name__)
LOG_PREFIX = 'RemoveEmptyIpAddress'


class RemoveEmptyIpAddress(Modifier):
    def run(self, host: dict, transformed_obj: dict, **kwargs):
        """Remove 'ip_addresses' field."""
        ip_addresses = host.get('ip_addresses')
        if ip_addresses is None or ip_addresses == []:
            try:
                del host['ip_addresses']
                transformed_obj['removed'].append('empty ip_addresses')
            except KeyError:
                LOG.info(f'{LOG_PREFIX} - ipaddress field is not present in host object')
