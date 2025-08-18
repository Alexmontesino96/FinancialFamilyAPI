"""Rename telegram_id to auth0_user_id on members

Revision ID: a02e3f9b8c1d
Revises: 001_unique_debt_cache
Create Date: 2025-08-18 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'a02e3f9b8c1d'
down_revision = '001_unique_debt_cache'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Apply schema changes."""
    # Rename column telegram_id -> auth0_user_id in members table
    with op.batch_alter_table('members') as batch_op:
        batch_op.alter_column('telegram_id', new_column_name='auth0_user_id', existing_type=sa.String())


def downgrade() -> None:
    """Revert schema changes."""
    with op.batch_alter_table('members') as batch_op:
        batch_op.alter_column('auth0_user_id', new_column_name='telegram_id', existing_type=sa.String())

