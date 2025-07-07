from flask import Flask
from flask_cors import CORS
from neo4j import GraphDatabase
import os
import logging
from dotenv import load_dotenv

# Import route blueprints
from routes.chat_routes import chat_bp
from routes.servicenow_routes import servicenow_bp
from routes.agent_routes import agent_bp
from routes.workflow_routes import workflow_bp
from routes.integration_routes import integration_bp
from routes.auth_routes import auth_bp
from routes.admin_routes import admin_bp

# Import auth manager
from auth import AuthManager

load_dotenv()

def create_app():
    """Application factory pattern"""
    app = Flask(__name__)
    CORS(app)  # Enable CORS for all routes
    
    # Configure logging
    logging.basicConfig(level=logging.INFO)
    
    # Initialize authentication manager
    secret_key = os.environ.get("JWT_SECRET_KEY", "your-secret-key-change-in-production")
    neo4j_uri = os.environ.get('NEO4J_CONNECTION_URL')
    neo4j_username = os.environ.get('NEO4J_USER')
    neo4j_password = os.environ.get('NEO4J_PASSWORD')
    
    # Initialize Neo4j for auth manager
    neo4j_driver = None
    if all([neo4j_uri, neo4j_username, neo4j_password]):
        neo4j_driver = GraphDatabase.driver(neo4j_uri, auth=(neo4j_username, neo4j_password))
    
    app.auth_manager = AuthManager(secret_key, neo4j_driver)
    
    # Register blueprints
    app.register_blueprint(chat_bp)
    app.register_blueprint(servicenow_bp)
    app.register_blueprint(agent_bp)
    app.register_blueprint(workflow_bp)
    app.register_blueprint(integration_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(admin_bp)
    
    return app

# Create app instance
app = create_app()

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5500))
    debug_mode = os.environ.get("FLASK_ENV", "development") == "development"
    app.run(host='0.0.0.0', port=port, debug=debug_mode)