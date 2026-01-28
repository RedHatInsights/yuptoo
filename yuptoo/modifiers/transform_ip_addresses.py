from yuptoo.processor.utils import Modifier
import logging

LOG = logging.getLogger(__name__)


class TransformIPAddress(Modifier):
    def run(self, host: dict, transformed_obj: dict, **kwargs):
        """Remove empty & make 'ip_addresses' unique. Drop blank items."""
        ip_addresses = host.get('ip_addresses')
        try:
            if ip_addresses is None:
                return

            # Drop blank, duplicate items & keep the order of the ip_addresses
            valid_ip_addresses = []
            is_modified = False
            seen = set()
            for _ip_addr in ip_addresses:
                ip_addr = _ip_addr.strip()
                if ip_addr and ip_addr not in seen:
                    valid_ip_addresses.append(ip_addr)
                    seen.add(ip_addr)
                else:
                    is_modified = True

            if len(valid_ip_addresses) == 0:
                del host['ip_addresses']
                transformed_obj['removed'].append('empty ip_addresses')
                return

            elif is_modified:
                host['ip_addresses'] = valid_ip_addresses
                transformed_obj['modified'].append(
                    'transformed ip_addresses to store unique values')
                return

        except KeyError:
            LOG.debug("ipaddress field is not present in host object.")
