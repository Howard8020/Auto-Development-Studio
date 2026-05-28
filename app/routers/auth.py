import json
from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import RedirectResponse
from authlib.integrations.httpx_client import AsyncOAuth2Client
from app.config import Settings
from app.database import SessionLocal
from app.models.user import User
from starlette.templating import Jinja2Templates

router = APIRouter()
templates = None
settings = Settings()

def _init_templates(tpl: Jinja2Templates):
    global templates
    templates = tpl

@router.get("/login")
async def login_page(request: Request):
    if "user" in request.session:
        return RedirectResponse(url="/dashboard")
    return templates.TemplateResponse(request, "login.html", {"request": request})

@router.get("/auth/login")
async def auth_login(request: Request):
    if not settings.google_client_id or not settings.google_client_secret:
        db = SessionLocal()
        mock_user = db.query(User).filter(User.email == "dev@localhost").first()
        if not mock_user:
            mock_user = User(email="dev@localhost", name="Dev User", picture="")
            db.add(mock_user); db.commit(); db.refresh(mock_user)
        db.close()
        request.session["user"] = mock_user.to_dict()
        return RedirectResponse(url="/dashboard")
    redirect_uri = str(request.url_for("auth_callback"))
    client = AsyncOAuth2Client(settings.google_client_id, client_secret=settings.google_client_secret, redirect_uri=redirect_uri)
    authorization_url, state = client.create_authorization_url("https://accounts.google.com/o/oauth2/auth", prompt="select_account")
    request.session["oauth_state"] = state
    return RedirectResponse(url=authorization_url)

@router.get("/auth/callback")
async def auth_callback(request: Request, code: str = "", state: str = "", error: str = ""):
    if error:
        return templates.TemplateResponse(request, "login.html", {"request": request, "error": f"Google auth error: {error}"})
    stored_state = request.session.get("oauth_state")
    if not stored_state or stored_state != state:
        raise HTTPException(status_code=400, detail="State mismatch")
    redirect_uri = str(request.url_for("auth_callback"))
    client = AsyncOAuth2Client(settings.google_client_id, client_secret=settings.google_client_secret, redirect_uri=redirect_uri)
    token = await client.fetch_token("https://oauth2.googleapis.com/token", authorization_response=str(request.url), code=code)
    resp = await client.get("https://www.googleapis.com/oauth2/v2/userinfo")
    google_user = resp.json()
    db = SessionLocal()
    user = db.query(User).filter(User.email == google_user["email"]).first()
    if not user:
        user = User(email=google_user["email"], name=google_user.get("name",""), picture=google_user.get("picture",""))
        db.add(user); db.commit(); db.refresh(user)
    db.close()
    request.session["user"] = user.to_dict()
    return RedirectResponse(url="/dashboard")

@router.get("/logout")
async def logout(request: Request):
    request.session.pop("user", None)
    return RedirectResponse(url="/")

@router.get("/dashboard")
async def dashboard(request: Request):
    if "user" not in request.session:
        return RedirectResponse(url="/login")
    return templates.TemplateResponse(request, "dashboard.html", {"request": request, "user": request.session["user"]})