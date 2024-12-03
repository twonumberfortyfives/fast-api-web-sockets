"""initialized

Revision ID: b4ae3629fa27
Revises: 79c3cbf26af1
Create Date: 2024-12-02 16:15:32.477096

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b4ae3629fa27'
down_revision: Union[str, None] = '79c3cbf26af1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
