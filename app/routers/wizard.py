import json, os, subprocess, zipfile, uuid, sys
from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import RedirectResponse, FileResponse
from starlette.templating import Jinja2Templates

router = APIRouter()
templates = None
_wizard_store: dict[str, dict] = {}

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
print(f'WIZARD_BOOT: PROJECT_ROOT={PROJECT_ROOT}', flush=True)


def _init_templates(tpl: Jinja2Templates):
    global templates
    templates = tpl


def _session_key(request: Request) -> str:
    user = request.session.get("user", {})
    return user.get("id", user.get("email", uuid.uuid4().hex))


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
    sk = _session_key(request)
    if sk not in _wizard_store:
        _wizard_store[sk] = {}
    _wizard_store[sk]["scope"] = form.get("scope", "")
    return RedirectResponse(url="/wizard/answers", status_code=303)


@router.get("/wizard/answers")
async def wizard_answers(request: Request):
    if "user" not in request.session:
        return RedirectResponse(url="/login")
    store = _wizard_store.get(_session_key(request), {})
    scope = store.get("scope", "")
    if not scope:
        return RedirectResponse(url="/wizard")
    return templates.TemplateResponse(request, "wizard/answers.html", {"request": request, "user": request.session["user"], "scope": scope})


@router.post("/wizard/save-answers")
async def wizard_save_answers(request: Request):
    if "user" not in request.session:
        return RedirectResponse(url="/login")
    form = await request.form()
    sk = _session_key(request)
    if sk not in _wizard_store:
        _wizard_store[sk] = {}
    _wizard_store[sk].update({
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
    store = _wizard_store.get(_session_key(request), {})
    if not store.get("project_name"):
        return RedirectResponse(url="/wizard")
    return templates.TemplateResponse(request, "wizard/preview.html", {"request": request, "user": request.session["user"], "data": store})


@router.post("/wizard/generate")
async def wizard_generate(request: Request):
    if "user" not in request.session:
        return RedirectResponse(url="/login")
    store = _wizard_store.get(_session_key(request), {})
    if not store.get("project_name"):
        return RedirectResponse(url="/wizard")
    project_name = store["project_name"].replace(" ", "-").lower()
    output_dir = os.path.join(PROJECT_ROOT, "generated", project_name)
    print(f'WIZARD_GEN: output_dir={output_dir} script={os.path.join(PROJECT_ROOT, "scripts", "generate_project.py")} store_keys={list(store.keys())}', flush=True)
    os.makedirs(output_dir, exist_ok=True)
    input_path = os.path.join(output_dir, "input.json")
    with open(input_path, "w") as f:
        json.dump(store, f, indent=2)
    script_path = os.path.join(PROJECT_ROOT, "scripts", "generate_project.py")
    if os.path.exists(script_path):
        result = subprocess.run(
            [sys.executable, script_path, "--input", input_path, "--output", output_dir],
            capture_output=True, text=True, timeout=30,
        )
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
    generated_dir = os.path.join(PROJECT_ROOT, "generated", name, name)
    zip_path = os.path.join(generated_dir, f"{name}.zip")
    if not os.path.exists(zip_path):
        parent_dir = os.path.dirname(generated_dir)
        if not os.path.exists(parent_dir):
            raise HTTPException(status_code=404, detail="Generated project not found")
        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
            for root, dirs, files in os.walk(parent_dir):
                for fname in files:
                    if fname.endswith(".json") or fname.endswith(".zip"):
                        continue
                    filepath = os.path.join(root, fname)
                    arcname = os.path.relpath(filepath, parent_dir)
                    zf.write(filepath, arcname)
    return FileResponse(zip_path, media_type="application/zip", filename=f"{name}.zip")