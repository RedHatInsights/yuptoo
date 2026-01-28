from yuptoo.modifiers.transform_ip_addresses import TransformIPAddress


def test_remove_empty_ip_addresses():
    """Test remove host ip_addresses."""
    host = {'ip_addresses': []}
    transformed_obj = {'removed': []}
    TransformIPAddress().run(host, transformed_obj)
    assert not host
    assert 'empty ip_addresses' in transformed_obj['removed']


def test_do_not_remove_set_ip_addresses():
    """Test do not remove set host ip_addresses."""
    host = {
        'ip_addresses': ['192.168.10.10']}
    transformed_obj = {'removed': []}
    TransformIPAddress().run(host, transformed_obj)
    assert host == {'ip_addresses': ['192.168.10.10']}
    assert len(transformed_obj['removed']) == 0


def test_ip_addresses_field():
    """Test remove both empty ip and mac addresses."""
    host = {}
    transformed_obj = {'removed': []}
    TransformIPAddress().run(host, transformed_obj)
    assert len(transformed_obj['removed']) == 0
    assert not host


def test_remove_duplicate_ip_addresses():
    """Test remove duplicate entries & make host ip_addresses unique."""
    host = {
        'ip_addresses': ['192.168.10.10', '192.168.10.10']}
    transformed_obj = {'modified': []}
    TransformIPAddress().run(host, transformed_obj)
    assert host == {'ip_addresses': ['192.168.10.10']}
    assert transformed_obj['modified']


def test_remove_empty_items_in_ip_addresses():
    """Test remove empty items in ip_addresses."""
    host = {
        'ip_addresses': ['192.168.10.10', '', '192.168.10.11']}
    transformed_obj = {'modified': []}
    TransformIPAddress().run(host, transformed_obj)
    assert host == {'ip_addresses': ['192.168.10.10', '192.168.10.11']}
    assert transformed_obj['modified']
