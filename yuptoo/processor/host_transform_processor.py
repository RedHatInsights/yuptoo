import copy
import re
from uuid import UUID
from yuptoo.config.base import get_logger


LOG = get_logger(__name__)
OS_RELEASE_PATTERN = re.compile(
    r'(?P<name>[a-zA-Z\s]*)?\s*((?P<major>\d*)(\.?(?P<minor>\d*)(\.?(?P<patch>\d*))?)?)\s*'
    r'(\((?P<code>\S*)\))?'
)
OS_VS_ENUM = {'Red Hat': 'RHEL', 'CentOS': 'CentOS'}
TRANSFORMED_DICT = dict({'removed': [], 'modified': [], 'missing_data': []})


class HostTransformProcessor:
    @staticmethod
    def transform_tags(
            host: dict, transformed_obj=copy.deepcopy(TRANSFORMED_DICT)):
        """Convert tag's value into string."""
        tags = host.get('tags')
        if tags is None:
            return [host, transformed_obj]

        tags_modified = False
        for tag in tags:
            if tag['value'] is None or isinstance(tag['value'], str):
                continue

            if tag['value'] is True:
                tag['value'] = 'true'
            elif tag['value'] is False:
                tag['value'] = 'false'
            else:
                tag['value'] = str(tag['value'])

            tags_modified = True

        if tags_modified:
            transformed_obj['modified'].append('tags')

        host['tags'] = tags
        return [host, transformed_obj]

    @staticmethod
    def remove_display_name(
            host: dict, transformed_obj=copy.deepcopy(TRANSFORMED_DICT)):
        """Remove 'display_name' field."""
        display_name = host.get('display_name')
        if display_name is None:
            return [host, transformed_obj]

        del host['display_name']
        transformed_obj['removed'].append('display_name')
        return [host, transformed_obj]

    @staticmethod
    def remove_empty_ip_addresses(
            host: dict, transformed_obj=copy.deepcopy(TRANSFORMED_DICT)):
        """Remove 'ip_addresses' field."""
        ip_addresses = host.get('ip_addresses')
        if ip_addresses is None or ip_addresses:
            return [host, transformed_obj]

        del host['ip_addresses']
        transformed_obj['removed'].append('empty ip_addresses')
        return [host, transformed_obj]

    @staticmethod
    def transform_mac_addresses(
            host: dict, transformed_obj=copy.deepcopy(TRANSFORMED_DICT)):
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
        return [host, transformed_obj]

    @staticmethod
    def is_valid_uuid(uuid):
        """Validate a UUID string."""
        try:
            uuid_obj = UUID(str(uuid))
        except ValueError:
            return False

        return str(uuid_obj) == uuid.lower()

    def remove_invalid_bios_uuid(
            self, host, transformed_obj=copy.deepcopy(TRANSFORMED_DICT)):
        """Remove invalid bios UUID."""
        uuid = host.get('bios_uuid')
        if uuid is None:
            return [host, transformed_obj]

        if not self.is_valid_uuid(uuid):
            transformed_obj['removed'].append('invalid uuid: %s' % uuid)
            del host['bios_uuid']

        return [host, transformed_obj]

    @staticmethod
    def match_regex_and_find_os_details(os_release):
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

    def transform_os_release(
            self, host: dict, transformed_obj=copy.deepcopy(TRANSFORMED_DICT)):
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

        return [host, transformed_obj]

    @staticmethod
    def transform_os_kernel_version(
            host: dict, transformed_obj=copy.deepcopy(TRANSFORMED_DICT)):
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

        return [host, transformed_obj]

    def transform_network_interfaces(
            self, host: dict, transformed_obj=copy.deepcopy(TRANSFORMED_DICT)):
        """Transform 'system_profile.network_interfaces[]."""
        system_profile = host.get('system_profile', {})
        network_interfaces = system_profile.get('network_interfaces')
        if not network_interfaces:
            return [host, transformed_obj]
        filtered_nics = list(filter(lambda nic: nic.get('name'), network_interfaces))
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
        return [host, transformed_obj]

    @staticmethod
    def transform_ipv6(nic: dict, increment_counts: dict):
        """Remove empty 'network_interfaces[]['ipv6_addresses']."""
        old_len = len(nic['ipv6_addresses'])
        nic['ipv6_addresses'] = list(
            filter(lambda ipv6: ipv6, nic['ipv6_addresses'])
        )
        new_len = len(nic['ipv6_addresses'])
        if old_len != new_len:
            increment_counts['ipv6_addresses'] += 1

        return increment_counts, nic

    @staticmethod
    def transform_mtu(nic: dict, increment_counts: dict):
        """Transform 'system_profile.network_interfaces[]['mtu'] to Integer."""
        if (
                'mtu' not in nic or not nic['mtu'] or isinstance(
                    nic['mtu'], int)
        ):
            return increment_counts, nic
        nic['mtu'] = int(nic['mtu'])
        increment_counts['mtu'] += 1
        return increment_counts, nic

    @staticmethod
    def remove_installed_packages(
            host: dict, transformed_obj=copy.deepcopy(TRANSFORMED_DICT)):
        """Delete installed_packages.

        Kafka message exceeds the maximum request size.
        """
        if 'installed_packages' in host['system_profile']:
            del host['system_profile']['installed_packages']
            host['tags'].append({
                'namespace': 'report_slice_preprocessor',
                'key': 'package_list_truncated',
                'value': 'True'})
            transformed_obj['removed'].append('installed_packages')

        return [host, transformed_obj]
