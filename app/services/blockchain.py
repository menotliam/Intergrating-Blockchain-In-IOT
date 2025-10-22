from web3 import Web3
import os
import json
from pydantic import BaseModel, Field, validator, model_validator
from typing import Optional, Dict, Any, List
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


class BlockchainConfig(BaseModel):
    provider_url: str
    contract_address: str
    private_key: str
    account_address: str
    contract_abi_path: str = Field(..., description="Path to the contract ABI JSON file")
    contract_abi: list = None

    @validator('provider_url')
    def validate_provider_url(cls, v):
        if not v.startswith(('http://', 'https://', 'ws://', 'wss://')):
            raise ValueError('Provider URL must be a valid HTTP, HTTPS, WS, or WSS URL')
        return v

    @validator('contract_address', 'account_address')
    def validate_ethereum_address(cls, v):
        if not Web3.is_address(v):
            raise ValueError(f"Invalid Ethereum address: {v}")
        return v

    @validator('contract_abi_path')
    def validate_abi_path(cls, v):
        path = Path(v)
        if not path.exists():
            raise FileNotFoundError(f"ABI file not found at {v}")
        return v

    @model_validator(mode="after")
    def load_abi(self) -> "BlockchainConfig":
        path = self.contract_abi_path
        if path:
            try:
                with open(path, 'r') as abi_file:
                    abi_data = json.load(abi_file)
                    if isinstance(abi_data, dict) and 'abi' in abi_data:
                        abi_data = abi_data['abi']
                    self.contract_abi = abi_data
            except json.JSONDecodeError:
                raise ValueError(f"Invalid JSON in ABI file: {path}")
        return self


class TransactionResult(BaseModel):
    tx_hash: str
    status: int
    block_number: int


class BlockchainService:
    def __init__(self, config: Optional[BlockchainConfig] = None):
        if config is None:
            config = BlockchainConfig(
                provider_url=os.getenv('BLOCKCHAIN_RPC_URL', ''),
                contract_address=os.getenv('CONTRACT_ADDRESS', ''),
                private_key=os.getenv('PRIVATE_KEY', ''),
                account_address=os.getenv('ACCOUNT_ADDRESS', ''),
                contract_abi_path=os.getenv('CONTRACT_ABI_PATH', 'contracts/build/artifacts/DataStorage.json')
            )

        self.config = config

        # Connect to Ethereum-compatible network
        if self.config.provider_url.startswith(('ws://', 'wss://')):
            self.w3 = Web3(Web3.WebsocketProvider(self.config.provider_url))
        else:
            self.w3 = Web3(Web3.HTTPProvider(self.config.provider_url))

        if not self.w3.is_connected():
            raise ConnectionError("Failed to connect to the Ethereum node.")

        self.contract = self.w3.eth.contract(
            address=self.config.contract_address,
            abi=self.config.contract_abi
        )

    def store_data_hash(self, ipfs_hash: str, data_type: str, device_address: str, data_hash: bytes) -> Optional[TransactionResult]:
        """
        Store a data hash from an IoT device on the blockchain.
        """
        result = self.execute_contract_function("storeDataHash", ipfs_hash, data_type, device_address, data_hash)
        return TransactionResult(**result) if result else None

    def get_data_hash(self, index: int) -> Optional[str]:
        """
        Get IPFS hash at a given index (if contract supports).
        """
        return self.call_contract_function("getDataHash", index)

    def execute_contract_function(self, function_name: str, *args) -> Optional[Dict[str, Any]]:
        """
        Execute a smart contract function (transaction).
        """
        try:
            logger.info(f"Calling contract function: {function_name} with args: {args}")
            contract_function = getattr(self.contract.functions, function_name)(*args)

            nonce = self.w3.eth.get_transaction_count(self.config.account_address)
            tx = contract_function.build_transaction({
                'from': self.config.account_address,
                'nonce': nonce,
                'gas': 2000000,
                'gasPrice': self.w3.eth.gas_price
            })

            signed_tx = self.w3.eth.account.sign_transaction(tx, private_key=self.config.private_key)
            tx_hash = self.w3.eth.send_raw_transaction(signed_tx.rawTransaction)
            receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash, timeout=120)

            return {
                'tx_hash': tx_hash.hex(),
                'status': receipt.status,
                'block_number': receipt.blockNumber
            }

        except Exception as e:
            logger.error(f"An error occurred executing {function_name}: {e}")
            return None

    def call_contract_function(self, function_name: str, *args) -> Any:
        """
        Call a view/pure smart contract function.
        """
        try:
            contract_function = getattr(self.contract.functions, function_name)
            result = contract_function(*args).call()
            return result
        except Exception as e:
            logger.error(f"An error occurred calling {function_name}: {e}")
            return None
