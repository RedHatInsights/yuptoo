from yuptoo.modifiers.remove_empty_ip_addresses import RemoveEmptyIpAddress


def test_remove_empty_ip_addresses():
    """Test remove host ip_addresses."""
    host = {'ip_addresses': []}
    transformed_obj = {'removed': []}
    RemoveEmptyIpAddress().run(host, transformed_obj)
    assert host == {}
    assert 'empty ip_addresses' in transformed_obj['removed']


def test_do_not_remove_set_ip_addresses():
    """Test do not remove set host ip_addresses."""
    host = {
        'ip_addresses': ['192.168.10.10']}
    transformed_obj = {'removed': []}
    RemoveEmptyIpAddress().run(host, transformed_obj)
    assert host == {'ip_addresses': ['192.168.10.10']}
    assert len(transformed_obj['removed']) == 0


def test_ip_addresses_field():
    """Test remove both empty ip and mac addresses."""
    host = {}
    transformed_obj = {'removed': []}
    RemoveEmptyIpAddress().run(host, transformed_obj)
    assert len(transformed_obj['removed']) == 0
    assert host == {}
