from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from .. import db

class User(UserMixin, db.Model):
    """User model for authentication"""
    __tablename__ = 'workboard.users'  # Using fully qualified table name
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, index=True)
    password_hash = db.Column(db.String(255))  # Increased length to accommodate longer hashes
    is_admin = db.Column(db.Boolean, default=False)
    
    @property
    def password(self):
        raise AttributeError('password is not a readable attribute')
    
    @password.setter
    def password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def verify_password(self, password):
        print(f"Verifying password hash: {self.password_hash}")
        print(f"Input password: {password}")
        result = check_password_hash(self.password_hash, password)
        print(f"Hash verification result: {result}")
        return result
    
    @staticmethod
    def create_admin(username, password):
        """Create admin user if none exists"""
        if not User.query.filter_by(username=username).first():
            user = User(username=username, is_admin=True)
            user.password = password
            db.session.add(user)
            db.session.commit()
            return user
        return None
