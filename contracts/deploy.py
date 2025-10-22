#!/usr/bin/env python3
"""
Smart Contract Deployment Script
Deploys compiled contracts to Polygon network (Mumbai testnet)
"""

import json
import os
import sys
import time
from pathlib import Path
from typing import Dict, Any, Optional

try:
    from web3 import Web3
    from web3.middleware import geth_poa_middleware
except ImportError:
    print("Error: web3 not installed. Run: pip install web3")
    sys.exit(1)

try:
    from dotenv import load_dotenv
except ImportError:
    print("Error: python-dotenv not installed. Run: pip install python-dotenv")
    sys.exit(1)

# Load environment variables
load_dotenv()

# Configuration
CONTRACTS_DIR = Path(__file__).parent
ARTIFACTS_DIR = CONTRACTS_DIR / "build" / "artifacts"
DEPLOYMENT_FILE = CONTRACTS_DIR / "deployments.json"

# Network configurations
NETWORKS = {
    "amoy": {
        "name": "Polygon Amoy Testnet",
        "rpc_url": "https://polygon-amoy.g.alchemy.com/v2/your-amoy-api-key",
        "chain_id": 80002,
        "explorer": "https://www.oklink.com/amoy/address"
    },
    "polygon": {
        "name": "Polygon Mainnet",
        "rpc_url": "https://polygon-rpc.com",
        "chain_id": 137,
        "explorer": "https://polygonscan.com"
    },
    "localhost": {
        "name": "Local Development",
        "rpc_url": "http://127.0.0.1:8545",
        "chain_id": 1337,
        "explorer": None
    }
}

class ContractDeployer:
    """Smart contract deployment utility"""

    def __init__(self, network: str = "amoy"):
        self.network = network
        self.network_config = NETWORKS.get(network)

        if not self.network_config:
            raise ValueError(f"Unsupported network: {network}")

        self.w3 = self.setup_web3()
        self.account = self.setup_account()

    def setup_web3(self) -> Web3:
        """Setup Web3 connection"""
        # Get RPC URL from environment or use default
        rpc_url = os.getenv("BLOCKCHAIN_RPC_URL", self.network_config["rpc_url"])

        print(f"Connecting to {self.network_config['name']}...")
        print(f"RPC URL: {rpc_url}")

        w3 = Web3(Web3.HTTPProvider(rpc_url))

        # Add PoA middleware for Polygon testnets
        if self.network in ["amoy", "mumbai", "polygon"]:
            w3.middleware_onion.inject(geth_poa_middleware, layer=0)

        if not w3.is_connected():
            raise ConnectionError(f"Failed to connect to {self.network_config['name']}")

        print(f"Connected to {self.network_config['name']} (Chain ID: {w3.eth.chain_id})")
        return w3

    def setup_account(self):
        """Setup deployment account"""
        private_key = os.getenv("PRIVATE_KEY")

        if not private_key:
            raise ValueError("PRIVATE_KEY environment variable not set")

        # Remove 0x prefix if present
        if private_key.startswith("0x"):
            private_key = private_key[2:]

        account = self.w3.eth.account.from_key(private_key)
        balance = self.w3.eth.get_balance(account.address)
        balance_eth = self.w3.from_wei(balance, 'ether')

        print(f"Deployer address: {account.address}")
        print(f"Balance: {balance_eth:.4f} {'MATIC' if self.network != 'localhost' else 'ETH'}")

        if balance == 0:
            raise ValueError("Insufficient balance for deployment")

        return account

    def load_contract_artifact(self, contract_name: str) -> Dict[str, Any]:
        """Load compiled contract artifact"""
        artifact_file = ARTIFACTS_DIR / f"{contract_name}.json"

        if not artifact_file.exists():
            raise FileNotFoundError(f"Contract artifact not found: {artifact_file}")

        with open(artifact_file, 'r') as f:
            return json.load(f)

    def estimate_gas(self, contract_bytecode: str, constructor_args: tuple = ()) -> int:
        """Estimate gas for contract deployment"""
        try:
            # Create a transaction to estimate gas
            transaction = {
                'from': self.account.address,
                'data': contract_bytecode,
                'value': 0
            }

            if constructor_args:
                # If there are constructor arguments, we need to encode them
                # This is a simplified estimation
                pass

            gas_estimate = self.w3.eth.estimate_gas(transaction)
            return int(gas_estimate * 1.2)  # Add 20% buffer
        except Exception as e:
            print(f"Gas estimation failed: {e}")
            return 2000000  # Default gas limit

    def deploy_contract(
        self, 
        contract_name: str, 
        constructor_args: tuple = (),
        gas_limit: Optional[int] = None
    ) -> Dict[str, Any]:
        """Deploy a smart contract"""
        print(f"\n=== Deploying {contract_name} ===")

        # Load contract artifact
        artifact = self.load_contract_artifact(contract_name)
        abi = artifact["abi"]
        bytecode = artifact["bytecode"]

        if not bytecode or bytecode == "0x":
            raise ValueError(f"No bytecode found for {contract_name}")

        # Create contract factory
        contract = self.w3.eth.contract(abi=abi, bytecode=bytecode)

        # Estimate gas if not provided
        if gas_limit is None:
            gas_limit = self.estimate_gas(bytecode, constructor_args)

        print(f"Gas limit: {gas_limit:,}")

        # Get current gas price
        gas_price = self.w3.eth.gas_price
        print(f"Gas price: {self.w3.from_wei(gas_price, 'gwei'):.2f} Gwei")

        # Calculate deployment cost
        deployment_cost = gas_limit * gas_price
        deployment_cost_eth = self.w3.from_wei(deployment_cost, 'ether')
        print(f"Estimated cost: {deployment_cost_eth:.6f} {'MATIC' if self.network != 'localhost' else 'ETH'}")

        # Build deployment transaction
        transaction = contract.constructor().build_transaction({
            'from': self.account.address,
            'gas': gas_limit,
            'gasPrice': gas_price,
            'nonce': self.w3.eth.get_transaction_count(self.account.address),
        })

        # Sign and send transaction
        signed_txn = self.w3.eth.account.sign_transaction(transaction, self.account.key)

        print("Sending deployment transaction...")
        tx_hash = self.w3.eth.send_raw_transaction(signed_txn.rawTransaction)
        print(f"Transaction hash: {tx_hash.hex()}")

        # Wait for confirmation
        print("Waiting for confirmation...")
        tx_receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash, timeout=300)

        if tx_receipt.status == 0:
            raise Exception("Contract deployment failed")

        contract_address = tx_receipt.contractAddress
        gas_used = tx_receipt.gasUsed
        actual_cost = gas_used * gas_price
        actual_cost_eth = self.w3.from_wei(actual_cost, 'ether')

        print(f"✅ Contract deployed successfully!")
        print(f"Contract address: {contract_address}")
        print(f"Gas used: {gas_used:,} ({gas_used/gas_limit*100:.1f}% of limit)")
        print(f"Actual cost: {actual_cost_eth:.6f} {'MATIC' if self.network != 'localhost' else 'ETH'}")

        if self.network_config["explorer"]:
            print(f"Explorer: {self.network_config['explorer']}/address/{contract_address}")

        return {
            "name": contract_name,
            "address": contract_address,
            "transaction_hash": tx_hash.hex(),
            "block_number": tx_receipt.blockNumber,
            "gas_used": gas_used,
            "gas_limit": gas_limit,
            "gas_price": gas_price,
            "cost": actual_cost_eth,
            "network": self.network,
            "timestamp": int(time.time()),
            "abi": abi
        }

    def save_deployment(self, deployment_info: Dict[str, Any]):
        """Save deployment information to file"""
        deployments = {}

        # Load existing deployments
        if DEPLOYMENT_FILE.exists():
            with open(DEPLOYMENT_FILE, 'r') as f:
                deployments = json.load(f)

        # Add new deployment
        network_deployments = deployments.get(self.network, {})
        network_deployments[deployment_info["name"]] = deployment_info
        deployments[self.network] = network_deployments

        # Save to file
        with open(DEPLOYMENT_FILE, 'w') as f:
            json.dump(deployments, f, indent=2, default=str)

        print(f"Deployment info saved to: {DEPLOYMENT_FILE}")

    def get_deployed_contract(self, contract_name: str) -> Optional[Dict[str, Any]]:
        """Get deployment information for a contract"""
        if not DEPLOYMENT_FILE.exists():
            return None

        with open(DEPLOYMENT_FILE, 'r') as f:
            deployments = json.load(f)

        return deployments.get(self.network, {}).get(contract_name)

    def verify_deployment(self, contract_name: str, address: str) -> bool:
        """Verify contract deployment"""
        try:
            code = self.w3.eth.get_code(address)
            return code != b'0x' and len(code) > 0
        except Exception:
            return False

def main():
    """Main deployment function"""
    print("=== IoT Blockchain Smart Contract Deployer ===")

    # Parse command line arguments
    network = "amoy"  # Default network
    if len(sys.argv) > 1:
        network = sys.argv[1]

    # Initialize deployer
    try:
        deployer = ContractDeployer(network)
    except Exception as e:
        print(f"Failed to initialize deployer: {e}")
        sys.exit(1)

    # List of contracts to deploy
    contracts_to_deploy = [
        {
            "name": "DataStorage",
            "constructor_args": (os.getenv("ACCOUNT_ADDRESS"),)
        }
    ]

    deployed_contracts = []

    for contract_info in contracts_to_deploy:
        try:
            # Check if already deployed
            existing = deployer.get_deployed_contract(contract_info["name"])
            if existing:
                print(f"\n{contract_info['name']} already deployed at: {existing['address']}")

                # Verify deployment
                if deployer.verify_deployment(contract_info["name"], existing["address"]):
                    print("✅ Deployment verified")
                    deployed_contracts.append(existing)
                    continue
                else:
                    print("❌ Deployment verification failed, redeploying...")

            # Deploy contract
            deployment_info = deployer.deploy_contract(
                contract_info["name"],
                contract_info["constructor_args"]
            )

            # Save deployment info
            deployer.save_deployment(deployment_info)
            deployed_contracts.append(deployment_info)

        except Exception as e:
            print(f"Failed to deploy {contract_info['name']}: {e}")
            continue

    # Summary
    print(f"\n=== Deployment Summary ===")
    print(f"Network: {deployer.network_config['name']}")
    print(f"Deployed {len(deployed_contracts)} contract(s):")

    total_cost = 0
    for contract in deployed_contracts:
        print(f"  - {contract['name']}: {contract['address']}")
        if 'cost' in contract:
            total_cost += float(contract['cost'])

    if total_cost > 0:
        currency = 'MATIC' if network != 'localhost' else 'ETH'
        print(f"Total deployment cost: {total_cost:.6f} {currency}")

if __name__ == "__main__":
    main()