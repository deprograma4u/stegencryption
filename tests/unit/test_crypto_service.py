"""
Unit tests for the crypto service.
"""
import pytest
from unittest.mock import Mock, patch
import os
import tempfile

from core.crypto.crypto_service import CryptoService
from core.exceptions import CryptographyError, VerificationError


class TestCryptoService:
    """Test cases for CryptoService."""
    
    def setup_method(self):
        """Setup test fixtures."""
        self.crypto_service = CryptoService()
        self.test_message = "This is a test message for encryption."
        self.test_aes_key = os.urandom(32)  # 256-bit key
    
    def test_encrypt_decrypt_message(self):
        """Test message encryption and decryption."""
        # Encrypt
        encrypted_data, iv = self.crypto_service.encrypt_message(
            self.test_message, self.test_aes_key
        )
        
        assert encrypted_data is not None
        assert iv is not None
        assert len(iv) == 16  # IV should be 16 bytes
        assert len(encrypted_data) > 0
        
        # Decrypt
        decrypted_message = self.crypto_service.decrypt_message(
            encrypted_data, iv, self.test_aes_key
        )
        
        assert decrypted_message == self.test_message
    
    def test_encrypt_with_different_keys(self):
        """Test that encryption with different keys produces different results."""
        key1 = os.urandom(32)
        key2 = os.urandom(32)
        
        encrypted1, iv1 = self.crypto_service.encrypt_message(self.test_message, key1)
        encrypted2, iv2 = self.crypto_service.encrypt_message(self.test_message, key2)
        
        # Results should be different due to different keys and random IVs
        assert encrypted1 != encrypted2
        assert iv1 != iv2
    
    def test_decrypt_with_wrong_key(self):
        """Test decryption with wrong key fails."""
        wrong_key = os.urandom(32)
        encrypted_data, iv = self.crypto_service.encrypt_message(
            self.test_message, self.test_aes_key
        )
        
        with pytest.raises(CryptographyError):
            self.crypto_service.decrypt_message(encrypted_data, iv, wrong_key)
    
    def test_sign_verify_message(self):
        """Test message signing and verification."""
        from cryptography.hazmat.primitives.asymmetric import rsa
        
        # Generate test keys
        private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048
        )
        public_key = private_key.public_key()
        
        # Sign
        signature = self.crypto_service.sign_message(self.test_message, private_key)
        
        assert signature is not None
        assert len(signature) > 0
        
        # Verify
        is_valid = self.crypto_service.verify_signature(
            self.test_message, signature, public_key
        )
        
        assert is_valid is True
    
    def test_verify_tampered_message(self):
        """Test verification fails for tampered message."""
        from cryptography.hazmat.primitives.asymmetric import rsa
        
        private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048
        )
        public_key = private_key.public_key()
        
        signature = self.crypto_service.sign_message(self.test_message, private_key)
        tampered_message = self.test_message + " TAMPERED"
        
        with pytest.raises(VerificationError):
            self.crypto_service.verify_signature(tampered_message, signature, public_key)
    
    def test_create_parse_payload(self):
        """Test payload creation and parsing."""
        from cryptography.hazmat.primitives.asymmetric import rsa
        
        private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048
        )
        
        signature = self.crypto_service.sign_message(self.test_message, private_key)
        metadata = {"sender": "test_user", "timestamp": "2023-01-01"}
        
        # Create payload
        payload_bytes = self.crypto_service.create_payload(
            self.test_message, signature, metadata
        )
        
        assert payload_bytes is not None
        
        # Parse payload
        parsed_message, parsed_signature, parsed_metadata = self.crypto_service.parse_payload(
            payload_bytes
        )
        
        assert parsed_message == self.test_message
        assert parsed_signature == signature
        assert parsed_metadata["sender"] == "test_user"
        assert parsed_metadata["timestamp"] == "2023-01-01"
    
    def test_generate_integrity_hash(self):
        """Test integrity hash generation."""
        test_data = b"test data for hashing"
        hash_value = self.crypto_service.generate_integrity_hash(test_data)
        
        assert isinstance(hash_value, str)
        assert len(hash_value) == 64  # SHA-256 produces 64-character hex string
        
        # Same data should produce same hash
        hash_value2 = self.crypto_service.generate_integrity_hash(test_data)
        assert hash_value == hash_value2
        
        # Different data should produce different hash
        different_data = b"different test data"
        hash_value3 = self.crypto_service.generate_integrity_hash(different_data)
        assert hash_value != hash_value3
    
    def test_verify_integrity_hash(self):
        """Test integrity hash verification."""
        test_data = b"test data for integrity"
        correct_hash = self.crypto_service.generate_integrity_hash(test_data)
        
        # Correct hash should verify
        assert self.crypto_service.verify_integrity_hash(test_data, correct_hash) is True
        
        # Wrong hash should not verify
        wrong_hash = "0" * 64
        assert self.crypto_service.verify_integrity_hash(test_data, wrong_hash) is False
        
        # Modified data should not verify with original hash
        modified_data = test_data + b" modified"
        assert self.crypto_service.verify_integrity_hash(modified_data, correct_hash) is False
