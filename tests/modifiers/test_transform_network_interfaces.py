from yuptoo.modifiers.transform_network_interfaces import TransformNetworkInterfaces


def test_transform_mtu_to_integer():
    """Test mtu transformation for host."""
    host = {
        'system_profile': {
            'network_interfaces': [
                {'ipv4_addresses': [], 'ipv6_addresses': [],
                    'mtu': 1400, 'name': 'eth0'},
                {'ipv4_addresses': [], 'ipv6_addresses': [],
                    'mtu': '1500', 'name': 'eth1'}]
        }}
    transformed_obj = {'removed': [], 'modified': [], 'missing_data': []}
    TransformNetworkInterfaces().run(host, transformed_obj)
    result = {
            'system_profile': {
                'network_interfaces': [
                    {'ipv4_addresses': [], 'ipv6_addresses': [],
                        'mtu': 1400, 'name': 'eth0'},
                    {'ipv4_addresses': [], 'ipv6_addresses': [],
                        'mtu': 1500, 'name': 'eth1'}]
            }
        }
    assert host == result


def test_remove_nic_when_empty_string_in_name():
    """Test to remove network_interface when name is empty."""
    host = {
        'system_profile': {
            'network_interfaces': [
                {'ipv4_addresses': [], 'ipv6_addresses': [], 'name': ''},
                {'ipv4_addresses': [], 'ipv6_addresses': []},
                {'ipv4_addresses': [],
                    'ipv6_addresses': [], 'name': 'eth0'}
            ]
        }}
    transformed_obj = {'removed': [], 'modified': [], 'missing_data': []}
    TransformNetworkInterfaces().run(host, transformed_obj)
    assert host == {'system_profile': {
                    'network_interfaces': [
                        {
                            'ipv4_addresses': [], 'ipv6_addresses': [], 'name': 'eth0'
                        }
                        ]}
                    }


def test_remove_empty_strings_in_ipv6_addresses():
    """Test to verify transformation for 'ipv6 addresses' in host."""
    ipv6_address = '2021:0db8:85a3:0000:0000:8a2e:0370:7335'
    host = {
        'system_profile': {
            'network_interfaces': [
                {'ipv4_addresses': [],
                    'ipv6_addresses': ['', ipv6_address, ''],
                    'name': 'eth0'},
                {'ipv4_addresses': [],
                    'ipv6_addresses': [''], 'name': 'eth1'}]
        }}

    transformed_obj = {'removed': [], 'modified': [], 'missing_data': []}
    TransformNetworkInterfaces().run(host, transformed_obj)
    result = {
            'system_profile': {
                'network_interfaces': [
                    {'ipv4_addresses': [],
                        'ipv6_addresses': [ipv6_address],
                        'name': 'eth0'},
                    {'ipv4_addresses': [],
                        'ipv6_addresses': [], 'name': 'eth1'}]
            }
        }
    assert host == result
    nics = host['system_profile']['network_interfaces']
    assert len(nics) == 2
    filtered_nics = [nic for nic in nics if nic.get('name') == 'eth0']
    assert len(filtered_nics)
    assert len(filtered_nics[0]['ipv6_addresses']) == 1


def test_do_not_run_mtu_transformation_when_not_exists():
    """Test not to run mtu transformation when it doesn't exist."""
    host = {
        'system_profile': {
            'network_interfaces': [
                {'ipv4_addresses': [], 'ipv6_addresses': [],
                    'name': 'eth0'}]
        }}

    transformed_obj = {'removed': [], 'modified': [], 'missing_data': []}
    TransformNetworkInterfaces().run(host, transformed_obj)
    result = {
            'system_profile': {
                'network_interfaces': [
                    {'ipv4_addresses': [], 'ipv6_addresses': [],
                        'name': 'eth0'}]
            }
        }
    assert host == result


def test_do_not_run_mtu_transformation_when_none():
    """Test not to run mtu transformation when it is None."""
    host = {
        'system_profile': {
            'network_interfaces': [
                {'ipv4_addresses': [], 'ipv6_addresses': [],
                    'mtu': None, 'name': 'eth0'}]
        }}

    transformed_obj = {'removed': [], 'modified': [], 'missing_data': []}
    TransformNetworkInterfaces().run(host, transformed_obj)
    result = {
            'system_profile': {
                'network_interfaces': [
                    {'ipv4_addresses': [], 'ipv6_addresses': [],
                        'mtu': None, 'name': 'eth0'}]
            }
        }
    assert host == result


def test_omit_nics_starts_with_cali():
    """Test omit nics starts with cali from host."""
    host = {
            'mac_addresses': ['value', 'test'],
            'system_profile': {
                'network_interfaces': [
                    {'ipv4_addresses': ['192.168.10.10'], 'ipv6_addresses': [],
                     'mac_address': 'value', 'name': 'cali916c8937279'},
                    {'ipv4_addresses': ['192.168.10.11'], 'ipv6_addresses': [],
                     'mac_address': 'test', 'name': 'testcali'},
                ]
            }}
    transformed_obj = {'removed': [], 'modified': [], 'missing_data': []}
    TransformNetworkInterfaces().run(host, transformed_obj)
    result = {
        'mac_addresses': ['test'],
        'system_profile': {
            'network_interfaces': [
                {'ipv4_addresses': ['192.168.10.11'],
                 'ipv6_addresses': [],
                 'mac_address': 'test', 'name': 'testcali'}
            ]}}
    assert host == result


def test_remove_empty_mac_addresses_while_omitting_nics():
    """Test remove mac addrs for omitted nics,remove empty mac_addrs."""
    host = {
            'mac_addresses': ['value'],
            'system_profile': {
                'network_interfaces': [
                    {'ipv4_addresses': ['192.168.10.10'], 'ipv6_addresses': [],
                     'mac_address': 'value', 'name': 'cali916c8937279'}
                ]
            }}
    transformed_obj = {'removed': [], 'modified': [], 'missing_data': []}
    TransformNetworkInterfaces().run(host, transformed_obj)
    result = {'system_profile': {'network_interfaces': []}}
    assert host == result
