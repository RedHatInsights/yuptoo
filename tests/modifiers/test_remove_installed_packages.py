from unittest.mock import patch
from yuptoo.modifiers.remove_installed_packages import RemoveInstalledPackages


def test_remove_installed_packages():
    """Test remove installed_packages when message size exceeds."""
    host = {
            'system_profile': {
                'installed_packages': [
                    'pkg1', 'pkg2', 'pkg3'
                ]
            },
            'tags': []
        }
    transformed_obj = {'removed': [], 'modified': [], 'missing_data': []}
    with patch('yuptoo.modifiers.remove_installed_packages.KAFKA_PRODUCER_OVERRIDE_MAX_REQUEST_SIZE', 0):
        RemoveInstalledPackages().run(host, transformed_obj)
    assert 'installed_packages' in transformed_obj['removed']
    assert host['system_profile'].get('installed_packages', 0) == 0
