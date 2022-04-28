from yuptoo.modifiers.remove_display_name import RemoveDisplayName


def test_remove_display_name():
    host = {'display_name': 'test.example.com'}
    transformed_obj = {'removed': [], 'modified': [], 'missing_data': []}
    RemoveDisplayName().run(host, transformed_obj)
    assert host == {}
    assert 'display_name' in transformed_obj['removed']
