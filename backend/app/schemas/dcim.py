from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, RootModel

class InterfaceTypeBase(BaseModel):
    name: str
    speed: Optional[int] = None
    connector_type: Optional[str] = None
    media_type: Optional[str] = None
    category: Optional[str] = Field(None, description="Connection category (network, pcie, nvlink)")

class InterfaceTypeCreate(InterfaceTypeBase):
    pass

class InterfaceType(InterfaceTypeBase):
    id: int

    class Config:
        orm_mode = True

class InterfaceBase(BaseModel):
    name: str
    type: str
    position: str  # front, back, left, right
    speed: Optional[int] = None
    enabled: Optional[int] = 1
    mtu: Optional[int] = None
    mac_address: Optional[str] = None
    mgmt_only: Optional[int] = 0
    description: Optional[str] = None

class InterfaceCreate(InterfaceBase):
    pass

class Interface(InterfaceBase):
    id: int
    device_id: Optional[int] = None
    device_type_id: Optional[int] = None
    interface_type_id: Optional[int] = None
    connected_interface_id: Optional[int] = None
    interface_type: Optional[InterfaceType] = None

    class Config:
        orm_mode = True

class DeviceTypeBase(BaseModel):
    name: str
    manufacturer: str
    model: str
    category: str = Field(..., description="Device category (gpu, nic, switch)")
    part_number: Optional[str] = None
    u_height: Optional[int] = 1
    is_full_depth: Optional[int] = 1
    netbox_id: Optional[int] = None
    specs: Optional[Dict[str, Any]] = Field(None, description="Device-specific specifications")
    interfaces: List[InterfaceCreate] = []

class DeviceTypeCreate(DeviceTypeBase):
    pass

class DeviceType(DeviceTypeBase):
    id: int
    interface_types: List[InterfaceType] = []
    interfaces: List[Interface] = []

    class Config:
        orm_mode = True

class DeviceBase(BaseModel):
    name: str
    serial: Optional[str] = None
    position_x: Optional[float] = None
    position_y: Optional[float] = None
    custom_fields: Optional[Dict[str, Any]] = None

class DevicePlacement(BaseModel):
    device_type_id: int
    position_x: float
    position_y: float
    cluster_id: Optional[int] = None
    name: Optional[str] = None

class DeviceSearch(BaseModel):
    query: str
    category: Optional[str] = None

class DeviceCreate(DeviceBase):
    device_type_id: int
    cluster_id: Optional[int] = None

class Device(DeviceBase):
    id: int
    device_type_id: int
    cluster_id: Optional[int] = None
    device_type: DeviceType
    interfaces: List[Interface] = []

    class Config:
        orm_mode = True

class CableBase(BaseModel):
    type: str
    length: Optional[float] = None
    color: Optional[str] = None
    label: Optional[str] = None
    status: Optional[str] = "connected"

class CableCreate(CableBase):
    interface_a_id: int
    interface_b_id: int

class CableUpdate(CableBase):
    interface_a_id: Optional[int] = None
    interface_b_id: Optional[int] = None

class Cable(CableBase):
    id: int
    interface_a_id: int
    interface_b_id: int

    class Config:
        orm_mode = True

class CableList(RootModel[List[Cable]]):
    class Config:
        orm_mode = True

class ClusterBase(BaseModel):
    name: str
    description: Optional[str] = None
    site: Optional[str] = None
    status: Optional[str] = "active"
    parent_id: Optional[int] = None
    custom_fields: Optional[Dict[str, Any]] = None

class ClusterCreate(ClusterBase):
    pass

class Cluster(ClusterBase):
    id: int
    devices: List[Device] = []
    children: List['Cluster'] = []

    class Config:
        orm_mode = True

# Required for forward references in Cluster model
Cluster.update_forward_refs()

class TopologyNode(BaseModel):
    id: str
    type: str
    label: str
    position: Dict[str, float]

class TopologyEdge(BaseModel):
    source: str
    target: str
    type: str

class TopologyCreate(BaseModel):
    nodes: List[TopologyNode]
    edges: List[TopologyEdge]

class TopologyResponse(BaseModel):
    success: bool
    message: Optional[str] = None
    cluster_id: Optional[int] = None

class NetBoxImportResponse(BaseModel):
    success: bool
    message: Optional[str] = None
    imported_count: Optional[int] = None
    errors: Optional[List[str]] = None
