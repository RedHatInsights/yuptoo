from uuid import UUID
from yuptoo.processor.utils import Modifier


class RemoveInvalidBiosUUID(Modifier):
    def run(self, host: dict, transformed_obj: dict, **kwargs):
        """Remove invalid bios UUID."""
        uuid = host.get('bios_uuid')
        if uuid is None:
            return [host, transformed_obj]

        if not self.is_valid_uuid(uuid):
            transformed_obj['removed'].append('invalid uuid: %s' % uuid)
            del host['bios_uuid']

    def is_valid_uuid(self, uuid):
        """Validate a UUID string."""
        try:
            uuid_obj = UUID(str(uuid))
        except ValueError:
            return False

        return str(uuid_obj) == uuid.lower()
