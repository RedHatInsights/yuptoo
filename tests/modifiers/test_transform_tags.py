from yuptoo.modifiers.transform_tags import TransformTags


def test_transform_tags_value_to_string():
    """Test tags transformation for host."""
    host = {'tags': [
        {
            'namespace': 'satellite_parameter',
            'key': 'host_registration_insights',
            'value': True
        },
        {
            'namespace': 'satellite_parameter',
            'key': 'host_registration_remote_execution',
            'value': False
        },
        {
            'namespace': 'satellite',
            'key': 'organization_id',
            'value': 1
        }
    ]}

    transformed_obj = {'removed': [], 'modified': [], 'missing_data': []}
    TransformTags().run(host, transformed_obj)

    result = {'tags': [
            {
                'namespace': 'satellite_parameter',
                'key': 'host_registration_insights',
                'value': 'true'
            },
            {
                'namespace': 'satellite_parameter',
                'key': 'host_registration_remote_execution',
                'value': 'false'
            },
            {
                'namespace': 'satellite',
                'key': 'organization_id',
                'value': '1'
            }
        ]}

    assert host == result
    assert 'tags' in transformed_obj['modified']
