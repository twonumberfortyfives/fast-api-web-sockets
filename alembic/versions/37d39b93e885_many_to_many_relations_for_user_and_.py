"""many to many relations for user and chats

Revision ID: 37d39b93e885
Revises: 284bffc3db68
Create Date: 2024-10-18 19:00:26.450034

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '37d39b93e885'
down_revision: Union[str, None] = '284bffc3db68'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    pass
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    pass
    # ### end Alembic commands ###
