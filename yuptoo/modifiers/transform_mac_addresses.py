from yuptoo.processor.utils import Modifier


class TransformMacAddresses(Modifier):
    def run(self, host: dict, transformed_obj: dict, request_obj: dict):
        """Make values unique and remove empty 'mac_addresses' field."""
        mac_addresses = host.get('mac_addresses')
        if mac_addresses is None:
            return [host, transformed_obj]
        if mac_addresses:
            host['mac_addresses'] = list(set(mac_addresses))
            transformed_obj['modified'].append(
                'transformed mac_addresses to store unique values')
            return [host, transformed_obj]
        del host['mac_addresses']
        transformed_obj['removed'].append('empty mac_addresses')
