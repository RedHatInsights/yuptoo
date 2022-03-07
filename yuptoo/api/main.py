from flask_restful import Api
from yuptoo.api.routes import initialize_routes
from flask import Flask

app = Flask(__name__)
api = Api(app)
initialize_routes(api)

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8000)
