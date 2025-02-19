from unittest.mock import patch
from yuptoo.modifiers.transform_installed_packages import TransfromInstalledPackages


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
    with patch('yuptoo.modifiers.transform_installed_packages.KAFKA_PRODUCER_OVERRIDE_MAX_REQUEST_SIZE', 0):
        TransfromInstalledPackages().run(host, transformed_obj)
    assert len(transformed_obj['modified']) == 0
    assert len(transformed_obj['removed']) == 1
    assert 'installed_packages' in transformed_obj['removed']
    assert host['system_profile'].get('installed_packages', 0) == 0


def test_modify_installed_packages():
    """Test modify installed_packages when missing epoch."""
    # installed_packages epoch modified successfully
    host = {
            'system_profile': {
                "installed_packages": [
                    "kmod-25-19.el8.x86_64",
                    "subscription-manager-1.28.40-1.el8_9.x86_64",
                    "openssl-1:1.1.1k-9.el8_7.x86_64",
                    "kernel-4.18.0-513.5.1.el8_9.x86_64",
                    "qemu-guest-agent-15:6.2.0-40.module+el8.9.0+20056+d9fb1ac3.1.x86_64",
                    "lvm2-libs-8:2.03.14-13.el8_9.x86_64",
                    "insights-client-3.2.2-1.el8_9.noarch"
                ]
            },
            'tags': []
        }
    transformed_obj = {'removed': [], 'modified': [], 'missing_data': []}
    TransfromInstalledPackages().run(host, transformed_obj)
    assert len(transformed_obj['removed']) == 0
    assert len(transformed_obj['modified']) == 1
    assert 'installed_packages: prepending default epoch of 0 when missing' in transformed_obj['modified']
    assert len(host['system_profile']['installed_packages']) == 7
    assert host['system_profile']['installed_packages'] == [
                    "kmod-0:25-19.el8.x86_64",
                    "subscription-manager-0:1.28.40-1.el8_9.x86_64",
                    "openssl-1:1.1.1k-9.el8_7.x86_64",
                    "kernel-0:4.18.0-513.5.1.el8_9.x86_64",
                    "qemu-guest-agent-15:6.2.0-40.module+el8.9.0+20056+d9fb1ac3.1.x86_64",
                    "lvm2-libs-8:2.03.14-13.el8_9.x86_64",
                    "insights-client-0:3.2.2-1.el8_9.noarch"
                ]

    # installed_packages epoch modified failure: error in package converting
    host = {
            'system_profile': {
                "installed_packages": [
                    "openssl-1:1.1.1k-9.el8_7.x86_64",
                    "openssh-server#$%^5.3p1$%^104.el6.x86_64",
                    "kernel-4.18.0-513.5.1.el8_9.x86_64",
                    "insights-client-3.2.2-1.el8_9.noarch"
                ]
            },
            'tags': []
        }
    transformed_obj = {'removed': [], 'modified': [], 'missing_data': []}
    TransfromInstalledPackages().run(host, transformed_obj)
    assert len(transformed_obj['modified']) == 0
    assert len(transformed_obj['removed']) == 1
    assert 'installed_packages: prepending default epoch failure: ' in transformed_obj['removed'][0]
    assert 'installed_packages' not in host['system_profile']
