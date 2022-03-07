from flask import send_file
from flask_restful import Resource


class OpenAPI(Resource):
    def get(self):
        return send_file("../openapi/openapi.json")
