# models.py
from datetime import datetime, timedelta
from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Integer,
    String,
    ForeignKey,
    DECIMAL,
    Enum,
)
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
import enum
from passlib.context import CryptContext

Base = declarative_base()


class StatusEnum(enum.Enum):
    new = "new"
    paid = "paid"
    processing = "processing"
    shipped = "shipped"
    delivered = "delivered"
    canceled = "canceled"


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True)
    hashed_password = Column(String(255))

    def verify_password(self, password: str):
        return pwd_context.verify(password, self.hashed_password)

    def hash_password(self, password: str):
        self.hashed_password = pwd_context.hash(password)


class Customer(Base):
    __tablename__ = "customers"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255))
    phone = Column(String(50))
    email = Column(String(255))

    orders = relationship("Order", back_populates="customer")


class Order(Base):
    __tablename__ = "orders"

    order_id = Column(String(50), primary_key=True, index=True)
    customer_id = Column(Integer, ForeignKey("customers.id"))
    payment_system = Column(String(50))
    status = Column(Enum(StatusEnum), default=StatusEnum.new)
    total_amount = Column(DECIMAL(10, 2))
    form_id = Column(String(100))
    form_name = Column(String(100))

    customer = relationship("Customer", back_populates="orders")
    products = relationship("Product", back_populates="order")
    status_changes = relationship("StatusChange", back_populates="order")


class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.order_id"))
    name = Column(String(255))
    sku = Column(String(50))
    price = Column(DECIMAL(10, 2))
    quantity = Column(Integer)
    amount = Column(DECIMAL(10, 2))
    is_assembled = Column(Boolean, default=False)

    order = relationship("Order", back_populates="products")
    options = relationship("ProductOption", back_populates="product")


class ProductOption(Base):
    __tablename__ = "product_options"

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id"))
    option_name = Column(String(255))
    variant = Column(String(255))

    product = relationship("Product", back_populates="options")


class StatusChange(Base):
    __tablename__ = "status_changes"

    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(String(50), ForeignKey("orders.order_id"))
    status = Column(Enum(StatusEnum))
    created_at = Column(
        DateTime, default=lambda: datetime.utcnow() + timedelta(hours=5)
    )

    order = relationship("Order", back_populates="status_changes")
