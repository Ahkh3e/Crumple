"""add device category and specs

Revision ID: 20250202_0629
Revises: 20250202_0514
Create Date: 2025-02-02 06:29:34.123456

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '20250202_0629'
down_revision: Union[str, None] = '20250202_0514'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    # Add category column to device_types
    op.add_column('device_types', sa.Column('category', sa.String(), nullable=True))
    op.add_column('device_types', sa.Column('specs', postgresql.JSONB(astext_type=sa.Text()), nullable=True))
    
    # Add category column to interface_types
    op.add_column('interface_types', sa.Column('category', sa.String(), nullable=True))
    
    # Update existing device types with default category
    op.execute("""
        UPDATE device_types 
        SET category = CASE
            WHEN name ILIKE '%gpu%' THEN 'gpu'
            WHEN name ILIKE '%nic%' OR name ILIKE '%network%' THEN 'nic'
            ELSE 'switch'
        END
    """)
    
    # Make category non-nullable after setting defaults
    op.alter_column('device_types', 'category', nullable=False)

def downgrade() -> None:
    op.drop_column('interface_types', 'category')
    op.drop_column('device_types', 'specs')
    op.drop_column('device_types', 'category')
