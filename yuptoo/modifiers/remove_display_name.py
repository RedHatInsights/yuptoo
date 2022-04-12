def run(host: dict, transformed_obj: dict, request_obj: dict):
    """Remove 'display_name' field."""
    display_name = host.get('display_name')
    if display_name is not None:
        del host['display_name']
        transformed_obj['removed'].append('display_name')
