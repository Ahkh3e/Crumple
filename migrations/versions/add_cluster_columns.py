"""add cluster columns

Revision ID: add_cluster_columns
Revises: 
Create Date: 2025-02-04 04:31:37.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

# revision identifiers, used by Alembic.
revision = 'add_cluster_columns'
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    # Create workboard schema if it doesn't exist
    op.execute('CREATE SCHEMA IF NOT EXISTS workboard')
    
    # Create clusters table
    op.create_table('clusters',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('netbox_id', sa.Integer(), nullable=True),
        sa.Column('name', sa.String(length=255), nullable=True),
        sa.Column('type', sa.String(length=255), nullable=True),
        sa.Column('status', sa.String(length=50), nullable=True),
        sa.Column('device_count', sa.Integer(), nullable=True),
        sa.Column('meta_info', JSONB(), nullable=True),
        sa.Column('position', JSONB(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('netbox_id'),
        schema='workboard'
    )
    
    # Create devices table
    op.create_table('devices',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('netbox_id', sa.Integer(), nullable=True),
        sa.Column('cluster_id', sa.Integer(), nullable=True),
        sa.Column('name', sa.String(length=255), nullable=True),
        sa.Column('device_type', JSONB(), nullable=True),
        sa.Column('role', sa.String(length=255), nullable=True),
        sa.Column('status', sa.String(length=50), nullable=True),
        sa.Column('interfaces', JSONB(), nullable=True),
        sa.Column('meta_info', JSONB(), nullable=True),
        sa.Column('position', JSONB(), nullable=True),
        sa.ForeignKeyConstraint(['cluster_id'], ['workboard.clusters.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('netbox_id'),
        schema='workboard'
    )
    
    # Create connections table
    op.create_table('connections',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('netbox_id', sa.Integer(), nullable=True),
        sa.Column('cluster_id', sa.Integer(), nullable=True),
        sa.Column('device_a_id', sa.Integer(), nullable=True),
        sa.Column('interface_a', sa.String(length=255), nullable=True),
        sa.Column('device_b_id', sa.Integer(), nullable=True),
        sa.Column('interface_b', sa.String(length=255), nullable=True),
        sa.Column('status', sa.String(length=50), nullable=True),
        sa.Column('meta_info', JSONB(), nullable=True),
        sa.ForeignKeyConstraint(['cluster_id'], ['workboard.clusters.id'], ),
        sa.ForeignKeyConstraint(['device_a_id'], ['workboard.devices.id'], ),
        sa.ForeignKeyConstraint(['device_b_id'], ['workboard.devices.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('netbox_id'),
        schema='workboard'
    )

def downgrade():
    op.drop_table('connections', schema='workboard')
    op.drop_table('devices', schema='workboard')
    op.drop_table('clusters', schema='workboard')
    op.execute('DROP SCHEMA IF EXISTS workboard')
