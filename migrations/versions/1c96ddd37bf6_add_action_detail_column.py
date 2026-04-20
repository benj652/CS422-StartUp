"""add action detail column

Revision ID: 1c96ddd37bf6
Revises: 
Create Date: 2026-04-20 10:58:06.359349

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '1c96ddd37bf6'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('action', sa.Column('detail', sa.JSON(), nullable=True))


def downgrade():
    op.drop_column('action', 'detail')
