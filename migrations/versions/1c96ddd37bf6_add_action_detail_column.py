"""add action detail column

Revision ID: 1c96ddd37bf6
Revises: 
Create Date: 2026-04-20 10:58:06.359349

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


# revision identifiers, used by Alembic.
revision = '1c96ddd37bf6'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    inspector = inspect(bind)
    columns = {column["name"] for column in inspector.get_columns("action")}

    if "detail" not in columns:
        op.add_column("action", sa.Column("detail", sa.JSON(), nullable=True))


def downgrade():
    bind = op.get_bind()
    inspector = inspect(bind)
    columns = {column["name"] for column in inspector.get_columns("action")}

    if "detail" in columns:
        op.drop_column("action", "detail")
