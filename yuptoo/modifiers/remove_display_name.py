from yuptoo.processor.utils import Modifier


class RemoveDisplayName(Modifier):
    def run(self, host: dict, transformed_obj: dict, **kwargs):
        """Remove 'display_name' field."""
        display_name = host.get('display_name')
        if display_name is not None:
            del host['display_name']
            transformed_obj['removed'].append('display_name')
