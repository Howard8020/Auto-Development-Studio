import json, os, subprocess, zipfile, uuid
from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import RedirectResponse, FileResponse
from starlette.templating import Jinja2Templates

router = APIRouter()
templates = None
_wizard_store: dict[str, dict] = {}

def _init_templates(tpl: Jinja2Templates):
    global templates
    templates = tpl

@router.get("/")
async def index(request: Request):
    user = request.session.get("user", None)
    return templates.TemplateResponse(request, "index.html", {"request": request, "user": user})

@router.get("/wizard")
async def wizard_scope(request: Request):
    if "user" not in request.session:
        return RedirectResponse(url="/login")
    return templates.TemplateResponse(request, "wizard/scope.html", {"request": request, "user": request.session["user"]})

@router.post("/wizard/save-scope")
async def wizard_save_scope(request: Request):
    if "user" not in request.session:
        return RedirectResponse(url="/login")
    form = await request.form()
    session_key = request.session.get("id", request.session.get("session", str(uuid.uuid4())))
    if session_key not in _wizard_store:
        _wizard_store[session_key] = {}
    _wizard_store[session_key]["scope"] = form.get("scope", "")
    return RedirectResponse(url="/wizard/answers", status_code=303)

@router.get("/wizard/answers")
async def wizard_answers(request: Request):
    if "user" not in request.session:
        return RedirectResponse(url="/login")
    session_key = request.session.get("id", request.session.get("session", ""))
    store = _wizard_store.get(session_key, {})
    scope = store.get("scope", "")
    if not scope:
        return RedirectResponse(url="/wizard")
    return templates.TemplateResponse(request, "wizard/answers.html", {"request": request, "user": request.session["user"], "scope": scope})

@router.post("/wizard/save-answers")
async def wizard_save_answers(request: Request):
    if "user" not in request.session:
        return RedirectResponse(url="/login")
    form = await request.form()
    session_key = request.session.get("id", request.session.get("session", str(uuid.uuid4())))
    if session_key not in _wizard_store:
        _wizard_store[session_key] = {}
    _wizard_store[session_key].update({
        "project_name": form.get("project_name", "my-app"),
        "tagline": form.get("tagline", "Built with Auto Development Studio"),
        "brand_color": form.get("brand_color", "#ff6600"),
        "use_auth": form.get("use_auth", "yes"),
        "use_db": form.get("use_db", "yes"),
        "models": form.get("models", ""),
        "pages": form.get("pages", ""),
        "extras": form.get("extras", ""),
        "deploy_target": form.get("deploy_target", "render"),
    })
    return RedirectResponse(url="/wizard/preview", status_code=303)

@router.get("/wizard/preview")
async def wizard_preview(request: Request):
    if "user" not in request.session:
        return RedirectResponse(url="/login")
    session_key = request.session.get("id", request.session.get("session", ""))
    store = _wizard_store.get(session_key, {})
    if not store.get("project_name"):
        return RedirectResponse(url="/wizard")
    return templates.TemplateResponse(request, "wizard/preview.html", {"request": request, "user": request.session["user"], "data": store})

@router.post("/wizard/generate")
async def wizard_generate(request: Request):
    if "user" not in request.session:
        return RedirectResponse(url="/login")
    session_key = request.session.get("id", request.session.get("session", ""))
    store = _wizard_store.get(session_key, {})
    if not store.get("project_name"):
        return RedirectResponse(url="/wizard")
    project_name = store["project_name"].replace(" ", "-").lower()
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    output_dir = os.path.join(project_root, "generated", project_name)
    os.makedirs(output_dir, exist_ok=True)
    input_path = os.path.join(output_dir, "input.json")
    with open(input_path, "w") as f:
        json.dump(store, f, indent=2)
    script_path = os.path.join(project_root, "scripts", "generate_project.py")
    if os.path.exists(script_path):
        result = subprocess.run([".venv/bin/python", script_path, "--input", input_path, "--output", output_dir], capture_output=True, text=True, timeout=30)
        if result.returncode != 0:
            raise HTTPException(status_code=500, detail=f"Generation failed: {result.stderr}")
    request.session["wizard_data"] = {"generated_path": output_dir, "generated_name": project_name}
    return RedirectResponse(url=f"/wizard/success/{project_name}", status_code=303)

@router.get("/wizard/success/{name}")
async def wizard_success(request: Request, name: str):
    if "user" not in request.session:
        return RedirectResponse(url="/login")
    return templates.TemplateResponse(request, "wizard/success.html", {"request": request, "name": name})

@router.get("/wizard/download/{name}")
async def wizard_download(request: Request, name: str):
    if "user" not in request.session:
        return RedirectResponse(url="/login")
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    generated_dir = os.path.join(project_root, "generated", name)
    zip_path = f"{generated_dir}.zip"
    if not os.path.exists(zip_path):
        if not os.path.exists(generated_dir):
            raise HTTPException(status_code=404, detail="Generated project not found")
        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
            for root, dirs, files in os.walk(generated_dir):
                for fname in files:
                    if fname.endswith(".json"): continue
                    filepath = os.path.join(root, fname)
                    arcname = os.path.relpath(filepath, generated_dir)
                    zf.write(filepath, arcname)
    return FileResponse(zip_path, media_type="application/zip", filename=f"{name}.zip")