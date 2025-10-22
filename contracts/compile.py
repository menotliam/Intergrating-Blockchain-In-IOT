#!/usr/bin/env python3
"""
Smart Contract Compilation Script
Compiles Solidity contracts using solcx and outputs ABI and bytecode
"""

import json
import os
import sys
from pathlib import Path
from typing import Dict, Any, Optional

try:
    from solcx import compile_standard, install_solc, get_installed_solc_versions
except ImportError:
    print("Error: solcx not installed. Run: pip install py-solc-x")
    sys.exit(1)

# Configuration
SOLIDITY_VERSION = "0.8.20"
CONTRACTS_DIR = Path(__file__).parent
BUILD_DIR = CONTRACTS_DIR / "build"
ARTIFACTS_DIR = BUILD_DIR / "artifacts"

# OpenZeppelin imports mapping for local compilation
REMAPPINGS = [
    "@openzeppelin/contracts/=node_modules/@openzeppelin/contracts/",
]

class ContractCompiler:
    """Smart contract compilation utility"""

    def __init__(self, solc_version: str = SOLIDITY_VERSION):
        self.solc_version = solc_version
        self.ensure_solc_installed()

    def ensure_solc_installed(self):
        """Ensure the required Solidity compiler version is installed"""
        installed_versions = get_installed_solc_versions()
        if self.solc_version not in [str(v) for v in installed_versions]:
            print(f"Installing Solidity compiler version {self.solc_version}...")
            install_solc(self.solc_version)
            print(f"Solidity {self.solc_version} installed successfully!")
        else:
            print(f"Solidity {self.solc_version} already installed")

    def read_contract_file(self, file_path: Path) -> str:
        """Read contract source code from file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                return file.read()
        except FileNotFoundError:
            raise FileNotFoundError(f"Contract file not found: {file_path}")
        except Exception as e:
            raise Exception(f"Error reading contract file {file_path}: {e}")

    def create_compilation_input(self, contracts: Dict[str, str]) -> Dict[str, Any]:
        """Create compilation input for solc"""
        return {
            "language": "Solidity",
            "sources": {
                contract_name: {
                    "content": source_code
                }
                for contract_name, source_code in contracts.items()
            },
            "settings": {
                "outputSelection": {
                    "*": {
                        "*": [
                            "abi",
                            "evm.bytecode",
                            "evm.deployedBytecode",
                            "evm.methodIdentifiers",
                            "evm.gasEstimates",
                            "metadata"
                        ]
                    }
                },
                "optimizer": {
                    "enabled": True,
                    "runs": 200
                },
                "remappings": REMAPPINGS,
                "evmVersion": "london"
            }
        }

    def compile_contracts(self, contract_files: list) -> Dict[str, Any]:
        """Compile multiple contract files"""
        contracts = {}

        # Read all contract files
        for file_path in contract_files:
            if not file_path.exists():
                raise FileNotFoundError(f"Contract file not found: {file_path}")

            source_code = self.read_contract_file(file_path)
            contracts[file_path.name] = source_code

        # Create compilation input
        compilation_input = self.create_compilation_input(contracts)

        try:
            print("Compiling contracts...")
            compiled_sol = compile_standard(
                compilation_input,
                solc_version=self.solc_version
            )
            print("Compilation successful!")
            return compiled_sol
        except Exception as e:
            print(f"Compilation failed: {e}")
            raise

    def save_artifacts(self, compiled_contracts: Dict[str, Any]):
        """Save compilation artifacts to files"""
        # Create build directories
        BUILD_DIR.mkdir(exist_ok=True)
        ARTIFACTS_DIR.mkdir(exist_ok=True)

        # Save full compilation output
        with open(BUILD_DIR / "contracts.json", 'w') as f:
            json.dump(compiled_contracts, f, indent=2)

        # Extract and save individual contract artifacts
        contracts = compiled_contracts.get("contracts", {})

        for file_name, file_contracts in contracts.items():
            for contract_name, contract_data in file_contracts.items():
                artifact = {
                    "contractName": contract_name,
                    "abi": contract_data["abi"],
                    "bytecode": contract_data["evm"]["bytecode"]["object"],
                    "deployedBytecode": contract_data["evm"]["deployedBytecode"]["object"],
                    "methodIdentifiers": contract_data["evm"]["methodIdentifiers"],
                    "gasEstimates": contract_data["evm"]["gasEstimates"],
                    "metadata": json.loads(contract_data["metadata"]),
                    "sourceFile": file_name,
                    "compiler": {
                        "version": self.solc_version,
                        "optimizer": True,
                        "runs": 200
                    }
                }

                # Save individual artifact
                artifact_file = ARTIFACTS_DIR / f"{contract_name}.json"
                with open(artifact_file, 'w') as f:
                    json.dump(artifact, f, indent=2)

                print(f"Saved artifact: {artifact_file}")

                # Save ABI separately for easy access
                abi_file = ARTIFACTS_DIR / f"{contract_name}_abi.json"
                with open(abi_file, 'w') as f:
                    json.dump(contract_data["abi"], f, indent=2)

                print(f"Saved ABI: {abi_file}")

    def get_contract_info(self, contract_name: str) -> Optional[Dict[str, Any]]:
        """Get compiled contract information"""
        artifact_file = ARTIFACTS_DIR / f"{contract_name}.json"

        if not artifact_file.exists():
            return None

        with open(artifact_file, 'r') as f:
            return json.load(f)

    def clean_build(self):
        """Clean build artifacts"""
        if BUILD_DIR.exists():
            import shutil
            shutil.rmtree(BUILD_DIR)
            print("Build directory cleaned")

def main():
    """Main compilation function"""
    print("=== IoT Blockchain Smart Contract Compiler ===")

    # Initialize compiler
    compiler = ContractCompiler()

    # Find all Solidity files in contracts directory
    contract_files = list(CONTRACTS_DIR.glob("*.sol"))

    if not contract_files:
        print("No Solidity files found in contracts directory")
        return

    print(f"Found {len(contract_files)} contract file(s):")
    for file in contract_files:
        print(f"  - {file.name}")

    try:
        # Compile contracts
        compiled_contracts = compiler.compile_contracts(contract_files)

        # Save artifacts
        compiler.save_artifacts(compiled_contracts)

        print("\n=== Compilation Summary ===")
        contracts = compiled_contracts.get("contracts", {})
        total_contracts = sum(len(file_contracts) for file_contracts in contracts.values())
        print(f"Successfully compiled {total_contracts} contract(s)")

        # Show contract details
        for file_name, file_contracts in contracts.items():
            print(f"\nFile: {file_name}")
            for contract_name, contract_data in file_contracts.items():
                bytecode_size = len(contract_data["evm"]["bytecode"]["object"]) // 2
                print(f"  - {contract_name}: {bytecode_size} bytes")

        print(f"\nArtifacts saved to: {ARTIFACTS_DIR}")

    except Exception as e:
        print(f"Compilation failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()