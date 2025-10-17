"""add user and plan fields

Revision ID: add_user_and_plan_fields
Revises: add_payment_models
Create Date: 2025-10-17 09:58:00.000000

"""
from alembic import op
import sqlalchemy as sa
from datetime import datetime, timezone


# revision identifiers, used by Alembic.
revision = 'add_user_and_plan_fields'
down_revision = 'add_payment_models'
branch_labels = None
depends_on = None


def upgrade():
    # Add columns to user table if they don't exist
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    user_columns = [col['name'] for col in inspector.get_columns('user')]
    
    # Add subscription_plan_id column
    if 'subscription_plan_id' not in user_columns:
        op.add_column('user', sa.Column('subscription_plan_id', sa.Integer(), nullable=True))
        op.create_foreign_key('fk_user_subscription_plan', 'user', 'subscription_plan', ['subscription_plan_id'], ['id'])
    
    # Add created_at column if it doesn't exist
    if 'created_at' not in user_columns:
        # Add column with default for existing rows
        op.add_column('user', sa.Column('created_at', sa.DateTime(), nullable=True))
        # Update existing rows with current timestamp
        op.execute("UPDATE \"user\" SET created_at = NOW() WHERE created_at IS NULL")
    
    # Add subscription_start_date column if it doesn't exist
    if 'subscription_start_date' not in user_columns:
        op.add_column('user', sa.Column('subscription_start_date', sa.DateTime(), nullable=True))
        # Set subscription_start_date from subscription_date for existing subscribers
        op.execute("UPDATE \"user\" SET subscription_start_date = subscription_date WHERE is_subscriber = TRUE AND subscription_date IS NOT NULL")
    
    # Add columns to subscription_plan table
    plan_columns = [col['name'] for col in inspector.get_columns('subscription_plan')]
    
    # Add plan_type column
    if 'plan_type' not in plan_columns:
        op.add_column('subscription_plan', sa.Column('plan_type', sa.String(length=20), nullable=True))
        # Set default value for existing plans
        op.execute("UPDATE subscription_plan SET plan_type = 'subscription' WHERE plan_type IS NULL")
    
    # Add duration_months column
    if 'duration_months' not in plan_columns:
        op.add_column('subscription_plan', sa.Column('duration_months', sa.Integer(), nullable=True))
        # Calculate from duration_days for existing plans
        op.execute("UPDATE subscription_plan SET duration_months = ROUND(duration_days / 30.0) WHERE duration_months IS NULL")
    
    # Add access control columns
    if 'has_unlimited_tests' not in plan_columns:
        op.add_column('subscription_plan', sa.Column('has_unlimited_tests', sa.Boolean(), nullable=True))
        op.execute("UPDATE subscription_plan SET has_unlimited_tests = TRUE WHERE has_unlimited_tests IS NULL")
    
    if 'test_credits' not in plan_columns:
        op.add_column('subscription_plan', sa.Column('test_credits', sa.Integer(), nullable=True))
        op.execute("UPDATE subscription_plan SET test_credits = 0 WHERE test_credits IS NULL")
    
    if 'max_tests_per_month' not in plan_columns:
        op.add_column('subscription_plan', sa.Column('max_tests_per_month', sa.Integer(), nullable=True))
    
    if 'has_download_access' not in plan_columns:
        op.add_column('subscription_plan', sa.Column('has_download_access', sa.Boolean(), nullable=True))
        op.execute("UPDATE subscription_plan SET has_download_access = TRUE WHERE has_download_access IS NULL")
    
    if 'has_progress_tracking' not in plan_columns:
        op.add_column('subscription_plan', sa.Column('has_progress_tracking', sa.Boolean(), nullable=True))
        op.execute("UPDATE subscription_plan SET has_progress_tracking = TRUE WHERE has_progress_tracking IS NULL")
    
    if 'has_performance_analytics' not in plan_columns:
        op.add_column('subscription_plan', sa.Column('has_performance_analytics', sa.Boolean(), nullable=True))
        op.execute("UPDATE subscription_plan SET has_performance_analytics = TRUE WHERE has_performance_analytics IS NULL")
    
    if 'is_featured' not in plan_columns:
        op.add_column('subscription_plan', sa.Column('is_featured', sa.Boolean(), nullable=True))
        op.execute("UPDATE subscription_plan SET is_featured = FALSE WHERE is_featured IS NULL")


def downgrade():
    # Remove columns from subscription_plan
    op.drop_column('subscription_plan', 'is_featured')
    op.drop_column('subscription_plan', 'has_performance_analytics')
    op.drop_column('subscription_plan', 'has_progress_tracking')
    op.drop_column('subscription_plan', 'has_download_access')
    op.drop_column('subscription_plan', 'max_tests_per_month')
    op.drop_column('subscription_plan', 'test_credits')
    op.drop_column('subscription_plan', 'has_unlimited_tests')
    op.drop_column('subscription_plan', 'duration_months')
    op.drop_column('subscription_plan', 'plan_type')
    
    # Remove columns from user
    op.drop_column('user', 'subscription_start_date')
    op.drop_column('user', 'created_at')
    op.drop_constraint('fk_user_subscription_plan', 'user', type_='foreignkey')
    op.drop_column('user', 'subscription_plan_id')
