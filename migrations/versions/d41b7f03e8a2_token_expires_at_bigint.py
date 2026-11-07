"""token_expires_at integer -> bigint

Timestamp unix em Integer (32 bits) estoura em 19/01/2038.

Revision ID: d41b7f03e8a2
Revises: c7e2a91d4f10
Create Date: 2026-11-07 12:30:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'd41b7f03e8a2'
down_revision = 'c7e2a91d4f10'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.alter_column(
            'token_expires_at',
            existing_type=sa.Integer(),
            type_=sa.BigInteger(),
            existing_nullable=True,
        )


def downgrade():
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.alter_column(
            'token_expires_at',
            existing_type=sa.BigInteger(),
            type_=sa.Integer(),
            existing_nullable=True,
        )
