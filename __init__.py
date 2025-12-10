from flask import Flask
from config import init_clients

def create_app():
    app = Flask(__name__)
    
    # Initialize clients and store in app context
    mongo_client, groq_client = init_clients()
    app.mongo_client = mongo_client
    app.groq_client = groq_client
    
    # Import and register routes
    from routes import bp
    app.register_blueprint(bp)
    
    return app