"""
Cryptographic service for encryption, decryption, signing, and verification.
"""
import zlib
import json
import os
from typing import Tuple, Dict, Any
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding, rsa
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
import base64

from core.exceptions import CryptographyError, VerificationError
from config.settings import settings


class CryptoService:
    """Handles all cryptographic operations."""
    
    def __init__(self):
        self.backend = default_backend()
    
    def encrypt_message(self, message: str, aes_key: bytes) -> Tuple[bytes, bytes]:
        """
        Encrypt a message using AES-256-CBC.
        
        Args:
            message: Plain text message to encrypt
            aes_key: 256-bit AES key
            
        Returns:
            Tuple of (encrypted_data, iv)
        """
        try:
            # Compress the message first
            compressed_message = zlib.compress(
                message.encode(), 
                level=settings.COMPRESSION_LEVEL
            )
            
            # Generate random IV
            iv = os.urandom(16)
            
            # Encrypt using AES-256-CBC
            cipher = Cipher(
                algorithms.AES(aes_key),
                modes.CBC(iv),
                backend=self.backend
            )
            encryptor = cipher.encryptor()
            
            # Pad the data to block size
            padded_data = self._pad_data(compressed_message)
            encrypted_data = encryptor.update(padded_data) + encryptor.finalize()
            
            return encrypted_data, iv
            
        except Exception as e:
            raise CryptographyError(f"Encryption failed: {str(e)}")
    
    def decrypt_message(self, encrypted_data: bytes, iv: bytes, aes_key: bytes) -> str:
        """
        Decrypt a message using AES-256-CBC.
        
        Args:
            encrypted_data: Encrypted data
            iv: Initialization vector
            aes_key: 256-bit AES key
            
        Returns:
            Decrypted plain text message
        """
        try:
            # Decrypt using AES-256-CBC
            cipher = Cipher(
                algorithms.AES(aes_key),
                modes.CBC(iv),
                backend=self.backend
            )
            decryptor = cipher.decryptor()
            
            padded_data = decryptor.update(encrypted_data) + decryptor.finalize()
            
            # Remove padding
            compressed_message = self._unpad_data(padded_data)
            
            # Decompress
            message = zlib.decompress(compressed_message).decode()
            
            return message
            
        except Exception as e:
            raise CryptographyError(f"Decryption failed: {str(e)}")
    
    def sign_message(self, message: str, private_key: rsa.RSAPrivateKey) -> bytes:
        """
        Sign a message using RSA private key.
        
        Args:
            message: Message to sign
            private_key: RSA private key
            
        Returns:
            Digital signature
        """
        try:
            # Hash the message
            message_hash = hashes.Hash(hashes.SHA256(), backend=self.backend)
            message_hash.update(message.encode())
            digest = message_hash.finalize()
            
            # Sign the hash
            signature = private_key.sign(
                digest,
                padding.PSS(
                    mgf=padding.MGF1(hashes.SHA256()),
                    salt_length=padding.PSS.MAX_LENGTH
                ),
                hashes.SHA256()
            )
            
            return signature
            
        except Exception as e:
            raise CryptographyError(f"Signing failed: {str(e)}")
    
    def verify_signature(self, message: str, signature: bytes, public_key: rsa.RSAPublicKey) -> bool:
        """
        Verify a message signature using RSA public key.
        
        Args:
            message: Original message
            signature: Digital signature to verify
            public_key: RSA public key
            
        Returns:
            True if signature is valid, False otherwise
        """
        try:
            # Hash the message
            message_hash = hashes.Hash(hashes.SHA256(), backend=self.backend)
            message_hash.update(message.encode())
            digest = message_hash.finalize()
            
            # Verify the signature
            public_key.verify(
                signature,
                digest,
                padding.PSS(
                    mgf=padding.MGF1(hashes.SHA256()),
                    salt_length=padding.PSS.MAX_LENGTH
                ),
                hashes.SHA256()
            )
            
            return True
            
        except Exception as e:
            raise VerificationError(f"Signature verification failed: {str(e)}")
    
    def create_payload(self, message: str, signature: bytes, metadata: Dict[str, Any] = None) -> bytes:
        """
        Create a structured payload with message, signature, and metadata.
        
        Args:
            message: The original message
            signature: Digital signature
            metadata: Optional metadata dictionary
            
        Returns:
            JSON-encoded payload as bytes
        """
        try:
            payload = {
                'message': message,
                'signature': base64.b64encode(signature).decode(),
                'metadata': metadata or {},
                'version': '1.0'
            }
            
            payload_json = json.dumps(payload, separators=(',', ':'))
            return payload_json.encode()
            
        except Exception as e:
            raise CryptographyError(f"Payload creation failed: {str(e)}")
    
    def parse_payload(self, payload_bytes: bytes) -> Tuple[str, bytes, Dict[str, Any]]:
        """
        Parse a structured payload into components.
        
        Args:
            payload_bytes: JSON-encoded payload
            
        Returns:
            Tuple of (message, signature, metadata)
        """
        try:
            payload = json.loads(payload_bytes.decode())
            
            message = payload['message']
            signature = base64.b64decode(payload['signature'])
            metadata = payload.get('metadata', {})
            
            return message, signature, metadata
            
        except Exception as e:
            raise CryptographyError(f"Payload parsing failed: {str(e)}")
    
    def generate_integrity_hash(self, data: bytes) -> str:
        """
        Generate SHA-256 hash for integrity checking.
        
        Args:
            data: Data to hash
            
        Returns:
            Hexadecimal hash string
        """
        try:
            hasher = hashes.Hash(hashes.SHA256(), backend=self.backend)
            hasher.update(data)
            return hasher.finalize().hex()
            
        except Exception as e:
            raise CryptographyError(f"Hash generation failed: {str(e)}")
    
    def verify_integrity_hash(self, data: bytes, expected_hash: str) -> bool:
        """
        Verify data integrity using SHA-256 hash.
        
        Args:
            data: Data to verify
            expected_hash: Expected hash value
            
        Returns:
            True if hash matches, False otherwise
        """
        try:
            actual_hash = self.generate_integrity_hash(data)
            return actual_hash == expected_hash
            
        except Exception as e:
            raise CryptographyError(f"Hash verification failed: {str(e)}")
    
    def _pad_data(self, data: bytes) -> bytes:
        """Apply PKCS7 padding to data."""
        block_size = 16  # AES block size
        padding_length = block_size - (len(data) % block_size)
        padding = bytes([padding_length] * padding_length)
        return data + padding
    
    def _unpad_data(self, padded_data: bytes) -> bytes:
        """Remove PKCS7 padding from data."""
        padding_length = padded_data[-1]
        return padded_data[:-padding_length]
