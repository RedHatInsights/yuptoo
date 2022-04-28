import json
import base64

from yuptoo.lib.config import get_logger
from yuptoo.lib.config import DISCOVERY_HOST_TTL, SATELLITE_HOST_TTL
from datetime import datetime, timedelta
from yuptoo.processor.utils import Modifier

LOG = get_logger(__name__)
prefix = 'ADD_HOST_FACTS'


class AddHostFacts(Modifier):
    def run(self, host: dict, transformed_obj: dict, **kwargs):
        request_obj = kwargs['request_obj']
        cert_cn = None
        try:
            raw_b64_identity = base64.b64decode(request_obj['b64_identity']).decode('utf-8')
            identity = json.loads(raw_b64_identity)
            cert_cn = identity['identity']['system']['cn']
        except KeyError as err:
            LOG.error(
                prefix, 'Invalid identity. Key not found: %s', err)

        unique_id_base = '{}:{}:'.format(request_obj['request_id'],
                                         request_obj['report_platform_id'])

        host['system_unique_id'] = unique_id_base + host['yupana_host_id']

        host['account'] = request_obj['account']
        host_facts = host.get('facts', [])
        host_facts.append({'namespace': 'yupana',
                           'facts': {'yupana_host_id': host['yupana_host_id'],
                                        'report_platform_id': str(request_obj['report_platform_id']),
                                        'report_slice_id': host['report_slice_id'],
                                        'account': request_obj['account'],
                                        'source': request_obj['source']}})
        host['stale_timestamp'] = self.get_stale_time(request_obj)
        host['reporter'] = 'yupana'
        host['facts'] = host_facts
        if cert_cn and ('system_profile' in host):
            host['system_profile']['owner_id'] = cert_cn
        transformed_obj['modified'].append('facts')

    def get_stale_time(self, request_obj):
        """Compute the stale date based on the host source."""
        ttl = int(DISCOVERY_HOST_TTL)
        if request_obj['source'] == 'satellite':
            ttl = int(SATELLITE_HOST_TTL)
        current_time = datetime.utcnow()
        stale_time = current_time + timedelta(hours=ttl)

        return stale_time.strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z'
