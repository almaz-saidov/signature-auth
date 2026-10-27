import uuid

from sqlalchemy import UUID, ForeignKey, LargeBinary, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from database.models.base import BaseModel


class SignatureReferenceModel(BaseModel):
    __tablename__ = "signature_references"
    __table_args__ = (
        UniqueConstraint(
            "user_id",
            "subject_id",
            name="uq_signature_references_user_subject",
        ),
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
    )
    subject_id: Mapped[str] = mapped_column(String, nullable=False)
    data: Mapped[bytes] = mapped_column(LargeBinary, nullable=False)
