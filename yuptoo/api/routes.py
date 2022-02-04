from .v1.status import Status

def initialize_routes(api):
    api.add_resource(Status, '/api/yuptoo/v1/status')
