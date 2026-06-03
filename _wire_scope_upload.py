#!/usr/bin/env python3
"""Patch ADS wizard: wire scope upload, fix field names, fix HTMX flow, use scope in generator."""
import os, shutil
from pathlib import Path

REPO = Path(__file__).parent
BACKUP = REPO / "_backup_pre_wire"

def backup():
    """Backup files we're about to modify."""
    BACKUP.mkdir(exist_ok=True)
    targets = [
        "app/routers/wizard.py",
        "app/templates/wizard/scope.html",
        "app/templates/wizard/questions.html",
        "app/templates/wizard/preview.html",
        "app/templates/wizard/success.html",
        "scripts/generate_project.py",
    ]
    for t in targets:
        src = REPO / t
        if src.exists():
            dest = BACKUP / t
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dest)
            print(f"  Backed up: {t}")

# ── wizard.py ──────────────────────────────────────────────────────────────────
WIZARD_PY = '''"""Wizard router — multi-step project scoping and generation."""

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

GENERATED_DIR = Path(__file__).resolve().parent.parent.parent / "generated"
GENERATED_DIR.mkdir(exist_ok=True)

GENERATE_SCRIPT = Path(__file__).resolve().parent.parent.parent / "scripts" / "generate_project.py"


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
                    scope_text = f"{file_text}\\n\\n--- Additional Context ---\\n{scope_text}"
                else:
scope_text = file_text
        except Exception:
            pass

    if not scope_text:
        return HTMLResponse(
            \'<div class="p-4 bg-red-50 text-red-700 rounded-lg"><strong>Error:</strong> Please enter or upload a project scope.</div>\',
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

    # Build command
    cmd = [
        "python3", str(GENERATE_SCRIPT),
        "--name", name,
        "--tagline", tagline,
        "--color", color,
        "--pages", pages,
        "--deps", deps,
        "--scope", scope,
        "--output-dir", str(GENERATED_DIR),
    ]
    if not with_auth:
        cmd.append("--no-auth")
    if not with_db:
        cmd.append("--no-db")

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        if result.returncode != 0:
            return JSONResponse({
                "error": f"Generation failed: {result.stderr[:500]}",
            }, status_code=500)

        # Parse output: last line should contain the path
        lines = [l for l in result.stdout.strip().split("\\n") if l.strip()]
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
'''

# ── scope.html ─────────────────────────────────────────────────────────────────
SCOPE_HTML = '''{% extends "base.html" %}
{% block title %}New Project — Scope{% endblock %}
{% block content %}
<div class="max-w-3xl mx-auto py-8">
    <!-- Step indicator -->
    <div class="mb-6 flex items-center space-x-2 text-sm text-gray-500">
        <span class="font-medium text-brand-600">Step 1</span>
        <span>of 4: Scope</span>
        <div class="flex-1 h-2 bg-gray-200 rounded-full ml-2">
            <div class="h-2 bg-brand-500 rounded-full" style="width: 25%"></div>
        </div>
    </div>

    <div class="mb-8">
        <h1 class="text-3xl font-bold text-gray-900 mb-2">Describe your project</h1>
        <p class="text-gray-600">Paste a scope document, upload a file, or just type what you're building.</p>
    </div>

    <div class="bg-white p-8 rounded-xl shadow-sm border border-gray-200"
         x-data="{
            dragOver: false,
            fileName: '',
            fileContent: '',
            async handleFile(file) {
                this.fileName = file.name;
                this.fileContent = await file.text();
            },
            async handleDrop(e) {
                this.dragOver = false;
                const files = e.dataTransfer.files;
                if (files.length > 0) await this.handleFile(files[0]);
            }
         }">
        <form
            hx-post="/wizard/save-scope"
            hx-target="#wizard-feedback"
            hx-swap="innerHTML"
            hx-encoding="multipart/form-data"
        >
            <!-- File upload zone -->
            <div class="mb-6">
                <label class="block text-sm font-medium text-gray-700 mb-2">Upload Scope File <span class="text-gray-400">(optional — .txt, .md)</span></label>
                <div
                    class="relative border-2 border-dashed rounded-lg p-8 text-center transition-all"
                    :class="dragOver ? 'border-brand-500 bg-brand-50' : 'border-gray-300 hover:border-gray-400'"
                    @dragover.prevent="dragOver = true"
                    @dragleave.prevent="dragOver = false"
                    @drop.prevent="handleDrop()"
                >
                    <input type="file" name="scope_file" accept=".txt,.md,.text"
                        class="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
                        @change="if (.target.files[0]) handleFile(.target.files[0])">
                    <div x-show="!fileName">
                        <svg class="w-12 h-12 mx-auto text-gray-400 mb-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12"/>
                        </svg>
                        <p class="text-gray-600">Drag & drop or <span class="text-brand-600 font-medium">click to browse</span></p>
                        <p class="text-xs text-gray-400 mt-1">Supports .txt and .md files</p>
                    </div>
                    <div x-show="fileName" class="flex items-center justify-center space-x-3">
                        <svg class="w-8 h-8 text-green-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"/>
                        </svg>
                        <div class="text-left">
                            <p class="font-medium text-gray-900" x-text="fileName"></p>
                            <p class="text-xs text-gray-500">File ready to upload</p>
                        </div>
                        <button type="button" @click="fileName = ''; fileContent = ''"
                            class="ml-4 text-gray-400 hover:text-red-500">
                            <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/>
                            </svg>
                        </button>
                    </div>
                </div>
            </div>

            <!-- Textarea -->
            <div class="mb-6">
                <label for="scope" class="block text-sm font-medium text-gray-700 mb-2">Or Type Your Scope <span class="text-gray-400">(optional if file uploaded)</span></label>
                <textarea
                    id="scope"
                    name="scope"
                    rows="8"
                    class="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-brand-500 focus:border-brand-500 outline-none transition-all font-mono text-sm"
                    placeholder="Example: A task management app for remote teams. Users can create projects, assign tasks, set deadlines, and track progress with a Kanban board view. Integrates with Slack for notifications and Google Calendar for deadlines."
                ></textarea>
            </div>

            <button type="submit" class="px-6 py-3 bg-brand-500 text-white rounded-lg hover:bg-brand-600 transition-colors font-medium">
                Next: Answer Questions →
            </button>
        </form>
    </div>
    <div id="wizard-feedback" class="mt-4"></div>
</div>
{% endblock %}
'''

# ── questions.html ─────────────────────────────────────────────────────────────
QUESTIONS_HTML = '''{% extends "base.html" %}
{% block title %}New Project — Details{% endblock %}
{% block content %}
<div class="max-w-3xl mx-auto py-8" x-data="{ currentStep: 1, totalSteps: 6 }">
    <!-- Global step indicator -->
    <div class="mb-6 flex items-center space-x-2 text-sm text-gray-500">
        <span class="font-medium text-brand-600">Step 2</span>
        <span>of 4: Details</span>
        <div class="flex-1 h-2 bg-gray-200 rounded-full ml-2">
            <div class="h-2 bg-brand-500 rounded-full" style="width: 50%"></div>
        </div>
    </div>

    {% if scope %}
    <div class="mb-6 p-4 bg-brand-50 border border-brand-200 rounded-lg">
        <div class="flex items-center justify-between">
            <span class="text-sm font-medium text-brand-700">Scope captured ✓</span>
            <span class="text-xs text-brand-600">{{ scope[:80] }}{% if scope|length > 80 %}...{% endif %}</span>
        </div>
    </div>
    {% endif %}

    <div class="mb-8">
        <h1 class="text-3xl font-bold text-gray-900 mb-2">Project Details</h1>
        <p class="text-gray-600">A few quick questions to customize your scaffold.</p>
        <div class="mt-4 flex items-center space-x-2 text-sm text-gray-500">
            <span x-text="'Question ' + currentStep + ' of ' + totalSteps"></span>
            <div class="flex-1 h-2 bg-gray-200 rounded-full ml-2">
                <div class="h-2 bg-brand-500 rounded-full transition-all duration-300" :style="'width: ' + ((currentStep / totalSteps) * 100) + '%'"></div>
            </div>
        </div>
    </div>

    <form
        hx-post="/wizard/save-answers"
        hx-target="#wizard-content"
        hx-swap="innerHTML"
        x-ref="form"
    >
<div class="bg-white p-8 rounded-xl shadow-sm border border-gray-200" x-show="currentStep === 1">
            <h2 class="text-xl font-semibold text-gray-900 mb-2">Project Name</h2>
            <p class="text-gray-600 mb-4">What's the name of your project?</p>
            <input type="text" name="project_name" required
                class="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-brand-500 focus:border-brand-500 outline-none transition-all"
                placeholder="e.g. TaskFlow">
        </div>

        <div class="bg-white p-8 rounded-xl shadow-sm border border-gray-200 mt-4" x-show="currentStep === 2">
            <h2 class="text-xl font-semibold text-gray-900 mb-2">Tagline</h2>
            <p class="text-gray-600 mb-4">A short description for your app's hero section.</p>
            <input type="text" name="tagline"
                class="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-brand-500 focus:border-brand-500 outline-none transition-all"
                placeholder="e.g. Task management for remote teams">
        </div>

        <div class="bg-white p-8 rounded-xl shadow-sm border border-gray-200 mt-4" x-show="currentStep === 3">
            <h2 class="text-xl font-semibold text-gray-900 mb-2">Brand Color</h2>
            <p class="text-gray-600 mb-4">Pick a primary accent color for your app's theme.</p>
            <div class="flex items-center space-x-4">
                <input type="color" name="brand_color" value="#f97316"
                    class="w-16 h-16 rounded-lg border border-gray-300 cursor-pointer">
                <p class="text-xs text-gray-400">A full 10-stop palette will be generated from this hex.</p>
            </div>
        </div>

        <div class="bg-white p-8 rounded-xl shadow-sm border border-gray-200 mt-4" x-show="currentStep === 4">
            <h2 class="text-xl font-semibold text-gray-900 mb-4">Features</h2>
            <div class="space-y-4">
                <label class="flex items-center space-x-3">
                    <input type="checkbox" name="enable_auth" value="yes"
                        class="w-5 h-5 text-brand-500 border-gray-300 rounded focus:ring-brand-500">
                    <div>
                        <span class="font-medium text-gray-900">Google OAuth</span>
                        <p class="text-sm text-gray-500">User authentication with Google sign-in</p>
                    </div>
                </label>
                <label class="flex items-center space-x-3">
                    <input type="checkbox" name="enable_database" value="yes" checked
                        class="w-5 h-5 text-brand-500 border-gray-300 rounded focus:ring-brand-500">
                    <div>
                        <span class="font-medium text-gray-900">Database</span>
                        <p class="text-sm text-gray-500">SQLite + SQLAlchemy models</p>
                    </div>
                </label>
            </div>
        </div>

        <div class="bg-white p-8 rounded-xl shadow-sm border border-gray-200 mt-4" x-show="currentStep === 5">
            <h2 class="text-xl font-semibold text-gray-900 mb-2">Pages</h2>
            <p class="text-gray-600 mb-4">Page routes you'd like pre-created (comma-separated).</p>
            <input type="text" name="pages"
                class="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-brand-500 focus:border-brand-500 outline-none transition-all"
                placeholder="e.g. about, pricing, contact, features">
            <div class="mt-6">
                <h2 class="text-xl font-semibold text-gray-900 mb-2">Extra Dependencies</h2>
                <p class="text-gray-600 mb-4">Additional PyPI packages (comma-separated).</p>
                <input type="text" name="extra_deps"
                    class="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-brand-500 focus:border-brand-500 outline-none transition-all"
placeholder="e.g. httpx, pandas, celery">
            </div>
        </div>

        <div class="bg-white p-8 rounded-xl shadow-sm border border-gray-200 mt-4" x-show="currentStep === 6">
            <h2 class="text-xl font-semibold text-gray-900 mb-2">Almost Done!</h2>
            <p class="text-gray-600 mb-4">Review your answers on the next page, then generate.</p>
        </div>

        <div class="mt-8 flex justify-between">
            <button type="button" @click="currentStep--" x-show="currentStep > 1"
                class="px-6 py-3 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors text-gray-700 font-medium">
                ← Back
            </button>
            <div class="flex space-x-3">
                <a href="/wizard" class="px-6 py-3 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors text-gray-700 font-medium">
                    ← Start Over
                </a>
                <button type="button" @click="currentStep++" x-show="currentStep < totalSteps"
                    class="px-6 py-3 bg-brand-500 text-white rounded-lg hover:bg-brand-600 transition-colors font-medium">
                    Next →
                </button>
                <button type="submit" x-show="currentStep === totalSteps"
                    class="px-8 py-3 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors font-medium">
                    Review & Generate →
                </button>
            </div>
        </div>
    </form>
    <div id="wizard-content" class="mt-4"></div>
</div>
{% endblock %}
'''

# ── preview.html ───────────────────────────────────────────────────────────────
PREVIEW_HTML = '''{% extends "base.html" %}
{% block title %}Review Your Project{% endblock %}
{% block content %}
<div class="max-w-3xl mx-auto py-8">
    <!-- Global step indicator -->
    <div class="mb-6 flex items-center space-x-2 text-sm text-gray-500">
        <span class="font-medium text-brand-600">Step 3</span>
        <span>of 4: Review</span>
        <div class="flex-1 h-2 bg-gray-200 rounded-full ml-2">
            <div class="h-2 bg-brand-500 rounded-full" style="width: 75%"></div>
        </div>
    </div>

    <div class="mb-8">
        <h1 class="text-3xl font-bold text-gray-900 mb-2">Review Your Project</h1>
        <p class="text-gray-600">Here's what we'll generate. Make sure everything looks right.</p>
    </div>
    <div class="bg-white p-8 rounded-xl shadow-sm border border-gray-200">
        <dl class="space-y-6">
            <div>
                <dt class="text-sm font-medium text-gray-500">Project Name</dt>
                <dd class="mt-1 text-lg font-semibold text-gray-900">{{ data.name }}</dd>
            </div>
            <div>
                <dt class="text-sm font-medium text-gray-500">Tagline</dt>
                <dd class="mt-1 text-gray-900">{{ data.tagline or '—' }}</dd>
            </div>
            <div>
                <dt class="text-sm font-medium text-gray-500">Brand Color</dt>
                <dd class="mt-1 flex items-center space-x-2">
                    <span class="w-6 h-6 rounded border border-gray-300" style="background-color: {{ data.color }}"></span>
                    <span class="text-gray-900">{{ data.color }}</span>
                </dd>
            </div>
            <div>
                <dt class="text-sm font-medium text-gray-500">Google OAuth</dt>
                <dd class="mt-1">
                    {% if data.with_auth == 'yes' %}
                        <span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800">Enabled</span>
                    {% else %}
                        <span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-gray-100 text-gray-800">Disabled</span>
                    {% endif %}
                </dd>
            </div>
            <div>
                <dt class="text-sm font-medium text-gray-500">Database</dt>
                <dd class="mt-1">
{% if data.with_db == 'yes' %}
                        <span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800">Enabled</span>
                    {% else %}
                        <span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-gray-100 text-gray-800">Disabled</span>
                    {% endif %}
                </dd>
            </div>
            <div>
                <dt class="text-sm font-medium text-gray-500">Pages</dt>
                <dd class="mt-1 text-gray-900">{{ data.pages or '—' }}</dd>
            </div>
            <div>
                <dt class="text-sm font-medium text-gray-500">Extra Dependencies</dt>
                <dd class="mt-1 text-gray-900">{{ data.deps or '—' }}</dd>
            </div>
            {% if data.scope %}
            <div>
                <dt class="text-sm font-medium text-gray-500">Project Scope</dt>
                <dd class="mt-1 text-gray-700 whitespace-pre-wrap text-sm bg-gray-50 p-4 rounded-lg max-h-48 overflow-y-auto">{{ data.scope[:500] }}{% if data.scope|length > 500 %}...{% endif %}</dd>
            </div>
            {% endif %}
        </dl>
        <div class="mt-8 flex justify-between">
            <a href="/wizard" class="px-6 py-3 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors text-gray-700 font-medium">
                ← Start Over
            </a>
            <div id="result">
                <button
                    hx-post="/wizard/generate"
                    hx-target="#result"
                    hx-swap="innerHTML"
                    hx-indicator="#gen-spinner"
                    class="px-8 py-3 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors font-medium">
                    <span id="gen-spinner" class="htmx-indicator">⏳ Generating...</span>
                    <span>Generate Project →</span>
                </button>
            </div>
        </div>
    </div>
</div>
{% endblock %}
'''

# ── success.html ────────────────────────────────────────────────────────────────
SUCCESS_HTML = '''{% extends "base.html" %}
{% block title %}Project Generated!{% endblock %}
{% block content %}
<div class="max-w-2xl mx-auto py-16 text-center">
    <!-- Global step indicator -->
    <div class="mb-6 flex items-center justify-center space-x-2 text-sm text-gray-500">
        <span class="font-medium text-green-600">Step 4</span>
        <span>of 4: Done ✓</span>
        <div class="w-32 h-2 bg-gray-200 rounded-full ml-2">
            <div class="h-2 bg-green-500 rounded-full" style="width: 100%"></div>
        </div>
    </div>

    <div class="w-20 h-20 bg-green-100 rounded-2xl flex items-center justify-center mx-auto mb-6">
        <svg class="w-10 h-10 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"/>
        </svg>
    </div>
    <h1 class="text-3xl font-bold text-gray-900 mb-2">Project Generated!</h1>
    <p class="text-gray-600 mb-8">Your scaffolded project is ready to download.</p>
    <a href="/wizard/download/{{ project_name }}" download
        class="inline-flex items-center px-8 py-3 bg-brand-500 text-white rounded-lg hover:bg-brand-600 transition-colors text-lg font-medium shadow-sm">
        <svg class="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"/>
        </svg>
        Download {{ project_name }}.zip
    </a>
    <div class="mt-8 text-left bg-gray-50 p-6 rounded-lg border border-gray-200">
        <h3 class="font-semibold text-gray-900 mb-2">Next Steps</h3>
        <ol class="list-decimal list-inside text-sm text-gray-700 space-y-1">
            <li>Unzip the downloaded project</li>
<li>Run <code class="bg-gray-100 px-1.5 py-0.5 rounded text-brand-600">cp .env.example .env</code></li>
            <li>Run <code class="bg-gray-100 px-1.5 py-0.5 rounded text-brand-600">./scripts/build.sh</code> to install deps + build CSS</li>
            <li>Run <code class="bg-gray-100 px-1.5 py-0.5 rounded text-brand-600">uv run uvicorn app.main:app --reload</code></li>
        </ol>
    </div>
    <div class="mt-6">
        <a href="/wizard" class="text-brand-600 hover:text-brand-700 font-medium">
            Create another project →
        </a>
    </div>
</div>
{% endblock %}
'''


def patch_generate_project():
    """Patch generate_project.py to write scope to SCOPE.md and use it in README."""
    gen_script = REPO / "scripts" / "generate_project.py"
    if not gen_script.exists():
        print("  SKIP: scripts/generate_project.py not found")
        return

    content = gen_script.read_text(encoding="utf-8")

    # Check if already patched
    if "SCOPE.md" in content:
        print("  SKIP: generate_project.py already has SCOPE.md logic")
        return

    # Add scope writing logic at the end of customize_project function
    # Find the last function definition or end of customize_project
    scope_block = '''
    # --- Write scope to SCOPE.md ---
    if args.scope:
        scope_file = output_dir / "SCOPE.md"
        scope_content = f"""# Project Scope

{args.scope}
"""
        scope_file.write_text(scope_content)

        # Also add scope summary to README
        readme = output_dir / "README.md"
        if readme.exists():
            readme_text = readme.read_text()
            scope_snippet = args.scope[:200] + "..." if len(args.scope) > 200 else args.scope
            insert_point = readme_text.find("\\n## ")  # Find first heading after title
            if insert_point == -1:
                insert_point = len(readme_text)
            scope_section = f"\\n\\n## Scope\\n\\n> {scope_snippet}\\n\\nSee [SCOPE.md](SCOPE.md) for the full project scope.\\n"
            readme_text = readme_text[:insert_point] + scope_section + readme_text[insert_point:]
            readme.write_text(readme_text)
'''

    # Insert before the "def init_git" line
    if "def init_git" in content:
        content = content.replace("def init_git", scope_block + "\\n\\ndef init_git")
        gen_script.write_text(content, encoding="utf-8")
        print("  PATCHED: generate_project.py — added SCOPE.md generation + README scope section")
    else:
        print("  WARNING: Could not find insertion point in generate_project.py")


def main():
    print("=" * 60)
    print("ADS Wizard Wiring Patch")
    print("=" * 60)

    print("\\n1. Backing up current files...")
    backup()

    print("\\n2. Writing app/routers/wizard.py...")
    (REPO / "app" / "routers" / "wizard.py").write_text(WIZARD_PY, encoding="utf-8")
    print("   ✓ Written")

    print("\\n3. Writing app/templates/wizard/scope.html...")
    (REPO / "app" / "templates" / "wizard" / "scope.html").write_text(SCOPE_HTML, encoding="utf-8")
    print("   ✓ Written")

    print("\\n4. Writing app/templates/wizard/questions.html...")
    (REPO / "app" / "templates" / "wizard" / "questions.html").write_text(QUESTIONS_HTML, encoding="utf-8")
    print("   ✓ Written")

    print("\\n5. Writing app/templates/wizard/preview.html...")
    (REPO / "app" / "templates" / "wizard" / "preview.html").write_text(PREVIEW_HTML, encoding="utf-8")
    print("   ✓ Written")

    print("\\n6. Writing app/templates/wizard/success.html...")
    (REPO / "app" / "templates" / "wizard" / "success.html").write_text(SUCCESS_HTML, encoding="utf-8")
    print("   ✓ Written")

    print("\\n7. Patching scripts/generate_project.py...")
    patch_generate_project()

    print("\\n" + "=" * 60)
    print("Done! Changes applied.")
    print("Backups saved to: _backup_pre_wire/")
    print("\\nNext steps:")
    print("=" * 60)

if __name__ == "__main__":
    main()
