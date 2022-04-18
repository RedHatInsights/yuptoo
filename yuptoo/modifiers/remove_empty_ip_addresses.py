from yuptoo.processor.utils import Modifier


class RemoveEmptyIpAddress(Modifier):
    def run(self, host: dict, transformed_obj: dict, request_obj: dict):
        """Remove 'ip_addresses' field."""
        ip_addresses = host.get('ip_addresses')
        if ip_addresses is None or ip_addresses:
            return [host, transformed_obj]

        del host['ip_addresses']
        transformed_obj['removed'].append('empty ip_addresses')
