"""add verify_ssl and timeout columns

Revision ID: 20250204_145600
Revises: 20250204_131900
Create Date: 2025-02-04 14:56:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '20250204_145600'
down_revision = '20250204_131900'
branch_labels = None
depends_on = None


def upgrade():
    # Add verify_ssl and timeout columns to app_settings table
    op.add_column('app_settings', sa.Column('verify_ssl', sa.Boolean(), server_default='true', nullable=False), schema='workboard')
    op.add_column('app_settings', sa.Column('timeout', sa.Integer(), server_default='30', nullable=False), schema='workboard')


def downgrade():
    # Drop verify_ssl and timeout columns from app_settings table
    op.drop_column('app_settings', 'timeout', schema='workboard')
    op.drop_column('app_settings', 'verify_ssl', schema='workboard')
