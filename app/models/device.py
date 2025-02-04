from .. import db
from sqlalchemy.dialects.postgresql import JSONB, UUID
import uuid

class Device(db.Model):
    """Device model representing a Netbox device"""
    __tablename__ = 'devices'
    __table_args__ = {'schema': 'workboard'}

    id = db.Column(UUID, primary_key=True, default=uuid.uuid4)
    cluster_id = db.Column(UUID, db.ForeignKey('workboard.clusters.id', ondelete='CASCADE'))
    netbox_id = db.Column(db.Integer, unique=True, nullable=False)
    name = db.Column(db.String(255), nullable=False)
    device_type = db.Column(db.String(255))
    interfaces = db.Column(JSONB)
    position = db.Column(JSONB)  # For Cytoscape layout
    meta_data = db.Column(JSONB)
    created_at = db.Column(db.DateTime(timezone=True), server_default=db.func.current_timestamp())
    updated_at = db.Column(db.DateTime(timezone=True), server_default=db.func.current_timestamp())

    # Relationships for connections
    connections_a = db.relationship('Connection', 
                                  backref='device_a',
                                  foreign_keys='Connection.device_a_id',
                                  lazy=True,
                                  cascade='all, delete-orphan')
    connections_b = db.relationship('Connection',
                                  backref='device_b',
                                  foreign_keys='Connection.device_b_id',
                                  lazy=True,
                                  cascade='all, delete-orphan')

    def update_from_netbox(self, data):
        """Update device from Netbox data"""
        from .device_role import DeviceRole  # Import here to avoid circular dependency
        
        self.netbox_id = data['id']
        self.name = data['name']
        self.device_type = data.get('device_type', {}).get('model')
        
        # Get role and ensure it has a color
        role_name = data.get('role', {}).get('name')
        role = None
        if role_name:
            role = DeviceRole.get_or_create(role_name)
        
        # Store metadata
        self.meta_data = {
            'manufacturer': data.get('device_type', {}).get('manufacturer', {}).get('name'),
            'role': role_name,
            'role_color': role.color if role else None,  # Store color in metadata
            'status': data.get('status', {}).get('value'),
            'description': data.get('description', ''),
            'comments': data.get('comments', ''),
            'tags': data.get('tags', []),
            'custom_fields': data.get('custom_fields', {}),
            'created': data.get('created'),
            'last_updated': data.get('last_updated')
        }
        
        db.session.add(self)
        db.session.commit()

    def update_interfaces(self, interfaces_data):
        """Update device interfaces from Netbox data"""
        self.interfaces = []
        for interface in interfaces_data:
            # Get connected device info if available
            connected_to = None
            if interface.get('connected_endpoints'):
                endpoint = interface['connected_endpoints'][0]
                connected_to = {
                    'device': endpoint['device']['name'],
                    'interface': endpoint['name']
                }
            
            # Store interface info
            self.interfaces.append({
                'id': interface['id'],
                'name': interface['name'],
                'type': interface.get('type', {}).get('value'),
                'enabled': interface.get('enabled', True),
                'mgmt_only': interface.get('mgmt_only', False),
                'description': interface.get('description', ''),
                'connected_to': connected_to
            })
        
        db.session.add(self)

    def to_dict(self):
        """Convert device to dictionary"""
        return {
            'id': str(self.id),
            'netbox_id': self.netbox_id,
            'cluster_id': str(self.cluster_id) if self.cluster_id else None,
            'name': self.name,
            'device_type': self.device_type,
            'role': self.meta_data.get('role') if isinstance(self.meta_data, dict) else None,
            'status': self.meta_data.get('status') if isinstance(self.meta_data, dict) else None,
            'interfaces': list(self.interfaces) if self.interfaces else [],
            'position': dict(self.position) if self.position else {},
            'meta_data': dict(self.meta_data) if self.meta_data else {},
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

    def __repr__(self):
        return f'<Device {self.name}>'
