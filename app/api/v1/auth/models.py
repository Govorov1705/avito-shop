from datetime import datetime
from sqlalchemy import CheckConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db.base import Base


class User(Base):
    __table_args__ = (CheckConstraint("coins >= 0", name="check_coins_non_negative"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(unique=True)
    password: Mapped[str]
    created_at: Mapped[datetime] = mapped_column(default=datetime.now())
    coins: Mapped[int] = mapped_column(default=1000)
