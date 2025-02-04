"""add device roles

Revision ID: 20250204_131900
Revises: 20250204_122600
Create Date: 2025-02-04 13:19:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '20250204_131900'
down_revision = '20250204_122600'
branch_labels = None
depends_on = None

def upgrade():
    op.create_table('device_roles',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('color', sa.String(length=7), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name'),
        schema='workboard'
    )

def downgrade():
    op.drop_table('device_roles', schema='workboard')
