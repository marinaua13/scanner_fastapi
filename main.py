# from fastapi import FastAPI, Request, Form
# from fastapi.responses import HTMLResponse
# from fastapi.templating import Jinja2Templates
# from database import SessionLocal
# from fastapi.staticfiles import StaticFiles
# from sqlalchemy import text
#
# app = FastAPI()
# templates = Jinja2Templates(directory="templates")
# app.mount("/static", StaticFiles(directory="static"), name="static")
#
# @app.get("/", response_class=HTMLResponse)
# def home(request: Request):
#     return templates.TemplateResponse("scan.html", {"request": request})
#
# @app.post("/lookup", response_class=HTMLResponse)
# def lookup(request: Request, code: str = Form(...)):
#     db = SessionLocal()
#     stmt = text(f"SELECT * FROM productsTest WHERE artikul = :code LIMIT 1")
#     result = db.execute(stmt, {"code": code}).fetchone()
#     db.close()
#     return templates.TemplateResponse("scan.html", {
#         "request": request,
#         "result": result
#     })

from fastapi import FastAPI, Request, Form
from sqlalchemy import text
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
# from starlette.middleware.sessions import SessionMiddleware

from database import SessionLocal
from fastapi.staticfiles import StaticFiles


app = FastAPI()

# app.add_middleware(SessionMiddleware, secret_key="supersecretkey")

templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")

# GET: показуємо форму
@app.get("/login", response_class=HTMLResponse)
def login_get(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

# POST: обробка логіну
@app.post("/login", response_class=HTMLResponse)
def login_post(request: Request, username: str = Form(...), password: str = Form(...)):
    db = SessionLocal()
    error = None

    try:
        stmt = text("""
            SELECT id, login FROM user
            WHERE login = :username AND password = :password
            LIMIT 1
        """)
        user = db.execute(stmt, {"username": username, "password": password}).fetchone()

        if user:
            request.session["user_id"] = user["id"]
            request.session["username"] = user["login"]
            return RedirectResponse(url="/", status_code=302)
        else:
            error = "Невірний логін або пароль"
    except Exception as e:
        error = str(e)
    finally:
        db.close()

    return templates.TemplateResponse("login.html", {"request": request, "error": error})


# @app.get("/", response_class=HTMLResponse)
# def home(request: Request):
#     return templates.TemplateResponse("scan.html", {"request": request})
#
#
# @app.post("/lookup", response_class=HTMLResponse)
# def lookup(request: Request, code: str = Form(...)):
#     db = SessionLocal()
#     result = None
#     error = None
#
#     try:
#         stmt = text("SELECT * FROM orders_shipment_scanner WHERE ttn = :code LIMIT 1")
#         result = db.execute(stmt, {"code": code}).fetchone()
#     except Exception as e:
#         error = str(e)
#     finally:
#         db.close()
#
#     return templates.TemplateResponse("scan.html", {
#         "request": request,
#         "result": result,
#         "error": error,
#         "code": code,
#     })


# Симуляція сесії (поки що глобальна)
session_state = {
    "shelf": None,
    "product": None,
    "confirm_shelf": None
}


@app.get("/scan-shelf", response_class=HTMLResponse)
def scan_shelf_get(request: Request):
    return templates.TemplateResponse("place_on_shelf.html", {
        "request": request,
        "shelf": session_state["shelf"],
        "product": session_state["product"],
        "confirm_shelf": session_state["confirm_shelf"],
        "step": get_step_label(),
        "success": "",
        "error": ""
    })


@app.post("/scan-shelf", response_class=HTMLResponse)
def scan_shelf_post(request: Request, scan_input: str = Form(...)):
    db = SessionLocal()
    success = ""
    error = ""

    try:
        if not session_state["shelf"]:
            session_state["shelf"] = scan_input
        elif not session_state["product"]:
            session_state["product"] = scan_input
        elif not session_state["confirm_shelf"]:
            session_state["confirm_shelf"] = scan_input

            if session_state["shelf"] == session_state["confirm_shelf"]:
                # ✅ Полички співпали — пробуємо знайти товар і записати
                try:
                    product_query = text("""
                        SELECT sku
                        FROM productsNewside
                        WHERE sku = :sku
                        LIMIT 1
                    """)
                    product = db.execute(product_query, {"sku": session_state["product"]}).fetchone()

                    if not product:
                        error = "Товар не знайдено в базі."
                    else:
                        insert_stmt = text("""
                            INSERT INTO shelves_history (shelf, sku, size, barcode, action, packer_id)
                            VALUES (:shelf, :sku, :size, :barcode, 'placed', :packer_id)
                        """)
                        db.execute(insert_stmt, {
                            "shelf": session_state["shelf"],
                            "sku": product["sku"],
                            "size": "",  # поки нема поля size
                            "barcode": "",  # теж пусто
                            "packer_id": 1
                        })
                        db.commit()
                        success = "Товар успішно розміщено на поличку!"

                        # 🔁 Скидаємо сесію після успіху
                        session_state["shelf"] = None
                        session_state["product"] = None
                        session_state["confirm_shelf"] = None

                except Exception as insert_error:
                    error = f"Помилка запису в БД: {insert_error}"
            else:
                # ❌ Полички не збіглись
                error = "Полички не співпадають. Спробуйте ще раз."
                session_state["confirm_shelf"] = None

    except Exception as e:
        error = f"Помилка виконання: {e}"
    finally:
        db.close()

    return templates.TemplateResponse("place_on_shelf.html", {
        "request": request,
        "shelf": session_state["shelf"],
        "product": session_state["product"],
        "confirm_shelf": session_state["confirm_shelf"],
        "step": get_step_label(),
        "success": success,
        "error": error
    })


@app.post("/scan-shelf/reset", response_class=HTMLResponse)
def reset_scan_session(request: Request):
    session_state["shelf"] = None
    session_state["product"] = None
    session_state["confirm_shelf"] = None
    return RedirectResponse(url="/scan-shelf", status_code=303)


def get_step_label():
    if not session_state["shelf"]:
        return "Очікується сканування ПОЛИЦІ"
    elif not session_state["product"]:
        return "Очікується сканування ТОВАРУ"
    elif not session_state["confirm_shelf"]:
        return "Підтвердьте полицю (повторне сканування)"
    return "Завершено"




#SCAN_TTN

# 1. Роут: сторінка сканування ТТН
@app.get("/scan-ttn", response_class=HTMLResponse)
def get_scan_ttn(request: Request):
    return templates.TemplateResponse("scan.html", {"request": request})

# 2. Роут: обробка вводу ТТН
@app.post("/scan-ttn", response_class=HTMLResponse)
def post_scan_ttn(request: Request, ttn: str = Form(...)):
    db = SessionLocal()
    product = None
    error = ""

    try:
        # 3. Пошук інформації з ТТН в arrival_scanner_* або products_shipment_scanner
        query = text("""
            SELECT sku, size, shelf, image_url
            FROM products_shipment_scanner
            WHERE ttn = :ttn
            LIMIT 1
        """)
        result = db.execute(query, {"ttn": ttn}).fetchone()

        if result:
            product = {
                "sku": result["sku"],
                "size": result["size"],
                "shelf": result["shelf"],
                "image_url": result["image_url"]
            }
        else:
            error = "Товар з такою ТТН не знайдено."

    except Exception as e:
        error = str(e)
    finally:
        db.close()

    return templates.TemplateResponse("scan.html", {
        "request": request,
        "product": product,
        "error": error
    })
