"""
Key management module for secure cryptographic operations.
"""
import os
import json
from typing import Tuple, Optional
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.backends import default_backend
from cryptography.fernet import Fernet
import base64

from core.exceptions import KeyManagementError
from config.settings import settings


class KeyManager:
    """Manages cryptographic keys for encryption and signing."""
    
    def __init__(self, key_storage_path: str = None):
        self.key_storage_path = key_storage_path or settings.KEY_STORAGE_PATH
        self._ensure_key_directory()
    
    def _ensure_key_directory(self) -> None:
        """Create key storage directory if it doesn't exist."""
        if not os.path.exists(self.key_storage_path):
            os.makedirs(self.key_storage_path, mode=0o700)
    
    def generate_rsa_key_pair(self, key_size: int = None) -> Tuple[rsa.RSAPrivateKey, rsa.RSAPublicKey]:
        """Generate a new RSA key pair for digital signatures."""
        try:
            key_size = key_size or settings.RSA_KEY_SIZE
            private_key = rsa.generate_private_key(
                public_exponent=65537,
                key_size=key_size,
                backend=default_backend()
            )
            public_key = private_key.public_key()
            return private_key, public_key
        except Exception as e:
            raise KeyManagementError(f"Failed to generate RSA key pair: {str(e)}")
    
    def generate_aes_key(self, password: str = None, salt: bytes = None) -> bytes:
        """Generate AES key from password using PBKDF2."""
        try:
            if password:
                salt = salt or os.urandom(16)
                kdf = PBKDF2HMAC(
                    algorithm=hashes.SHA256(),
                    length=settings.AES_KEY_SIZE // 8,
                    salt=salt,
                    iterations=100000,
                    backend=default_backend()
                )
                key = kdf.derive(password.encode())
                return key, salt
            else:
                return os.urandom(settings.AES_KEY_SIZE // 8), None
        except Exception as e:
            raise KeyManagementError(f"Failed to generate AES key: {str(e)}")
    
    def save_rsa_keys(self, private_key: rsa.RSAPrivateKey, public_key: rsa.RSAPublicKey, 
                     key_name: str) -> None:
        """Save RSA key pair to files."""
        try:
            # Saving private key
            private_pem = private_key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.PKCS8,
                encryption_algorithm=serialization.NoEncryption()
            )
            private_path = os.path.join(self.key_storage_path, f"{key_name}_private.pem")
            with open(private_path, 'wb') as f:
                f.write(private_pem)
            os.chmod(private_path, 0o600)
            
            # Saving public key
            public_pem = public_key.public_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PublicFormat.SubjectPublicKeyInfo
            )
            public_path = os.path.join(self.key_storage_path, f"{key_name}_public.pem")
            with open(public_path, 'wb') as f:
                f.write(public_pem)
            os.chmod(public_path, 0o644)
            
        except Exception as e:
            raise KeyManagementError(f"Failed to save RSA keys: {str(e)}")
    
    def load_rsa_private_key(self, key_name: str) -> rsa.RSAPrivateKey:
        """Load RSA private key from file."""
        try:
            private_path = os.path.join(self.key_storage_path, f"{key_name}_private.pem")
            with open(private_path, 'rb') as f:
                private_pem = f.read()
            
            private_key = serialization.load_pem_private_key(
                private_pem,
                password=None,
                backend=default_backend()
            )
            return private_key
        except Exception as e:
            raise KeyManagementError(f"Failed to load RSA private key: {str(e)}")
    
    def load_rsa_public_key(self, key_name: str) -> rsa.RSAPublicKey:
        """Load RSA public key from file."""
        try:
            public_path = os.path.join(self.key_storage_path, f"{key_name}_public.pem")
            with open(public_path, 'rb') as f:
                public_pem = f.read()
            
            public_key = serialization.load_pem_public_key(
                public_pem,
                backend=default_backend()
            )
            return public_key
        except Exception as e:
            raise KeyManagementError(f"Failed to load RSA public key: {str(e)}")
    
    def save_aes_key(self, key: bytes, salt: bytes, key_name: str) -> None:
        """Save AES key and salt to file."""
        try:
            key_data = {
                'key': base64.b64encode(key).decode(),
                'salt': base64.b64encode(salt).decode() if salt else None
            }
            key_path = os.path.join(self.key_storage_path, f"{key_name}_aes.json")
            with open(key_path, 'w') as f:
                json.dump(key_data, f)
            os.chmod(key_path, 0o600)
        except Exception as e:
            raise KeyManagementError(f"Failed to save AES key: {str(e)}")
    
    def load_aes_key(self, key_name: str) -> Tuple[bytes, Optional[bytes]]:
        """Load AES key and salt from file."""
        try:
            key_path = os.path.join(self.key_storage_path, f"{key_name}_aes.json")
            with open(key_path, 'r') as f:
                key_data = json.load(f)
            
            key = base64.b64decode(key_data['key'])
            salt = base64.b64decode(key_data['salt']) if key_data['salt'] else None
            return key, salt
        except Exception as e:
            raise KeyManagementError(f"Failed to load AES key: {str(e)}")
    
    def key_exists(self, key_name: str, key_type: str = "rsa") -> bool:
        """Check if key files exist."""
        if key_type == "rsa":
            private_path = os.path.join(self.key_storage_path, f"{key_name}_private.pem")
            public_path = os.path.join(self.key_storage_path, f"{key_name}_public.pem")
            return os.path.exists(private_path) and os.path.exists(public_path)
        elif key_type == "aes":
            key_path = os.path.join(self.key_storage_path, f"{key_name}_aes.json")
            return os.path.exists(key_path)
        return False
