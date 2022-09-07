from yuptoo.processor.utils import Modifier
from yuptoo.common.mac_addresses import (
    _remove_mac_addrs_for_omitted_nics)

NETWORK_INTERFACES_TOKENS_TO_OMIT = ['cali']


class TransformNetworkInterfaces(Modifier):
    def run(self, host: dict, transformed_obj: dict, **kwargs):
        """Transform 'system_profile.network_interfaces[]."""
        system_profile = host.get('system_profile', {})
        network_interfaces = system_profile.get('network_interfaces')
        if network_interfaces:
            mac_addresses_to_omit = []
            filtered_nics = []
            for nic in network_interfaces:
                if nic.get('name'):
                    lowercase_name = nic['name'].lower()
                    if any(map(lowercase_name.startswith,
                               NETWORK_INTERFACES_TOKENS_TO_OMIT)):
                        mac_addresses_to_omit.append(nic.get('mac_address'))
                        continue
                    filtered_nics.append(nic)
            host, transformed_obj = _remove_mac_addrs_for_omitted_nics(
                host, mac_addresses_to_omit, transformed_obj)

            increment_counts = {
                'mtu': 0,
                'ipv6_addresses': 0
            }
            filtered_nics = list({nic['name']: nic for nic in filtered_nics}.values())
            for nic in filtered_nics:
                increment_counts, nic = self.transform_mtu(
                    nic, increment_counts)
                increment_counts, nic = self.transform_ipv6(
                    nic, increment_counts)

            modified_fields = [
                field for field, count in increment_counts.items() if count > 0
            ]
            if len(modified_fields) > 0:
                transformed_obj['modified'].extend(modified_fields)

            host['system_profile']['network_interfaces'] = filtered_nics

    def transform_mtu(self, nic: dict, increment_counts: dict):
        """Transform 'system_profile.network_interfaces[]['mtu'] to Integer."""
        if (
                'mtu' not in nic or not nic['mtu'] or isinstance(
                    nic['mtu'], int)
        ):
            return increment_counts, nic
        nic['mtu'] = int(nic['mtu'])
        increment_counts['mtu'] += 1
        return increment_counts, nic

    def transform_ipv6(self, nic: dict, increment_counts: dict):
        """Remove empty 'network_interfaces[]['ipv6_addresses']."""
        old_len = len(nic['ipv6_addresses'])
        nic['ipv6_addresses'] = list(
            filter(lambda ipv6: ipv6, nic['ipv6_addresses'])
        )
        new_len = len(nic['ipv6_addresses'])
        if old_len != new_len:
            increment_counts['ipv6_addresses'] += 1

        return increment_counts, nic
