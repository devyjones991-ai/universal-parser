"""create parse results table"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = "20240314_0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "parse_results",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("profile_name", sa.String(), nullable=False),
        sa.Column("data_json", sa.Text(), nullable=False),
        sa.Column("count", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column(
            "timestamp",
            sa.DateTime(),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
    )
    op.create_index("ix_parse_results_id", "parse_results", ["id"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_parse_results_id", table_name="parse_results")
    op.drop_table("parse_results")
