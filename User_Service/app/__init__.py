from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from dotenv import load_dotenv
import os
from flask_jwt_extended import JWTManager
from datetime import timedelta
from flask_pydantic_spec import FlaskPydanticSpec


db = SQLAlchemy()
api = FlaskPydanticSpec('flask')

def create_app():
    # Create and configure the flask app
    app = Flask(__name__)
    # Create the db
    app.config['SQLALCHEMY_DATABASE_URI'] = "postgresql://user:password@localhost:1234/postgres"
    app.config["SQLALCHEMY_BINDS"] = {"db1": "postgresql://user:password@localhost:1234/postgres"}
    db.init_app(app)
    
    from app.user_apis import user_blueprint
    app.register_blueprint(user_blueprint)
    
    with app.app_context():
        db.create_all(bind_key=[None, "db1"])

    # Add the validator and docs creator
    api.register(app)

    # JWT set up
    app.config["JWT_SECRET_KEY"] = 'secret_key'
    app.config["JWT_ACCESS_TOKEN_EXPIRES"] = timedelta(hours=1)
    JWTManager(app)

    return app