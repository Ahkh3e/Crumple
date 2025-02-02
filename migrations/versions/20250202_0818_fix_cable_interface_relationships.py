"""fix cable interface relationships

Revision ID: 20250202_0818
Revises: 20250202_0629_add_device_category_and_specs
Create Date: 2025-02-02 08:18:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '20250202_0818'
down_revision = '20250202_0629_add_device_category_and_specs'
branch_labels = None
depends_on = None

def upgrade():
    # Drop existing relationships
    op.drop_constraint('cables_interface_a_id_fkey', 'cables', type_='foreignkey')
    op.drop_constraint('cables_interface_b_id_fkey', 'cables', type_='foreignkey')

    # Re-create relationships with explicit foreign keys
    op.create_foreign_key(
        'cables_interface_a_id_fkey',
        'cables', 'interfaces',
        ['interface_a_id'], ['id'],
        ondelete='CASCADE'
    )
    op.create_foreign_key(
        'cables_interface_b_id_fkey',
        'cables', 'interfaces',
        ['interface_b_id'], ['id'],
        ondelete='CASCADE'
    )

def downgrade():
    # Drop new constraints
    op.drop_constraint('cables_interface_a_id_fkey', 'cables', type_='foreignkey')
    op.drop_constraint('cables_interface_b_id_fkey', 'cables', type_='foreignkey')

    # Re-create original constraints
    op.create_foreign_key(
        'cables_interface_a_id_fkey',
        'cables', 'interfaces',
        ['interface_a_id'], ['id']
    )
    op.create_foreign_key(
        'cables_interface_b_id_fkey',
        'cables', 'interfaces',
        ['interface_b_id'], ['id']
    )
