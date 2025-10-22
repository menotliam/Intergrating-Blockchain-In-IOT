import ipfshttpclient
import json

# Kết nối IPFS client (mặc định localhost:5001)
client = ipfshttpclient.connect()

def upload_to_ipfs(data: dict) -> str:
    """
    Upload a Python dict as JSON to IPFS, return the CID.
    Args:
        data: dict to upload
    Returns:
        str: IPFS CID
    """
    # Serialize data to JSON bytes
    json_bytes = json.dumps(data).encode()
    res = client.add_bytes(json_bytes)
    return res
