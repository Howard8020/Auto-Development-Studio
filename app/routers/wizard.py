"""Wizard router — multi-step project scoping and generation."""

import json
import os
import subprocess
import zipfile
from pathlib import Path

from fastapi import APIRouter, File, Form, Request, UploadFile
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

router = APIRouter(prefix="/wizard", tags=["wizard"])

templates = Jinja2Templates(directory="app/templates")
templates.env.globals["app_name"] = "Auto Development Studio"

_HERE = Path(__file__).resolve().parent.parent.parent
GENERATED_DIR = _HERE / "generated"
GENERATED_DIR.mkdir(exist_ok=True)

GENERATE_SCRIPT = _HERE / "scripts" / "generate_project.py"


@router.get("")
async def wizard_start(request: Request):
    """Step 1: Project scope input."""
    return templates.TemplateResponse(request, "wizard/scope.html")


@router.get("/questions")
async def wizard_questions(request: Request):
    """Step 2: Guided questionnaire."""
    scope = request.session.get("wizard_data", {}).get("scope", "")
    return templates.TemplateResponse(request, "wizard/questions.html", {"scope": scope})


@router.get("/preview")
async def wizard_preview(request: Request):
    """Step 3: Preview before generation."""
    data = request.session.get("wizard_data", {})
    if not data or not data.get("name"):
        return RedirectResponse("/wizard", status_code=302)
    return templates.TemplateResponse(request, "wizard/preview.html", {"data": data})


@router.post("/save-scope")
async def save_scope(
    request: Request,
    scope: str = Form(""),
    scope_file: UploadFile = File(None),
):
    """Save the project scope and redirect to questions."""
    scope_text = scope.strip()

    # If a file was uploaded, read its content
    if scope_file and scope_file.filename:
        try:
            content = await scope_file.read()
            file_text = content.decode("utf-8", errors="replace").strip()
            if file_text:
                # Prepend file content; keep any typed text as additional context
                if scope_text:
                    scope_text = f"{file_text}\n\n--- Additional Context ---\n{scope_text}"
                else:
                    scope_text = file_text
        except Exception:
            pass

    if not scope_text:
        return HTMLResponse(
            '<div class="p-4 bg-red-50 text-red-700 rounded-lg"><strong>Error:</strong> Please enter or upload a project scope.</div>',
            status_code=400,
        )

    # Save to session
    request.session["wizard_data"] = {"scope": scope_text}

    # Use HX-Redirect header to tell HTMX to navigate
    resp = HTMLResponse("", status_code=200)
    resp.headers["HX-Redirect"] = "/wizard/questions"
    return resp


@router.post("/save-answers")
async def save_answers(
    request: Request,
    name: str = Form(alias="project_name", default=""),
    tagline: str = Form(""),
    color: str = Form(alias="brand_color", default="#ff6600"),
    with_auth: str = Form(alias="enable_auth", default="no"),
    with_db: str = Form(alias="enable_database", default="yes"),
    pages: str = Form(""),
    deps: str = Form(alias="extra_deps", default=""),
):
    """Save questionnaire answers and redirect to preview."""
    data = request.session.get("wizard_data", {})
    data.update({
        "name": name,
        "tagline": tagline,
        "color": color,
        "with_auth": with_auth,
        "with_db": with_db,
        "pages": pages,
        "deps": deps,
    })
    request.session["wizard_data"] = data

    resp = HTMLResponse("", status_code=200)
    resp.headers["HX-Redirect"] = "/wizard/preview"
    return resp


@router.post("/generate")
async def generate_project(request: Request):
    """Generate the project from wizard data."""
    data = request.session.get("wizard_data", {})
    if not data or not data.get("name"):
        return JSONResponse({"error": "No project data found. Please start the wizard again."}, status_code=400)

    name = data["name"]
    tagline = data.get("tagline", "")
    color = data.get("color", "#ff6600")
    with_auth = data.get("with_auth", "no") == "yes"
    with_db = data.get("with_db", "yes") == "yes"
    pages = data.get("pages", "")
    deps = data.get("deps", "")
    scope = data.get("scope", "")

    # Build JSON input for generator
    # Remap field names to match generate_project.py expectations
    input_data = {
        "project_name": name,
        "tagline": tagline,
        "brand_color": color,
        "use_auth": "yes" if with_auth else "no",
        "use_db": "yes" if with_db else "no",
        "pages": pages,
        "models": deps,
        "scope": scope,
    }
    safe_name = name.replace(" ", "_").lower()
    input_path = GENERATED_DIR / f"_input_{safe_name}.json"
    input_path.write_text(json.dumps(input_data, indent=2))

    cmd = [
        "python", str(GENERATE_SCRIPT),
        "--input", str(input_path),
        "--output", str(GENERATED_DIR),
    ]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        input_path.unlink(missing_ok=True)
        if result.returncode != 0:
            return JSONResponse({
                "error": f"Generation failed: {result.stderr[:500]}",
            }, status_code=500)

        # Parse output: last line should contain the path
        lines = [l for l in result.stdout.strip().split("\n") if l.strip()]
        output_path = lines[-1].split(":")[-1].strip() if lines else ""
        if not output_path or not Path(output_path).exists():
            return JSONResponse({"error": "Generation produced no output directory."}, status_code=500)

        project_name = Path(output_path).name
        return JSONResponse({
            "success": True,
            "project_name": project_name,
            "download_url": f"/wizard/download/{project_name}",
        })

    except subprocess.TimeoutExpired:
        return JSONResponse({"error": "Generation timed out. Please try again."}, status_code=500)
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)


@router.get("/download/{project_name}")
async def download_project(project_name: str):
    """Download a generated project as zip."""
    project_dir = GENERATED_DIR / project_name
    if not project_dir.exists():
        return JSONResponse({"error": "Project not found."}, status_code=404)

    zip_path = GENERATED_DIR / f"{project_name}.zip"
    if zip_path.exists():
        zip_path.unlink()

    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for root, _, files in os.walk(project_dir):
            for filename in files:
                file_path = Path(root) / filename
                arcname = str(file_path.relative_to(project_dir))
                zf.write(file_path, arcname)

    return FileResponse(
        zip_path,
        media_type="application/zip",
        filename=f"{project_name}.zip",
    )


@router.get("/success/{project_name}")
async def wizard_success(request: Request, project_name: str):
    """Success page after generation."""
    request.session.pop("wizard_data", None)
    return templates.TemplateResponse(request, "wizard/success.html", {"project_name": project_name})
