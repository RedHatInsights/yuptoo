from yuptoo.processor.utils import Modifier
import logging

LOG = logging.getLogger(__name__)


class TransformIPAddress(Modifier):
    def run(self, host: dict, transformed_obj: dict, **kwargs):
        """Remove empty & make 'ip_addresses' unique."""
        ip_addresses = host.get('ip_addresses')
        try:
            if (
                    ip_addresses is None or (
                        ip_addresses and (
                            len(ip_addresses) == len(set(ip_addresses))
                        )
                    )
            ):
                return
            if ip_addresses:
                host['ip_addresses'] = list(set(ip_addresses))
                transformed_obj['modified'].append(
                    'transformed ip_addresses to store unique values')
                return
            del host['ip_addresses']
            transformed_obj['removed'].append('empty ip_addresses')

        except KeyError:
            LOG.debug("ipaddress field is not present in host object.")
