# Blockchain Solution

## 1. Rationale for Blockchain Integration
Blockchain provides a decentralized, tamper-proof ledger that ensures data integrity, transparency, and trust without relying on a central authority. This is crucial for IoT systems where device data authenticity and provenance are essential.

## 2. Smart Contract Design
- **DataStorage.sol:** Stores hashes of IoT data and references to IPFS.
- **DeviceRegistry.sol:** Manages device identities (DIDs) and public keys.
- **AccessControl.sol:** Implements role-based access control for data operations.
- **AuditLog.sol:** Records access and system events for traceability.

## 3. Data Flow
1. IoT device generates data and signs it.
2. Data is sent to the backend, which hashes the data and stores the hash on blockchain via smart contract.
3. Raw data is uploaded to IPFS; the IPFS hash is also stored on blockchain.
4. Users can retrieve and verify data integrity and provenance using blockchain records.

## 4. Security Features
- Immutable storage of data hashes.
- Decentralized verification of device and data authenticity.
- Audit trails for all data access and modifications.

## 5. Benefits
- Prevents data tampering and forgery.
- Enables transparent and auditable IoT data management.
- Reduces reliance on centralized trust models.
