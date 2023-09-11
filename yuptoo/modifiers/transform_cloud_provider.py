from yuptoo.processor.utils import Modifier
import logging

LOG = logging.getLogger(__name__)
GOOGLE_PROVIDER_NAME = 'gcp'


class TransformCloudProvider(Modifier):
    def run(self, host: dict, transformed_obj: dict, **kwargs):
        """Transform 'system_profile.cloud_provider.
        When system_profile.cloud_provider is 'google',
        transform it to 'gcp' for consistency.
        """
        system_profile = host.get('system_profile', {})
        cloud_provider = system_profile.get('cloud_provider')
        if cloud_provider is not None and 'google' in cloud_provider.lower():
            host['system_profile']['cloud_provider'] = GOOGLE_PROVIDER_NAME
            transformed_obj['modified'].append(
                'transformed cloud_provider from google to gcp')
            return
