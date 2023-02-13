from yuptoo.processor.utils import Modifier


class TransformTags(Modifier):
    def run(self, host: dict, transformed_obj: dict, **kwargs):
        tags = host.get('tags')
        if tags:
            tags_modified = False
            for tag in tags:

                if len(str(tag['value'])) > 250:
                    tag['value'] = "Original value exceeds 250 characters."
                    tags_modified = True

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
