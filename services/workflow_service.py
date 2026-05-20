"""
Workflow service for orchestrating end-to-end secure communication pipeline.
"""
import os
from typing import Tuple, Dict, Any, Optional
from io import BytesIO

from core.crypto.crypto_service import CryptoService
from core.steganography.stego_service import StegoService
from core.key_management.key_manager import KeyManager
from core.exceptions import SteganographyError, CryptographyError, VerificationError
from config.settings import settings


class WorkflowService:
    """Orchestrates the complete secure steganography workflow."""
    
    def __init__(self):
        self.crypto_service = CryptoService()
        self.stego_service = StegoService()
        self.key_manager = KeyManager()
    
    def sender_workflow(self, message: str, image_path: str, 
                       sender_key_name: str = "sender",
                       recipient_key_name: str = "recipient",
                       seed: Optional[int] = None) -> Tuple[bytes, Dict[str, Any]]:
        """
        Complete sender workflow: sign -> encrypt -> embed.
        
        Args:
            message: Plain text message to send
            image_path: Path to cover image
            sender_key_name: Name of sender's key pair
            recipient_key_name: Name of recipient's encryption key
            seed: Random seed for steganography
            
        Returns:
            Tuple of (stego_image_bytes, metadata)
        """
        try:
            # Step 1: Load or generate keys
            if not self.key_manager.key_exists(sender_key_name, "rsa"):
                private_key, public_key = self.key_manager.generate_rsa_key_pair()
                self.key_manager.save_rsa_keys(private_key, public_key, sender_key_name)
            else:
                private_key = self.key_manager.load_rsa_private_key(sender_key_name)
            
            if not self.key_manager.key_exists(recipient_key_name, "aes"):
                aes_key, salt = self.key_manager.generate_aes_key()
                self.key_manager.save_aes_key(aes_key, salt, recipient_key_name)
            else:
                aes_key, salt = self.key_manager.load_aes_key(recipient_key_name)
            
            # Step 2: Sign the message
            signature = self.crypto_service.sign_message(message, private_key)
            
            # Step 3: Create payload with message and signature
            metadata = {
                'sender': sender_key_name,
                'recipient': recipient_key_name,
                'timestamp': self._get_timestamp(),
                'message_length': len(message),
                'signature_length': len(signature)
            }
            
            payload = self.crypto_service.create_payload(message, signature, metadata)
            
            # Step 4: Encrypt the payload
            encrypted_data, iv = self.crypto_service.encrypt_message(payload.decode(), aes_key)
            
            # Step 5: Prepare final data with IV for decryption
            final_data = iv + encrypted_data
            
            # Step 6: Generate integrity hash
            integrity_hash = self.crypto_service.generate_integrity_hash(final_data)
            
            # Step 7: Embed in image
            stego_image = self.stego_service.embed_data(image_path, final_data, seed)
            
            # Step 8: Analyze image quality
            quality_metrics = self.stego_service.analyze_image_quality(image_path, stego_image)
            
            # Step 9: Prepare final metadata
            final_metadata = {
                **metadata,
                'iv': iv.hex() if iv else None,
                'salt': salt.hex() if salt else None,
                'integrity_hash': integrity_hash,
                'seed': seed,
                'quality_metrics': quality_metrics,
                'data_size': len(final_data),
                'capacity_used': len(final_data) / self.stego_service.calculate_capacity(image_path)
            }
            
            return stego_image, final_metadata
            
        except Exception as e:
            raise SteganographyError(f"Sender workflow failed: {str(e)}")
    
    def receiver_workflow(self, stego_image_bytes: bytes,
                         sender_key_name: str = "sender",
                         recipient_key_name: str = "recipient",
                         seed: Optional[int] = None) -> Tuple[str, Dict[str, Any]]:
        """
        Complete receiver workflow: extract -> decrypt -> verify.
        
        Args:
            stego_image_bytes: Stego image data
            sender_key_name: Name of sender's key pair for verification
            recipient_key_name: Name of recipient's decryption key
            seed: Random seed used during embedding
            
        Returns:
            Tuple of (verified_message, metadata)
        """
        try:
            # Step 1: Load keys
            if not self.key_manager.key_exists(recipient_key_name, "aes"):
                raise CryptographyError(f"Recipient AES key '{recipient_key_name}' not found")
            
            if not self.key_manager.key_exists(sender_key_name, "rsa"):
                raise CryptographyError(f"Sender RSA key '{sender_key_name}' not found")
            
            aes_key, salt = self.key_manager.load_aes_key(recipient_key_name)
            sender_public_key = self.key_manager.load_rsa_public_key(sender_key_name)
            
            # Step 2: Extract data from image
            extracted_data = self.stego_service.extract_data(stego_image_bytes, seed)
            
            # Step 3: Split IV and encrypted data
            if len(extracted_data) < 16:
                raise ExtractionError("Extracted data too small to contain IV")
            
            iv = extracted_data[:16]
            encrypted_data = extracted_data[16:]
            
            # Step 4: Verify integrity
            integrity_hash = self.crypto_service.generate_integrity_hash(extracted_data)
            
            # Step 5: Decrypt the payload
            payload_str = self.crypto_service.decrypt_message(encrypted_data, iv, aes_key)
            
            # Step 6: Parse payload
            message, signature, metadata = self.crypto_service.parse_payload(payload_str.encode())
            
            # Step 7: Verify signature
            is_signature_valid = self.crypto_service.verify_signature(
                message, signature, sender_public_key
            )
            
            if not is_signature_valid:
                raise VerificationError("Digital signature verification failed")
            
            # Step 8: Prepare final metadata
            final_metadata = {
                **metadata,
                'verification_status': 'verified',
                'integrity_hash': integrity_hash,
                'extraction_successful': True,
                'recipient_key_name': recipient_key_name,
                'sender_key_name': sender_key_name
            }
            
            return message, final_metadata
            
        except Exception as e:
            raise SteganographyError(f"Receiver workflow failed: {str(e)}")
    
    def validate_image_capacity(self, image_path: str, message: str) -> Dict[str, Any]:
        """
        Validate if an image has sufficient capacity for a message.
        
        Args:
            image_path: Path to the image
            message: Message to be embedded
            
        Returns:
            Dictionary with capacity analysis
        """
        try:
            # Calculate actual data size (rough estimate)
            estimated_payload_size = len(message) * 2  # Rough estimate for signed+encrypted data
            capacity = self.stego_service.calculate_capacity(image_path)
            
            can_embed = estimated_payload_size <= capacity
            usage_ratio = estimated_payload_size / capacity if capacity > 0 else 1.0
            
            return {
                'image_path': image_path,
                'message_length': len(message),
                'estimated_payload_size': estimated_payload_size,
                'available_capacity': capacity,
                'can_embed': can_embed,
                'usage_ratio': usage_ratio,
                'recommended': usage_ratio <= 0.8  # Recommend keeping under 80% capacity
            }
            
        except Exception as e:
            raise SteganographyError(f"Capacity validation failed: {str(e)}")
    
    def generate_key_pairs(self, user_name: str) -> Dict[str, Any]:
        """
        Generate new key pairs for a user.
        
        Args:
            user_name: Name/identifier for the user
            
        Returns:
            Dictionary with key generation results
        """
        try:
            # Generate RSA key pair
            private_key, public_key = self.key_manager.generate_rsa_key_pair()
            self.key_manager.save_rsa_keys(private_key, public_key, user_name)
            
            # Generate AES key
            aes_key, salt = self.key_manager.generate_aes_key()
            self.key_manager.save_aes_key(aes_key, salt, user_name)
            
            return {
                'user_name': user_name,
                'rsa_key_size': settings.RSA_KEY_SIZE,
                'aes_key_size': settings.AES_KEY_SIZE,
                'keys_generated': True,
                'key_storage_path': self.key_manager.key_storage_path
            }
            
        except Exception as e:
            raise SteganographyError(f"Key generation failed: {str(e)}")
    
    def list_available_keys(self) -> Dict[str, Any]:
        """
        List all available keys in the system.
        
        Returns:
            Dictionary with available keys information
        """
        try:
            key_path = self.key_manager.key_storage_path
            if not os.path.exists(key_path):
                return {'rsa_keys': [], 'aes_keys': [], 'total_keys': 0}
            
            files = os.listdir(key_path)
            rsa_keys = set()
            aes_keys = set()
            
            for file in files:
                if file.endswith('_private.pem'):
                    key_name = file.replace('_private.pem', '')
                    rsa_keys.add(key_name)
                elif file.endswith('_aes.json'):
                    key_name = file.replace('_aes.json', '')
                    aes_keys.add(key_name)
            
            return {
                'rsa_keys': sorted(list(rsa_keys)),
                'aes_keys': sorted(list(aes_keys)),
                'total_keys': len(rsa_keys) + len(aes_keys),
                'key_storage_path': key_path
            }
            
        except Exception as e:
            raise SteganographyError(f"Key listing failed: {str(e)}")
    
    def _get_timestamp(self) -> str:
        """Get current timestamp in ISO format."""
        from datetime import datetime
        return datetime.utcnow().isoformat() + 'Z'
