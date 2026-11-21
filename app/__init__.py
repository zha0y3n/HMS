from flask import Flask
from app.routes.rooms import room_bp
from app.routes.orders import order_bp


def create_app() -> Flask:
    app = Flask(__name__)
    app.register_blueprint(room_bp)
    app.register_blueprint(order_bp)
    return app
