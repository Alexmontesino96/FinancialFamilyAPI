"""Add unique constraint to debt_cache

Revision ID: 001_unique_debt_cache
Revises: 912a1d143c89
Create Date: 2025-08-03 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '001_unique_debt_cache'
down_revision = '912a1d143c89'
branch_labels = None
depends_on = None


def upgrade():
    # Remove duplicates first
    op.execute("""
        DELETE FROM debt_cache a USING debt_cache b 
        WHERE a.id > b.id 
        AND a.family_id = b.family_id 
        AND a.from_member_id = b.from_member_id 
        AND a.to_member_id = b.to_member_id
    """)
    
    # Add unique constraint
    op.create_unique_constraint(
        'unique_debt_per_pair',
        'debt_cache',
        ['family_id', 'from_member_id', 'to_member_id']
    )


def downgrade():
    # Remove unique constraint
    op.drop_constraint('unique_debt_per_pair', 'debt_cache', type_='unique')