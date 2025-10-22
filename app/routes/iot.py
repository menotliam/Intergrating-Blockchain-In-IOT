from fastapi import APIRouter, HTTPException, status
from app.models.iot_data import IoTData
from app.services.signature import verify_signature, DEVICE_PUBLIC_KEYS
from app.services.ipfs import upload_to_ipfs
from app.services.blockchain import BlockchainService
import logging
from pydantic import BaseModel
import hashlib
from web3 import Web3
# initialize router & logger
router = APIRouter()
logger = logging.getLogger("iot")

# Initialize BlockchainService once (singleton pattern)
blockchain_service = BlockchainService()


# Helper: Lấy address thực sự của device từ registry (nếu có), fallback về account_address
def get_device_address(device_id: str) -> str:
    # Nếu device_id là address hex, trả về checksum address
    try:
        return Web3.to_checksum_address(device_id)
    except Exception:
        # Nếu device_id không phải address, fallback về account_address
        return Web3.to_checksum_address(blockchain_service.config.account_address)

def store_hash_on_chain(device_id: str, cid: str, data: dict, data_type: str = "sensor"):
    # Chuẩn bị tham số đúng cho storeDataHash của smart contract
    # _ipfsHash: cid, _dataType: data_type, _deviceId: address, _dataHash: hash của data
    device_address = get_device_address(device_id)
    data_bytes = str(sorted(data.items())).encode()
    data_hash = hashlib.sha256(data_bytes).digest()
    tx_result = blockchain_service.store_data_hash(
        cid,              # _ipfsHash
        data_type,        # _dataType
        device_address,   # _deviceId
        data_hash         # _dataHash (bytes32)
    )
    if not tx_result:
        raise Exception("Blockchain transaction failed")
    return tx_result.tx_hash

# In-memory device registry (for demo, replace with DB in production)
device_registry = {}

# Device registration model
class DeviceRegisterRequest(BaseModel):
    device_id: str
    public_key: str

# API endpoint: Đăng ký thiết bị
@router.post("/register")
def register_device(req: DeviceRegisterRequest):
    # Kiểm tra device_id có hợp lệ không (có thể là address hoặc chuỗi tuỳ ý)
    if not req.device_id or not req.public_key:
        raise HTTPException(status_code=400, detail="device_id and public_key are required")
    device_registry[req.device_id] = req.public_key
    DEVICE_PUBLIC_KEYS[req.device_id] = req.public_key
    logger.info(f"Registered device: {req.device_id}")
    return {"message": "Device registered successfully"}




# endpoint POST /upload
@router.post("/upload")
async def upload_iot_data(iot_data: IoTData):
    logger.info(f"Received data from device: {iot_data.device_id}")

    # Kiểm tra device_id đã đăng ký chưa
    if iot_data.device_id not in device_registry:
        logger.warning(f"Device not registered: {iot_data.device_id}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Device not registered"
        )

    # verify signature
    if not verify_signature(
        device_id=iot_data.device_id,
        data=iot_data.data,
        signature=iot_data.signature
    ):
        logger.warning(f"Invalid signature from device: {iot_data.device_id}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid signature or fake device"
        )

    # upload data to ipfs
    try:
        cid = upload_to_ipfs(iot_data.data)
        logger.info(f"Uploaded to IPFS: CID={cid}")
    except Exception as e:
        logger.error(f"IPFS upload error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"IPFS upload failed: {str(e)}"
        )

    # write new cid & device id on block chain
    try:
        tx_hash = store_hash_on_chain(
            device_id=iot_data.device_id,
            cid=cid,
            data=iot_data.data,
            data_type="sensor"  # hoặc lấy từ iot_data nếu có
        )
        logger.info(f"Stored on blockchain: TX={tx_hash}")
    except Exception as e:
        logger.error(f"Blockchain store error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Blockchain write failed: {str(e)}"
        )

    return {
        "message": "Upload successful",
        "device_id": iot_data.device_id,
        "ipfs_cid": cid,
        "tx_hash": tx_hash
    }