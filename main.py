# main.py
from fastapi import FastAPI, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from models import Customer, Order, Product, ProductOption, Base
from database import SessionLocal, engine, get_db
import json
from schemas import OrderSchema
from typing import List

# Initialize the FastAPI app
app = FastAPI()

# Create the tables in the database
Base.metadata.create_all(bind=engine)


@app.post("/tilda/orders/")
async def tilda_order_webhook(request: Request, db: Session = Depends(get_db)):
    try:
        # Parse the incoming JSON data
        customer_data = await request.json()
        
        formatted_data = json.dumps(customer_data, indent=4)
        print(formatted_data)  # This will print formatted JSON to the terminal
        

        # Extract customer information
        name = customer_data["Name"]
        phone = customer_data["Phone"]
        email = customer_data["Email"]

        # Create or get customer
        customer = db.query(Customer).filter(Customer.email == email).first()
        if not customer:
            customer = Customer(name=name, phone=phone, email=email)
            db.add(customer)
            db.commit()
            db.refresh(customer)

        # Extract order information
        payment_data = customer_data["payment"]
        order_id = payment_data["orderid"]
        payment_system = customer_data["paymentsystem"]
        total_amount = payment_data["amount"]
        form_id = customer_data["formid"]
        form_name = customer_data["formname"]

        # Create the order
        order = Order(
            customer_id=customer.id,
            order_id=order_id,
            payment_system=payment_system,
            total_amount=total_amount,
            form_id=form_id,
            form_name=form_name,
        )
        db.add(order)
        db.commit()
        db.refresh(order)

        # Process products in the order
        for product_data in payment_data["products"]:
            product_name = product_data["name"]
            sku = product_data["sku"]
            price = product_data["price"]
            quantity = product_data["quantity"]
            amount = product_data["amount"]

            # Create the product
            product = Product(
                order_id=order.id,
                name=product_name,
                sku=sku,
                price=price,
                quantity=quantity,
                amount=amount,
            )
            db.add(product)
            db.commit()
            db.refresh(product)

            # Process options for the product (if any)
            if "options" in product_data:
                for option_data in product_data["options"]:
                    option_name = option_data["option"]
                    variant = option_data["variant"]

                    # Create the product option
                    product_option = ProductOption(
                        product_id=product.id,
                        option_name=option_name,
                        variant=variant,
                    )
                    db.add(product_option)

        db.commit()

        return {"status": "success"}

    except Exception as e:
        return {"status": "error", "message": str(e)}


@app.get("/orders/", response_model=List[OrderSchema])
def get_orders(db: Session = Depends(get_db)):
    """Get all orders with customer and product details"""
    orders = db.query(Order).all()
    return orders


@app.get("/orders/{order_id}", response_model=OrderSchema)
def get_order(order_id: int, db: Session = Depends(get_db)):
    """Get a single order by ID with customer and product details"""
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    return order
