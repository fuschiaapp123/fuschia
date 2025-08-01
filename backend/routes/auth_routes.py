from flask import Blueprint, request, jsonify, current_app
from auth import token_required, org_admin_required, UserRole
import logging

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/auth/register', methods=['POST'])
def register_organization():
    """Register new organization with admin user"""
    try:
        data = request.get_json()
        
        required_fields = ['organization_name', 'domain', 'admin_email', 'admin_password', 
                          'admin_first_name', 'admin_last_name']
        
        if not all(field in data for field in required_fields):
            return jsonify({"error": "Missing required fields"}), 400
        
        # Check if email already exists
        existing_user = current_app.auth_manager.authenticate_user(data['admin_email'], "dummy")
        if existing_user:
            return jsonify({"error": "Email already exists"}), 400
        
        # Create organization and admin user
        organization, admin_user = current_app.auth_manager.create_organization(
            name=data['organization_name'],
            domain=data['domain'],
            admin_email=data['admin_email'],
            admin_password=data['admin_password'],
            admin_first_name=data['admin_first_name'],
            admin_last_name=data['admin_last_name']
        )
        
        # Generate token
        token = current_app.auth_manager.generate_token(admin_user)
        
        return jsonify({
            "message": "Organization created successfully",
            "token": token,
            "user": {
                "id": admin_user.id,
                "email": admin_user.email,
                "first_name": admin_user.first_name,
                "last_name": admin_user.last_name,
                "role": admin_user.role.value
            },
            "organization": {
                "id": organization.id,
                "name": organization.name,
                "domain": organization.domain,
                "subscription_tier": organization.subscription_tier.value
            }
        }), 201
        
    except Exception as e:
        logging.error(f"Error registering organization: {str(e)}")
        return jsonify({"error": str(e)}), 500

@auth_bp.route('/auth/login', methods=['POST'])
def login():
    """User login"""
    try:
        data = request.get_json()
        
        if not data or 'email' not in data or 'password' not in data:
            return jsonify({"error": "Email and password required"}), 400
        
        # Authenticate user
        user = current_app.auth_manager.authenticate_user(data['email'], data['password'])
        if not user:
            return jsonify({"error": "Invalid credentials"}), 401
        
        # Get organization info
        organization = current_app.auth_manager.get_organization_by_id(user.organization_id)
        
        # Generate token
        token = current_app.auth_manager.generate_token(user)
        
        return jsonify({
            "token": token,
            "user": {
                "id": user.id,
                "email": user.email,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "role": user.role.value
            },
            "organization": {
                "id": organization.id if organization else None,
                "name": organization.name if organization else None,
                "domain": organization.domain if organization else None,
                "subscription_tier": organization.subscription_tier.value if organization else None
            }
        })
        
    except Exception as e:
        logging.error(f"Error during login: {str(e)}")
        return jsonify({"error": str(e)}), 500

@auth_bp.route('/auth/me', methods=['GET'])
@token_required
def get_current_user():
    """Get current user info"""
    try:
        user_data = request.current_user
        user = current_app.auth_manager.get_user_by_id(user_data['user_id'])
        organization = current_app.auth_manager.get_organization_by_id(user_data['organization_id'])
        
        return jsonify({
            "user": {
                "id": user.id,
                "email": user.email,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "role": user.role.value
            },
            "organization": {
                "id": organization.id if organization else None,
                "name": organization.name if organization else None,
                "domain": organization.domain if organization else None,
                "subscription_tier": organization.subscription_tier.value if organization else None
            }
        })
        
    except Exception as e:
        logging.error(f"Error getting current user: {str(e)}")
        return jsonify({"error": str(e)}), 500

@auth_bp.route('/auth/users', methods=['GET'])
@org_admin_required
def get_organization_users():
    """Get all users in the organization"""
    try:
        current_user = request.current_user
        
        # Get all users in the same organization
        users = current_app.auth_manager.get_users_by_organization(current_user['organization_id'])
        
        return jsonify({
            "users": [{
                "id": user.id,
                "email": user.email,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "role": user.role.value,
                "is_active": user.is_active,
                "created_at": user.created_at.isoformat() if user.created_at else None,
                "last_login": user.last_login.isoformat() if user.last_login else None
            } for user in users]
        })
        
    except Exception as e:
        logging.error(f"Error getting organization users: {str(e)}")
        return jsonify({"error": str(e)}), 500

@auth_bp.route('/auth/users', methods=['POST'])
@org_admin_required
def create_user():
    """Create new user in organization (admin only)"""
    try:
        data = request.get_json()
        current_user = request.current_user
        
        required_fields = ['email', 'password', 'first_name', 'last_name', 'role']
        if not all(field in data for field in required_fields):
            return jsonify({"error": "Missing required fields"}), 400
        
        # Validate role
        try:
            role = UserRole(data['role'])
        except ValueError:
            return jsonify({"error": "Invalid role"}), 400
        
        # Create user
        user = current_app.auth_manager.create_user(
            email=data['email'],
            password=data['password'],
            first_name=data['first_name'],
            last_name=data['last_name'],
            role=role,
            organization_id=current_user['organization_id']
        )
        
        return jsonify({
            "message": "User created successfully",
            "user": {
                "id": user.id,
                "email": user.email,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "role": user.role.value
            }
        }), 201
        
    except Exception as e:
        logging.error(f"Error creating user: {str(e)}")
        return jsonify({"error": str(e)}), 500