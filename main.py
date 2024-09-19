# main.py
import os
from dotenv import load_dotenv
from datetime import timedelta
from fastapi import FastAPI, Depends, HTTPException, Request, status, BackgroundTasks
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError
from sqlalchemy.orm import Session
from fastapi.middleware.cors import CORSMiddleware
from auth import (
    create_access_token,
    decode_access_token,
    get_current_user,
    verify_password,
)
from models import (
    Customer,
    Order,
    Product,
    ProductOption,
    StatusChange,
    StatusEnum,
    User,
    Base,
)
from database import SessionLocal, engine, get_db
import json
from schemas import OrderSchema, ProductSchema, TrackOrderSchema, UserSchema
from typing import List
from fastapi_mail import FastMail, MessageSchema, ConnectionConfig

load_dotenv()

# Initialize the FastAPI app
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # The frontend origin you want to allow
    allow_credentials=True,
    allow_methods=["*"],  # Allows all HTTP methods (GET, POST, etc.)
    allow_headers=["*"],  # Allows all headers
)

# Create the tables in the database
Base.metadata.create_all(bind=engine)


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


conf = ConnectionConfig(
    MAIL_USERNAME=os.getenv("MAIL_USERNAME"),
    MAIL_PASSWORD=os.getenv("MAIL_PASSWORD"),
    MAIL_FROM=os.getenv("MAIL_FROM"),
    MAIL_PORT=int(os.getenv("MAIL_PORT")),  # Ensure this is an integer
    MAIL_SERVER=os.getenv("MAIL_SERVER"),
    MAIL_STARTTLS=os.getenv("MAIL_STARTTLS") == "True",  # Convert to boolean
    MAIL_SSL_TLS=os.getenv("MAIL_SSL_TLS") == "True",  # Ensure SSL is disabled
    USE_CREDENTIALS=True,
    VALIDATE_CERTS=True,
)


@app.post("/token")
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.username == form_data.username).first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=30)
    access_token = create_access_token(
        {"sub": user.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}


@app.get("/users/me/", response_model=UserSchema)
async def read_users_me(
    current_user: User = Depends(get_current_user),
):
    return current_user


@app.post("/tilda/orders/")
async def tilda_order_webhook(request: Request, db: Session = Depends(get_db)):
    try:
        customer_data = await request.json()

        formatted_data = json.dumps(customer_data, indent=4)
        print(formatted_data)  # This will print formatted JSON to the terminal

        name = customer_data["Name"]
        phone = customer_data["Phone"]
        email = customer_data["Email"]

        customer = db.query(Customer).filter(Customer.email == email).first()
        if not customer:
            customer = Customer(name=name, phone=phone, email=email)
            db.add(customer)
            db.commit()
            db.refresh(customer)

        payment_data = customer_data["payment"]
        order_id = payment_data["orderid"]
        payment_system = customer_data["paymentsystem"]
        total_amount = payment_data["amount"]
        form_id = customer_data["formid"]
        form_name = customer_data["formname"]

        order = Order(
            customer_id=customer.id,
            order_id=order_id,
            payment_system=payment_system,
            total_amount=total_amount,
            form_id=form_id,
            form_name=form_name,
        )
        db.add(order)
        status_change = StatusChange(order_id=order.order_id, status=StatusEnum.new)
        db.add(status_change)
        db.commit()
        db.refresh(order)

        for product_data in payment_data["products"]:
            product_name = product_data["name"]
            sku = product_data["sku"]
            price = product_data["price"]
            quantity = product_data["quantity"]
            amount = product_data["amount"]

            product = Product(
                order_id=order.order_id,
                name=product_name,
                sku=sku,
                price=price,
                quantity=quantity,
                amount=amount,
            )
            db.add(product)
            db.commit()
            db.refresh(product)

            if "options" in product_data:
                for option_data in product_data["options"]:
                    option_name = option_data["option"]
                    variant = option_data["variant"]

                    product_option = ProductOption(
                        product_id=product.id,
                        option_name=option_name,
                        variant=variant,
                    )
                    db.add(product_option)

        db.commit()

        return {"status": "success"}

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/orders/", response_model=List[OrderSchema])
async def get_orders(
    db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
):
    """Get all orders with customer and product details"""
    orders = db.query(Order).all()
    return orders


@app.get("/orders/{order_id}", response_model=OrderSchema)
async def get_order(order_id: int, db: Session = Depends(get_db)):
    """Get a single order by ID with customer and product details"""
    order = db.query(Order).filter(Order.order_id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    return order


@app.patch("/orders/{order_id}", response_model=OrderSchema)
async def update_order(
    order_id: str,
    status: str,
    background_tasks: BackgroundTasks,  # Use BackgroundTasks as a dependency
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):

    order = db.query(Order).filter(Order.order_id == order_id).first()

    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    valid_statuses = [e.value for e in StatusEnum]
    if status not in valid_statuses:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid status. Valid statuses are: {', '.join(valid_statuses)}",
        )

    if order.status == StatusEnum(status):
        raise HTTPException(
            status_code=400, detail=f"Order already has status: {status}"
        )

    order.status = StatusEnum(status)
    status_change = StatusChange(order_id=order_id, status=status)
    customer = db.query(Customer).filter(Customer.id == order.customer_id).first()
    db.add(status_change)
    db.commit()
    db.refresh(order)

    message = MessageSchema(
        subject="Order Status Update",
        recipients=[customer.email],  # List of recipients
        body=f"Your order with ID {order_id} has been updated to status: {status}",
        subtype="html",
        headers={  # Add these headers to mark the email as important
            "Importance": "high",  # For Outlook and other clients
            "X-Priority": "1",  # 1 = High, 3 = Normal, 5 = Low (RFC standard)
            "X-MSMail-Priority": "High",  # For Microsoft email clients
        },
    )

    # Try to send the email, handle exceptions
    try:
        fm = FastMail(conf)
        background_tasks.add_task(
            fm.send_message, message
        )  # Queue email sending in the background
        print(f"Email queued for order {order_id} status update.")
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to send email notification: {str(e)}"
        )

    print(f"Order {order_id} updated to status: {status}")
    return order


@app.patch("/products/{product_id}", response_model=ProductSchema)
def assemble_product(
    product_id: int,
    assemble: bool,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    product.is_assembled = assemble
    db.commit()
    db.refresh(product)
    return product


@app.get("/order-tracking/{order_id}", response_model=TrackOrderSchema)
def track_order(order_id: int, db: Session = Depends(get_db)):
    order = db.query(Order).filter(Order.order_id == order_id).first()

    if not order:
        return {"detail": "Order not found"}

    # Query all status changes for this order
    # status_changes = (
    #     db.query(StatusChange).filter(StatusChange.order_id == order_id).all()
    # )

    # # Attach status changes to the response
    # return {
    #     "order_id": order.order_id,
    #     "status": order.status,
    #     "total_amount": order.total_amount,
    #     "status_changes": status_changes,
    # }
    return order
