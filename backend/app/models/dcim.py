from sqlalchemy import Column, Integer, String, ForeignKey, Float, JSON, Table
from sqlalchemy.orm import relationship
from .base import Base

# Association table for device types and interface types
device_interface_types = Table(
    'device_interface_types',
    Base.metadata,
    Column('device_type_id', Integer, ForeignKey('device_types.id')),
    Column('interface_type_id', Integer, ForeignKey('interface_types.id'))
)

class DeviceType(Base):
    """Device type model for all types of devices (GPUs, NICs, switches, etc.)"""
    __tablename__ = 'device_types'

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    manufacturer = Column(String, nullable=False)
    model = Column(String, nullable=False)
    category = Column(String, nullable=False)  # gpu, nic, switch, etc.
    part_number = Column(String)
    u_height = Column(Integer, default=1)
    is_full_depth = Column(Integer, default=1)
    netbox_id = Column(Integer, unique=True)  # ID from NetBox
    specs = Column(JSON)  # Device-specific specifications (e.g., GPU cores, memory, etc.)
    interface_types = relationship("InterfaceType", secondary=device_interface_types)
    interfaces = relationship("Interface", back_populates="device_type")
    devices = relationship("Device", back_populates="device_type")

class InterfaceType(Base):
    """Interface type model for all types of connections (PCIe, NVLink, Network, etc.)"""
    __tablename__ = 'interface_types'

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)  # e.g., QSFP28, PCIe4, NVLink
    category = Column(String, nullable=False)  # network, pcie, nvlink, etc.
    speed = Column(Integer)  # Speed in appropriate units (Mbps, GT/s, etc.)
    connector_type = Column(String)  # Physical connector type
    media_type = Column(String)  # e.g., fiber, copper, direct
    specs = Column(JSON)  # Interface-specific specifications
    interfaces = relationship("Interface", back_populates="interface_type")

class Device(Base):
    """Device instance model"""
    __tablename__ = 'devices'

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    device_type_id = Column(Integer, ForeignKey('device_types.id'), nullable=False)
    device_type = relationship("DeviceType", back_populates="devices")
    serial = Column(String)
    position_x = Column(Float)  # X coordinate in topology
    position_y = Column(Float)  # Y coordinate in topology
    cluster_id = Column(Integer, ForeignKey('clusters.id'))
    cluster = relationship("Cluster", back_populates="devices")
    interfaces = relationship("Interface", back_populates="device")
    custom_fields = Column(JSON)  # For additional device-specific data

class Interface(Base):
    """Generic interface model for all types of connections"""
    __tablename__ = 'interfaces'

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)  # e.g., eth0, PCIe0, NVLink0
    device_id = Column(Integer, ForeignKey('devices.id'))
    device = relationship("Device", back_populates="interfaces")
    device_type_id = Column(Integer, ForeignKey('device_types.id'))
    device_type = relationship("DeviceType", back_populates="interfaces")
    interface_type_id = Column(Integer, ForeignKey('interface_types.id'))
    interface_type = relationship("InterfaceType", back_populates="interfaces")
    position = Column(String, nullable=False)  # front, back, left, right
    enabled = Column(Integer, default=1)
    mtu = Column(Integer)
    mac_address = Column(String)
    mgmt_only = Column(Integer, default=0)
    description = Column(String)
    connected_interface_id = Column(Integer, ForeignKey('interfaces.id'))
    cable_a = relationship("Cable", foreign_keys="Cable.interface_a_id", back_populates="interface_a")
    cable_b = relationship("Cable", foreign_keys="Cable.interface_b_id", back_populates="interface_b")

class Cable(Base):
    """Physical cable connection model"""
    __tablename__ = 'cables'

    id = Column(Integer, primary_key=True)
    interface_a_id = Column(Integer, ForeignKey('interfaces.id'), nullable=False)
    interface_b_id = Column(Integer, ForeignKey('interfaces.id'), nullable=False)
    interface_a = relationship("Interface", foreign_keys=[interface_a_id], back_populates="cable_a")
    interface_b = relationship("Interface", foreign_keys=[interface_b_id], back_populates="cable_b")
    type = Column(String, nullable=False)  # ethernet, fiber, twinax
    length = Column(Float)  # Length in meters
    color = Column(String)
    label = Column(String)
    status = Column(String, default='connected')  # connected, planned, maintenance

class Cluster(Base):
    """Network topology cluster model"""
    __tablename__ = 'clusters'

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    description = Column(String)
    site = Column(String)
    status = Column(String, default='active')  # active, planned, maintenance
    parent_id = Column(Integer, ForeignKey('clusters.id'))
    devices = relationship("Device", back_populates="cluster")
    custom_fields = Column(JSON)  # For additional cluster-specific data
    
    # Parent-child relationships
    parent = relationship("Cluster", remote_side=[id], backref="children")
