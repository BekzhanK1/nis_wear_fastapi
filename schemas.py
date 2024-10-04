# schemas.py
from datetime import datetime
from pydantic import BaseModel, EmailStr
from typing import List, Optional
from enum import Enum
from decimal import Decimal


# Enum for status choices
class StatusEnum(str, Enum):
    new = "new"
    paid = "paid"
    processing = "processing"
    shipped = "shipped"
    delivered = "delivered"
    canceled = "canceled"


# Schema for ProductOption
class ProductOptionSchema(BaseModel):
    id: int
    option_name: str
    variant: str

    class Config:
        orm_mode = True


# Schema for Product
class ProductSchema(BaseModel):
    id: int
    name: str
    sku: str
    price: Decimal
    quantity: int
    amount: Decimal
    is_assembled: bool
    options: List[ProductOptionSchema] = []

    class Config:
        orm_mode = True


# Schema for Customer
class CustomerSchema(BaseModel):
    id: int
    name: str
    phone: str
    email: str

    class Config:
        orm_mode = True


class StatusChangeSchema(BaseModel):
    id: int
    status: StatusEnum
    created_at: datetime

    class Config:
        orm_mode = True


# Schema for Order
class OrderSchema(BaseModel):
    order_id: str
    payment_system: str
    status: StatusEnum
    school: str
    grade: int
    letter: str
    total_amount: Decimal
    form_id: str
    form_name: str
    customer: CustomerSchema
    shipping_date: datetime
    products: List[ProductSchema] = []

    class Config:
        orm_mode = True


class UserSchema(BaseModel):
    username: str

    class Config:
        orm_mode = True


class EmailSchema(BaseModel):
    email: EmailStr
    subject: str
    body: str


class TrackOrderSchema(BaseModel):
    order_id: str
    status: StatusEnum
    total_amount: Decimal
    products: List[ProductSchema] = []
    shipping_date: datetime
    school: str
    status_changes: List[StatusChangeSchema] = []

    class Config:
        orm_mode = True
