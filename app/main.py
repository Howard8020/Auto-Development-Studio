import os
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware
from starlette.templating import Jinja2Templates
from app.config import Settings
from app.database import Base, engine
from app.routers import auth, wizard, brand_studio

settings = Settings()

def create_app() -> FastAPI:
    app = FastAPI(title=settings.app_name, debug=settings.debug)
    
    templates_dir = os.path.join(os.path.dirname(__file__), "templates")
    templates = Jinja2Templates(directory=templates_dir)
    app.add_middleware(SessionMiddleware, secret_key=settings.session_secret, max_age=7*24*60*60)
    static_dir = os.path.join(os.path.dirname(__file__), "static")
    os.makedirs(static_dir, exist_ok=True)
    app.mount("/static", StaticFiles(directory=static_dir), name="static")
    Base.metadata.create_all(bind=engine)
    auth._init_templates(templates)
    brand_studio._init_templates(templates)
    app.include_router(auth.router)
    app.include_router(wizard.router)
    app.include_router(brand_studio.router)
    app.state.templates = templates
    
    # Add /mockup route here, before return
    @app.get("/mockup")
    async def serve_mockup():
        from fastapi.responses import FileResponse
        return FileResponse(os.path.join("mockup", "index.html"))
    
    return app

app = create_app()
