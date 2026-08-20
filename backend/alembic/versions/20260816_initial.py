"""Create the initial documents and transcripts schema.

Revision ID: 20260816_initial
Revises:
Create Date: 2026-08-16 21:00:00.000000

"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "20260816_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "documents",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("original_filename", sa.String(length=255), nullable=False),
        sa.Column("safe_filename", sa.String(length=255), nullable=False, unique=True),
        sa.Column("mime_type", sa.String(length=128), nullable=True),
        sa.Column(
            "file_size_bytes", sa.BigInteger(), nullable=False, server_default="0"
        ),
        sa.Column(
            "status", sa.String(length=32), nullable=False, server_default="uploaded"
        ),
        sa.Column("raw_text", sa.Text(), nullable=True),
        sa.Column("cleaned_text", sa.Text(), nullable=True),
        sa.Column("language_code", sa.String(length=16), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )

    op.create_index(op.f("ix_documents_status"), "documents", ["status"], unique=False)
    op.create_index(
        op.f("ix_documents_created_at"), "documents", ["created_at"], unique=False
    )

    op.create_table(
        "transcripts",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column(
            "document_id",
            sa.Integer(),
            sa.ForeignKey("documents.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("raw_text", sa.Text(), nullable=False),
        sa.Column("cleaned_text", sa.Text(), nullable=True),
        sa.Column(
            "language_code", sa.String(length=16), nullable=False, server_default="uz"
        ),
        sa.Column(
            "source_type", sa.String(length=32), nullable=False, server_default="upload"
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_index(
        op.f("ix_transcripts_document_id"), "transcripts", ["document_id"], unique=False
    )
    op.create_index(
        op.f("ix_transcripts_language_code"),
        "transcripts",
        ["language_code"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_transcripts_language_code"), table_name="transcripts")
    op.drop_index(op.f("ix_transcripts_document_id"), table_name="transcripts")
    op.drop_table("transcripts")
    op.drop_index(op.f("ix_documents_created_at"), table_name="documents")
    op.drop_index(op.f("ix_documents_status"), table_name="documents")
    op.drop_table("documents")
