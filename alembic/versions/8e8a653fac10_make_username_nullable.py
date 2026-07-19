
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '8e8a653fac10'
down_revision: Union[str, Sequence[str], None] = '785319498f31'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.alter_column('username',
               existing_type=sa.String(length=50),
               nullable=True)



def downgrade() -> None:
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.alter_column('username',
               existing_type=sa.String(length=50),
               nullable=False)

