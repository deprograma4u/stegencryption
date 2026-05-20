"""
Custom exceptions for the secure steganography system.
"""


class SteganographyError(Exception):
    """Base exception for all steganography-related errors."""
    pass


class CryptographyError(SteganographyError):
    """Raised when cryptographic operations fail."""
    pass


class InsufficientCapacityError(SteganographyError):
    """Raised when the image doesn't have enough capacity for the data."""
    pass


class ExtractionError(SteganographyError):
    """Raised when data extraction from image fails."""
    pass


class VerificationError(SteganographyError):
    """Raised when signature verification fails."""
    pass


class KeyManagementError(SteganographyError):
    """Raised when key management operations fail."""
    pass


class ValidationError(SteganographyError):
    """Raised when input validation fails."""
    pass


class ImageProcessingError(SteganographyError):
    """Raised when image processing operations fail."""
    pass
