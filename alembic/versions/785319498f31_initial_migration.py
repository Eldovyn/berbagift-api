
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '785319498f31'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('nonces',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('wallet_address', sa.String(length=56), nullable=False),
    sa.Column('nonce_message', sa.String(length=255), nullable=False),
    sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_nonces_id'), 'nonces', ['id'], unique=False)
    op.create_index(op.f('ix_nonces_wallet_address'), 'nonces', ['wallet_address'], unique=True)
    op.create_table('users',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('username', sa.String(length=50), nullable=False),
    sa.Column('email', sa.String(length=100), nullable=True),
    sa.Column('wallet_address', sa.String(length=56), nullable=False),
    sa.Column('role', sa.Enum('user', 'admin', name='user_roles'), server_default='user', nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=True)
    op.create_index(op.f('ix_users_id'), 'users', ['id'], unique=False)
    op.create_index(op.f('ix_users_username'), 'users', ['username'], unique=False)
    op.create_index(op.f('ix_users_wallet_address'), 'users', ['wallet_address'], unique=True)


def downgrade() -> None:
    op.drop_index(op.f('ix_users_wallet_address'), table_name='users')
    op.drop_index(op.f('ix_users_username'), table_name='users')
    op.drop_index(op.f('ix_users_id'), table_name='users')
    op.drop_index(op.f('ix_users_email'), table_name='users')
    op.drop_table('users')
    op.drop_index(op.f('ix_nonces_wallet_address'), table_name='nonces')
    op.drop_index(op.f('ix_nonces_id'), table_name='nonces')
    op.drop_table('nonces')
