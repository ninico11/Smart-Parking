from flask import Flask
from dotenv import load_dotenv
import os
import requests
from prometheus_flask_exporter import PrometheusMetrics


# Load environment variables
load_dotenv()
def create_app():
    # Create and configure the Flask app
    app = Flask(__name__)
    metrics = PrometheusMetrics(app)
    
    # Register the parking blueprint
    from app.parking_apis import parking_blueprint
    app.register_blueprint(parking_blueprint)
    
    try:
        # Load address and port from environment variables
        address = os.getenv("PARKING_SERVICE_ADDRESS", 'http://localhost')
        port = os.getenv("PARKING_SERVICE_PORT", '8000')
        name = os.getenv("PARKING_SERVICE_NAME", 'no')
        service_discovery_url = os.getenv('SERVICE_DISCOVERY_HOST', 'localhost:3000')
        response = requests.post(
            url=f"http://{service_discovery_url}/add-service",
            json={"name": name, "address": address, "port": port}
        )

        if response.status_code == 201:
            print("Service registered successfully!")
        elif response.status_code == 409:
            print("Service already registered. Skipping registration.")
        else:
            print(f"Failed to register service: {response.status_code} - {response.text}")
    except requests.exceptions.RequestException as e:
        print(f"Error during service registration: {e}")
    # print(app.url_map)
    return app
