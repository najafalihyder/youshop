from fastapi import FastAPI, Request, Form, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware

from utils import hash_passowrd, verify_password
# Make sure your database.py contains both init_db and the get_db_session generator!
from database import init_db, get_db_session

# 1. Run your table check once on startup
init_db()

# 2. Initialize your clean app instance
app = FastAPI()

import os
app.add_middleware(SessionMiddleware, secret_key=os.environ.get('SECRET_KEY', 'najaf-youshop-2026'))

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")


@app.get("/admin/add-product")
def add_product_get(request: Request, db = Depends(get_db_session)):

    user_id = request.session.get('user_id')
    if not user_id:
        return RedirectResponse(url="/login", status_code=303)
    
    row = db.execute("SELECT is_admin FROM users WHERE id = ?", (user_id,)).fetchone()
    if row['is_admin'] == 0:
        return templates.TemplateResponse(
            request=request, name="apology.html", context={"message": "Unauthorised user!"}
        )
    return templates.TemplateResponse(
        request=request, name="add_product.html", context={}
    )


@app.post("/admin/add-product")
def add_product_post(
    request:Request,
    db = Depends(get_db_session),
    name:str = Form(...),
    image_url:str = Form(...),
    price:int = Form(...),
    description:str = Form(None),
    unit: str = Form(...)
):

    user_id = request.session.get('user_id')
    if not user_id:
        return RedirectResponse(url="/login", status_code=303)
    
    row = db.execute("SELECT is_admin FROM users WHERE id = ?", (user_id,)).fetchone()
    if row['is_admin'] == 0:
        return templates.TemplateResponse(
            request=request, name="apology.html", context={"message": "Unauthorised user!"}
        )

    db.execute("INSERT INTO products (name, image_url, price, description, unit) VALUES (?, ?, ?, ?, ?)", (name, image_url, price, description, unit))

    db.commit()
    return RedirectResponse(url="/shop", status_code=303)



@app.get("/admin/products")
def products(
    request:Request,
    db = Depends(get_db_session)
   
):

    user_id = request.session.get('user_id')
    if not user_id:
        return RedirectResponse(url="/login", status_code=303)
    
    row = db.execute("SELECT is_admin FROM users WHERE id = ?", (user_id,)).fetchone()
    if row['is_admin'] == 0:
        return templates.TemplateResponse(
            request=request, name="apology.html", context={"message": "Unauthorised user!"}
        )

    rows = db.execute("SELECT * FROM products").fetchall()
    return templates.TemplateResponse(
        request=request,
        name="admin_products.html",
        context={"products": rows}
    )

@app.post("/admin/delete-product")
def delete_product(
    request:Request,
    db = Depends(get_db_session),
    product_id: int = Form(...)
   
):

    user_id = request.session.get('user_id')
    if not user_id:
        return RedirectResponse(url="/login", status_code=303)
    
    row = db.execute("SELECT is_admin FROM users WHERE id = ?", (user_id,)).fetchone()
    if row['is_admin'] == 0:
        return templates.TemplateResponse(
            request=request, name="apology.html", context={"message": "Unauthorised user!"}
        )
    db.execute("DELETE FROM orders WHERE product_id = ?", (product_id,))
    db.execute("DELETE FROM products WHERE id = ?", (product_id,))
    db.commit()
    return RedirectResponse("/admin/products", status_code=303)



@app.get("/admin/dashboard")
def admin_dashboard(
    request:Request,
    db = Depends(get_db_session)
):

    user_id = request.session.get('user_id')
    if not user_id:
        return RedirectResponse(url="/login", status_code=303)
    
    row = db.execute("SELECT is_admin FROM users WHERE id = ?", (user_id,)).fetchone()
    if row['is_admin'] == 0:
        return templates.TemplateResponse(
            request=request, name="apology.html", context={"message": "Unauthorised user!"}
        )

    summary = db.execute("""
            SELECT products.name, products.price, SUM(orders.quantity) as total_quantity,
            (products.price * SUM(orders.quantity)) as total_cost
            FROM orders JOIN products ON products.id = orders.product_id WHERE orders.status = 'active' GROUP BY orders.product_id   
    """).fetchall()

    delivery = db.execute("""
        SELECT orders.user_id, users.phone, users.username, users.email, products.name, 
        products.price, SUM(orders.quantity) as total_quantity, 
        (products.price * SUM(orders.quantity)) as total_cost 
        FROM orders 
        JOIN products ON products.id = orders.product_id 
        JOIN users ON users.id = orders.user_id 
        WHERE orders.status = 'active' 
        GROUP BY orders.user_id, orders.product_id

    """).fetchall()


    return templates.TemplateResponse(
    request=request,
    name="admin_dashboard.html",
    context={"summary": summary, "delivery": delivery}
)


@app.post("/admin/mark_delivered")
def mark_delivered(
    request:Request,
    db = Depends(get_db_session),
    target_user_id:int = Form(...)
):

    user_id = request.session.get('user_id')
    if not user_id:
        return RedirectResponse(url="/login", status_code=303)
    
    row = db.execute("SELECT is_admin FROM users WHERE id = ?", (user_id,)).fetchone()
    if row['is_admin'] == 0:
        return templates.TemplateResponse(
            request=request, name="apology.html", context={"message": "Unauthorised user!"}
        )

    db.execute("UPDATE orders SET status = 'inactive' WHERE user_id = ?", (target_user_id,))
    db.commit()
    return RedirectResponse("/admin/dashboard", status_code=303)


@app.get("/shop")
def shop(
    request:Request,
    db = Depends(get_db_session)
):
    user_id = request.session.get("user_id")
    if not user_id:
        return RedirectResponse("/login", status_code=303)
    
    rows = db.execute("SELECT * FROM products").fetchall()
    
    return templates.TemplateResponse(
        request=request,
        name="shop.html",
        context={"products": rows}
    )    


@app.get("/orders")
def orders(request:Request, db = Depends(get_db_session)):

    user_id = request.session.get("user_id")
    if not user_id:
        return RedirectResponse("/login", status_code=303)
    
   
    rows = db.execute("""
        SELECT products.id as product_id, products.name, products.image_url, products.price, products.unit, 
        (products.price * SUM(orders.quantity)) as subtotal, 
        SUM(orders.quantity) as total_quantity 
        FROM orders JOIN products ON orders.product_id = products.id 
        WHERE orders.user_id = ? AND orders.status = 'active' 
        GROUP BY orders.product_id
    """, (user_id,)).fetchall()

    return templates.TemplateResponse(
        request=request,
        name="orders.html",
        context={"orders": rows}
    )


@app.post("/buy")
def buy(request:Request, db = Depends(get_db_session), product_id:int = Form(...)):

    user_id = request.session.get("user_id")
    if not user_id:
        return RedirectResponse("/login", status_code=303)
    
    db.execute("INSERT INTO orders (product_id, user_id, quantity) VALUES (?, ?, ?)", (product_id, user_id, 1))
    db.commit()
    return RedirectResponse("/shop", status_code=303)


@app.post("/cancel-order")
def cancel_order(request:Request, db = Depends(get_db_session), product_id:int = Form(...)):

    user_id = request.session.get("user_id")
    if not user_id:
        return RedirectResponse("/login", status_code=303)
    
    row = db.execute("SELECT * FROM orders WHERE user_id = ? AND product_id = ? AND status = 'active' LIMIT 1", (user_id, product_id)).fetchone()
    if not row:
        return templates.TemplateResponse(
            request=request,
            name="apology.html",
            context={"message": "No active orders!"}
        )
    db.execute("UPDATE orders SET status = 'inactive' WHERE id = ?", (row['id'],))
    db.commit()
    return RedirectResponse("/orders", status_code=303)

    



@app.get("/")
def index(request: Request):
    return templates.TemplateResponse(
        request=request, name="index.html", context={}
    )


@app.get("/register")
def register(request: Request):
    return templates.TemplateResponse(
        request=request, name="register.html", context={}
    )


# 3. Fixed route injection: We assign the dependency to the 'db' variable!
@app.post("/register")
def register_post(
    request: Request, 
    email: str = Form(...), 
    username: str = Form(...), 
    phone: str = Form(...),
    password: str = Form(...), 
    confirmation: str = Form(...), 
    db = Depends(get_db_session)
):
    row = db.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
    if row:
        return templates.TemplateResponse(
            request=request, name="apology.html", context={"message": "Email already exists"}
        )
    
    phone_row = db.execute("SELECT * FROM users WHERE phone = ?", (phone,)).fetchone()
    if phone_row:
        return templates.TemplateResponse(
            request=request, name="apology.html", context={"message": "Phone number already registered"}
        )
    
    elif confirmation != password:
        return templates.TemplateResponse(
            request=request, name="apology.html", context={"message": "Confirm password does not match"}
        )
    else:
        hashed = hash_passowrd(password)
        db.execute("INSERT INTO users (username, email, phone, password) VALUES (?, ?, ?, ?)", (username, email, phone, hashed))
        db.commit()
        return RedirectResponse(url="/login", status_code=303)


@app.get("/login")
def login(request: Request):
    return templates.TemplateResponse(
        request=request, name="login.html", context={}
    )


# 4. Added the 'db' dependency injection here to match!
@app.post("/login")
def login_post(
    request: Request, 
    email: str = Form(...), 
    password: str = Form(...),
    db = Depends(get_db_session)  # ◄── Injected here too
):
    row = db.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
    if not row:
        return templates.TemplateResponse(
            request=request, name="apology.html", context={"message": "Email not registered!"}
        )
    
    if not verify_password(password, row['password']):
        return templates.TemplateResponse(
            request=request, name="apology.html", context={"message": "Invalid password"}
        )
        
    request.session['user_id'] = row['id']
    return RedirectResponse(url="/shop", status_code=303)

@app.get("/logout")
def logout(request: Request):
    request.session.clear()
    return RedirectResponse("/login", status_code=303)