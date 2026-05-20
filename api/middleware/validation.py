"""
Request validation middleware for the API.
"""
import os
from typing import Dict, Any, Optional
from werkzeug.datastructures import FileStorage
from flask import request
import imghdr

from core.exceptions import ValidationError


class RequestValidator:
    """Validates incoming API requests."""
    
    @staticmethod
    def validate_image_file(file: FileStorage) -> Dict[str, Any]:
        """
        Validate uploaded image file.
        
        Args:
            file: Uploaded file object
            
        Returns:
            Dictionary with file information
            
        Raises:
            ValidationError: If file is invalid
        """
        if not file:
            raise ValidationError("No file provided")
        
        if file.filename == '':
            raise ValidationError("No filename provided")
        
        # Check file extension
        allowed_extensions = {'.png', '.jpg', '.jpeg', '.bmp', '.tiff'}
        file_ext = os.path.splitext(file.filename)[1].lower()
        
        if file_ext not in allowed_extensions:
            raise ValidationError(f"File type {file_ext} not allowed. Allowed types: {allowed_extensions}")
        
        # Check file size (max 16MB)
        file.seek(0, os.SEEK_END)
        file_size = file.tell()
        file.seek(0)
        
        if file_size > 16 * 1024 * 1024:  # 16MB
            raise ValidationError("File size exceeds 16MB limit")
        
        # Validate image content
        file_content = file.read()
        file.seek(0)
        
        # Use imghdr to verify it's actually an image
        file_type = imghdr.what(None, h=file_content)
        if not file_type:
            raise ValidationError("Invalid image file")
        
        return {
            'filename': file.filename,
            'size': file_size,
            'type': file_type,
            'extension': file_ext,
            'file': file
        }
    
    @staticmethod
    def validate_message(message: str) -> str:
        """
        Validate message content.
        
        Args:
            message: Message text
            
        Returns:
            Validated message
            
        Raises:
            ValidationError: If message is invalid
        """
        if not message:
            raise ValidationError("Message cannot be empty")
        
        if len(message.strip()) == 0:
            raise ValidationError("Message cannot be whitespace only")
        
        if len(message) > 10000:  # 10KB limit
            raise ValidationError("Message too long (max 10KB)")
        
        return message.strip()
    
    @staticmethod
    def validate_key_names(sender_key: str, recipient_key: str) -> tuple:
        """
        Validate key names.
        
        Args:
            sender_key: Sender key name
            recipient_key: Recipient key name
            
        Returns:
            Tuple of validated key names
            
        Raises:
            ValidationError: If key names are invalid
        """
        if not sender_key:
            raise ValidationError("Sender key name cannot be empty")
        
        if not recipient_key:
            raise ValidationError("Recipient key name cannot be empty")
        
        # Key name validation (alphanumeric, underscore, hyphen)
        import re
        key_pattern = re.compile(r'^[a-zA-Z0-9_-]+$')
        
        if not key_pattern.match(sender_key):
            raise ValidationError("Sender key name contains invalid characters")
        
        if not key_pattern.match(recipient_key):
            raise ValidationError("Recipient key name contains invalid characters")
        
        if len(sender_key) > 50 or len(recipient_key) > 50:
            raise ValidationError("Key names too long (max 50 characters)")
        
        return sender_key.strip(), recipient_key.strip()
    
    @staticmethod
    def validate_seed(seed: Optional[str]) -> Optional[int]:
        """
        Validate seed parameter.
        
        Args:
            seed: Seed string or None
            
        Returns:
            Validated seed as integer or None
            
        Raises:
            ValidationError: If seed is invalid
        """
        if seed is None:
            return None
        
        try:
            seed_int = int(seed)
            if seed_int < 0 or seed_int > 2**31 - 1:
                raise ValidationError("Seed must be between 0 and 2^31-1")
            return seed_int
        except ValueError:
            raise ValidationError("Seed must be a valid integer")
    
    @staticmethod
    def validate_json_payload(data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate JSON payload for API requests.
        
        Args:
            data: JSON data dictionary
            
        Returns:
            Validated data
            
        Raises:
            ValidationError: If payload is invalid
        """
        if not isinstance(data, dict):
            raise ValidationError("Invalid JSON payload")
        
        return data


class APIResponse:
    """Standardized API response format."""
    
    @staticmethod
    def success(data: Any = None, message: str = "Success", status_code: int = 200) -> tuple:
        """
        Create a successful API response.
        
        Args:
            data: Response data
            message: Success message
            status_code: HTTP status code
            
        Returns:
            Flask response tuple
        """
        response = {
            'success': True,
            'message': message,
            'data': data
        }
        return response, status_code
    
    @staticmethod
    def error(message: str, status_code: int = 400, error_code: str = None) -> tuple:
        """
        Create an error API response.
        
        Args:
            message: Error message
            status_code: HTTP status code
            error_code: Internal error code
            
        Returns:
            Flask response tuple
        """
        response = {
            'success': False,
            'message': message,
            'error_code': error_code
        }
        return response, status_code
