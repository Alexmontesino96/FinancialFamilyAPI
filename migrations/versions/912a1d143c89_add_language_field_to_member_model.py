"""Add language field to Member model

Revision ID: 912a1d143c89
Revises: 
Create Date: 2025-03-18 01:35:05.412275

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import String, Enum
from app.models.models import Language


# revision identifiers, used by Alembic.
revision: str = '912a1d143c89'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Agregar la columna 'language' a la tabla 'members'
    op.add_column('members', sa.Column('language', sa.Enum(Language), nullable=False, server_default='EN'))


def downgrade() -> None:
    """Downgrade schema."""
    # Eliminar la columna 'language' de la tabla 'members'
    op.drop_column('members', 'language')
