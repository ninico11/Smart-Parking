from flask import Flask
from dotenv import load_dotenv
import os
from flask_jwt_extended import JWTManager
from datetime import timedelta
import requests
from flask_sqlalchemy import SQLAlchemy
from flask_socketio import SocketIO
from prometheus_flask_exporter import PrometheusMetrics
# Load environment variables
load_dotenv()

# Initialize extensions
db = SQLAlchemy()
jwt = JWTManager()
socketio = SocketIO(cors_allowed_origins="*", async_mode='threading')

def create_app():
    app = Flask(__name__)
    metrics = PrometheusMetrics(app)
    # Application configurations
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv("DATABASE_URL", 'postgresql://user:password@db1/postgres')
    app.config["JWT_SECRET_KEY"] = os.getenv("JWT_SECRET_KEY", 'supersecretkey')
    app.config["JWT_ACCESS_TOKEN_EXPIRES"] = timedelta(hours=1)

    # Initialize extensions with app
    db.init_app(app)
    jwt.init_app(app)
    socketio.init_app(app)

    # Register blueprints (e.g., user and parking services)
    from app.user_apis import user_blueprint
    app.register_blueprint(user_blueprint)

    # Create database tables if they don't exist
    with app.app_context():
        db.create_all()
        
    # Service discovery registration
    try:
        address = os.getenv("USER_SERVICE_ADDRESS", 'http://localhost')
        port = os.getenv("USER_SERVICE_PORT", '8080')
        name = os.getenv("USER_SERVICE_NAME", 'no') 
        service_discovery_url = os.getenv('SERVICE_DISCOVERY_HOST', 'localhost:3000')
        
        # Register this service with the service discovery
        response = requests.post(
            url=f"http://{service_discovery_url}/add-service",
            json={"name": name, "address": address, "port": port}
        )
        if response.status_code == 201:
            print("Service registered successfully!")
        elif response.status_code == 409:
            print("Service already registered.")
        else:
            print(f"Failed to register service: {response.status_code} - {response.text}")
    except requests.exceptions.RequestException as e:
        print(f"Error during service registration: {e}")

    return app
