# Test Plan

## 1. Objectives
- Validate the security, integrity, and reliability of the IoT-blockchain system.
- Ensure all functional and non-functional requirements are met.

## 2. Test Scope
- Device registration and authentication
- Data hash storage and retrieval on blockchain
- Data integrity verification
- IPFS integration
- Access control and audit logging

## 3. Test Types
- **Unit Tests:** Test individual modules (blockchain, IPFS, signature, etc.).
- **Integration Tests:** Test end-to-end data flow from device to blockchain and IPFS.
- **Security Tests:** Simulate attacks (device forgery, data tampering, replay attacks).
- **Performance Tests:** Measure system throughput and latency under load.

## 4. Test Cases
- Register a new device and verify blockchain record
- Submit IoT data and check hash on blockchain
- Retrieve and verify data integrity
- Attempt data tampering and ensure detection
- Simulate unauthorized device and ensure rejection
- Store and retrieve data from IPFS

## 5. Tools
- **Pytest:** For automated testing
- **Ganache/Hardhat:** For local blockchain testing
- **IPFS local node:** For storage tests

## 6. Success Criteria
- All tests pass without errors
- System detects and prevents all simulated attacks
- Data integrity and provenance are always verifiable
