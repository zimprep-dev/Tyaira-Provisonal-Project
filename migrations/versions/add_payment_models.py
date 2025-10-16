"""add payment models

Revision ID: add_payment_models
Revises: update_file_storage
Create Date: 2025-10-16 14:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'add_payment_models'
down_revision = 'update_file_storage'
branch_labels = None
depends_on = None


def upgrade():
    # Create subscription_plan table
    op.create_table('subscription_plan',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(length=100), nullable=False),
    sa.Column('duration_days', sa.Integer(), nullable=False),
    sa.Column('price', sa.Float(), nullable=False),
    sa.Column('currency', sa.String(length=3), nullable=True),
    sa.Column('description', sa.Text(), nullable=True),
    sa.Column('is_active', sa.Boolean(), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    
    # Create pending_payment table
    op.create_table('pending_payment',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.Column('payment_reference', sa.String(length=100), nullable=False),
    sa.Column('poll_url', sa.String(length=500), nullable=True),
    sa.Column('amount', sa.Float(), nullable=False),
    sa.Column('currency', sa.String(length=3), nullable=True),
    sa.Column('plan_id', sa.Integer(), nullable=True),
    sa.Column('status', sa.String(length=20), nullable=True),
    sa.Column('paynow_reference', sa.String(length=100), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.Column('updated_at', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['plan_id'], ['subscription_plan.id'], ),
    sa.ForeignKeyConstraint(['user_id'], ['user.id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('payment_reference')
    )
    
    # Create transaction table
    op.create_table('transaction',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.Column('amount', sa.Float(), nullable=False),
    sa.Column('currency', sa.String(length=3), nullable=True),
    sa.Column('reference', sa.String(length=100), nullable=False),
    sa.Column('paynow_reference', sa.String(length=100), nullable=True),
    sa.Column('status', sa.String(length=20), nullable=False),
    sa.Column('payment_method', sa.String(length=50), nullable=True),
    sa.Column('plan_id', sa.Integer(), nullable=True),
    sa.Column('subscription_start', sa.DateTime(), nullable=True),
    sa.Column('subscription_end', sa.DateTime(), nullable=True),
    sa.Column('notes', sa.Text(), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['plan_id'], ['subscription_plan.id'], ),
    sa.ForeignKeyConstraint(['user_id'], ['user.id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('reference')
    )


def downgrade():
    op.drop_table('transaction')
    op.drop_table('pending_payment')
    op.drop_table('subscription_plan')
