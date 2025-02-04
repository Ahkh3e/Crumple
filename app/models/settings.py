from datetime import datetime
from .. import db

class AppSettings(db.Model):
    """Application settings model"""
    __tablename__ = 'app_settings'
    
    id = db.Column(db.Integer, primary_key=True)
    netbox_url = db.Column(db.String(255))
    netbox_token = db.Column(db.String(255))
    sync_interval = db.Column(db.Integer, default=300)  # 5 minutes default
    last_sync = db.Column(db.DateTime)
    is_connected = db.Column(db.Boolean, default=False)
    verify_ssl = db.Column(db.Boolean, default=True)
    timeout = db.Column(db.Integer, default=30)  # 30 seconds default
    
    @classmethod
    def get_settings(cls):
        """Get or create settings"""
        settings = cls.query.first()
        if not settings:
            settings = cls()
            db.session.add(settings)
            db.session.commit()
        return settings
    
    def update(self, data):
        """Update settings from dict"""
        for key, value in data.items():
            if hasattr(self, key):
                setattr(self, key, value)
        db.session.commit()
    
    def to_dict(self):
        """Convert to dict"""
        return {
            'netbox_url': self.netbox_url,
            'netbox_token': self.netbox_token,
            'sync_interval': self.sync_interval,
            'last_sync': self.last_sync.strftime('%Y-%m-%d %H:%M:%S UTC') if self.last_sync else None,
            'is_connected': self.is_connected,
            'verify_ssl': self.verify_ssl,
            'timeout': self.timeout
        }
