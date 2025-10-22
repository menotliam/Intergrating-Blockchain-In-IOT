# URL for the Ethereum RPC endpoint.
RPC_URL = "http://127.0.0.1:8545"

# Address of the deployed DataStorage smart contract (contracts/deploy.py).
CONTRACT_ADDRESS = "YOUR_CONTRACT_ADDRESS"

# The ABI of the DataStorage smart contract.

CONTRACT_ABI = """
[
    {
        "constant": false,
        "inputs": [
            {
                "name": "timestamp",
                "type": "uint256"
            },
            {
                "name": "ipfsHash",
                "type": "string"
            }
        ],
        "name": "storeData",
        "outputs": [],
        "payable": false,
        "stateMutability": "nonpayable",
        "type": "function"
    },
    {
        "constant": true,
        "inputs": [
            {
                "name": "index",
                "type": "uint256"
            }
        ],
        "name": "getData",
        "outputs": [
            {
                "name": "",
                "type": "uint256"
            },
            {
                "name": "",
                "type": "string"
            }
        ],
        "payable": false,
        "stateMutability": "view",
        "type": "function"
    }
]
"""

# The private key by the backend to sign and send transactions.
BACKEND_ACCOUNT_PRIVATE_KEY = "YOUR_BACKEND_ACCOUNT_PRIVATE_KEY"

# Configuration for connecting to the IPFS client.
IPFS_CONFIG = {
    'host': '127.0.0.1',
    'port': 5001
}


# DID Key
DEVICE_PRIVATE_KEY = "YOUR_IOT_DEVICE_PRIVATE_KEY"

def init_config():
    """
    Khởi tạo và trả về dict config cho backend sử dụng.
    Lấy các giá trị từ biến môi trường nếu có, ưu tiên .env.
    """
    import os, json
    return {
        "RPC_URL": os.getenv("BLOCKCHAIN_RPC_URL", RPC_URL),
        "CONTRACT_ADDRESS": os.getenv("CONTRACT_ADDRESS", CONTRACT_ADDRESS),
        "CONTRACT_ABI": json.loads(os.getenv("CONTRACT_ABI", CONTRACT_ABI)),
        "PRIVATE_KEY": os.getenv("PRIVATE_KEY", BACKEND_ACCOUNT_PRIVATE_KEY),
        "IPFS_CONFIG": IPFS_CONFIG,
        "DEVICE_PRIVATE_KEY": os.getenv("DEVICE_PRIVATE_KEY", DEVICE_PRIVATE_KEY)
    }