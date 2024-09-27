"""added new field for posts tags

Revision ID: e55445f1ffcb
Revises: 7ead7ef8045c
Create Date: 2024-09-27 13:27:22.623879

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "e55445f1ffcb"
down_revision: Union[str, None] = "7ead7ef8045c"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column("posts", sa.Column("tags", sa.String(length=100), nullable=True))
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column("posts", "tags")
    # ### end Alembic commands ###
