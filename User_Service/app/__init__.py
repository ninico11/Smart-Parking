from flask import Flask
from dotenv import load_dotenv
import os
from flask_jwt_extended import JWTManager
from datetime import timedelta
from flask_pydantic_spec import FlaskPydanticSpec
import requests
import sys
import logging
from flask_sqlalchemy import SQLAlchemy
from flask_socketio import SocketIO

# Load environment variables
load_dotenv()

db = SQLAlchemy()
api = FlaskPydanticSpec('flask')

# Initialize SocketIO with threading mode
socketio = SocketIO(cors_allowed_origins="*", async_mode='threading')

def create_app():
    app = Flask(__name__)

    # Database setup
    database_url = os.getenv("DATABASE_URL", 'postgresql://user:password@db1/postgres')
    
    app.config['SQLALCHEMY_DATABASE_URI'] = database_url
    db.init_app(app)

    from app.user_apis import user_blueprint
    app.register_blueprint(user_blueprint)

    with app.app_context():
        db.create_all()

    # Register API specs
    api.register(app)

    # JWT setup
    app.config["JWT_SECRET_KEY"] = 'secret_key'
    app.config["JWT_ACCESS_TOKEN_EXPIRES"] = timedelta(hours=1)
    JWTManager(app)

    # Register with service discovery
    address = os.getenv("USER_SERVICE_ADDRESS", 'http://localhost')
    port = os.getenv("USER_SERVICE_PORT", '8080')
    name = os.getenv("USER_SERVICE_NAME", 'no')
    service_discovery_url = os.getenv('SERVICE_DISCOVERY_HOST', 'localhost:3000')

    try:
        response = requests.post(
            url=f"http://{service_discovery_url}/add-service",
            json={"name": name, "address": address, "port": port}
        )

        if response.status_code == 201:
            logging.info("Service registered successfully!")
        elif response.status_code == 409:
            logging.warning("Here is json")
            logging.warning(response.json())
            logging.warning("Service already registered. Skipping registration.")
        else:
            logging.error(f"Failed to register service: {response.status_code} - {response.text}")
            sys.exit(1)

    except requests.exceptions.RequestException as e:
        logging.error(f"Error during service registration: {e}")
        sys.exit(1)

    # Initialize SocketIO with the app
    socketio.init_app(app)

    return app
