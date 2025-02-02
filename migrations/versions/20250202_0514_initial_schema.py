"""initial schema

Revision ID: 20250202_0514
Revises: 
Create Date: 2025-02-02 05:14:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '20250202_0514'
down_revision = None
branch_labels = None
depends_on = None

def upgrade() -> None:
    # Create device_types table
    op.create_table('device_types',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('manufacturer', sa.String(), nullable=False),
        sa.Column('model', sa.String(), nullable=False),
        sa.Column('part_number', sa.String(), nullable=True),
        sa.Column('u_height', sa.Integer(), nullable=True),
        sa.Column('is_full_depth', sa.Integer(), nullable=True),
        sa.Column('netbox_id', sa.Integer(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('netbox_id')
    )

    # Create interface_types table
    op.create_table('interface_types',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('speed', sa.Integer(), nullable=True),
        sa.Column('connector_type', sa.String(), nullable=True),
        sa.Column('media_type', sa.String(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )

    # Create device_interface_types association table
    op.create_table('device_interface_types',
        sa.Column('device_type_id', sa.Integer(), nullable=True),
        sa.Column('interface_type_id', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['device_type_id'], ['device_types.id'], ),
        sa.ForeignKeyConstraint(['interface_type_id'], ['interface_types.id'], )
    )

    # Create clusters table
    op.create_table('clusters',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('description', sa.String(), nullable=True),
        sa.Column('site', sa.String(), nullable=True),
        sa.Column('status', sa.String(), nullable=True),
        sa.Column('parent_id', sa.Integer(), nullable=True),
        sa.Column('custom_fields', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['parent_id'], ['clusters.id'], )
    )

    # Create devices table
    op.create_table('devices',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('device_type_id', sa.Integer(), nullable=False),
        sa.Column('serial', sa.String(), nullable=True),
        sa.Column('position_x', sa.Float(), nullable=True),
        sa.Column('position_y', sa.Float(), nullable=True),
        sa.Column('cluster_id', sa.Integer(), nullable=True),
        sa.Column('custom_fields', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.ForeignKeyConstraint(['cluster_id'], ['clusters.id'], ),
        sa.ForeignKeyConstraint(['device_type_id'], ['device_types.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

    # Create interfaces table
    op.create_table('interfaces',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('device_id', sa.Integer(), nullable=True),
        sa.Column('device_type_id', sa.Integer(), nullable=True),
        sa.Column('interface_type_id', sa.Integer(), nullable=True),
        sa.Column('position', sa.String(), nullable=False),
        sa.Column('enabled', sa.Integer(), nullable=True),
        sa.Column('mtu', sa.Integer(), nullable=True),
        sa.Column('mac_address', sa.String(), nullable=True),
        sa.Column('mgmt_only', sa.Integer(), nullable=True),
        sa.Column('description', sa.String(), nullable=True),
        sa.Column('connected_interface_id', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['connected_interface_id'], ['interfaces.id'], ),
        sa.ForeignKeyConstraint(['device_id'], ['devices.id'], ),
        sa.ForeignKeyConstraint(['device_type_id'], ['device_types.id'], ),
        sa.ForeignKeyConstraint(['interface_type_id'], ['interface_types.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

    # Create cables table
    op.create_table('cables',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('interface_a_id', sa.Integer(), nullable=False),
        sa.Column('interface_b_id', sa.Integer(), nullable=False),
        sa.Column('type', sa.String(), nullable=False),
        sa.Column('length', sa.Float(), nullable=True),
        sa.Column('color', sa.String(), nullable=True),
        sa.Column('label', sa.String(), nullable=True),
        sa.Column('status', sa.String(), nullable=True),
        sa.ForeignKeyConstraint(['interface_a_id'], ['interfaces.id'], ),
        sa.ForeignKeyConstraint(['interface_b_id'], ['interfaces.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

    # Create NetBox tables
    op.create_table('netbox_connections',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('url', sa.String(), nullable=False),
        sa.Column('api_key', sa.String(), nullable=False),
        sa.Column('ssl_verify', sa.Integer(), nullable=True),
        sa.Column('custom_fields', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )

    op.create_table('netbox_import_logs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('connection_id', sa.Integer(), nullable=False),
        sa.Column('timestamp', sa.Integer(), nullable=False),
        sa.Column('operation', sa.String(), nullable=False),
        sa.Column('status', sa.String(), nullable=False),
        sa.Column('details', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )

    op.create_table('netbox_sync_queue',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('connection_id', sa.Integer(), nullable=False),
        sa.Column('operation', sa.String(), nullable=False),
        sa.Column('status', sa.String(), nullable=False),
        sa.Column('priority', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.Integer(), nullable=False),
        sa.Column('started_at', sa.Integer(), nullable=True),
        sa.Column('completed_at', sa.Integer(), nullable=True),
        sa.Column('parameters', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('result', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )

def downgrade() -> None:
    op.drop_table('netbox_sync_queue')
    op.drop_table('netbox_import_logs')
    op.drop_table('netbox_connections')
    op.drop_table('cables')
    op.drop_table('interfaces')
    op.drop_table('devices')
    op.drop_table('clusters')
    op.drop_table('device_interface_types')
    op.drop_table('interface_types')
    op.drop_table('device_types')
