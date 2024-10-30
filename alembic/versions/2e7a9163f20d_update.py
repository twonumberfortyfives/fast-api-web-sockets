"""update

Revision ID: 2e7a9163f20d
Revises: b7eef78c7b3a
Create Date: 2024-10-30 11:18:58.288064

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "2e7a9163f20d"
down_revision: Union[str, None] = "b7eef78c7b3a"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column(
        "conversation_members", "user_id", existing_type=sa.INTEGER(), nullable=True
    )
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column(
        "conversation_members", "user_id", existing_type=sa.INTEGER(), nullable=False
    )
    # ### end Alembic commands ###
