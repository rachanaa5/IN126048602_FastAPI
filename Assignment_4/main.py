from fastapi import FastAPI, HTTPException, Query, status
from pydantic import BaseModel, Field
from typing import List

app = FastAPI(title="Shopping Cart API")

# --- DATA MODELS ---

class CheckoutRequest(BaseModel):
    customer_name: str = Field(..., min_length=2)
    delivery_address: str = Field(..., min_length=10)

# --- IN-MEMORY DATABASE ---

products = [
    {"id": 1, "name": "Wireless Mouse", "price": 499, "category": "Electronics", "in_stock": True},
    {"id": 2, "name": "Notebook", "price": 99, "category": "Stationery", "in_stock": True},
    {"id": 3, "name": "USB Hub", "price": 799, "category": "Electronics", "in_stock": False},
    {"id": 4, "name": "Pen Set", "price": 49, "category": "Stationery", "in_stock": True},
]

cart = []
orders = []

# --- ENDPOINTS ---

@app.get("/cart")
def view_cart():
    if not cart:
        return {"message": "Cart is empty", "items": [], "grand_total": 0}
    grand_total = sum(item["subtotal"] for item in cart)
    return {"items": cart, "item_count": len(cart), "grand_total": grand_total}

@app.post("/cart/add")
def add_to_cart(product_id: int, quantity: int = Query(1, gt=0)):
    product = next((p for p in products if p["id"] == product_id), None)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    if not product["in_stock"]:
        raise HTTPException(status_code=400, detail=f"{product['name']} is out of stock")
    
    for item in cart:
        if item["product_id"] == product_id:
            item["quantity"] += quantity
            item["subtotal"] = item["quantity"] * item["unit_price"]
            return {"message": "Cart updated", "cart_item": item}
    
    new_item = {
        "product_id": product["id"],
        "product_name": product["name"],
        "quantity": quantity,
        "unit_price": product["price"],
        "subtotal": product["price"] * quantity
    }
    cart.append(new_item)
    return {"message": "Added to cart", "cart_item": new_item}

@app.delete("/cart/{product_id}")
def remove_from_cart(product_id: int):
    global cart
    item = next((item for item in cart if item["product_id"] == product_id), None)
    if not item:
        raise HTTPException(status_code=404, detail="Item not in cart")
    cart = [i for i in cart if i["product_id"] != product_id]
    return {"message": f"Removed {item['product_name']} from cart"}

@app.get("/orders")
def get_orders():
    return {"orders": orders, "total_orders": len(orders)}

@app.post("/cart/checkout")
def checkout(details: CheckoutRequest):
    global cart
    if not cart:
        raise HTTPException(status_code=400, detail="CART_EMPTY")
    
    placed_orders = []
    for item in cart:
        new_order = {
            "order_id": len(orders) + 1,
            "customer_name": details.customer_name,
            "product": item["product_name"],
            "quantity": item["quantity"],
            "total_price": item["subtotal"],
            "status": "confirmed"
        }
        orders.append(new_order)
        placed_orders.append(new_order)
    cart = []
    return {"message": "Checkout successful!", "orders_placed": placed_orders}