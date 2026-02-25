"""AgentERP Flask Application Factory."""
import os
import redis
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_cors import CORS
from flask_jwt_extended import JWTManager

from config import config

# Extensions
db = SQLAlchemy()
migrate = Migrate()
jwt = JWTManager()
redis_client = None


def create_app(config_name=None):
    """Create and configure the Flask application."""
    if config_name is None:
        config_name = os.environ.get('FLASK_ENV', 'development')

    app = Flask(__name__)
    app.config.from_object(config.get(config_name, config['default']))

    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    CORS(app, origins=app.config.get('CORS_ORIGINS', '*'))
    jwt.init_app(app)

    # Initialize Redis
    global redis_client
    try:
        redis_client = redis.from_url(
            app.config.get('REDIS_URL', 'redis://localhost:6379/0'),
            decode_responses=True
        )
        redis_client.ping()
        app.logger.info('Redis connection established')
    except Exception as e:
        app.logger.warning(f'Redis connection failed: {e}. Running without Redis.')
        redis_client = None

    # Register blueprints
    from app.routes.auth import auth_bp
    from app.routes.tenant import tenant_bp
    from app.routes.subscription import subscription_bp
    from app.routes.admin import admin_bp
    from app.routes.analytics import analytics_bp
    from app.routes.organisation import org_bp
    from app.routes.modules import modules_bp
    from app.routes.inventory import inventory_bp
    from app.routes.sales import sales_bp
    from app.routes.purchasing import purchasing_bp

    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(tenant_bp, url_prefix='/api/tenants')
    app.register_blueprint(subscription_bp, url_prefix='/api/subscriptions')
    app.register_blueprint(admin_bp, url_prefix='/api/admin')
    app.register_blueprint(analytics_bp, url_prefix='/api/analytics')
    app.register_blueprint(org_bp, url_prefix='/api/organisation')
    app.register_blueprint(modules_bp, url_prefix='/api/modules')
    app.register_blueprint(inventory_bp, url_prefix='/api/inventory')
    app.register_blueprint(sales_bp, url_prefix='/api/sales')
    app.register_blueprint(purchasing_bp, url_prefix='/api/purchasing')

    # Register error handlers
    register_error_handlers(app)

    # Health check
    @app.route('/api/health')
    def health():
        return {'status': 'healthy', 'version': '0.3.0', 'phase': 3}

    return app


def register_error_handlers(app):
    """Register application error handlers."""

    @app.errorhandler(400)
    def bad_request(e):
        return {'error': 'Bad Request', 'message': str(e)}, 400

    @app.errorhandler(401)
    def unauthorized(e):
        return {'error': 'Unauthorized', 'message': 'Authentication required'}, 401

    @app.errorhandler(403)
    def forbidden(e):
        return {'error': 'Forbidden', 'message': 'Access denied'}, 403

    @app.errorhandler(404)
    def not_found(e):
        return {'error': 'Not Found', 'message': 'Resource not found'}, 404

    @app.errorhandler(500)
    def internal_error(e):
        return {'error': 'Internal Server Error', 'message': 'An unexpected error occurred'}, 500
