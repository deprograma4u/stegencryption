"""
Steganography service for embedding and extracting data in images.
"""
import os
import random
import struct
from typing import List, Tuple, Optional
import numpy as np
from PIL import Image
import cv2

from core.exceptions import SteganographyError, InsufficientCapacityError, ExtractionError
from config.settings import settings


class StegoService:
    """Handles steganographic embedding and extraction operations."""
    
    def __init__(self):
        self.lsb_bits = settings.LSB_BITS
        self.max_capacity_ratio = 0.1  # Use max 10% of image capacity
    
    def calculate_capacity(self, image_path: str) -> int:
        """
        Calculate the maximum embedding capacity of an image.
        
        Args:
            image_path: Path to the image file
            
        Returns:
            Maximum capacity in bytes
        """
        try:
            with Image.open(image_path) as img:
                width, height = img.size
                # For RGB images, we have 3 channels per pixel
                total_pixels = width * height * 3
                # Each pixel can store lsb_bits of information
                capacity_bits = total_pixels * self.lsb_bits
                capacity_bytes = capacity_bits // 8
                
                # Apply safety margin
                safe_capacity = int(capacity_bytes * self.max_capacity_ratio)
                
                return safe_capacity
                
        except Exception as e:
            raise SteganographyError(f"Failed to calculate capacity: {str(e)}")
    
    def embed_data(self, image_path: str, data: bytes, seed: Optional[int] = None) -> bytes:
        """
        Embed data into an image using randomized LSB steganography.
        
        Args:
            image_path: Path to the cover image
            data: Data to embed
            seed: Random seed for pixel selection (deterministic extraction)
            
        Returns:
            Stego image as bytes
        """
        try:
            # Load image
            img = Image.open(image_path)
            if img.mode != 'RGB':
                img = img.convert('RGB')
            
            img_array = np.array(img)
            original_shape = img_array.shape
            
            # Check capacity
            capacity = self.calculate_capacity(image_path)
            data_with_header = self._prepare_data_with_header(data)
            
            if len(data_with_header) > capacity:
                raise InsufficientCapacityError(
                    f"Data size ({len(data_with_header)} bytes) exceeds capacity ({capacity} bytes)"
                )
            
            # Generate pixel selection sequence
            pixel_indices = self._generate_pixel_sequence(
                original_shape[0], original_shape[1], len(data_with_header), seed
            )
            
            # Embed data
            stego_array = self._embed_lsb_data(img_array, data_with_header, pixel_indices)
            
            # Convert back to image
            stego_img = Image.fromarray(stego_array, 'RGB')
            
            # Save to bytes
            from io import BytesIO
            buffer = BytesIO()
            stego_img.save(buffer, format='PNG')
            return buffer.getvalue()
            
        except Exception as e:
            raise SteganographyError(f"Embedding failed: {str(e)}")
    
    def extract_data(self, stego_image_bytes: bytes, seed: Optional[int] = None) -> bytes:
        """
        Extract data from a stego image.
        
        Args:
            stego_image_bytes: Stego image as bytes
            seed: Random seed used during embedding
            
        Returns:
            Extracted data
        """
        try:
            # Load stego image
            from io import BytesIO
            stego_img = Image.open(BytesIO(stego_image_bytes))
            if stego_img.mode != 'RGB':
                stego_img = stego_img.convert('RGB')
            
            stego_array = np.array(stego_img)
            height, width = stego_array.shape[:2]
            
            # First extract header to get data length
            header_size = 32  # 4 bytes for magic + 4 bytes for length + 24 bytes reserved
            pixel_indices = self._generate_pixel_sequence(height, width, header_size, seed)
            
            header_data = self._extract_lsb_data(stego_array, pixel_indices)
            data_length = self._parse_header(header_data)
            
            if data_length <= 0:
                raise ExtractionError("Invalid data length in header")
            
            # Extract actual data
            total_size = header_size + data_length
            pixel_indices = self._generate_pixel_sequence(height, width, total_size, seed)
            
            data_with_header = self._extract_lsb_data(stego_array, pixel_indices)
            
            # Remove header and return data
            return data_with_header[header_size:]
            
        except Exception as e:
            raise ExtractionError(f"Extraction failed: {str(e)}")
    
    def analyze_image_quality(self, original_path: str, stego_image_bytes: bytes) -> dict:
        """
        Analyze the quality degradation between original and stego images.
        
        Args:
            original_path: Path to original image
            stego_image_bytes: Stego image as bytes
            
        Returns:
            Dictionary with PSNR and SSIM values
        """
        try:
            # Load images
            original = Image.open(original_path)
            if original.mode != 'RGB':
                original = original.convert('RGB')
            
            from io import BytesIO
            stego = Image.open(BytesIO(stego_image_bytes))
            if stego.mode != 'RGB':
                stego = stego.convert('RGB')
            
            # Convert to numpy arrays
            orig_array = np.array(original)
            stego_array = np.array(stego)
            
            # Calculate PSNR
            mse = np.mean((orig_array - stego_array) ** 2)
            if mse == 0:
                psnr = float('inf')
            else:
                psnr = 20 * np.log10(255.0 / np.sqrt(mse))
            
            # Calculate SSIM (simplified version)
            ssim = self._calculate_ssim(orig_array, stego_array)
            
            return {
                'psnr': psnr,
                'ssim': ssim,
                'meets_psnr_target': psnr >= settings.TARGET_PSNR,
                'meets_ssim_target': ssim >= settings.TARGET_SSIM
            }
            
        except Exception as e:
            raise SteganographyError(f"Quality analysis failed: {str(e)}")
    
    def _generate_pixel_sequence(self, height: int, width: int, data_size: int, 
                                seed: Optional[int] = None) -> List[Tuple[int, int, int]]:
        """
        Generate a deterministic sequence of pixel coordinates for embedding.
        
        Args:
            height: Image height
            width: Image width
            data_size: Size of data to embed in bytes
            seed: Random seed for reproducibility
            
        Returns:
            List of (row, col, channel) tuples
        """
        if seed is not None:
            random.seed(seed)
        
        # Calculate how many pixels we need
        bits_needed = data_size * 8
        pixels_needed = (bits_needed + self.lsb_bits - 1) // self.lsb_bits
        
        # Generate all possible pixel positions
        positions = []
        for row in range(height):
            for col in range(width):
                for channel in range(3):  # RGB channels
                    positions.append((row, col, channel))
        
        # Randomly shuffle and select required positions
        random.shuffle(positions)
        return positions[:pixels_needed]
    
    def _embed_lsb_data(self, img_array: np.ndarray, data: bytes, 
                       pixel_indices: List[Tuple[int, int, int]]) -> np.ndarray:
        """Embed data into image using LSB substitution."""
        stego_array = img_array.copy()
        data_bits = ''.join(format(byte, '08b') for byte in data)
        
        bit_index = 0
        for row, col, channel in pixel_indices:
            if bit_index >= len(data_bits):
                break
            
            # Get current pixel value
            pixel_value = stego_array[row, col, channel]
            
            # Clear LSB bits and set new bits
            mask = ~(2 ** self.lsb_bits - 1)
            pixel_value = pixel_value & mask
            
            # Extract bits to embed
            bits_to_embed = data_bits[bit_index:bit_index + self.lsb_bits]
            bits_to_embed = bits_to_embed.ljust(self.lsb_bits, '0')
            
            # Set new bits
            pixel_value |= int(bits_to_embed, 2)
            
            # Update pixel
            stego_array[row, col, channel] = pixel_value
            bit_index += self.lsb_bits
        
        return stego_array
    
    def _extract_lsb_data(self, stego_array: np.ndarray, 
                          pixel_indices: List[Tuple[int, int, int]]) -> bytes:
        """Extract data from image using LSB substitution."""
        extracted_bits = []
        
        for row, col, channel in pixel_indices:
            pixel_value = stego_array[row, col, channel]
            
            # Extract LSB bits
            for i in range(self.lsb_bits):
                bit = (pixel_value >> i) & 1
                extracted_bits.append(str(bit))
        
        # Convert bits to bytes
        data_bytes = []
        for i in range(0, len(extracted_bits), 8):
            if i + 8 <= len(extracted_bits):
                byte_bits = ''.join(extracted_bits[i:i + 8])
                data_bytes.append(int(byte_bits, 2))
        
        return bytes(data_bytes)
    
    def _prepare_data_with_header(self, data: bytes) -> bytes:
        """Prepare data with header containing length information."""
        # Magic number for identification
        magic = b'STEG'
        
        # Data length (4 bytes)
        length_bytes = struct.pack('>I', len(data))
        
        # Reserved space (24 bytes)
        reserved = b'\x00' * 24
        
        # Combine header and data
        return magic + length_bytes + reserved + data
    
    def _parse_header(self, header_data: bytes) -> int:
        """Parse header to extract data length."""
        if len(header_data) < 32:
            raise ExtractionError("Invalid header size")
        
        # Check magic number
        magic = header_data[:4]
        if magic != b'STEG':
            raise ExtractionError("Invalid magic number in header")
        
        # Extract length
        length = struct.unpack('>I', header_data[4:8])[0]
        return length
    
    def _calculate_ssim(self, img1: np.ndarray, img2: np.ndarray) -> float:
        """Calculate Structural Similarity Index (simplified version)."""
        # Convert to grayscale for SSIM calculation
        if len(img1.shape) == 3:
            img1_gray = np.dot(img1[...,:3], [0.2989, 0.5870, 0.1140])
            img2_gray = np.dot(img2[...,:3], [0.2989, 0.5870, 0.1140])
        else:
            img1_gray = img1
            img2_gray = img2
        
        # Calculate means
        mu1 = np.mean(img1_gray)
        mu2 = np.mean(img2_gray)
        
        # Calculate variances and covariance
        sigma1_sq = np.var(img1_gray)
        sigma2_sq = np.var(img2_gray)
        sigma12 = np.mean((img1_gray - mu1) * (img2_gray - mu2))
        
        # SSIM constants
        c1 = 0.01 ** 2
        c2 = 0.03 ** 2
        
        # Calculate SSIM
        numerator = (2 * mu1 * mu2 + c1) * (2 * sigma12 + c2)
        denominator = (mu1**2 + mu2**2 + c1) * (sigma1_sq + sigma2_sq + c2)
        
        ssim = numerator / denominator
        return float(ssim)
