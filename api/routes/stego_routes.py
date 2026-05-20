
import os
import tempfile
import io
from flask import Blueprint, request, jsonify, send_file
from werkzeug.datastructures import FileStorage

from api.middleware.validation import RequestValidator, APIResponse
from services.workflow_service import WorkflowService
from core.exceptions import SteganographyError, ValidationError


stego_bp = Blueprint('steganography', __name__, url_prefix='/api/stego')
workflow_service = WorkflowService()


@stego_bp.route('/embed', methods=['POST'])
def embed_message():
    """
    Embed a message into an image.
    
    Request:
    - message: Text message to embed
    - image: Image file
    - sender_key: Sender key name (optional, default: 'sender')
    - recipient_key: Recipient key name (optional, default: 'recipient')
    - seed: Random seed for steganography (optional)
    
    Response:
    - stego_image: Stego image file
    - metadata: Embedding metadata
    """
    try:
        # Validate request
        if 'image' not in request.files:
            return APIResponse.error("No image file provided")
        
        message = RequestValidator.validate_message(request.form.get('message', ''))
        image_file = RequestValidator.validate_image_file(request.files['image'])
        
        sender_key = request.form.get('sender_key', 'sender').strip()
        recipient_key = request.form.get('recipient_key', 'recipient').strip()
        sender_key, recipient_key = RequestValidator.validate_key_names(sender_key, recipient_key)
        
        seed = RequestValidator.validate_seed(request.form.get('seed'))
        
        # Save image temporarily
        print("Image File: ", image_file)
        with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(image_file['filename'])[1]) as temp_file:
            image_file['file'].save(temp_file.name)
            temp_image_path = temp_file.name
        
        try:
            # Perform embedding
            stego_image_bytes, metadata = workflow_service.sender_workflow(
                message=message,
                image_path=temp_image_path,
                sender_key_name=sender_key,
                recipient_key_name=recipient_key,
                seed=seed
            )
            
            # Prepare response
            response_data = {
                'metadata': metadata,
                'original_filename': image_file['filename'],
                'original_size': image_file['size'],
                'stego_size': len(stego_image_bytes)
            }
            
            # Return stego image as file download
            return send_file(
                path_or_file=io.BytesIO(stego_image_bytes),
                mimetype='image/png',
                as_attachment=True,
                download_name=f'stego_{os.path.splitext(image_file["filename"])[0]}.png'
            )
            
        finally:
            # Clean up temporary file
            if os.path.exists(temp_image_path):
                os.unlink(temp_image_path)
                
    except ValidationError as e:
        print(f"Validation error: {e}")
        return APIResponse.error(str(e), 400, 'VALIDATION_ERROR')
    except SteganographyError as e:
        print(f"Steganography error: {e}")
        return APIResponse.error(str(e), 500, 'STEGANOGRAPHY_ERROR')
    except Exception as e:
        print(f"Internal server error: {e}")
        return APIResponse.error(f"Internal server error: {str(e)}", 500, 'INTERNAL_ERROR')


@stego_bp.route('/extract', methods=['POST'])
def extract_message():
    """
    Extract a message from a stego image.
    
    Request:
    - image: Stego image file
    - sender_key: Sender key name (optional, default: 'sender')
    - recipient_key: Recipient key name (optional, default: 'recipient')
    - seed: Random seed used during embedding (optional)
    
    Response:
    - message: Extracted message
    - metadata: Extraction metadata
    """
    try:
        # Validate request
        if 'image' not in request.files:
            return APIResponse.error("No image file provided")
        
        image_file = RequestValidator.validate_image_file(request.files['image'])
        
        sender_key = request.form.get('sender_key', 'sender').strip()
        recipient_key = request.form.get('recipient_key', 'recipient').strip()
        sender_key, recipient_key = RequestValidator.validate_key_names(sender_key, recipient_key)
        
        seed = RequestValidator.validate_seed(request.form.get('seed'))
        
        # Read image bytes
        image_bytes = image_file['file'].read()
        
        # Perform extraction
        message, metadata = workflow_service.receiver_workflow(
            stego_image_bytes=image_bytes,
            sender_key_name=sender_key,
            recipient_key_name=recipient_key,
            seed=seed
        )
        
        response_data = {
            'message': message,
            'metadata': metadata,
            'original_filename': image_file['filename']
        }
        
        return APIResponse.success(response_data, "Message extracted successfully")
        
    except ValidationError as e:
        print(f"Validation error: {e}")
        return APIResponse.error(str(e), 400, 'VALIDATION_ERROR')
    except SteganographyError as e:
        print(f"Steganography error: {e}")
        return APIResponse.error(str(e), 500, 'STEGANOGRAPHY_ERROR')
    except Exception as e:
        print(f"Internal server error: {e}")
        return APIResponse.error(f"Internal server error: {str(e)}", 500, 'INTERNAL_ERROR')


@stego_bp.route('/validate-capacity', methods=['POST'])
def validate_capacity():
    """
    Validate if an image has sufficient capacity for a message.
    
    Request:
    - message: Text message to embed
    - image: Image file
    
    Response:
    - capacity_info: Capacity analysis
    """
    try:
        # Validate request
        if 'image' not in request.files:
            return APIResponse.error("No image file provided")
        
        message = RequestValidator.validate_message(request.form.get('message', ''))
        image_file = RequestValidator.validate_image_file(request.files['image'])
        
        # Save image temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(image_file['filename'])[1]) as temp_file:
            image_file['file'].save(temp_file.name)
            temp_image_path = temp_file.name
        
        try:    
            # Validate capacity
            capacity_info = workflow_service.validate_image_capacity(temp_image_path, message)
            
            return APIResponse.success(capacity_info, "Capacity validation completed")
            
        finally:
            # Clean up temporary file
            if os.path.exists(temp_image_path):
                os.unlink(temp_image_path)
                
    except ValidationError as e:
        print(f"Validation error: {e}")
        return APIResponse.error(str(e), 400, 'VALIDATION_ERROR')
    except SteganographyError as e:
        print(f"Steganography error: {e}")
        return APIResponse.error(str(e), 500, 'STEGANOGRAPHY_ERROR')
    except Exception as e:
        print(f"Internal server error: {e}")
        return APIResponse.error(f"Internal server error: {str(e)}", 500, 'INTERNAL_ERROR')


@stego_bp.route('/analyze-quality', methods=['POST'])
def analyze_quality():
    """
    Analyze quality metrics between original and stego images.
    
    Request:
    - original_image: Original image file
    - stego_image: Stego image file
    
    Response:
    - quality_metrics: PSNR and SSIM values
    """
    try:
        # Validate request
        if 'original_image' not in request.files or 'stego_image' not in request.files:
            return APIResponse.error("Both original and stego images must be provided")
        
        original_file = RequestValidator.validate_image_file(request.files['original_image'])
        stego_file = RequestValidator.validate_image_file(request.files['stego_image'])
        
        # Save original image temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(original_file['filename'])[1]) as temp_file:
            original_file['file'].save(temp_file.name)
            temp_original_path = temp_file.name
        
        try:
            # Read stego image bytes
            stego_image_bytes = stego_file['file'].read()
            
            # Analyze quality
            quality_metrics = workflow_service.stego_service.analyze_image_quality(
                temp_original_path, stego_image_bytes
            )
            
            return APIResponse.success(quality_metrics, "Quality analysis completed")
            
        finally:
            # Clean up temporary file
            if os.path.exists(temp_original_path):
                os.unlink(temp_original_path)
                
    except ValidationError as e:
        print(f"Validation error: {e}")
        return APIResponse.error(str(e), 400, 'VALIDATION_ERROR')
    except SteganographyError as e:
        print(f"Steganography error: {e}")
        return APIResponse.error(str(e), 500, 'STEGANOGRAPHY_ERROR')
    except Exception as e:
        print(f"Internal server error: {e}")
        return APIResponse.error(f"Internal server error: {str(e)}", 500, 'INTERNAL_ERROR')
