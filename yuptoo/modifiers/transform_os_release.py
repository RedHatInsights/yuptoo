import re
from yuptoo.processor.utils import Modifier

OS_RELEASE_PATTERN = re.compile(
        r'(?P<name>[a-zA-Z\s]*)?\s*((?P<major>\d*)(\.?(?P<minor>\d*)(\.?(?P<patch>\d*))?)?)\s*'
        r'(\((?P<code>\S*)\))?'
    )
OS_VS_ENUM = {'Red Hat': 'RHEL', 'CentOS': 'CentOS'}


class TransformOsRelease(Modifier):
    def run(self, host: dict, transformed_obj: dict, request_obj: dict):
        """Transform 'system_profile.os_release' label."""
        system_profile = host.get('system_profile', {})
        os_release = system_profile.get('os_release')
        if not isinstance(os_release, str):
            return [host, transformed_obj]

        os_details = self.match_regex_and_find_os_details(os_release)

        # Removed logging from here as no other method has logging
        # inside it's definition

        if not os_details or not os_details['major']:
            del host['system_profile']['os_release']
            transformed_obj['removed'].append('empty os_release')
            return [host, transformed_obj]

        host['system_profile']['os_release'] = os_details['version']

        os_enum = next((
            value for key, value in OS_VS_ENUM.items()
            if key.lower() in os_details['name'].lower()), None)
        if os_enum:
            host['system_profile']['operating_system'] = {
                'major': os_details['major'],
                'minor': os_details['minor'],
                'name': os_enum
            }
        else:
            transformed_obj['missing_data'].append(
                "operating system info for os release '%s'" % os_release
            )

        if os_release == os_details['version']:
            return [host, transformed_obj]

        transformed_obj['modified'].append(
            "os_release from '%s' to '%s'" %
            (os_release, os_details['version']))

    def match_regex_and_find_os_details(self, os_release):
        """Match Regex with os_release and return os_details."""
        source_os_release = os_release.strip()
        if not source_os_release:
            return None

        match_result = OS_RELEASE_PATTERN.match(source_os_release)
        os_details = match_result.groupdict()
        if os_details['minor']:
            os_details['version'] = f"{os_details['major']}.{os_details['minor']}"
        else:
            os_details['version'] = os_details['major']
            os_details['minor'] = '0'

        return os_details
