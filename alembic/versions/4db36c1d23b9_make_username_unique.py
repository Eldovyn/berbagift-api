
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '4db36c1d23b9'
down_revision: Union[str, Sequence[str], None] = '8e8a653fac10'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_users_username'))
        batch_op.create_index(batch_op.f('ix_users_username'), ['username'], unique=True)



def downgrade() -> None:
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_users_username'))
        batch_op.create_index(batch_op.f('ix_users_username'), ['username'], unique=False)

