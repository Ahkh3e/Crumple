"""add users table

Revision ID: add_users_table
Revises: hash_existing_tokens
Create Date: 2025-02-04 12:26:00

"""
from alembic import op
import sqlalchemy as sa
from werkzeug.security import generate_password_hash

# revision identifiers, used by Alembic.
revision = 'add_users_table'
down_revision = 'hash_existing_tokens'
branch_labels = None
depends_on = None

def upgrade():
    # Create users table
    op.create_table('users',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('username', sa.String(length=64), nullable=True),
        sa.Column('password_hash', sa.String(length=128), nullable=True),
        sa.Column('is_admin', sa.Boolean(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_users_username'), 'users', ['username'], unique=True)
    
    # Create default admin user
    conn = op.get_bind()
    conn.execute(
        'INSERT INTO users (username, password_hash, is_admin) VALUES (%s, %s, %s)',
        ('admin', generate_password_hash('admin'), True)
    )

def downgrade():
    op.drop_index(op.f('ix_users_username'), table_name='users')
    op.drop_table('users')
