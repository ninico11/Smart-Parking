from flask import Flask
from dotenv import load_dotenv
import os
from flask_jwt_extended import JWTManager
from datetime import timedelta
from flask_pydantic_spec import FlaskPydanticSpec


api = FlaskPydanticSpec('flask')

def create_app():
    # Create and configure the flask app
    app = Flask(__name__)
    
    from app.parking_apis import parking_blueprint
    app.register_blueprint(parking_blueprint)

    # Add the validator and docs creator
    api.register(app)

    # JWT set up
    # app.config["JWT_SECRET_KEY"] = os.environ.get("JWT_SECRET_KEY")
    # app.config["JWT_ACCESS_TOKEN_EXPIRES"] = timedelta(hours=5)
    # JWTManager(app)

    return app