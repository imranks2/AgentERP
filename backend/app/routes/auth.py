"""Authentication routes."""
from datetime import datetime, timezone
from flask import Blueprint, request, jsonify
from flask_jwt_extended import (
    create_access_token, create_refresh_token,
    jwt_required, get_jwt_identity, get_jwt
)
from app import db
from app.models.user import User
from app.services.analytics_service import AnalyticsService

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/login', methods=['POST'])
def login():
    """Authenticate user and return JWT tokens."""
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Request body required'}), 400

    email = data.get('email')
    password = data.get('password')

    if not email or not password:
        return jsonify({'error': 'Email and password are required'}), 400

    user = User.query.filter_by(email=email, is_active=True).first()
    if not user or not user.check_password(password):
        return jsonify({'error': 'Invalid email or password'}), 401

    # Check tenant is active (if not platform admin)
    if not user.is_platform_admin and user.tenant:
        if not user.tenant.is_active:
            return jsonify({'error': 'Your organisation account is inactive'}), 403

    # Update last login
    user.last_login_at = datetime.now(timezone.utc)
    db.session.commit()

    # Create tokens with user_id as identity and claims for extra info
    claims = {
        'tenant_id': user.tenant_id,
        'email': user.email,
        'role': user.role,
        'is_platform_admin': user.is_platform_admin,
    }
    access_token = create_access_token(identity=user.id, additional_claims=claims)
    refresh_token = create_refresh_token(identity=user.id, additional_claims=claims)

    # Track login event
    AnalyticsService.track_event(
        event_type='auth',
        event_action='login',
        tenant_id=user.tenant_id,
        user_id=user.id,
        source='api',
    )

    return jsonify({
        'access_token': access_token,
        'refresh_token': refresh_token,
        'user': user.to_dict(),
    })


@auth_bp.route('/refresh', methods=['POST'])
@jwt_required(refresh=True)
def refresh():
    """Refresh access token."""
    user_id = get_jwt_identity()
    claims = get_jwt()
    additional_claims = {
        'tenant_id': claims.get('tenant_id'),
        'email': claims.get('email'),
        'role': claims.get('role'),
        'is_platform_admin': claims.get('is_platform_admin'),
    }
    access_token = create_access_token(identity=user_id, additional_claims=additional_claims)
    return jsonify({'access_token': access_token})


@auth_bp.route('/me', methods=['GET'])
@jwt_required()
def me():
    """Get current authenticated user."""
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    if not user:
        return jsonify({'error': 'User not found'}), 404
    return jsonify({'user': user.to_dict()})


@auth_bp.route('/register', methods=['POST'])
def register_tenant():
    """Register a new tenant with admin user (sign-up flow)."""
    from app.services.tenant_service import TenantService

    data = request.get_json()
    if not data:
        return jsonify({'error': 'Request body required'}), 400

    required_fields = ['company_name', 'email', 'first_name', 'last_name', 'password']
    missing = [f for f in required_fields if not data.get(f)]
    if missing:
        return jsonify({'error': f'Missing required fields: {", ".join(missing)}'}), 400

    try:
        tenant, admin_user = TenantService.create_tenant(
            name=data['company_name'],
            email=data['email'],
            admin_first_name=data['first_name'],
            admin_last_name=data['last_name'],
            admin_password=data['password'],
            phone=data.get('phone'),
            address=data.get('address'),
        )

        # Auto-login after registration
        claims = {
            'tenant_id': tenant.id,
            'email': admin_user.email,
            'role': admin_user.role,
            'is_platform_admin': False,
        }
        access_token = create_access_token(identity=admin_user.id, additional_claims=claims)
        refresh_token = create_refresh_token(identity=admin_user.id, additional_claims=claims)

        # Track registration
        AnalyticsService.track_event(
            event_type='auth',
            event_action='register',
            tenant_id=tenant.id,
            user_id=admin_user.id,
            source='api',
        )

        return jsonify({
            'message': 'Registration successful',
            'tenant': tenant.to_dict(),
            'user': admin_user.to_dict(),
            'access_token': access_token,
            'refresh_token': refresh_token,
        }), 201

    except ValueError as e:
        return jsonify({'error': str(e)}), 400
