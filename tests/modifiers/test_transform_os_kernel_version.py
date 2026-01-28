from yuptoo.modifiers.transform_os_kernel_version import TransformOsKernalVersion


def test_transform_os_kernel_field():
    """Test transform os fields."""
    host = {'system_profile': {
        'os_release': '7', 'os_kernel_version': '3.10.0-1127.el7.x86_64'
    }}
    transformed_obj = {'modified': []}
    TransformOsKernalVersion().run(host, transformed_obj)
    assert host == {'system_profile': {'os_release': '7', 'os_kernel_version': '3.10.0'}}
    assert "os_kernel_version from '3.10.0-1127.el7.x86_64' to '3.10.0'" in transformed_obj['modified']

    host = {'system_profile': {
        'os_release': '7', 'os_kernel_version': '4.10.0+'
    }}
    transformed_obj = {'modified': []}
    TransformOsKernalVersion().run(host, transformed_obj)
    assert host == {'system_profile': {'os_release': '7', 'os_kernel_version': '4.10.0'}}
    assert "os_kernel_version from '4.10.0+' to '4.10.0'" in transformed_obj['modified']


def test_do_not_tranform_os_kernel_field():
    """Test do not transform os fields when already in format."""
    host = {'system_profile': {
        'os_release': '7', 'os_kernel_version': '2.6.32'}}
    transformed_obj = {'modified': []}
    TransformOsKernalVersion().run(host, transformed_obj)
    assert host == {'system_profile': {'os_release': '7', 'os_kernel_version': '2.6.32'}}


def test_transform_os_kernel_field_with_special_value():
    """Test transform os fields with special values, the known examples are:
        - 6.12.48+deb13
        - 5.11.5.ppa.el.x86_64
        - 4.14.44.solos2
        - 6.1.35fio
    """
    host = {'system_profile': {'key_a': 'va', 'os_kernel_version': '6.12.48+deb13'}}
    transformed_obj = {'modified': []}
    TransformOsKernalVersion().run(host, transformed_obj)
    assert host == {'system_profile': {'key_a': 'va', 'os_kernel_version': '6.12.48'}}
    assert "os_kernel_version from '6.12.48+deb13' to '6.12.48'" in transformed_obj['modified']

    host = {'system_profile': {'key_a': 'va', 'os_kernel_version': '5.11.5.ppa.el.x86_64'}}
    transformed_obj = {'modified': []}
    TransformOsKernalVersion().run(host, transformed_obj)
    assert host == {'system_profile': {'key_a': 'va', 'os_kernel_version': '5.11.5'}}
    assert "os_kernel_version from '5.11.5.ppa.el.x86_64' to '5.11.5'" in transformed_obj['modified']

    host = {'system_profile': {'key_a': 'va', 'os_kernel_version': '4.14.44.solos2'}}
    transformed_obj = {'modified': []}
    TransformOsKernalVersion().run(host, transformed_obj)
    assert host == {'system_profile': {'key_a': 'va', 'os_kernel_version': '4.14.44'}}
    assert "os_kernel_version from '4.14.44.solos2' to '4.14.44'" in transformed_obj['modified']

    host = {'system_profile': {'key_a': 'va', 'os_kernel_version': '6.1.35fio'}}
    transformed_obj = {'modified': []}
    TransformOsKernalVersion().run(host, transformed_obj)
    assert host == {'system_profile': {'key_a': 'va', 'os_kernel_version': '6.1.35'}}
    assert "os_kernel_version from '6.1.35fio' to '6.1.35'" in transformed_obj['modified']
