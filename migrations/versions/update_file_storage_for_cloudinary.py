"""update file storage for cloudinary

Revision ID: update_file_storage
Revises: increase_password_hash
Create Date: 2025-10-11 15:50:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'update_file_storage'
down_revision = 'increase_password_hash'
branch_labels = None
depends_on = None


def upgrade():
    # Increase file_path length to accommodate URLs
    with op.batch_alter_table('uploaded_file', schema=None) as batch_op:
        batch_op.alter_column('file_path',
                              existing_type=sa.String(length=300),
                              type_=sa.String(length=500),
                              existing_nullable=False)
        batch_op.add_column(sa.Column('cloudinary_public_id', sa.String(length=300), nullable=True))
    
    # Increase image_path length in question table
    with op.batch_alter_table('question', schema=None) as batch_op:
        batch_op.alter_column('image_path',
                              existing_type=sa.String(length=200),
                              type_=sa.String(length=500),
                              existing_nullable=True)


def downgrade():
    # Revert changes
    with op.batch_alter_table('uploaded_file', schema=None) as batch_op:
        batch_op.alter_column('file_path',
                              existing_type=sa.String(length=500),
                              type_=sa.String(length=300),
                              existing_nullable=False)
        batch_op.drop_column('cloudinary_public_id')
    
    with op.batch_alter_table('question', schema=None) as batch_op:
        batch_op.alter_column('image_path',
                              existing_type=sa.String(length=500),
                              type_=sa.String(length=200),
                              existing_nullable=True)
