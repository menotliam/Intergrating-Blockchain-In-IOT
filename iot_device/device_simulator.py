import time
import json
import requests
import os
import base64
import hashlib
import logging

from dotenv import load_dotenv
from ecdsa import SigningKey, SECP256k1

# Load .env file
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ENV_PATH = os.path.join(BASE_DIR, "..", ".env")
load_dotenv(dotenv_path=ENV_PATH)

DEVICE_ID = os.getenv("DEVICE_ID")
PRIVATE_KEY_PATH = os.getenv("PRIVATE_KEY_PATH")
BACKEND_URL = os.getenv("BACKEND_UPLOAD_URL", "http://localhost:8000/api/iot/upload")

# Initialize logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("DeviceSimulator")

# Load private key
def load_private_key(pem_path: str) -> SigningKey:
    with open(pem_path, 'rb') as f:
        return SigningKey.from_pem(f.read())

# Write signature
def sign_data(private_key: SigningKey, data: dict) -> str:
    serialized = str(sorted(data.items())).encode()
    data_hash = hashlib.sha256(serialized).digest()
    signature = private_key.sign(data_hash)
    return base64.b64encode(signature).decode()

# Send payload to API
def send_payload(device_id: str, data: dict, signature: str):
    payload = {
        "device_id": device_id,
        "data": data,
        "signature": signature
    }
    try:
        response = requests.post(BACKEND_URL, json=payload)
        logger.info(f"Sent data from {device_id} to {BACKEND_URL}")
        logger.info(f"Server response: {response.status_code} {response.text}")
    except Exception as e:
        logger.error(f"Error sending data: {e}")

# Generate fake sensor data
def generate_mock_sensor_data():
    return {
        # Assumption
        "temperature": round(20 + (time.time() % 10), 2),
        "humidity": round(50 + (time.time() % 3), 2),
        "timestamp": int(time.time())
    }


# Đăng ký thiết bị lên backend
def register_device(device_id: str, private_key_path: str, backend_register_url: str = None):
    if backend_register_url is None:
        backend_register_url = os.getenv("BACKEND_REGISTER_URL", "http://localhost:8000/api/iot/register")
    try:
        sk = load_private_key(private_key_path)
        vk = sk.get_verifying_key()
        pubkey_hex = vk.to_string("uncompressed").hex()
        payload = {
            "device_id": device_id,
            "public_key": pubkey_hex
        }
        response = requests.post(backend_register_url, json=payload)
        logger.info(f"Register device {device_id} to {backend_register_url}")
        logger.info(f"Register response: {response.status_code} {response.text}")
        return response.status_code == 200
    except Exception as e:
        logger.error(f"Error registering device: {e}")
        return False

# Sending loop
def simulate_device_loop(interval_sec=5, repeat=5, auto_register=True):
    logger.info("Loading private key from file")
    private_key = load_private_key(PRIVATE_KEY_PATH)
    if auto_register:
        logger.info("Auto-register device before sending data...")
        register_device(DEVICE_ID, PRIVATE_KEY_PATH)
    for i in range(repeat):
        data = generate_mock_sensor_data()
        signature = sign_data(private_key, data)
        # In ra signature, device_id, data để bạn copy sử dụng
        print("\n--- SIGNATURE DEBUG ---")
        print(json.dumps({
            "device_id": DEVICE_ID,
            "data": data,
            "signature": signature
        }, indent=2))
        
        print("--- END SIGNATURE ---\n")
        send_payload(DEVICE_ID, data, signature)
        time.sleep(interval_sec)

def create_sample_device(pem_path: str, device_id: str = None):
    from ecdsa import SigningKey, SECP256k1
    sk = SigningKey.generate(curve=SECP256k1)
    with open(pem_path, 'wb') as f:
        f.write(sk.to_pem())
    # Sinh device_id nếu chưa có
    if device_id is None:
        pubkey_hex = sk.get_verifying_key().to_string("uncompressed").hex()
        device_id = f"IOT-{pubkey_hex[-8:].upper()}"
    print(f"DEVICE_ID={device_id}")
    print(f"PRIVATE_KEY_PATH={pem_path}")
    return device_id, pem_path

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "init_device":
        pem_path = "device_private_key.pem"
        create_sample_device(pem_path)
        print("\nHãy copy DEVICE_ID và PRIVATE_KEY_PATH vào file .env để sử dụng cho simulator!")
    elif DEVICE_ID is None or PRIVATE_KEY_PATH is None:
        logger.error("DEVICE_ID or PRIVATE_KEY_PATH not configured in .env")
    else:
        simulate_device_loop(interval_sec=3, repeat=10)
