import os
from flask import Flask, render_template
from dotenv import load_dotenv

load_dotenv()

def create_app():
    app = Flask(__name__, template_folder='../templates', static_folder='../static')
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')

    # Register API routes
    from app.routes import register_routes
    register_routes(app)

    # Add root route for homepage here
    @app.route('/')
    def index():
        return render_template('index.html')

    return app
