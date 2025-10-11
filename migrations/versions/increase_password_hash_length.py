"""increase password_hash length

Revision ID: increase_password_hash
Revises: add_subscription_end_date
Create Date: 2025-10-11 09:58:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'increase_password_hash'
down_revision = 'add_subscription_end_date'
branch_labels = None
depends_on = None


def upgrade():
    # Increase password_hash column length from 120 to 255
    with op.batch_alter_table('user', schema=None) as batch_op:
        batch_op.alter_column('password_hash',
                              existing_type=sa.String(length=120),
                              type_=sa.String(length=255),
                              existing_nullable=False)


def downgrade():
    # Revert password_hash column length back to 120
    with op.batch_alter_table('user', schema=None) as batch_op:
        batch_op.alter_column('password_hash',
                              existing_type=sa.String(length=255),
                              type_=sa.String(length=120),
                              existing_nullable=False)
