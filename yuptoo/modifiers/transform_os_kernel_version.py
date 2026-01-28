import re
from yuptoo.processor.utils import Modifier

# Follow the system_profile schema defination of the "os_kernel_version" field
KERNEL_VERSION_PATTERN = re.compile(r'^(\d+\.\d+\.\d+)(\.\d+)?')


class TransformOsKernalVersion(Modifier):
    def run(self, host: dict, transformed_obj: dict, **kwargs):
        """Transform 'system_profile.os_kernel_version' label."""
        system_profile = host.get('system_profile', {})
        os_kernel_version = system_profile.get('os_kernel_version')

        if isinstance(os_kernel_version, str):
            version_value = os_kernel_version.split('-')[0]
            match = KERNEL_VERSION_PATTERN.match(version_value)
            if match:
                version_value = match.group(1) + (match.group(2) or '')
            host['system_profile']['os_kernel_version'] = version_value
            transformed_obj['modified'].append(
                "os_kernel_version from '%s' to '%s'"
                % (os_kernel_version, version_value))
