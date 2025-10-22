pragma solidity ^0.8.20;

import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/utils/ReentrancyGuard.sol";

/**
 * @title DataStorage
 * @dev Smart contract for IoT-Blockchain security system
 * Handles DID management, public key storage, data hashes, and access control
 */
contract DataStorage is Ownable, ReentrancyGuard {
    /**
     * @dev Constructor sets the deployer as the contract owner.
     */
    constructor() Ownable(msg.sender) {}
    // Counter for device IDs
    uint256 private _deviceIdCounter = 0;

    // Structure for Device Identity Document (DID)
    struct DeviceIdentity {
        string did;           // Decentralized Identifier
        address publicKey;    // Device public key (derived from ECDSA)
        address controller;   // Controller address (owner/gateway)
        uint256 timestamp;    // Registration timestamp
        bool isActive;        // Device status
        string metadata;      // Additional device metadata (JSON string)
    }

    // Structure for Data Hash Storage
    struct DataRecord {
        string ipfsHash;      // IPFS hash (CID) of encrypted data
        string dataType;      // Type of data (temperature, camera_feed, etc.)
        address deviceId;     // Device that generated the data
        uint256 timestamp;    // Data creation timestamp
        bytes32 dataHash;     // Hash of the actual data for integrity
        bool isValid;         // Data validity status
    }

    // Structure for Access Control
    struct AccessPermission {
        address requester;    // Address requesting access
        string resourceId;    // Resource identifier (IPFS hash or data ID)
        bool hasAccess;      // Access permission status
        uint256 grantedAt;   // When access was granted
        uint256 expiresAt;   // When access expires (0 = no expiration)
    }

    // Mappings
    mapping(address => DeviceIdentity) public devices;           // publicKey => DeviceIdentity
    mapping(string => address) public didToAddress;              // DID => publicKey address
    mapping(string => DataRecord) public dataRecords;           // IPFS hash => DataRecord
    mapping(address => mapping(string => AccessPermission)) public accessControl; // requester => resourceId => permission
    mapping(address => string[]) public deviceDataHashes;       // device => array of IPFS hashes

    // Arrays for enumeration
    address[] public registeredDevices;
    string[] public allDataHashes;

    // Events
    event DeviceRegistered(string indexed did, address indexed publicKey, address indexed controller);
    event DataStored(string indexed ipfsHash, address indexed deviceId, string dataType);
    event AccessGranted(address indexed requester, string indexed resourceId, uint256 expiresAt);
    event AccessRevoked(address indexed requester, string indexed resourceId);
    event DeviceStatusChanged(address indexed deviceId, bool isActive);

    // Modifiers
    modifier onlyRegisteredDevice(address deviceKey) {
        require(devices[deviceKey].isActive, "Device not registered or inactive");
        _;
    }

    modifier onlyController(address deviceKey) {
        require(
            devices[deviceKey].controller == msg.sender || owner() == msg.sender,
            "Not authorized controller"
        );
        _;
    }

    /**
     * @dev Register a new IoT device with DID
     * @param _did Decentralized Identifier
     * @param _publicKey Device public key
     * @param _controller Controller address
     * @param _metadata Device metadata
     */
    function registerDevice(
        string memory _did,
        address _publicKey,
        address _controller,
        string memory _metadata
    ) external onlyOwner {
        require(bytes(_did).length > 0, "DID cannot be empty");
        require(_publicKey != address(0), "Invalid public key");
        require(_controller != address(0), "Invalid controller address");
        require(!devices[_publicKey].isActive, "Device already registered");
        require(didToAddress[_did] == address(0), "DID already exists");

        // Create device identity
        devices[_publicKey] = DeviceIdentity({
            did: _did,
            publicKey: _publicKey,
            controller: _controller,
            timestamp: block.timestamp,
            isActive: true,
            metadata: _metadata
        });

        // Map DID to address
        didToAddress[_did] = _publicKey;

        // Add to registered devices array
        registeredDevices.push(_publicKey);

        emit DeviceRegistered(_did, _publicKey, _controller);
    }

    /**
     * @dev Store data hash on blockchain
     * @param _ipfsHash IPFS hash of encrypted data
     * @param _dataType Type of data
     * @param _deviceId Device that generated the data
     * @param _dataHash Hash of actual data for integrity
     */
    function storeDataHash(
        string memory _ipfsHash,
        string memory _dataType,
        address _deviceId,
        bytes32 _dataHash
    ) external onlyRegisteredDevice(_deviceId) {
        require(bytes(_ipfsHash).length > 0, "IPFS hash cannot be empty");
        require(bytes(_dataType).length > 0, "Data type cannot be empty");
        require(
            devices[_deviceId].controller == msg.sender || _deviceId == msg.sender,
            "Not authorized to store data for this device"
        );
        require(!dataRecords[_ipfsHash].isValid, "Data hash already exists");

        // Create data record
        dataRecords[_ipfsHash] = DataRecord({
            ipfsHash: _ipfsHash,
            dataType: _dataType,
            deviceId: _deviceId,
            timestamp: block.timestamp,
            dataHash: _dataHash,
            isValid: true
        });

        // Add to device's data hashes
        deviceDataHashes[_deviceId].push(_ipfsHash);

        // Add to all data hashes
        allDataHashes.push(_ipfsHash);

        emit DataStored(_ipfsHash, _deviceId, _dataType);
    }

    /**
     * @dev Grant access to a resource
     * @param _requester Address requesting access
     * @param _resourceId Resource identifier
     * @param _expiresAt Expiration timestamp (0 for no expiration)
     */
    function grantAccess(
        address _requester,
        string memory _resourceId,
        uint256 _expiresAt
    ) external {
        require(_requester != address(0), "Invalid requester address");
        require(bytes(_resourceId).length > 0, "Resource ID cannot be empty");

        // Check if caller is authorized (device controller or contract owner)
        DataRecord memory record = dataRecords[_resourceId];
        require(
            devices[record.deviceId].controller == msg.sender || owner() == msg.sender,
            "Not authorized to grant access"
        );

        // Grant access
        accessControl[_requester][_resourceId] = AccessPermission({
            requester: _requester,
            resourceId: _resourceId,
            hasAccess: true,
            grantedAt: block.timestamp,
            expiresAt: _expiresAt
        });

        emit AccessGranted(_requester, _resourceId, _expiresAt);
    }

    /**
     * @dev Revoke access to a resource
     * @param _requester Address to revoke access from
     * @param _resourceId Resource identifier
     */
    function revokeAccess(
        address _requester,
        string memory _resourceId
    ) external {
        DataRecord memory record = dataRecords[_resourceId];
        require(
            devices[record.deviceId].controller == msg.sender || owner() == msg.sender,
            "Not authorized to revoke access"
        );

        accessControl[_requester][_resourceId].hasAccess = false;

        emit AccessRevoked(_requester, _resourceId);
    }

    /**
     * @dev Check if an address has access to a resource
     * @param _requester Address to check
     * @param _resourceId Resource identifier
     * @return bool Access permission status
     */
    function checkAccess(
        address _requester,
        string memory _resourceId
    ) external view returns (bool) {
        AccessPermission memory permission = accessControl[_requester][_resourceId];

        // Check if access exists and is not expired
        if (!permission.hasAccess) {
            return false;
        }

        if (permission.expiresAt > 0 && block.timestamp > permission.expiresAt) {
            return false;
        }

        return true;
    }

    /**
     * @dev Update device status
     * @param _deviceKey Device public key
     * @param _isActive New status
     */
    function updateDeviceStatus(
        address _deviceKey,
        bool _isActive
    ) external onlyController(_deviceKey) {
        devices[_deviceKey].isActive = _isActive;
        emit DeviceStatusChanged(_deviceKey, _isActive);
    }

    /**
     * @dev Verify data integrity
     * @param _ipfsHash IPFS hash
     * @param _dataHash Original data hash
     * @return bool Integrity verification result
     */
    function verifyDataIntegrity(
        string memory _ipfsHash,
        bytes32 _dataHash
    ) external view returns (bool) {
        DataRecord memory record = dataRecords[_ipfsHash];
        return record.isValid && record.dataHash == _dataHash;
    }

    /**
     * @dev Get device information by DID
     * @param _did Decentralized Identifier
     * @return DeviceIdentity Device information
     */
    function getDeviceByDID(string memory _did) external view returns (DeviceIdentity memory) {
        address deviceKey = didToAddress[_did];
        require(deviceKey != address(0), "Device not found");
        return devices[deviceKey];
    }

    /**
     * @dev Get data hashes for a device
     * @param _deviceKey Device public key
     * @return string[] Array of IPFS hashes
     */
    function getDeviceDataHashes(address _deviceKey) external view returns (string[] memory) {
        return deviceDataHashes[_deviceKey];
    }

    /**
     * @dev Get total number of registered devices
     * @return uint256 Number of devices
     */
    function getTotalDevices() external view returns (uint256) {
        return registeredDevices.length;
    }

    /**
     * @dev Get total number of data records
     * @return uint256 Number of data records
     */
    function getTotalDataRecords() external view returns (uint256) {
        return allDataHashes.length;
    }
}