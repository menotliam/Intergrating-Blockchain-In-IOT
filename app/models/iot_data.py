from pydantic import BaseModel, Field, validator
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone

class SensorReadingModel(BaseModel):
    device_id: str # Could potentially be removed if always part of an IoTDataModel context
    temperature: float = Field(..., ge=-40, le=125)
    humidity: Optional[float] = Field(None, ge=0, le=100)
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    @validator('device_id')
    def validate_device_id(cls, v):
        # Ensure device_id starts with 'IOT-'
        if not v.startswith('IOT-'):
            raise ValueError('device_id must start with IOT-')
        return v

class DeviceConfigModel(BaseModel):
    # device_id: str # Often, the device_id is part of the parent IoTDeviceModel context
    sampling_rate: int = Field(..., ge=1, le=3600)
    active: bool = True
    sensors: List[str]

    # No 'device_id' validator here if it's not a field of DeviceConfigModel directly

class IoTDataModel(BaseModel):
    device_id: str
    readings: List[SensorReadingModel] # A list of well-defined sensor readings
    batch_timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: Dict[str, Any] = Field(default_factory=dict)

    @validator('device_id')
    def validate_device_id_iot_data(cls, v):
        if not v.startswith('IOT-'):
            raise ValueError('device_id must start with IOT-')
        return v

class IoTDeviceModel(BaseModel):
    device_id: str
    name: str
    device_type: str
    config: DeviceConfigModel # <--- Composing DeviceConfigModel here
    location: Optional[Dict[str, Any]] = Field(default_factory=dict)
    registration_time: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    @validator('device_id')
    def validate_device_id_iot_device(cls, v):
        if not v.startswith('IOT-'):
            raise ValueError('device_id must start with IOT-')
        return v

class IoTData(BaseModel):
    device_id: str
    data: Dict[str, Any]
    signature: str

    @validator('device_id')
    def validate_device_id(cls, v):
        if not v.startswith('IOT-'):
            raise ValueError('device_id must start with IOT-')
        return v