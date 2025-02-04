"""Add sync_in_progress column to clusters

Revision ID: add_sync_in_progress
Revises: add_cluster_columns
Create Date: 2025-02-04 11:09:22.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'add_sync_in_progress'
down_revision = 'add_cluster_columns'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('clusters', sa.Column('sync_in_progress', sa.Boolean(), nullable=False, server_default='false'), schema='workboard')


def downgrade():
    op.drop_column('clusters', 'sync_in_progress', schema='workboard')
