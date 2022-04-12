def run(host: dict, transformed_obj: dict, request_obj: dict):
    """Transform 'system_profile.os_kernel_version' label."""
    system_profile = host.get('system_profile', {})
    os_kernel_version = system_profile.get('os_kernel_version')

    if not isinstance(os_kernel_version, str):
        return [host, transformed_obj]

    version_value = os_kernel_version.split('-')[0]
    host['system_profile']['os_kernel_version'] = version_value
    transformed_obj['modified'].append(
        "os_kernel_version from '%s' to '%s'"
        % (os_kernel_version, version_value))
