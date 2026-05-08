"""add wishlist items table

Revision ID: 7b6a6f0d9d62
Revises: 1c96ddd37bf6
Create Date: 2026-05-07 14:00:00.000000

"""
# pylint: disable=no-member,duplicate-code
from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


# revision identifiers, used by Alembic.
revision = "7b6a6f0d9d62"
down_revision = "1c96ddd37bf6"
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    inspector = inspect(bind)

    if "wishlist_item" not in inspector.get_table_names():
        op.create_table(
            "wishlist_item",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("user_id", sa.Integer(), nullable=False),
            sa.Column("roadmap_item_id", sa.String(length=255), nullable=False),
            sa.Column("title", sa.String(length=255), nullable=False),
            sa.Column("section", sa.String(length=100), nullable=True),
            sa.Column("summary", sa.Text(), nullable=True),
            sa.Column("href", sa.String(length=500), nullable=True),
            sa.Column("priority", sa.String(length=20), nullable=False),
            sa.Column("created_at", sa.DateTime(), nullable=True),
            sa.Column("updated_at", sa.DateTime(), nullable=True),
            sa.ForeignKeyConstraint(["user_id"], ["user.id"]),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint(
                "user_id",
                "roadmap_item_id",
                name="uq_wishlist_user_roadmap_item",
            ),
        )


def downgrade():
    bind = op.get_bind()
    inspector = inspect(bind)

    if "wishlist_item" in inspector.get_table_names():
        op.drop_table("wishlist_item")
