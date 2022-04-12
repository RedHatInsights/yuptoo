import json
from yuptoo.lib.config import KAFKA_PRODUCER_OVERRIDE_MAX_REQUEST_SIZE


def run(host: dict, transformed_obj: dict, request_obj: dict):
    """Delete installed_packages.
        Kafka message exceeds the maximum request size.
    """
    host_request_size = bytes(json.dumps(host), 'utf-8')
    if len(host_request_size) >= KAFKA_PRODUCER_OVERRIDE_MAX_REQUEST_SIZE:
        if 'installed_packages' in host['system_profile']:
            del host['system_profile']['installed_packages']
            host['tags'].append({
                'namespace': 'report_slice_preprocessor',
                'key': 'package_list_truncated',
                'value': 'True'})
            transformed_obj['removed'].append('installed_packages')
