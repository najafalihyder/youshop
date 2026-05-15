from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from starlette.middleware.sessions import SessionMiddleware


from utils import hash_passowrd, verify_password
from database import init_db, get_db
init_db()

app = FastAPI()

app.add_middleware(SessionMiddleware, secret_key='najaf-youshop-2026')

# Server static files: static/styles.css, /static/app.js, etc.
app.mount("/static", StaticFiles(directory="static"), name="static")

# Tell FastAPI where your HTML templates live
templates = Jinja2Templates(directory="templates")

@app.get("/")
def index(request: Request):

    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={}
    )

@app.get("/register")
def register(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="register.html",
        context={}
    )



@app.post("/register")
def register_post(request: Request, email: str = Form(...), username: str = Form(...), password: str = Form(...), confirmation: str = Form(...)):

    conn = get_db()
    row = conn.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
    
    if row:
        return templates.TemplateResponse(
            request=request,
            name="apology.html",
            context={"message": "Email already exists"}
        )
    elif confirmation != password:
        return templates.TemplateResponse(
            request=request,
            name="apology.html",
            context={"message": "Confirm password does not match"}
        )
    else:
        hashed = hash_passowrd(password)
        conn.execute("INSERT INTO users (username, email, password) VALUES (?, ?, ?)", (username, email, hashed))
        conn.commit()
        conn.close()
        return RedirectResponse(
            url="/login",
            status_code=303
        )




@app.get("/login")
def login(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="login.html",
        context={}
    )


@app.post("/login")
def login_post(request: Request, email: str = Form(...), password: str = Form(...)):

    conn = get_db()
    row = conn.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
    if not row:
        return templates.TemplateResponse(
            request=request,
            name="apology.html",
            context={"message": "Email not registered!"}
        )
    
    if not verify_password(password, row['password']):
            return templates.TemplateResponse(
                request=request,
                name="apology.html",
                context={"message": "Invalid password"}
            )
    request.session['user_id'] = row["id"]
    return RedirectResponse(
        url="/home",
        status_code=303
    )
