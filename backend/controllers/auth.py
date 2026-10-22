from typing import Optional

from fastapi import APIRouter, Request, Form, Depends
from fastapi.responses import RedirectResponse, HTMLResponse
from fastapi.templating import Jinja2Templates

from itsdangerous import URLSafeTimedSerializer, BadSignature, SignatureExpired
from werkzeug.security import generate_password_hash, check_password_hash

from sqlalchemy.orm import Session

from backend.config import settings
from backend.db import get_db
from backend.models.user import User


router = APIRouter()

templates = Jinja2Templates(directory="frontend/templates")

signer = URLSafeTimedSerializer(
    settings.SECRET_KEY,
    salt="session-salt",
    signer_kwargs={
        "key_derivation": "hmac",
        "digest_method": "sha256",
    },
)


def get_current_user(request: Request) -> Optional[str]:
    cookie_value = request.cookies.get(settings.SESSION_COOKIE_NAME)

    if not cookie_value:
        return None

    try:
        username = signer.loads(
            cookie_value,
            max_age=86400 * 7,
        )
        return username

    except (BadSignature, SignatureExpired):
        return None


# ============================================================
# LOGIN PAGE
# ============================================================

@router.get("/login", response_class=HTMLResponse)
async def login_form(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="login.html",
        context={
            "request": request,
        },
    )


# ============================================================
# LOGIN SUBMIT
# ============================================================

@router.post("/login", response_class=HTMLResponse)
async def login_submit(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db),
):
    user = db.query(User).filter(User.username == username).first()

    # Invalid login
    if user is None or not check_password_hash(
        user.password_hash,
        password,
    ):
        return templates.TemplateResponse(
            request=request,
            name="login.html",
            context={
                "request": request,
                "error": "Invalid username or password",
            },
            status_code=401,
        )

    # Successful login
    response = RedirectResponse(
        url="/app",
        status_code=303,
    )

    signed_value = signer.dumps(username)

    response.set_cookie(
        key=settings.SESSION_COOKIE_NAME,
        value=signed_value,
        max_age=86400 * 7,
        httponly=True,
        samesite="lax",
    )

    return response


# ============================================================
# SIGNUP PAGE
# ============================================================

@router.get("/signup", response_class=HTMLResponse)
async def signup_form(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="signup.html",
        context={
            "request": request,
            "error": None,
        },
    )


# ============================================================
# SIGNUP SUBMIT
# ============================================================

@router.post("/signup", response_class=HTMLResponse)
async def signup_submit(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db),
):
    existing = db.query(User).filter(
        User.username == username
    ).first()

    if existing is not None:
        return templates.TemplateResponse(
            request=request,
            name="signup.html",
            context={
                "request": request,
                "error": "Username already taken",
            },
            status_code=400,
        )

    new_user = User(
        username=username,
        password_hash=generate_password_hash(password),
    )

    db.add(new_user)
    db.commit()

    return RedirectResponse(
        url="/login",
        status_code=303,
    )


# ============================================================
# LOGOUT
# ============================================================

@router.get("/logout")
async def logout():
    response = RedirectResponse(
        url="/",
        status_code=303,
    )

    response.delete_cookie(
        key=settings.SESSION_COOKIE_NAME
    )

    return response


# ============================================================
# APPLICATION PAGE
# ============================================================

@router.get("/app", response_class=HTMLResponse)
async def app_page(request: Request):
    user = get_current_user(request)

    if user is None:
        return RedirectResponse(
            url="/login",
            status_code=303,
        )

    return templates.TemplateResponse(
        request=request,
        name="app.html",
        context={
            "request": request,
            "username": user,
        },
    )