from .. import db
import random

def generate_distinct_color():
    """Generate a visually distinct color using golden ratio in HSL color space"""
    # Get count of existing roles to use as an index
    from . import db
    count = db.session.query(DeviceRole).count()
    
    # Use golden ratio to get well-distributed hues
    golden_ratio = 0.618033988749895
    hue = (count * golden_ratio) % 1
    
    # Use fixed saturation and lightness for good visibility
    saturation = 0.7  # 70% saturation
    lightness = 0.6   # 60% lightness
    
    # Convert HSL to RGB
    def hue_to_rgb(p, q, t):
        if t < 0:
            t += 1
        if t > 1:
            t -= 1
        if t < 1/6:
            return p + (q - p) * 6 * t
        if t < 1/2:
            return q
        if t < 2/3:
            return p + (q - p) * (2/3 - t) * 6
        return p

    q = lightness * (1 + saturation) if lightness < 0.5 else lightness + saturation - lightness * saturation
    p = 2 * lightness - q

    r = hue_to_rgb(p, q, hue + 1/3)
    g = hue_to_rgb(p, q, hue)
    b = hue_to_rgb(p, q, hue - 1/3)

    # Convert RGB to hex
    return '#{:02x}{:02x}{:02x}'.format(
        int(r * 255),
        int(g * 255),
        int(b * 255)
    )

class DeviceRole(db.Model):
    """Model for storing device roles and their assigned colors"""
    __tablename__ = 'device_roles'
    __table_args__ = {'schema': 'workboard'}

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), unique=True, nullable=False)
    color = db.Column(db.String(7), nullable=False)  # Hex color code
    created_at = db.Column(db.DateTime(timezone=True), server_default=db.func.current_timestamp())

    @classmethod
    def get_or_create(cls, role_name):
        """Get existing role or create new one with random color"""
        role = cls.query.filter_by(name=role_name).first()
        if not role and role_name:
            role = cls(name=role_name, color=generate_distinct_color())
            db.session.add(role)
            db.session.commit()
        return role

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'color': self.color,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
