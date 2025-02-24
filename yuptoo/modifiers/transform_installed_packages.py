import json
import logging

from insights.parsers.installed_rpms import InstalledRpm
from yuptoo.lib.config import KAFKA_PRODUCER_OVERRIDE_MAX_REQUEST_SIZE
from yuptoo.processor.utils import Modifier

LOG = logging.getLogger(__name__)


class TransfromInstalledPackages(Modifier):
    def run(self, host: dict, transformed_obj: dict, **kwargs):
        """
        Tansform installed_packages:
            - Delete installed_packages:
                when Kafka message exceeds the maximum request size.
            - Modify installed_packages:
                with default epoch 0 when an epoch is missing in package.
        """
        # Delete installed_packages when Kafka message exceeds the maximum request size
        host_request_size = bytes(json.dumps(host), 'utf-8')
        if len(host_request_size) >= KAFKA_PRODUCER_OVERRIDE_MAX_REQUEST_SIZE:
            if 'installed_packages' in host['system_profile']:
                del host['system_profile']['installed_packages']
                host['tags'].append({
                    'namespace': 'report_slice_preprocessor',
                    'key': 'package_list_truncated',
                    'value': 'True'})
                transformed_obj['removed'].append('installed_packages')

        # Prepending an epoch of 0: when an epoch is missing in package
        elif 'installed_packages' in host['system_profile']:
            try:
                new_installed_packages = []
                for package in host['system_profile']['installed_packages']:
                    new_installed_packages.append(InstalledRpm.from_package(package).nevra)
                host['system_profile']['installed_packages'] = new_installed_packages
                transformed_obj['modified'].append(
                    'installed_packages: prepending default epoch of 0 when missing')
            except Exception as err:
                # When run into during epoch prepending, remove the 'installed_packages' from
                #   host['system_profile'] to make sure no invalid data be sent to HBI.
                # Note. delete the 'installed_packages' instead of the error package items for
                #   the data accuracy as a whole.
                LOG.debug("installed_packages epoch modify failure: %s" % str(err))
                del host['system_profile']['installed_packages']
                transformed_obj['removed'].append(
                    'installed_packages: prepending default epoch failure: %s' % str(err))
