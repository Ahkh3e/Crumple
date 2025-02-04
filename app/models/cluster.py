from .. import db
from sqlalchemy.dialects.postgresql import JSONB, UUID
import uuid

class Cluster(db.Model):
    """Cluster model representing a Netbox cluster"""
    __tablename__ = 'clusters'
    __table_args__ = {'schema': 'workboard'}

    id = db.Column(UUID, primary_key=True, default=uuid.uuid4)
    netbox_id = db.Column(db.Integer, unique=True, nullable=False)
    name = db.Column(db.String(255), nullable=False)
    type = db.Column(db.String(255))
    layout_data = db.Column(JSONB)  # For Cytoscape layout
    meta_data = db.Column(JSONB)  # For Netbox metadata
    last_sync = db.Column(db.DateTime(timezone=True))
    created_at = db.Column(db.DateTime(timezone=True), server_default=db.func.current_timestamp())
    updated_at = db.Column(db.DateTime(timezone=True), server_default=db.func.current_timestamp())

    # Relationships
    devices = db.relationship('Device', backref='cluster', lazy=True, cascade='all, delete-orphan')
    connections = db.relationship('Connection', backref='cluster', lazy=True, cascade='all, delete-orphan')

    def update_from_netbox(self, data):
        """Update cluster from Netbox data"""
        self.netbox_id = data['id']
        self.name = data['name']
        self.type = data.get('type', {}).get('name')
        self.meta_data = {
            'description': data.get('description', ''),
            'comments': data.get('comments', ''),
            'tags': data.get('tags', []),
            'custom_fields': data.get('custom_fields', {}),
            'created': data.get('created'),
            'last_updated': data.get('last_updated'),
            'status': data.get('status', {}).get('value'),
            'device_count': data.get('device_count', 0)
        }
        self.last_sync = db.func.current_timestamp()
        db.session.add(self)

    def to_dict(self):
        """Convert cluster to dictionary"""
        return {
            'id': str(self.id),
            'netbox_id': self.netbox_id,
            'name': self.name,
            'type': self.type,
            'status': self.meta_data.get('status') if isinstance(self.meta_data, dict) else None,
            'device_count': self.meta_data.get('device_count') if isinstance(self.meta_data, dict) else 0,
            'layout_data': dict(self.layout_data) if self.layout_data else {},
            'meta_data': dict(self.meta_data) if self.meta_data else {},
            'last_sync': self.last_sync.isoformat() if self.last_sync else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

    def __repr__(self):
        return f'<Cluster {self.name}>'
