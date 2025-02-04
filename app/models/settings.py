from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from .. import db

class AppSettings(db.Model):
    """Application settings model"""
    __tablename__ = 'app_settings'
    
    id = db.Column(db.Integer, primary_key=True)
    netbox_url = db.Column(db.String(255))
    _netbox_token = db.Column('netbox_token', db.String(255))  # Renamed to indicate private
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
    
    @property
    def netbox_token(self):
        """Never expose the actual token"""
        return None if not self._netbox_token else '••••••••'
    
    @netbox_token.setter
    def netbox_token(self, token):
        """Store the token directly"""
        if token:
            self._netbox_token = token
    
    def verify_token(self, token):
        """Verify a token matches the stored token"""
        if not self._netbox_token or not token:
            return False
        return self._netbox_token == token
    
    def get_token(self):
        """Get the actual token for internal use only"""
        return self._netbox_token
    
    def update(self, data):
        """Update settings from dict"""
        for key, value in data.items():
            if key == 'netbox_token' and value:
                # Only update token if a new one is provided
                self.netbox_token = value
            elif hasattr(self, key) and key != 'netbox_token':
                setattr(self, key, value)
        db.session.commit()
    
    def to_dict(self, include_token=False):
        """Convert to dict"""
        data = {
            'netbox_url': self.netbox_url,
            'sync_interval': self.sync_interval,
            'last_sync': self.last_sync.strftime('%Y-%m-%d %H:%M:%S UTC') if self.last_sync else None,
            'is_connected': self.is_connected,
            'verify_ssl': self.verify_ssl,
            'timeout': self.timeout
        }
        if include_token:
            data['netbox_token'] = self.netbox_token  # Returns masked version
        return data
