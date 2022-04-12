def run(host: dict, transformed_obj: dict, request_obj: dict):
    tags = host.get('tags')
    if tags is None:
        return [host, transformed_obj]

    tags_modified = False
    for tag in tags:
        if tag['value'] is None or isinstance(tag['value'], str):
            continue

        if tag['value'] is True:
            tag['value'] = 'true'
        elif tag['value'] is False:
            tag['value'] = 'false'
        else:
            tag['value'] = str(tag['value'])

        tags_modified = True

    if tags_modified:
        transformed_obj['modified'].append('tags')