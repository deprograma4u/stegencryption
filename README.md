# Secure Steganography System

A production-grade, modular secure communication system that combines encryption, digital signatures, and steganography to provide end-to-end secure messaging.

## Features

### 🔐 **Encryption (Confidentiality)**
- **AES-256-CBC** encryption with random IV
- Ensures data remains unreadable even if extracted
- Payload compression with zlib for efficiency

### ✍️ **Digital Signatures (Authentication + Integrity)**
- **RSA-2048** digital signatures with PSS padding
- SHA-256 hashing for message integrity
- Verifies sender identity and message authenticity

### 🖼️ **Steganography (Concealment)**
- **Adaptive LSB** embedding in RGB images
- Randomized pixel selection with seed-based determinism
- Capacity checks and quality preservation
- PSNR > 40 dB and SSIM > 0.95 targets

### ⚙️ **Integrated Workflow**
- **End-to-end pipeline** automation
- Sender: Sign → Encrypt → Embed
- Receiver: Extract → Decrypt → Verify
- No manual steps required

## Architecture

```
encsteg/
├── api/                          # API Layer
│   ├── routes/                   # Flask routes
│   │   ├── stego_routes.py       # Steganography endpoints
│   │   └── key_routes.py         # Key management endpoints
│   ├── middleware/               # Request validation
│   │   └── validation.py         # Input validation and responses
│   └── app_factory.py            # Flask application factory
├── services/                     # Service Layer
│   └── workflow_service.py        # Business logic orchestration
├── core/                         # Core Components
│   ├── crypto/                   # Cryptography
│   │   └── crypto_service.py     # AES/RSA operations
│   ├── steganography/            # Steganography
│   │   └── stego_service.py      # LSB embedding/extraction
│   ├── key_management/           # Key Management
│   │   └── key_manager.py        # Key generation/storage
│   └── exceptions.py             # Custom exceptions
├── frontend/                     # User Interface
│   ├── templates/                # HTML templates
│   │   └── index.html            # Main web interface
│   └── static/                   # Static assets
│       └── js/app.js             # Frontend JavaScript
├── config/                       # Configuration
│   └── settings.py               # Application settings
├── utils/                        # Utilities
│   └── helpers.py                # Helper functions
├── tests/                        # Testing
│   ├── unit/                     # Unit tests
│   └── integration/              # Integration tests
├── uploads/                      # File uploads
├── keys/                         # Key storage
├── app.py                        # Application entry point
└── requirements.txt               # Dependencies
```

## Installation

### Prerequisites
- Python 3.8+
- pip

### Setup

1. **Clone and navigate to the project:**
   ```bash
   cd encsteg
   ```

2. **Create virtual environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Create necessary directories:**
   ```bash
   mkdir -p uploads keys
   ```

5. **Run the application:**
   ```bash
   python app.py
   ```

6. **Access the web interface:**
   Open your browser and navigate to `http://localhost:5000`

## API Endpoints

### Steganography Operations

#### Embed Message
```http
POST /api/stego/embed
Content-Type: multipart/form-data

message: "Your secret message"
image: [image file]
sender_key: "sender" (optional)
recipient_key: "recipient" (optional)
seed: 12345 (optional)
```

#### Extract Message
```http
POST /api/stego/extract
Content-Type: multipart/form-data

image: [stego image file]
sender_key: "sender" (optional)
recipient_key: "recipient" (optional)
seed: 12345 (optional)
```

#### Validate Capacity
```http
POST /api/stego/validate-capacity
Content-Type: multipart/form-data

message: "Your message"
image: [image file]
```

#### Analyze Quality
```http
POST /api/stego/analyze-quality
Content-Type: multipart/form-data

original_image: [original image file]
stego_image: [stego image file]
```

### Key Management

#### Generate Keys
```http
POST /api/keys/generate
Content-Type: application/json

{
  "user_name": "alice"
}
```

#### List Keys
```http
GET /api/keys/list
```

#### Validate Keys
```http
POST /api/keys/validate
Content-Type: application/json

{
  "user_names": ["alice", "bob"]
}
```

## Security Features

### Encryption
- **AES-256-CBC** with cryptographically secure random IV
- **PKCS7 padding** for block alignment
- **zlib compression** before encryption for efficiency

### Digital Signatures
- **RSA-2048** keys with **PSS padding**
- **SHA-256** hashing algorithm
- **Salt length** maximized for security

### Steganography
- **Randomized LSB** embedding (not sequential)
- **Seed-based determinism** for extraction
- **Adaptive capacity** management
- **Quality preservation** with PSNR/SSIM monitoring

### Key Management
- **Secure key storage** with proper file permissions
- **PBKDF2** key derivation from passwords
- **No hardcoded secrets** in the codebase

## Usage Examples

### Command Line Usage

```python
from services.workflow_service import WorkflowService

# Initialize service
workflow = WorkflowService()

# Generate keys
workflow.generate_key_pairs("alice")
workflow.generate_key_pairs("bob")

# Sender workflow
stego_image, metadata = workflow.sender_workflow(
    message="Secret message for Bob",
    image_path="cover_image.png",
    sender_key_name="alice",
    recipient_key_name="bob",
    seed=12345
)

# Receiver workflow
extracted_message, metadata = workflow.receiver_workflow(
    stego_image_bytes=stego_image,
    sender_key_name="alice",
    recipient_key_name="bob",
    seed=12345
)

print(f"Extracted: {extracted_message}")
```

### Web Interface

1. **Open** `http://localhost:5000` in your browser
2. **Generate keys** using the Key Management tab
3. **Embed messages** by uploading an image and entering your message
4. **Extract messages** by uploading stego images
5. **Download** stego images with embedded secrets

## Testing

### Run Unit Tests
```bash
pytest tests/unit/
```

### Run Integration Tests
```bash
pytest tests/integration/
```

### Run All Tests
```bash
pytest
```

## Configuration

Environment variables can be set to customize behavior:

```bash
# Security settings
AES_KEY_SIZE=256
RSA_KEY_SIZE=2048
SIGNATURE_ALGORITHM=RSA

# Steganography settings
LSB_BITS=2
MIN_CAPACITY_BYTES=1024

# Performance targets
TARGET_PSNR=40.0
TARGET_SSIM=0.95

# File paths
KEY_STORAGE_PATH=keys
UPLOAD_FOLDER=uploads
MAX_CONTENT_LENGTH=16777216

# Flask settings
SECRET_KEY=your-secret-key-change-in-production
DEBUG=False
```

## Performance Targets

- **PSNR**: > 40 dB (imperceptible changes)
- **SSIM**: > 0.95 (high structural similarity)
- **Capacity**: Up to 10% of image pixels
- **Processing**: < 5 seconds for typical images

## Security Considerations

1. **Key Security**: Keys are stored with proper file permissions (600 for private keys)
2. **Random IV**: Each encryption uses a unique, cryptographically secure IV
3. **Signature Verification**: All messages are verified before acceptance
4. **Input Validation**: All inputs are validated before processing
5. **Error Handling**: No sensitive information leaked in error messages

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Run the test suite
6. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For issues and questions:
- Check the [Issues](https://github.com/deprograma4u/stegencryption/issues) page
<!-- - Review the documentation -->
- Run the test suite to verify functionality
