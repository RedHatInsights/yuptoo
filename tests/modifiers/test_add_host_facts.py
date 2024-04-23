from yuptoo.modifiers.add_host_facts import AddHostFacts
from datetime import datetime, timedelta
from yuptoo.lib.config import SATELLITE_HOST_TTL
import uuid


def test_add_host_facts():
    uuid1 = str(uuid.uuid4())
    b64_identity = ('eyJpZGVudGl0eSI6IHsiYWNjb3VudF9udW1iZXIiOiAic3lzYWNjb3VudCIsICJ0eXBlIjogIlN5c3R'
                    'lbSIsICJhdXRoX3R5cGUiOiAiY2VydC1hdXRoIiwgInN5c3RlbSI6IHsiY24iOiAiMWIzNmIyMGYtN2'
                    'ZhMC00NDU0LWE2ZDItMDA4Mjk0ZTA2Mzc4IiwgImNlcnRfdHlwZSI6ICJzeXN0ZW0ifSwgImludGVyb'
                    'mFsIjogeyJvcmdfaWQiOiAiMzM0MDg1MSIsICJhdXRoX3RpbWUiOiA2MzAwfX19')
    host = {'display_name': 'test.example.com', 'yupana_host_id': uuid1, 'report_slice_id': uuid1, "system_profile": {}}
    transformed_obj = {'removed': [], 'modified': [], 'missing_data': []}
    request_obj = {'b64_identity': b64_identity, 'account': '123', 'org_id': '123',
                   'report_platform_id': '123', 'source': 'satellite', 'request_id': uuid1}
    AddHostFacts().run(host, transformed_obj, request_obj=request_obj)
    assert host['facts'][0]['namespace'] == 'yupana'
    assert 'facts' in transformed_obj['modified']


def test_get_stale_time():
    """Test the get stale time method."""
    current_time = datetime.utcnow()
    stale_time = current_time + timedelta(hours=int(SATELLITE_HOST_TTL))
    expected = stale_time.strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z'
    request_obj = {}
    request_obj['source'] = 'satellite'
    actual = AddHostFacts().get_stale_time(request_obj)
    # the format looks like this: 2019-11-14T19:58:13.037Z
    # by cutting off the last 13 i am comparing 2019-11-14T
    # which is the year/month/day
    assert expected[:-13] == actual[:-13]
