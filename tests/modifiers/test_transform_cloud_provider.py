from yuptoo.modifiers.transform_cloud_provider import TransformCloudProvider


def test_transform_cloud_provider():
    """Test cloud_provider transformation for host
    when there is google."""
    host = {
        'system_profile': {
            'cloud_provider': 'google'
        }}
    transformed_obj = {'removed': [], 'modified': [], 'missing_data': []}
    TransformCloudProvider().run(host, transformed_obj)
    result = {
            'system_profile': {
                'cloud_provider': 'gcp'
            }
        }
    assert host == result


def test_cloud_provider_tranform_method_for_non_cloud():
    """Test transformation for non cloud host"""
    host = {
        'fqdn': 'virt-who-samplevpa11.mtn.co.za-1',
        'system_profile': {
            'infrastructure_type': 'physical'
        }}
    transformed_obj = {'removed': [], 'modified': [], 'missing_data': []}
    TransformCloudProvider().run(host, transformed_obj)
    result = {
        'fqdn': 'virt-who-samplevpa11.mtn.co.za-1',
        'system_profile': {
            'infrastructure_type': 'physical'
        }}
    assert host == result
