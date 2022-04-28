from yuptoo.modifiers.remove_invalid_bios_uuid import RemoveInvalidBiosUUID


def test_remove_invalid_bios_uuid():
    """Test remove invalid bios UUID."""
    host = {
        'fqdn': 'virt-who.example.com',
        'bios_uuid': '45AA7104-5CB0-4A75-945D-7173C8DC5744443'
    }
    transformed_obj = {'removed': []}
    RemoveInvalidBiosUUID().run(host, transformed_obj)
    assert host == {'fqdn': 'virt-who.example.com'}
    assert 'invalid uuid: 45AA7104-5CB0-4A75-945D-7173C8DC5744443' in transformed_obj['removed']


def test_remove_invalid_bios_uuid_of_boolean_type():
    """Test remove invalid bios UUID of boolean type."""
    host = {
        'fqdn': 'virt-who.example.com',
        'bios_uuid': True
    }
    transformed_obj = {'removed': []}
    RemoveInvalidBiosUUID().run(host, transformed_obj)
    assert host == {'fqdn': 'virt-who.example.com'}
    assert 'invalid uuid: True' in transformed_obj['removed']


def test_remove_invalid_bios_uuid_of_number_type():
    """Test remove invalid bios UUID of number type."""
    host = {
        'fqdn': 'virt-who.example.com',
        'bios_uuid': 100
    }
    transformed_obj = {'removed': []}
    RemoveInvalidBiosUUID().run(host, transformed_obj)
    assert host == {'fqdn': 'virt-who.example.com'}
    assert 'invalid uuid: 100' in transformed_obj['removed']


def test_remove_empty_bios_uuid():
    """Test remove empty bios UUID field."""
    host = {
        'fqdn': 'virt-who.example.com',
        'bios_uuid': ''
    }
    transformed_obj = {'removed': []}
    RemoveInvalidBiosUUID().run(host, transformed_obj)
    assert host == {'fqdn': 'virt-who.example.com'}
    assert 'invalid uuid: ' in transformed_obj['removed']


def test_bios_uuid_validation_should_be_case_insensitive():
    """Test bios UUID validation should be case insensitive."""
    host = {
        'fqdn': 'virt-who.example.com',
        'bios_uuid': '801CA199-9402-41CE-98DC-F3AA6E5BC6B3'
    }
    transformed_obj = {'removed': []}
    RemoveInvalidBiosUUID().run(host, transformed_obj)
    assert host['bios_uuid'] == '801CA199-9402-41CE-98DC-F3AA6E5BC6B3'
    assert len(transformed_obj['removed']) == 0


def test_do_not_remove_valid_bios_uuid():
    """Test do not remove valid bios UUID."""
    host = {
        'fqdn': 'virt-who.example.com',
        'bios_uuid': '123e4567-e89b-12d3-a456-426614174000'
    }
    transformed_obj = {'removed': []}
    RemoveInvalidBiosUUID().run(host, transformed_obj)
    assert host['bios_uuid'] == '123e4567-e89b-12d3-a456-426614174000'
    assert len(transformed_obj['removed']) == 0
