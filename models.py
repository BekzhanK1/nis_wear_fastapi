# models.py
from sqlalchemy import Column, Integer, String, ForeignKey, DECIMAL, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
import enum

Base = declarative_base()


class StatusEnum(enum.Enum):
    new = "new"
    paid = "paid"
    processing = "processing"
    shipped = "shipped"
    delivered = "delivered"
    canceled = "canceled"


class Customer(Base):
    __tablename__ = "customers"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255))
    phone = Column(String(50))
    email = Column(String(255))

    orders = relationship("Order", back_populates="customer")


class Order(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, index=True)
    customer_id = Column(Integer, ForeignKey("customers.id"))
    order_id = Column(String(50))
    payment_system = Column(String(50))
    status = Column(Enum(StatusEnum), default=StatusEnum.new)
    total_amount = Column(DECIMAL(10, 2))
    form_id = Column(String(100))
    form_name = Column(String(100))

    customer = relationship("Customer", back_populates="orders")
    products = relationship("Product", back_populates="order")


class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id"))
    name = Column(String(255))
    sku = Column(String(50))
    price = Column(DECIMAL(10, 2))
    quantity = Column(Integer)
    amount = Column(DECIMAL(10, 2))

    order = relationship("Order", back_populates="products")
    options = relationship("ProductOption", back_populates="product")


class ProductOption(Base):
    __tablename__ = "product_options"

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id"))
    option_name = Column(String(255))
    variant = Column(String(255))

    product = relationship("Product", back_populates="options")
