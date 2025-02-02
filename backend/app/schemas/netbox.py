from typing import Optional, List, Dict, Any
from pydantic import BaseModel, HttpUrl

class NetBoxConnectionBase(BaseModel):
    name: str
    url: HttpUrl
    api_key: str
    ssl_verify: Optional[int] = 1
    custom_fields: Optional[Dict[str, Any]] = None

class NetBoxConnectionCreate(NetBoxConnectionBase):
    pass

class NetBoxConnection(NetBoxConnectionBase):
    id: int

    class Config:
        orm_mode = True

class NetBoxImportLogBase(BaseModel):
    connection_id: int
    timestamp: int
    operation: str
    status: str
    details: Optional[Dict[str, Any]] = None

class NetBoxImportLogCreate(NetBoxImportLogBase):
    pass

class NetBoxImportLog(NetBoxImportLogBase):
    id: int

    class Config:
        orm_mode = True

class NetBoxSyncQueueBase(BaseModel):
    connection_id: int
    operation: str
    status: str
    priority: Optional[int] = 0
    created_at: int
    started_at: Optional[int] = None
    completed_at: Optional[int] = None
    parameters: Optional[Dict[str, Any]] = None
    result: Optional[Dict[str, Any]] = None

class NetBoxSyncQueueCreate(NetBoxSyncQueueBase):
    pass

class NetBoxSyncQueue(NetBoxSyncQueueBase):
    id: int

    class Config:
        orm_mode = True

class NetBoxDeviceTypeImport(BaseModel):
    netbox_id: int
    name: str
    manufacturer: str
    model: str
    part_number: Optional[str] = None
    u_height: Optional[int] = None
    is_full_depth: Optional[bool] = None
    interfaces: List[Dict[str, Any]] = []

class NetBoxImportRequest(BaseModel):
    connection_id: int
    device_type_ids: Optional[List[int]] = None  # If None, import all
    include_interfaces: Optional[bool] = True

class NetBoxImportStatus(BaseModel):
    success: bool
    message: Optional[str] = None
    imported_count: Optional[int] = None
    errors: Optional[List[str]] = None
    details: Optional[Dict[str, Any]] = None

class NetBoxSyncStatus(BaseModel):
    success: bool
    message: Optional[str] = None
    sync_id: Optional[int] = None
    status: Optional[str] = None
    details: Optional[Dict[str, Any]] = None

class NetBoxInterfaceTemplate(BaseModel):
    name: str
    type: str
    mgmt_only: bool = False
    description: Optional[str] = None

class NetBoxDeviceTypeDetail(BaseModel):
    id: int
    name: str
    manufacturer: Dict[str, Any]
    model: str
    part_number: Optional[str] = None
    u_height: int = 1
    is_full_depth: bool = True
    interface_templates: List[NetBoxInterfaceTemplate] = []
