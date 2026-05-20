"""
Integration tests for the complete workflow.
"""
import pytest
import os
import tempfile
from PIL import Image
import numpy as np

from services.workflow_service import WorkflowService
from core.exceptions import SteganographyError


class TestWorkflowIntegration:
    """Integration tests for the complete secure steganography workflow."""
    
    def setup_method(self):
        """Setup test fixtures."""
        self.workflow_service = WorkflowService()
        self.test_message = "This is a secret message for integration testing."
        self.sender_name = "test_sender"
        self.recipient_name = "test_recipient"
        
        # Create a test image
        self.test_image_path = self.create_test_image()
    
    def teardown_method(self):
        """Cleanup test fixtures."""
        if os.path.exists(self.test_image_path):
            os.unlink(self.test_image_path)
    
    def create_test_image(self):
        """Create a test image for testing."""
        # Create a simple RGB image
        width, height = 200, 200
        data = np.random.randint(0, 256, (height, width, 3), dtype=np.uint8)
        img = Image.fromarray(data, 'RGB')
        
        # Save to temporary file
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp:
            img.save(tmp.name)
            return tmp.name
    
    def test_complete_sender_receiver_workflow(self):
        """Test the complete sender and receiver workflow."""
        # Step 1: Generate keys for sender and recipient
        self.workflow_service.generate_key_pairs(self.sender_name)
        self.workflow_service.generate_key_pairs(self.recipient_name)
        
        # Step 2: Sender workflow - embed message
        stego_image_bytes, embed_metadata = self.workflow_service.sender_workflow(
            message=self.test_message,
            image_path=self.test_image_path,
            sender_key_name=self.sender_name,
            recipient_key_name=self.recipient_name,
            seed=12345
        )
        
        # Verify embedding was successful
        assert stego_image_bytes is not None
        assert len(stego_image_bytes) > 0
        assert embed_metadata is not None
        assert embed_metadata['sender'] == self.sender_name
        assert embed_metadata['recipient'] == self.recipient_name
        assert embed_metadata['verification_status'] not in embed_metadata  # Should not exist yet
        
        # Step 3: Receiver workflow - extract message
        extracted_message, extract_metadata = self.workflow_service.receiver_workflow(
            stego_image_bytes=stego_image_bytes,
            sender_key_name=self.sender_name,
            recipient_key_name=self.recipient_name,
            seed=12345
        )
        
        # Verify extraction was successful
        assert extracted_message == self.test_message
        assert extract_metadata is not None
        assert extract_metadata['verification_status'] == 'verified'
        assert extract_metadata['extraction_successful'] is True
        assert extract_metadata['sender'] == self.sender_name
    
    def test_workflow_with_different_seeds(self):
        """Test workflow with different seeds produces different results."""
        # Generate keys
        self.workflow_service.generate_key_pairs(self.sender_name)
        self.workflow_service.generate_key_pairs(self.recipient_name)
        
        # Embed with seed 1
        stego1, _ = self.workflow_service.sender_workflow(
            message=self.test_message,
            image_path=self.test_image_path,
            sender_key_name=self.sender_name,
            recipient_key_name=self.recipient_name,
            seed=1
        )
        
        # Embed with seed 2
        stego2, _ = self.workflow_service.sender_workflow(
            message=self.test_message,
            image_path=self.test_image_path,
            sender_key_name=self.recipient_name,
            recipient_key_name=self.sender_name,
            seed=2
        )
        
        # Results should be different
        assert stego1 != stego2
        
        # Both should be extractable with correct seeds
        extracted1, _ = self.workflow_service.receiver_workflow(
            stego_image_bytes=stego1,
            sender_key_name=self.sender_name,
            recipient_key_name=self.recipient_name,
            seed=1
        )
        
        extracted2, _ = self.workflow_service.receiver_workflow(
            stego_image_bytes=stego2,
            sender_key_name=self.recipient_name,
            recipient_key_name=self.sender_name,
            seed=2
        )
        
        assert extracted1 == self.test_message
        assert extracted2 == self.test_message
    
    def test_workflow_fails_with_wrong_keys(self):
        """Test workflow fails with wrong keys."""
        # Generate keys
        self.workflow_service.generate_key_pairs(self.sender_name)
        self.workflow_service.generate_key_pairs(self.recipient_name)
        
        # Embed message
        stego_image_bytes, _ = self.workflow_service.sender_workflow(
            message=self.test_message,
            image_path=self.test_image_path,
            sender_key_name=self.sender_name,
            recipient_key_name=self.recipient_name
        )
        
        # Try to extract with wrong sender key
        with pytest.raises(SteganographyError):
            self.workflow_service.receiver_workflow(
                stego_image_bytes=stego_image_bytes,
                sender_key_name="nonexistent_sender",
                recipient_key_name=self.recipient_name
            )
        
        # Try to extract with wrong recipient key
        with pytest.raises(SteganographyError):
            self.workflow_service.receiver_workflow(
                stego_image_bytes=stego_image_bytes,
                sender_key_name=self.sender_name,
                recipient_key_name="nonexistent_recipient"
            )
    
    def test_capacity_validation(self):
        """Test image capacity validation."""
        # Test with normal message
        capacity_info = self.workflow_service.validate_image_capacity(
            self.test_image_path, self.test_message
        )
        
        assert capacity_info is not None
        assert 'can_embed' in capacity_info
        assert 'usage_ratio' in capacity_info
        assert 'available_capacity' in capacity_info
        assert capacity_info['message_length'] == len(self.test_message)
        
        # Test with very large message (should fail)
        large_message = "A" * 100000  # 100KB message
        large_capacity_info = self.workflow_service.validate_image_capacity(
            self.test_image_path, large_message
        )
        
        assert large_capacity_info['can_embed'] is False
        assert large_capacity_info['usage_ratio'] > 1.0
    
    def test_key_management(self):
        """Test key management functionality."""
        # Generate keys
        result = self.workflow_service.generate_key_pairs("test_user")
        
        assert result is not None
        assert result['user_name'] == "test_user"
        assert result['keys_generated'] is True
        assert result['rsa_key_size'] == 2048
        assert result['aes_key_size'] == 256
        
        # List keys
        keys_info = self.workflow_service.list_available_keys()
        
        assert keys_info is not None
        assert 'test_user' in keys_info['rsa_keys']
        assert 'test_user' in keys_info['aes_keys']
        assert keys_info['total_keys'] >= 2  # At least RSA and AES for test_user
    
    def test_image_quality_analysis(self):
        """Test image quality analysis."""
        # Generate keys
        self.workflow_service.generate_key_pairs(self.sender_name)
        self.workflow_service.generate_key_pairs(self.recipient_name)
        
        # Embed message
        stego_image_bytes, _ = self.workflow_service.sender_workflow(
            message=self.test_message,
            image_path=self.test_image_path,
            sender_key_name=self.sender_name,
            recipient_key_name=self.recipient_name
        )
        
        # Analyze quality
        quality_metrics = self.workflow_service.stego_service.analyze_image_quality(
            self.test_image_path, stego_image_bytes
        )
        
        assert quality_metrics is not None
        assert 'psnr' in quality_metrics
        assert 'ssim' in quality_metrics
        assert 'meets_psnr_target' in quality_metrics
        assert 'meets_ssim_target' in quality_metrics
        
        # PSNR should be high (good quality)
        assert quality_metrics['psnr'] > 30.0
        
        # SSIM should be close to 1 (good similarity)
        assert quality_metrics['ssim'] > 0.9
