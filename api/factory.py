from quart import Quart
from api.blueprints.doorbell import doorbell_bp
from api.blueprints.errors import errors_bp

def create_app() -> Quart:
    app = Quart(__name__)
    
    app.config["MAX_CONTENT_LENGTH"] = 5 * 1024 * 1024
    
    app.register_blueprint(doorbell_bp)
    app.register_blueprint(errors_bp)
    
    return app