from yuptoo.processor.utils import Modifier


class TransformOsKernalVersion(Modifier):
    def run(self, host: dict, transformed_obj: dict, **kwargs):
        """Transform 'system_profile.os_kernel_version' label."""
        system_profile = host.get('system_profile', {})
        os_kernel_version = system_profile.get('os_kernel_version')

        if isinstance(os_kernel_version, str):
            version_value = os_kernel_version.split('-')[0]
            if version_value[-1] == '+':
                version_value = version_value[:-1]
            host['system_profile']['os_kernel_version'] = version_value
            transformed_obj['modified'].append(
                "os_kernel_version from '%s' to '%s'"
                % (os_kernel_version, version_value))
