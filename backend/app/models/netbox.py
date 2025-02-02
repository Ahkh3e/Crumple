from sqlalchemy import Column, Integer, String, JSON
from sqlalchemy.orm import relationship
from .base import Base

class NetBoxConnection(Base):
    """NetBox instance connection configuration"""
    __tablename__ = 'netbox_connections'

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    url = Column(String, nullable=False)
    api_key = Column(String, nullable=False)
    ssl_verify = Column(Integer, default=1)
    custom_fields = Column(JSON)  # For additional connection settings

    def get_headers(self):
        """Get HTTP headers for NetBox API requests"""
        return {
            'Authorization': f'Token {self.api_key}',
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        }

    def get_device_types_url(self):
        """Get URL for device types endpoint"""
        return f"{self.url.rstrip('/')}/api/dcim/device-types/"

    def get_manufacturers_url(self):
        """Get URL for manufacturers endpoint"""
        return f"{self.url.rstrip('/')}/api/dcim/manufacturers/"

    def get_interface_templates_url(self, device_type_id: int):
        """Get URL for interface templates endpoint"""
        return f"{self.url.rstrip('/')}/api/dcim/interface-templates/?devicetype_id={device_type_id}"

class NetBoxImportLog(Base):
    """Log of NetBox import operations"""
    __tablename__ = 'netbox_import_logs'

    id = Column(Integer, primary_key=True)
    connection_id = Column(Integer, nullable=False)
    timestamp = Column(Integer, nullable=False)  # Unix timestamp
    operation = Column(String, nullable=False)  # e.g., 'import_device_types'
    status = Column(String, nullable=False)  # success, error
    details = Column(JSON)  # Import results and any error messages

class NetBoxSyncQueue(Base):
    """Queue for NetBox synchronization tasks"""
    __tablename__ = 'netbox_sync_queue'

    id = Column(Integer, primary_key=True)
    connection_id = Column(Integer, nullable=False)
    operation = Column(String, nullable=False)  # e.g., 'sync_device_types'
    status = Column(String, nullable=False)  # pending, processing, completed, error
    priority = Column(Integer, default=0)
    created_at = Column(Integer, nullable=False)  # Unix timestamp
    started_at = Column(Integer)  # When processing started
    completed_at = Column(Integer)  # When processing finished
    parameters = Column(JSON)  # Operation-specific parameters
    result = Column(JSON)  # Operation results or error details
