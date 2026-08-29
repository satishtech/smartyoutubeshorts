"""initial schema: users, refresh_tokens, projects, transcripts, highlight_segments, shorts

Revision ID: 0001
Revises:
Create Date: 2026-08-29 00:00:00.000000

Note: written by hand (matching app/models/*) rather than via `alembic revision
--autogenerate` because no local/Docker PostgreSQL instance was reachable in this
environment. Verify with `alembic upgrade head` against a real Postgres DB before
relying on it, and re-run `alembic revision --autogenerate -m "..."` if it drifts
from the models.
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0001"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("hashed_password", sa.String(length=255), nullable=True),
        sa.Column("full_name", sa.String(length=100), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("google_id", sa.String(length=255), nullable=True),
        sa.Column("avatar_url", sa.String(length=500), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()),
    )
    op.create_index("ix_users_id", "users", ["id"])
    op.create_index("ix_users_email", "users", ["email"], unique=True)
    op.create_index("ix_users_google_id", "users", ["google_id"], unique=True)

    op.create_table(
        "refresh_tokens",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("token_hash", sa.String(length=255), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("revoked", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()),
    )
    op.create_index("ix_refresh_tokens_id", "refresh_tokens", ["id"])
    op.create_index("ix_refresh_tokens_user_id", "refresh_tokens", ["user_id"])
    op.create_index("ix_refresh_tokens_token_hash", "refresh_tokens", ["token_hash"], unique=True)

    source_type_enum = sa.Enum("upload", "youtube_url", name="sourcetype")
    project_status_enum = sa.Enum(
        "pending",
        "downloading",
        "transcribing",
        "detecting_highlights",
        "ready_for_review",
        "generating_shorts",
        "completed",
        "failed",
        name="projectstatus",
    )
    op.create_table(
        "projects",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("source_type", source_type_enum, nullable=False),
        sa.Column("source_url", sa.String(length=1000), nullable=True),
        sa.Column("source_video_path", sa.String(length=1000), nullable=True),
        sa.Column("duration_seconds", sa.Float(), nullable=True),
        sa.Column("status", project_status_enum, nullable=False, server_default="pending"),
        sa.Column("status_message", sa.Text(), nullable=True),
        sa.Column("num_shorts_requested", sa.Integer(), nullable=False, server_default="3"),
        sa.Column("burn_subtitles", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("use_broll", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()),
    )
    op.create_index("ix_projects_id", "projects", ["id"])
    op.create_index("ix_projects_user_id", "projects", ["user_id"])
    op.create_index("ix_projects_status", "projects", ["status"])

    op.create_table(
        "transcripts",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("project_id", sa.Integer(), sa.ForeignKey("projects.id", ondelete="CASCADE"), nullable=False),
        sa.Column("full_text", sa.Text(), nullable=False, server_default=""),
        sa.Column("segments", sa.JSON(), nullable=False),
        sa.Column("language", sa.String(length=20), nullable=True),
    )
    op.create_index("ix_transcripts_id", "transcripts", ["id"])
    op.create_index("ix_transcripts_project_id", "transcripts", ["project_id"], unique=True)

    op.create_table(
        "highlight_segments",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("project_id", sa.Integer(), sa.ForeignKey("projects.id", ondelete="CASCADE"), nullable=False),
        sa.Column("order", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("start_time", sa.Float(), nullable=False),
        sa.Column("end_time", sa.Float(), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("reason", sa.Text(), nullable=True),
        sa.Column("score", sa.Float(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()),
    )
    op.create_index("ix_highlight_segments_id", "highlight_segments", ["id"])
    op.create_index("ix_highlight_segments_project_id", "highlight_segments", ["project_id"])

    short_status_enum = sa.Enum("pending", "rendering", "ready", "failed", name="shortstatus")
    op.create_table(
        "shorts",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("project_id", sa.Integer(), sa.ForeignKey("projects.id", ondelete="CASCADE"), nullable=False),
        sa.Column(
            "highlight_segment_id",
            sa.Integer(),
            sa.ForeignKey("highlight_segments.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("file_path", sa.String(length=1000), nullable=True),
        sa.Column("thumbnail_path", sa.String(length=1000), nullable=True),
        sa.Column("duration_seconds", sa.Float(), nullable=True),
        sa.Column("has_subtitles", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("has_broll", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("status", short_status_enum, nullable=False, server_default="pending"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()),
    )
    op.create_index("ix_shorts_id", "shorts", ["id"])
    op.create_index("ix_shorts_project_id", "shorts", ["project_id"])
    op.create_index("ix_shorts_highlight_segment_id", "shorts", ["highlight_segment_id"], unique=True)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table("shorts")
    op.drop_table("highlight_segments")
    op.drop_table("transcripts")
    op.drop_table("projects")
    op.drop_table("refresh_tokens")
    op.drop_table("users")

    bind = op.get_bind()
    sa.Enum(name="shortstatus").drop(bind, checkfirst=True)
    sa.Enum(name="projectstatus").drop(bind, checkfirst=True)
    sa.Enum(name="sourcetype").drop(bind, checkfirst=True)
