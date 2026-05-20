
import os
from typing import Optional


class Settings:
    """Application settings with environment variable support."""
    
    # Security settings
    AES_KEY_SIZE: int = 256
    RSA_KEY_SIZE: int = 2048
    SIGNATURE_ALGORITHM: str = "RSA"
    
    # Steganography settings
    LSB_BITS: int = 2  # Number of LSB bits to use per pixel
    MIN_CAPACITY_BYTES: int = 1024  # Minimum required capacity
    
    # Performance targets
    TARGET_PSNR: float = 40.0
    TARGET_SSIM: float = 0.95
    
    # File paths
    KEY_STORAGE_PATH: str = os.getenv("KEY_STORAGE_PATH", "keys")
    UPLOAD_FOLDER: str = os.getenv("UPLOAD_FOLDER", "uploads")
    MAX_CONTENT_LENGTH: int = int(os.getenv("MAX_CONTENT_LENGTH", "16777216"))  # 16MB
    
    # Flask settings
    SECRET_KEY: str = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")
    DEBUG: bool = os.getenv("DEBUG", "False").lower() == "true"
    
    # Compression settings
    COMPRESSION_LEVEL: int = 6  # zlib compression level (0-9)
    
    @classmethod
    def validate(cls) -> None:
        """Validate critical settings."""
        if cls.AES_KEY_SIZE not in [128, 192, 256]:
            raise ValueError("AES_KEY_SIZE must be 128, 192, or 256")
        if cls.RSA_KEY_SIZE not in [1024, 2048, 3072, 4096]:
            raise ValueError("RSA_KEY_SIZE must be 1024, 2048, 3072, or 4096")
        if cls.LSB_BITS not in [1, 2, 3, 4]:
            raise ValueError("LSB_BITS must be between 1 and 4")


# Create global settings instance
settings = Settings()
settings.validate()
