from decimal import Decimal
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import  Mapped, mapped_column, relationship
from sqlalchemy import Integer, String, Numeric
from typing import List

db = SQLAlchemy()

class Stock(db.Model):
    __tablename__ = "stock"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    symbol: Mapped[str] = mapped_column(String(250), unique=True, nullable=False)
    company_name: Mapped[str | None] = mapped_column(String(250), unique=False)
    last_fetched_at: Mapped[str | None] = mapped_column(String(250), unique=False, nullable=True)

    prices: Mapped[List["StockPrice"]] = relationship(back_populates="stock", cascade="all, delete-orphan")


class StockPrice(db.Model):
    __tablename__ = "stock_prices"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    stock_id: Mapped[int] = mapped_column(Integer, db.ForeignKey("stock.id"))

    date: Mapped[str] = mapped_column(nullable=False)
    open: Mapped[Decimal | None] = mapped_column(Numeric(14, 4))
    high: Mapped[Decimal | None] = mapped_column(Numeric(14, 4))
    low: Mapped[Decimal | None] = mapped_column(Numeric(14, 4))
    close: Mapped[Decimal | None] = mapped_column(Numeric(14, 4))
    volume: Mapped[int | None] = mapped_column(db.BigInteger)
    adj_close: Mapped[Decimal | None] = mapped_column(db.Numeric(14, 4))

    stock: Mapped["Stock"] = relationship(back_populates="prices")
    __table_args__ = (
        db.UniqueConstraint(
            "stock_id",
            "date",
            name="unique_stock_date"
        ),
    )