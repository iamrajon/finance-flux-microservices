"""change_user_id_to_string

Revision ID: aa8e9d4540e1
Revises: 6c1469bb21ad
Create Date: 2026-01-05 09:09:50.623378

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'aa8e9d4540e1'
down_revision: Union[str, Sequence[str], None] = '6c1469bb21ad'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Alter user_id column type from INTEGER to VARCHAR(36)
    op.alter_column('expenses', 'user_id',
                    existing_type=sa.INTEGER(),
                    type_=sa.String(length=36),
                    existing_nullable=False)


def downgrade() -> None:
    """Downgrade schema."""
    # Revert user_id column type from VARCHAR(36) to INTEGER
    op.alter_column('expenses', 'user_id',
                    existing_type=sa.String(length=36),
                    type_=sa.INTEGER(),
                    existing_nullable=False)
