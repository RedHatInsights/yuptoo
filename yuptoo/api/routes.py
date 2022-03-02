from .v1.status import Status
from .v1.openapi import OpenAPI

def initialize_routes(api):
    api.add_resource(Status, '/api/yuptoo/v1/status')
    api.add_resource(OpenAPI, '/api/yuptoo/v1/openapi.json')
