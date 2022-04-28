from yuptoo.modifiers.transform_mac_addresses import TransformMacAddresses


def test_transform_mac_addresses():
    """Test transform mac_addresses."""
    host = {'mac_addresses': []}
    transformed_obj = {'removed': []}
    TransformMacAddresses().run(host, transformed_obj)
    assert host == {}
    assert 'empty mac_addresses' in transformed_obj['removed']


def test_do_not_remove_set_mac_addresses():
    """Test do not remove set host mac_addresses."""
    host = {'mac_addresses': ['aa:bb:00:11:22:33']}
    transformed_obj = {'modified': []}
    TransformMacAddresses().run(host, transformed_obj)
    assert host == {'mac_addresses': ['aa:bb:00:11:22:33']}
    assert 'transformed mac_addresses to store unique values' in transformed_obj['modified']


def test_remove_empty_mac_addresses():
    """Test remove both empty ip and mac addresses."""
    host = {}
    transformed_obj = {'removed': []}
    TransformMacAddresses().run(host, transformed_obj)
    assert host == {}
    assert len(transformed_obj['removed']) == 0
