# IoT Security Platform with Blockchain

A secure IoT platform using blockchain technology to ensure data integrity and prevent device forgery.

## Features

- **Data integrity verification** using blockchain immuatable ledger
- **Digital signatures** for device authentication and non-repudiation
- **Anti-forgery protection** for IoT devices with cryptographic validation
- **Distributed storage** with IPFS for decentralized data management
- **Real-time monitoring** dashboard with device status tracking

## Architecture

```
IoT Devices → Backend API → Smart Contracts → Blockchain
     ↓             ↓              ↓
Digital Sign   Validation    Data Storage
     ↓             ↓              ↓
  IPFS Store → Web Dashboard ← Monitoring
```

## Quick Start

### Prerequisites
- Python 3.8+
- Node.js & npm
- Git

### Installation

1. **Clone and setup**
```bash
git clone <repository-url>
cd iot-security-platform
pip install -r requirements.txt
npm install -g ganache-cli
```

2. **Start blockchain and deploy**
```bash
ganache-cli --host 0.0.0.0 --port 8545
cd contracts && python deploy.py
```

3. **Run application**
```bash
# Backend
cd app && python main.py

# Frontend
cd frontend && python -m http.server 8000
```

## Project Structure

```
├── contracts/           # Solidity smart contracts
│   ├── DataStorage.sol  # Main data storage contract
│   └── deploy.py        # Contract deployment
├── app/                 # Python backend API
│   ├── main.py          # Flask application
│   ├── routes/          # API endpoints
│   └── services/        # Business logic
├── frontend/            # Web interface
├── iot_device/          # Device simulator
├── tests/               # Test suites
└── docs/                # Documentation
```

## API Endpoints

- `POST /api/iot/data` - Submit IoT device data
- `GET /api/iot/verify/{device_id}` - Verify device authenticity  
- `GET /api/data/integrity/{hash}` - Check data integrity
- `GET /api/devices` - List registered devices

## Testing

```bash
# Run all tests
python -m pytest tests/ -v

# Run specific tests
python -m pytest tests/test_signature.py
python -m pytest tests/test_data_integrity.py
```

## Tech Stack

**Blockchain**
- Ethereum, Solidity
- Web3.py for interaction

**Backend**
- Python, Flask
- Cryptographic libraries
- IPFS integration

**Frontend**
- HTML5, JavaScript, CSS3
- Real-time visualization

## License

MIT License
