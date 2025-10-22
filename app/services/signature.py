
import base64
from ecdsa import VerifyingKey, SECP256k1, BadSignatureError
import hashlib

# Device public key registry (should sync with device_registry in routes/iot.py)
DEVICE_PUBLIC_KEYS = {}

def verify_signature(device_id: str, data: dict, signature: str) -> bool:
    """
    Verify ECDSA signature for IoT data.
    Args:
        device_id: ID of the device
        data: The data dict (will be hashed)
        signature: Base64-encoded signature
    Returns:
        True if valid, False otherwise
    """
    pubkey_hex = DEVICE_PUBLIC_KEYS.get(device_id)
    if not pubkey_hex or len(pubkey_hex) < 64:
        return False
    try:
        # Serialize data to bytes (simple hash of sorted string for demo)
        data_bytes = str(sorted(data.items())).encode()
        data_hash = hashlib.sha256(data_bytes).digest()
        vk = VerifyingKey.from_string(bytes.fromhex(pubkey_hex), curve=SECP256k1)
        sig_bytes = base64.b64decode(signature)
        return vk.verify(sig_bytes, data_hash)
    except (BadSignatureError, Exception):
        return False
