"""
Flask routes for key management operations.
"""
from flask import Blueprint, request

from api.middleware.validation import RequestValidator, APIResponse
from services.workflow_service import WorkflowService
from core.exceptions import SteganographyError, ValidationError


key_bp = Blueprint('keys', __name__, url_prefix='/api/keys')
workflow_service = WorkflowService()


@key_bp.route('/generate', methods=['POST'])
def generate_keys():
    """
    Generate new key pairs for a user.
    
    Request:
    - user_name: Name/identifier for the user
    
    Response:
    - key_info: Key generation results
    """
    try:
        # Validate request
        data = request.get_json()
        if not data or 'user_name' not in data:
            return APIResponse.error("user_name is required", 400, 'MISSING_USER_NAME')
        
        user_name = data['user_name'].strip()
        if not user_name:
            return APIResponse.error("user_name cannot be empty", 400, 'INVALID_USER_NAME')
        
        # Validate user name format
        import re
        if not re.match(r'^[a-zA-Z0-9_-]+$', user_name):
            return APIResponse.error("user_name contains invalid characters", 400, 'INVALID_USER_NAME')
        
        if len(user_name) > 50:
            return APIResponse.error("user_name too long (max 50 characters)", 400, 'INVALID_USER_NAME')
        
        # Generate keys
        key_info = workflow_service.generate_key_pairs(user_name)
        
        return APIResponse.success(key_info, f"Keys generated successfully for {user_name}")
        
    except SteganographyError as e:
        return APIResponse.error(str(e), 500, 'KEY_GENERATION_ERROR')
    except Exception as e:
        return APIResponse.error(f"Internal server error: {str(e)}", 500, 'INTERNAL_ERROR')


@key_bp.route('/list', methods=['GET'])
def list_keys():
    """
    List all available keys in the system.
    
    Response:
    - keys_info: Available keys information
    """
    try:
        keys_info = workflow_service.list_available_keys()
        
        return APIResponse.success(keys_info, "Keys listed successfully")
        
    except SteganographyError as e:
        return APIResponse.error(str(e), 500, 'KEY_LISTING_ERROR')
    except Exception as e:
        return APIResponse.error(f"Internal server error: {str(e)}", 500, 'INTERNAL_ERROR')


@key_bp.route('/validate', methods=['POST'])
def validate_keys():
    """
    Validate if keys exist for given users.
    
    Request:
    - user_names: List of user names to check
    
    Response:
    - validation_results: Key existence validation results
    """
    try:
        # Validate request
        data = request.get_json()
        if not data or 'user_names' not in data:
            return APIResponse.error("user_names is required", 400, 'MISSING_USER_NAMES')
        
        user_names = data['user_names']
        if not isinstance(user_names, list):
            return APIResponse.error("user_names must be a list", 400, 'INVALID_USER_NAMES')
        
        if not user_names:
            return APIResponse.error("user_names cannot be empty", 400, 'INVALID_USER_NAMES')
        
        # Validate each user name
        import re
        key_pattern = re.compile(r'^[a-zA-Z0-9_-]+$')
        
        for user_name in user_names:
            if not isinstance(user_name, str) or not user_name.strip():
                return APIResponse.error("All user names must be non-empty strings", 400, 'INVALID_USER_NAMES')
            
            if not key_pattern.match(user_name.strip()):
                return APIResponse.error(f"Invalid user name format: {user_name}", 400, 'INVALID_USER_NAMES')
            
            if len(user_name.strip()) > 50:
                return APIResponse.error(f"User name too long: {user_name}", 400, 'INVALID_USER_NAMES')
        
        # Check key existence
        validation_results = {}
        for user_name in user_names:
            user_name = user_name.strip()
            validation_results[user_name] = {
                'rsa_key_exists': workflow_service.key_manager.key_exists(user_name, 'rsa'),
                'aes_key_exists': workflow_service.key_manager.key_exists(user_name, 'aes'),
                'both_keys_exist': (
                    workflow_service.key_manager.key_exists(user_name, 'rsa') and
                    workflow_service.key_manager.key_exists(user_name, 'aes')
                )
            }
        
        return APIResponse.success(validation_results, "Key validation completed")
        
    except SteganographyError as e:
        return APIResponse.error(str(e), 500, 'KEY_VALIDATION_ERROR')
    except Exception as e:
        return APIResponse.error(f"Internal server error: {str(e)}", 500, 'INTERNAL_ERROR')
