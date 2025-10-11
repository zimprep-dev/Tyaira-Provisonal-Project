"""Add subscription_end_date to User model

Revision ID: add_subscription_end_date
Revises: 4b7f0b058715
Create Date: 2025-10-06 19:51:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'add_subscription_end_date'
down_revision = '4b7f0b058715'
branch_labels = None
depends_on = None


def upgrade():
    # Add subscription_end_date column to user table
    op.add_column('user', sa.Column('subscription_end_date', sa.DateTime(), nullable=True))


def downgrade():
    # Remove subscription_end_date column from user table
    op.drop_column('user', 'subscription_end_date')
