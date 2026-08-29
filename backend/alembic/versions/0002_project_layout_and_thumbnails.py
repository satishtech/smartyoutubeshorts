"""add output_layout and thumbnail_path to projects

Revision ID: 0002
Revises: 0001
Create Date: 2026-08-29 00:00:00.000000

Note: written by hand (matching app/models/project.py) rather than via `alembic
revision --autogenerate`, following the same convention as 0001_initial_schema.py.
Verify with `alembic upgrade head` against a real Postgres DB before relying on it.
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0002"
down_revision: Union[str, Sequence[str], None] = "0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

output_layout_enum = sa.Enum(
    "vertical_9_16",
    "square_1_1",
    "portrait_4_5",
    "landscape_16_9",
    "classic_4_3",
    name="outputlayout",
)


def upgrade() -> None:
    """Upgrade schema."""
    output_layout_enum.create(op.get_bind(), checkfirst=True)
    op.add_column(
        "projects",
        sa.Column(
            "output_layout",
            output_layout_enum,
            nullable=False,
            server_default="vertical_9_16",
        ),
    )
    op.add_column(
        "projects",
        sa.Column("thumbnail_path", sa.String(length=1000), nullable=True),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column("projects", "thumbnail_path")
    op.drop_column("projects", "output_layout")
    output_layout_enum.drop(op.get_bind(), checkfirst=True)
