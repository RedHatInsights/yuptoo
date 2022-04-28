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


def test_do_not_tranform_os_kernel_field():
    """Test do not transform os fields when already in format."""
    host = {'system_profile': {
        'os_release': '7', 'os_kernel_version': '2.6.32'}}
    transformed_obj = {'modified': []}
    TransformOsKernalVersion().run(host, transformed_obj)
    assert host == {'system_profile': {'os_release': '7', 'os_kernel_version': '2.6.32'}}
