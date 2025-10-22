# System Analysis

## 1. Stakeholders
- **IoT Device Owners:** Individuals or organizations deploying IoT devices.
- **System Administrators:** Manage and monitor the IoT-blockchain system.
- **End Users:** Consume and verify IoT data.
- **Attackers:** Potential adversaries attempting to compromise data integrity or device authenticity.

## 2. Functional Requirements
- Register and authenticate IoT devices securely.
- Collect and transmit data from IoT devices to the backend.
- Hash and store data on blockchain for immutability.
- Retrieve and verify data integrity and provenance.
- Store raw data on IPFS for decentralized storage.
- Provide RESTful APIs for data access and verification.

## 3. Non-Functional Requirements
- **Security:** End-to-end encryption, secure key management, access control.
- **Scalability:** Support for increasing number of devices and data volume.
- **Reliability:** High availability and fault tolerance.
- **Auditability:** Transparent and immutable logs of all operations.

## 4. Threat Analysis
- Device spoofing and unauthorized access.
- Data interception and tampering during transmission.
- Smart contract vulnerabilities.
- Denial of Service (DoS) attacks on backend or blockchain nodes.

## 5. System Constraints
- Limited resources on IoT devices (CPU, memory, storage).
- Network latency and reliability.
- Blockchain transaction costs and throughput.

## 6. Success Criteria
- Only authenticated devices can submit data.
- All data hashes stored on blockchain are immutable and verifiable.
- System can detect and reject tampered or forged data.
