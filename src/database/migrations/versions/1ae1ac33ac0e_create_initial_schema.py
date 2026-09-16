"""Создание начальной схемы

Идентификатор ревизии: 1ae1ac33ac0e
Предыдущая ревизия:
Дата создания: 2026-10-18 15:17:59.499392

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# Идентификаторы ревизии для Alembic.
revision: str = "1ae1ac33ac0e"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Применить изменения схемы."""
    op.create_table(
        "users",
        sa.Column("username", sa.String(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("api_key_hash", sa.String(), nullable=False),
        sa.Column(
            "api_key_created_at",
            sa.DateTime(timezone=True),
            nullable=False,
        ),
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("api_key_hash"),
        sa.UniqueConstraint("username"),
    )

    op.create_table(
        "signature_references",
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("subject_id", sa.String(), nullable=False),
        sa.Column("data", sa.LargeBinary(), nullable=False),
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "user_id",
            "subject_id",
            name="uq_signature_references_user_subject",
        ),
    )


def downgrade() -> None:
    """Отменить изменения схемы."""
    op.drop_table("signature_references")
    op.drop_table("users")
