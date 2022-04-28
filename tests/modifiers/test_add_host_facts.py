from yuptoo.modifiers.add_host_facts import AddHostFacts
from datetime import datetime, timedelta
from yuptoo.lib.config import SATELLITE_HOST_TTL


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
