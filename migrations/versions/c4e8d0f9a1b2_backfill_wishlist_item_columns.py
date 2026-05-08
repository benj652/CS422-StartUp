"""backfill wishlist item columns

Revision ID: c4e8d0f9a1b2
Revises: 7b6a6f0d9d62
Create Date: 2026-05-07 21:05:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


# revision identifiers, used by Alembic.
revision = "c4e8d0f9a1b2"
down_revision = "7b6a6f0d9d62"
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    inspector = inspect(bind)

    if "wishlist_item" not in inspector.get_table_names():
        return

    columns = {column["name"] for column in inspector.get_columns("wishlist_item")}

    if "roadmap_item_id" not in columns:
        op.add_column(
            "wishlist_item",
            sa.Column("roadmap_item_id", sa.String(length=255), nullable=True),
        )
    if "title" not in columns:
        op.add_column(
            "wishlist_item",
            sa.Column("title", sa.String(length=255), nullable=True),
        )
    if "section" not in columns:
        op.add_column(
            "wishlist_item",
            sa.Column("section", sa.String(length=100), nullable=True),
        )
    if "summary" not in columns:
        op.add_column(
            "wishlist_item",
            sa.Column("summary", sa.Text(), nullable=True),
        )
    if "href" not in columns:
        op.add_column(
            "wishlist_item",
            sa.Column("href", sa.String(length=500), nullable=True),
        )
    if "priority" not in columns:
        op.add_column(
            "wishlist_item",
            sa.Column(
                "priority",
                sa.String(length=20),
                nullable=False,
                server_default="low",
            ),
        )
    if "created_at" not in columns:
        op.add_column(
            "wishlist_item",
            sa.Column("created_at", sa.DateTime(), nullable=True),
        )
    if "updated_at" not in columns:
        op.add_column(
            "wishlist_item",
            sa.Column("updated_at", sa.DateTime(), nullable=True),
        )


def downgrade():
    bind = op.get_bind()
    inspector = inspect(bind)

    if "wishlist_item" not in inspector.get_table_names():
        return

    columns = {column["name"] for column in inspector.get_columns("wishlist_item")}

    for name in (
        "updated_at",
        "created_at",
        "priority",
        "href",
        "summary",
        "section",
        "title",
        "roadmap_item_id",
    ):
        if name in columns:
            op.drop_column("wishlist_item", name)
