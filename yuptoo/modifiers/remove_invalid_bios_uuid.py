from uuid import UUID

def run(host: dict, transformed_obj: dict, request_obj: dict):
    """Remove invalid bios UUID."""
    uuid = host.get('bios_uuid')
    if uuid is None:
        return [host, transformed_obj]

    if not is_valid_uuid(uuid):
        transformed_obj['removed'].append('invalid uuid: %s' % uuid)
        del host['bios_uuid']

def is_valid_uuid(uuid):
        """Validate a UUID string."""
        try:
            uuid_obj = UUID(str(uuid))
        except ValueError:
            return False

        return str(uuid_obj) == uuid.lower()