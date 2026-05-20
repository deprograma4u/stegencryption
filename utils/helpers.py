
import os
import hashlib
import base64
from typing import Union, Any
from datetime import datetime


def generate_unique_filename(original_filename: str, prefix: str = "") -> str:
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    name, ext = os.path.splitext(original_filename)
    
    # Generate hash of original filename for uniqueness
    filename_hash = hashlib.md5(f"{original_filename}{timestamp}".encode()).hexdigest()[:8]
    
    if prefix:
        return f"{prefix}_{name}_{timestamp}_{filename_hash}{ext}"
    else:
        return f"{name}_{timestamp}_{filename_hash}{ext}"


def safe_b64_encode(data: Union[str, bytes]) -> str:
    
    if isinstance(data, str):
        data = data.encode('utf-8')
    return base64.b64encode(data).decode('utf-8')


def safe_b64_decode(encoded_data: str) -> bytes:
    
    try:
        return base64.b64decode(encoded_data.encode('utf-8'))
    except Exception:
        # Handle URL-safe base64
        encoded_data = encoded_data.replace('-', '+').replace('_', '/')
        while len(encoded_data) % 4 != 0:
            encoded_data += '='
        return base64.b64decode(encoded_data.encode('utf-8'))


def format_bytes(size: int) -> str:
    
    if size == 0:
        return "0 B"
    
    size_names = ["B", "KB", "MB", "GB", "TB"]
    i = 0
    while size >= 1024 and i < len(size_names) - 1:
        size /= 1024.0
        i += 1
    
    return f"{size:.1f} {size_names[i]}"


def validate_image_format(image_path: str) -> bool:
    
    try:
        from PIL import Image
        with Image.open(image_path) as img:
            img.verify()
        return True
    except Exception:
        return False


def get_image_info(image_path: str) -> dict:
    
    try:
        from PIL import Image
        with Image.open(image_path) as img:
            return {
                'filename': os.path.basename(image_path),
                'format': img.format,
                'mode': img.mode,
                'size': img.size,
                'width': img.width,
                'height': img.height,
                'file_size': os.path.getsize(image_path)
            }
    except Exception:
        return {}


def sanitize_filename(filename: str) -> str:
    
    # Remove path separators
    filename = os.path.basename(filename)
    
    # Remove dangerous characters
    dangerous_chars = ['..', '/', '\\', ':', '*', '?', '"', '<', '>', '|']
    for char in dangerous_chars:
        filename = filename.replace(char, '_')
    
    # Limit length
    if len(filename) > 255:
        name, ext = os.path.splitext(filename)
        filename = name[:255-len(ext)] + ext
    
    return filename


def calculate_file_hash(file_path: str, algorithm: str = 'sha256') -> str:
    
    hash_func = getattr(hashlib, algorithm)()
    
    with open(file_path, 'rb') as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_func.update(chunk)
    
    return hash_func.hexdigest()


def ensure_directory_exists(directory: str) -> bool:
    
    try:
        os.makedirs(directory, exist_ok=True)
        return True
    except Exception:
        return False


def is_safe_path(base_path: str, target_path: str) -> bool:
    
    try:
        base_abs = os.path.abspath(base_path)
        target_abs = os.path.abspath(target_path)
        
        return os.path.commonpath([base_abs, target_abs]) == base_abs
    except Exception:
        return False


def serialize_metadata(metadata: dict) -> str:
    
    import json
    return json.dumps(metadata, separators=(',', ':'), default=str)


def deserialize_metadata(metadata_json: str) -> dict:
    
    import json
    try:
        return json.loads(metadata_json)
    except Exception:
        return {}


def truncate_string(text: str, max_length: int = 100) -> str:
    
    if len(text) <= max_length:
        return text
    return text[:max_length-3] + "..."