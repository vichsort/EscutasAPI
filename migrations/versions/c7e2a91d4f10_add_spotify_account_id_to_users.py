"""add spotify_account_id to users

Revision ID: c7e2a91d4f10
Revises: 3184898c3b3b
Create Date: 2026-11-07 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'c7e2a91d4f10'
down_revision = '3184898c3b3b'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.add_column(sa.Column('spotify_account_id', sa.String(length=100), nullable=True))
        batch_op.create_index(batch_op.f('ix_users_spotify_account_id'), ['spotify_account_id'], unique=True)


def downgrade():
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_users_spotify_account_id'))
        batch_op.drop_column('spotify_account_id')
