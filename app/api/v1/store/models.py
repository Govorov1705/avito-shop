from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import CheckConstraint, ForeignKey, Enum, UniqueConstraint
import enum
from datetime import datetime

from app.core.db.base import Base


class TransactionType(enum.Enum):
    PURCHASE = "purchase"
    GIFT = "gift"


class Item(Base):
    __table_args__ = (CheckConstraint("cost >= 0", name="check_cost_non_negative"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    type: Mapped[str]
    cost: Mapped[int]


class Transaction(Base):
    __table_args__ = (CheckConstraint("amount > 0", name="check_amount_positive"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    amount: Mapped[int] = mapped_column()
    type: Mapped[TransactionType] = mapped_column(Enum(TransactionType))
    timestamp: Mapped[datetime] = mapped_column(default=datetime.now())
    recipient_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id"), nullable=True
    )
    item_id: Mapped[int | None] = mapped_column(ForeignKey("items.id"), nullable=True)


class Inventory(Base):
    __tablename__ = "inventories"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), unique=True
    )

    items: Mapped[list["Item"]] = relationship(
        "InventoryItem", back_populates="inventory"
    )


class InventoryItem(Base):
    __tablename__ = "inventory_items"
    __table_args__ = (
        CheckConstraint("quantity > 0", name="check_quantity_positive"),
        UniqueConstraint("inventory_id", "item_id", name="uq_inventory_item"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    inventory_id: Mapped[int] = mapped_column(
        ForeignKey("inventories.id", ondelete="CASCADE")
    )
    item_id: Mapped[int] = mapped_column(ForeignKey("items.id", ondelete="CASCADE"))
    quantity: Mapped[int] = mapped_column(default=1)

    inventory: Mapped["Inventory"] = relationship("Inventory", back_populates="items")
