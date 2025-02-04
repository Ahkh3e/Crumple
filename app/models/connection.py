from .. import db
from sqlalchemy.dialects.postgresql import JSONB, UUID
import uuid

class Connection(db.Model):
    """Connection model representing a cable connection between devices"""
    __tablename__ = 'connections'
    __table_args__ = {'schema': 'workboard'}

    id = db.Column(UUID, primary_key=True, default=uuid.uuid4)
    cluster_id = db.Column(UUID, db.ForeignKey('workboard.clusters.id', ondelete='CASCADE'))
    device_a_id = db.Column(UUID, db.ForeignKey('workboard.devices.id', ondelete='CASCADE'))
    device_b_id = db.Column(UUID, db.ForeignKey('workboard.devices.id', ondelete='CASCADE'))
    interface_a = db.Column(db.String(255))
    interface_b = db.Column(db.String(255))
    meta_data = db.Column(JSONB)
    created_at = db.Column(db.DateTime(timezone=True), server_default=db.func.current_timestamp())
    updated_at = db.Column(db.DateTime(timezone=True), server_default=db.func.current_timestamp())

    def update_from_netbox(self, data):
        """Update connection from Netbox data"""
        # Store metadata
        self.meta_data = {
            'type': data.get('type'),
            'label': data.get('label', ''),
            'color': data.get('color', ''),
            'description': data.get('description', ''),
            'comments': data.get('comments', ''),
            'tags': data.get('tags', []),
            'custom_fields': data.get('custom_fields', {}),
            'created': data.get('created'),
            'last_updated': data.get('last_updated'),
            'status': data.get('status', {}).get('value')
        }
        
        db.session.add(self)

    def to_dict(self):
        """Convert connection to dictionary"""
        return {
            'id': str(self.id),
            'cluster_id': str(self.cluster_id) if self.cluster_id else None,
            'device_a': {
                'id': str(self.device_a_id),
                'name': self.device_a.name if self.device_a else None,
                'interface': self.interface_a
            },
            'device_b': {
                'id': str(self.device_b_id),
                'name': self.device_b.name if self.device_b else None,
                'interface': self.interface_b
            },
            'status': self.meta_data.get('status') if isinstance(self.meta_data, dict) else None,
            'meta_data': dict(self.meta_data) if self.meta_data else {},
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

    def to_cytoscape_edge(self):
        """Convert connection to Cytoscape edge format"""
        return {
            'data': {
                'id': f'e{self.id}',
                'source': str(self.device_a_id),
                'target': str(self.device_b_id),
                'sourceInterface': self.interface_a,
                'targetInterface': self.interface_b,
                'status': self.meta_data.get('status') if isinstance(self.meta_data, dict) else None,
                'meta_data': dict(self.meta_data) if self.meta_data else {}
            }
        }

    def __repr__(self):
        device_a_name = self.device_a.name if self.device_a else 'Unknown'
        device_b_name = self.device_b.name if self.device_b else 'Unknown'
        return f'<Connection {device_a_name}:{self.interface_a} -> {device_b_name}:{self.interface_b}>'
