from flask import Flask
from dotenv import load_dotenv
import os
from flask_jwt_extended import JWTManager
from datetime import timedelta
from flask_pydantic_spec import FlaskPydanticSpec
import requests
import sys
import logging

# Load environment variables
load_dotenv()

# Initialize Pydantic spec for validation
api = FlaskPydanticSpec('flask')

def create_app():
    # Create and configure the Flask app
    app = Flask(__name__)
    
    # Register the parking blueprint
    from app.parking_apis import parking_blueprint
    app.register_blueprint(parking_blueprint)

    # Add the validator and docs creator
    api.register(app)

    # Load address and port from environment variables
    address = os.getenv("PARKING_SERVICE_ADDRESS", 'http://localhost')
    port = os.getenv("PARKING_SERVICE_PORT", '8001')
    name = os.getenv("PARKING_SERVICE_NAME", 'no')
    service_discovery_url = os.getenv('SERVICE_DISCOVERY_HOST', 'localhost:3000')
    # Register the service if not already registered
    try:
        response = requests.post(
            url=f"http://{service_discovery_url}/add-service",
            json={"name": name, "address": address, "port": port}
        )

        if response.status_code == 201:
            logging.info("Service registered successfully!")
        elif response.status_code == 409:
            logging.warning("Service already registered. Skipping registration.")
        else:
            logging.error(f"Failed to register service: {response.status_code} - {response.text}")
            sys.exit(1)
    except requests.exceptions.RequestException as e:
        logging.error(f"Error during service registration: {e}")
        sys.exit(1)

    return app
