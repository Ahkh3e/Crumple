"""hash existing tokens

Revision ID: hash_existing_tokens
Revises: add_sync_in_progress
Create Date: 2025-02-04 12:25:00

"""
from alembic import op
import sqlalchemy as sa
from werkzeug.security import generate_password_hash

# revision identifiers, used by Alembic.
revision = 'hash_existing_tokens'
down_revision = 'add_sync_in_progress'
branch_labels = None
depends_on = None

def upgrade():
    # Get connection
    conn = op.get_bind()
    
    # Get all settings with tokens
    settings = conn.execute(
        'SELECT id, netbox_token FROM app_settings WHERE netbox_token IS NOT NULL'
    ).fetchall()
    
    # Hash each token
    for setting_id, token in settings:
        if token and not token.startswith('pbkdf2:sha256:'):  # Only hash if not already hashed
            hashed_token = generate_password_hash(token)
            conn.execute(
                'UPDATE app_settings SET netbox_token = %s WHERE id = %s',
                (hashed_token, setting_id)
            )

def downgrade():
    # Cannot safely downgrade hashed tokens
    pass
