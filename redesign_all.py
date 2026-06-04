from pathlib import Path

T = Path("app/templates")
W = T / "wizard"
W.mkdir(exist_ok=True)

files = {}

files["base.html"] = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{% block title %}{{ app_name }}{% endblock %}</title>
    <script defer src="https://cdn.jsdelivr.net/npm/alpinejs@3.x.x/dist/cdn.min.js"></script>
    <script src="https://unpkg.com/htmx.org@1.9.12" defer></script>
    <link href="/static/css/output.css" rel="stylesheet">
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet">
    <style>
        :root {
            --bg: #0b0d14;
            --bg-nav: #0f1119;
            --bg-surface: #131620;
            --bg-card: #191d2b;
            --bg-elevated: #1f2336;
            --border: rgba(255,255,255,0.06);
            --border-hover: rgba(255,255,255,0.12);
            --text: #e4e6eb;
            --text-dim: #9096a8;
            --text-muted: #5c6278;
            --accent: #6366f1;
            --accent-light: #818cf8;
            --accent-glow: rgba(99,102,241,0.2);
            --gradient: linear-gradient(135deg, #6366f1, #a855f7);
            --cta: #22c55e;
            --cta-hover: #16a34a;
            --danger: #ef4444;
            --r: 12px;
            --r-sm: 8px;
            --r-lg: 16px;
        }
        *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
        body {
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
            background: var(--bg);
            color: var(--text);
            min-height: 100vh;
            display: flex;
            flex-direction: column;
            -webkit-font-smoothing: antialiased;
        }
        main { flex: 1; }

        .nav-shell { background: var(--bg-nav); border-bottom: 1px solid var(--border); position: sticky; top: 0; z-index: 40; }
        .nav-inner { max-width: 1200px; margin: 0 auto; padding: 0 1.25rem; display: flex; justify-content: space-between; align-items: center; height: 52px; }
        .nav-logo { width: 30px; height: 30px; border-radius: 7px; background: var(--gradient); display: flex; align-items: center; justify-content: center; box-shadow: 0 2px 8px var(--accent-glow); }
        .nav-brand { font-weight: 600; font-size: 0.875rem; color: var(--text); text-decoration: none; display: flex; align-items: center; gap: 0.625rem; }
        .nav-brand:hover { color: white; }
        .nav-links { display: flex; align-items: center; gap: 1.25rem; }
        .nav-link { color: var(--text-dim); font-size: 0.8125rem; font-weight: 500; text-decoration: none; transition: color 0.15s; }
        .nav-link:hover { color: var(--text); }
        .nav-user { font-size: 0.75rem; color: var(--text-muted); padding-left: 0.75rem; border-left: 1px solid var(--border); margin-left: 0.25rem; }

        .ads-page { max-width: 680px; margin: 0 auto; padding: 2rem 1.5rem 3rem; }
        .ads-card { background: var(--bg-card); border: 1px solid var(--border); border-radius: var(--r); padding: 1.75rem; }
        .ads-card + .ads-card { margin-top: 0.75rem; }

        .ads-input {
            width: 100%; padding: 0.625rem 0.875rem;
            background: var(--bg-surface); border: 1px solid var(--border); border-radius: var(--r-sm);
            color: var(--text); font-size: 0.875rem; font-family: inherit;
            outline: none; transition: border-color 0.15s, box-shadow 0.15s;
        }
        .ads-input:focus { border-color: var(--accent); box-shadow: 0 0 0 3px var(--accent-glow); }
        .ads-input::placeholder { color: var(--text-muted); }
textarea.ads-input { resize: vertical; min-height: 140px; line-height: 1.6; }

        .ads-btn {
            display: inline-flex; align-items: center; gap: 0.5rem;
            padding: 0.5rem 1.125rem; border-radius: var(--r-sm);
            font-weight: 600; font-size: 0.8125rem; border: none;
            cursor: pointer; text-decoration: none; transition: all 0.15s; line-height: 1.5;
        }
        .ads-btn-primary { background: var(--gradient); color: white; }
        .ads-btn-primary:hover { transform: translateY(-1px); box-shadow: 0 4px 16px var(--accent-glow); }
        .ads-btn-cta { background: var(--cta); color: white; }
        .ads-btn-cta:hover { background: var(--cta-hover); transform: translateY(-1px); box-shadow: 0 4px 12px rgba(34,197,94,0.3); }
        .ads-btn-ghost { background: transparent; color: var(--text-dim); border: 1px solid var(--border); }
        .ads-btn-ghost:hover { border-color: var(--border-hover); color: var(--text); background: rgba(255,255,255,0.03); }
        .ads-btn-lg { padding: 0.625rem 1.5rem; font-size: 0.875rem; }

        .ads-badge {
            display: inline-flex; align-items: center; gap: 0.375rem;
            background: rgba(99,102,241,0.12); color: #a5b4fc;
            padding: 0.2rem 0.625rem; border-radius: 20px;
            font-size: 0.6875rem; font-weight: 500; letter-spacing: 0.02em;
        }
        .ads-badge-green { background: rgba(34,197,94,0.12); color: #86efac; }
        .ads-badge-gray { background: rgba(255,255,255,0.05); color: var(--text-muted); }

        .ads-label { display: block; font-size: 0.8125rem; font-weight: 500; color: var(--text-dim); margin-bottom: 0.375rem; }
        .ads-hint { font-size: 0.75rem; color: var(--text-muted); margin-top: 0.375rem; }
        .ads-hr { height: 1px; background: var(--border); margin: 1.5rem 0; border: none; }
        .ads-heading { font-size: 1.5rem; font-weight: 700; color: white; letter-spacing: -0.02em; }
        .ads-sub { font-size: 0.875rem; color: var(--text-dim); margin-top: 0.25rem; }

        .ads-upload-zone {
            border: 1.5px dashed var(--border-hover); border-radius: var(--r);
            padding: 1.5rem; text-align: center; cursor: pointer;
            background: rgba(255,255,255,0.015); transition: all 0.2s;
        }
        .ads-upload-zone:hover, .ads-upload-zone.dragover {
            border-color: var(--accent-light); background: rgba(99,102,241,0.04);
        }
        .ads-upload-icon {
            width: 28px; height: 28px; color: var(--text-muted);
            margin: 0 auto 0.5rem; display: block;
        }

        .gradient-text {
            background: var(--gradient);
            -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text;
        }
        .ads-progress-track { flex: 1; height: 4px; background: var(--bg-surface); border-radius: 2px; overflow: hidden; }
        .ads-progress-bar { height: 100%; background: var(--gradient); border-radius: 2px; transition: width 0.3s; }

        .footer-shell { background: var(--bg-nav); border-top: 1px solid var(--border); padding: 1.25rem 0; margin-top: auto; }
        .footer-inner { max-width: 1200px; margin: 0 auto; padding: 0 1.25rem; display: flex; align-items: center; justify-content: center; gap: 0.5rem; }
        .footer-logo { width: 18px; height: 18px; border-radius: 5px; background: var(--gradient); display: flex; align-items: center; justify-content: center; }
        .footer-text { font-size: 0.75rem; color: var(--text-muted); }
    </style>
    {% block extra_head %}{% endblock %}
</head>
<body>
    <nav class="nav-shell">
        <div class="nav-inner">
            <a href="/" class="nav-brand">
                <div class="nav-logo">
                    <svg width="14" height="14" viewBox="0 0 92 92" fill="none">
                        <path d="M26 70 L46 20 L66 70" stroke="white" stroke-width="6" stroke-linecap="round" stroke-linejoin="round"/>
                        <polygon points="43,48 43,60 54,54" fill="white" opacity="0.9"/>
</svg>
                </div>
                Auto Studio
            </a>
            <div class="nav-links">
                <a href="/wizard" class="nav-link">New Project</a>
                {% if user %}
                <a href="/dashboard" class="nav-link">Dashboard</a>
                <a href="/logout" class="nav-link">Logout</a>
                <span class="nav-user">{{ user.name }}</span>
                {% else %}
                <a href="/login" class="nav-link">Sign In</a>
                {% endif %}
            </div>
        </div>
    </nav>
    <main>{% block content %}{% endblock %}</main>
    <footer class="footer-shell">
        <div class="footer-inner">
            <div class="footer-logo">
                <svg width="8" height="8" viewBox="0 0 92 92" fill="none">
                    <path d="M26 70 L46 20 L66 70" stroke="white" stroke-width="6" stroke-linecap="round" stroke-linejoin="round"/>
                    <polygon points="43,48 43,60 54,54" fill="white" opacity="0.9"/>
                </svg>
            </div>
            <span class="footer-text">Auto Studio &middot; Building Apps with AI</span>
        </div>
    </footer>
</body>
</html>"""

files["index.html"] = """{% extends "base.html" %}
{% block title %}{{ app_name }}{% endblock %}
{% block extra_head %}
<style>
.hero { text-align: center; padding: 5rem 1.5rem 4rem; max-width: 720px; margin: 0 auto; }
.hero-logo { width: 48px; height: 48px; border-radius: 12px; background: var(--gradient); display: flex; align-items: center; justify-content: center; margin: 0 auto 1.25rem; box-shadow: 0 8px 32px var(--accent-glow); }
.hero h1 { font-size: 2.75rem; font-weight: 800; letter-spacing: -0.03em; line-height: 1.15; color: white; margin-bottom: 1rem; }
.hero p { font-size: 1.0625rem; color: var(--text-dim); line-height: 1.6; margin-bottom: 2rem; max-width: 540px; margin-left: auto; margin-right: auto; }
.hero-cta { display: flex; justify-content: center; gap: 0.75rem; }
.features { max-width: 900px; margin: 0 auto; padding: 0 1.5rem 4rem; }
.features-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 1rem; }
.feat-card { background: var(--bg-card); border: 1px solid var(--border); border-radius: var(--r); padding: 1.5rem; }
.feat-icon { width: 36px; height: 36px; border-radius: 8px; display: flex; align-items: center; justify-content: center; margin-bottom: 0.75rem; }
.feat-title { font-size: 0.9375rem; font-weight: 600; color: white; margin-bottom: 0.375rem; }
.feat-desc { font-size: 0.8125rem; color: var(--text-dim); line-height: 1.5; }
@media (max-width: 640px) { .features-grid { grid-template-columns: 1fr; } .hero h1 { font-size: 2rem; } }
</style>
{% endblock %}
{% block content %}
<section class="hero">
    <div class="hero-logo">
        <svg width="22" height="22" viewBox="0 0 92 92" fill="none">
            <path d="M26 70 L46 20 L66 70" stroke="white" stroke-width="6" stroke-linecap="round" stroke-linejoin="round"/>
            <polygon points="43,48 43,60 54,54" fill="white" opacity="0.9"/>
        </svg>
    </div>
    <h1>Build your next app<br><span class="gradient-text">in minutes, not days</span></h1>
    <p>Describe what you want, upload a scope doc, or both. Auto Studio generates a complete, production-ready FastAPI + Tailwind application &mdash; with auth, database, and deployment config built in.</p>
    <div class="hero-cta">
        <a href="/wizard" class="ads-btn ads-btn-primary ads-btn-lg">
            <svg width="16" height="16" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4"/></svg>
            Start New Project
        </a>
        {% if user %}
        <a href="/dashboard" class="ads-btn ads-btn-ghost ads-btn-lg">View Dashboard</a>
        {% endif %}
    </div>
</section>

<section class="features">
    <div class="features-grid">
        <div class="feat-card">
            <div class="feat-icon" style="background: rgba(99,102,241,0.12);">
<svg width="18" height="18" fill="none" stroke="#818cf8" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z"/></svg>
            </div>
            <div class="feat-title">AI-Powered Generation</div>
            <div class="feat-desc">Describe your vision in natural language. Our AI scaffolds the full project structure, routes, and models.</div>
        </div>
        <div class="feat-card">
            <div class="feat-icon" style="background: rgba(168,85,247,0.12);">
                <svg width="18" height="18" fill="none" stroke="#c084fc" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 21a4 4 0 01-4-4V5a2 2 0 012-2h4a2 2 0 012 2v12a4 4 0 01-4 4zm0 0h12a2 2 0 002-2v-4a2 2 0 00-2-2h-2.343M11 7.343l1.657-1.657a2 2 0 012.828 0l2.829 2.829a2 2 0 010 2.828l-8.486 8.485M7 17h.01"/></svg>
            </div>
            <div class="feat-title">Brand Studio</div>
            <div class="feat-desc">Drop in reference images and AI extracts your color palette, typography, and UI style into a complete design system.</div>
        </div>
        <div class="feat-card">
            <div class="feat-icon" style="background: rgba(34,197,94,0.12);">
                <svg width="18" height="18" fill="none" stroke="#4ade80" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4"/></svg>
            </div>
            <div class="feat-title">Download & Deploy</div>
            <div class="feat-desc">Get a ready-to-run zip with Dockerfile, env config, and build scripts. Push to your favorite host in seconds.</div>
        </div>
    </div>
</section>
{% endblock %}"""

files["wizard/scope.html"] = """{% extends "base.html" %}
{% block title %}New Project - Scope{% endblock %}
{% block content %}
<div class="ads-page" x-data="{ dragOver: false, fileName: '', fileContent: '', async handleFile(file) { this.fileName = file.name; this.fileContent = await file.text(); }, async handleDrop(e) { this.dragOver = false; const files = e.dataTransfer.files; if (files.length > 0) await this.handleFile(files[0]); } }">
    <div style="margin-bottom: 1.5rem;">
        <span class="ads-badge">Step 1 of 4</span>
        <div style="display: flex; align-items: center; gap: 0.5rem; margin-top: 0.75rem;">
            <div class="ads-progress-track">
                <div class="ads-progress-bar" style="width: 25%"></div>
            </div>
        </div>
    </div>

    <h1 class="ads-heading">Describe your project</h1>
    <p class="ads-sub">Paste a scope document, upload a file, or just type what you're building.</p>

    <div style="margin-top: 1.5rem;">
        <div class="ads-card">
            <form hx-post="/wizard/save-scope" hx-target="#wizard-feedback" hx-swap="innerHTML" hx-encoding="multipart/form-data">
                <div style="margin-bottom: 1.25rem;">
                    <label class="ads-label">Upload Scope File <span style="color: var(--text-muted); font-weight: 400;">(optional &mdash; .txt, .md)</span></label>
                    <div class="ads-upload-zone" :class="dragOver ? 'dragover' : ''" @dragover.prevent="dragOver = true" @dragleave.prevent="dragOver = false" @drop.prevent="handleDrop()">
                        <input type="file" name="scope_file" accept=".txt,.md,.text" style="position: absolute; inset: 0; width: 100%; height: 100%; opacity: 0; cursor: pointer;" @change="if ($event.target.files[0]) handleFile($event.target.files[0])">
                        <div x-show="!fileName">
                            <svg class="ads-upload-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z"/>
                            </svg>
<p style="color: var(--text-dim); font-size: 0.875rem; margin: 0;">Drop file or <span style="color: var(--accent-light); font-weight: 500;">click to browse</span></p>
                            <p style="color: var(--text-muted); font-size: 0.75rem; margin-top: 0.2rem;">Supports .txt and .md</p>
                        </div>
                        <div x-show="fileName" style="display: flex; align-items: center; justify-content: center; gap: 0.75rem;">
                            <svg width="24" height="24" fill="none" stroke="var(--cta)" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"/></svg>
                            <div style="text-align: left;">
                                <p style="font-weight: 600; font-size: 0.875rem;" x-text="fileName"></p>
                                <p style="font-size: 0.75rem; color: var(--text-muted);">Ready to upload</p>
                            </div>
                            <button type="button" @click="fileName = ''; fileContent = ''" style="background: none; border: none; color: var(--text-muted); cursor: pointer; padding: 0.25rem;">
                                <svg width="16" height="16" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/></svg>
                            </button>
                        </div>
                    </div>
                </div>

                <div style="margin-bottom: 1.25rem;">
                    <label for="scope" class="ads-label">Or Type Your Scope <span style="color: var(--text-muted); font-weight: 400;">(optional if file uploaded)</span></label>
                    <textarea id="scope" name="scope" class="ads-input" placeholder="Example: A task management app for remote teams. Users can create projects, assign tasks, set deadlines, and track progress with a Kanban board."></textarea>
                </div>

                <button type="submit" class="ads-btn ads-btn-primary ads-btn-lg">
                    Next: Answer Questions
                    <svg width="14" height="14" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7"/></svg>
                </button>
            </form>
        </div>
        <div id="wizard-feedback" style="margin-top: 0.75rem;"></div>
    </div>
</div>
{% endblock %}"""

files["wizard/questions.html"] = """{% extends "base.html" %}
{% block title %}New Project - Details{% endblock %}
{% block content %}
<div class="ads-page" x-data="{ currentStep: 1, totalSteps: 6 }">
    <div style="margin-bottom: 1.5rem;">
        <div style="display: flex; align-items: center; gap: 0.5rem; margin-bottom: 0.75rem;">
            <span class="ads-badge">Step 2 of 4</span>
            <span class="ads-badge-gray ads-badge" x-text="'Q' + currentStep + '/' + totalSteps"></span>
        </div>
        <div class="ads-progress-track">
            <div class="ads-progress-bar" style="width: 50%"></div>
        </div>
    </div>

    {% if scope %}
    <div class="ads-card" style="padding: 0.75rem 1rem; margin-bottom: 1rem; display: flex; align-items: center; justify-content: space-between;">
        <span style="font-size: 0.8125rem; color: var(--accent-light); font-weight: 500;">Scope captured &#10003;</span>
        <span style="font-size: 0.75rem; color: var(--text-muted); max-width: 60%; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">{{ scope[:80] }}{% if scope|length > 80 %}...{% endif %}</span>
    </div>
    {% endif %}

    <h1 class="ads-heading">Project Details</h1>
    <p class="ads-sub">A few quick questions to customize your scaffold.</p>

    <form hx-post="/wizard/save-answers" hx-target="#wizard-content" hx-swap="innerHTML" x-ref="form" style="margin-top: 1.5rem;">

<div class="ads-card" x-show="currentStep === 1">
            <h2 style="font-size: 1.0625rem; font-weight: 600; color: white; margin-bottom: 0.25rem;">Project Name</h2>
            <p style="font-size: 0.8125rem; color: var(--text-dim); margin-bottom: 0.75rem;">What's the name of your project?</p>
            <input type="text" name="project_name" required class="ads-input" placeholder="e.g. TaskFlow">
        </div>

        <div class="ads-card" x-show="currentStep === 2">
            <h2 style="font-size: 1.0625rem; font-weight: 600; color: white; margin-bottom: 0.25rem;">Tagline</h2>
            <p style="font-size: 0.8125rem; color: var(--text-dim); margin-bottom: 0.75rem;">A short description for your app's hero section.</p>
            <input type="text" name="tagline" class="ads-input" placeholder="e.g. Task management for remote teams">
        </div>

        <div class="ads-card" x-show="currentStep === 3">
            <h2 style="font-size: 1.0625rem; font-weight: 600; color: white; margin-bottom: 0.25rem;">Brand Color</h2>
            <p style="font-size: 0.8125rem; color: var(--text-dim); margin-bottom: 0.75rem;">Pick a primary accent color for your app's theme.</p>
            <div style="display: flex; align-items: center; gap: 0.75rem;">
                <input type="color" name="brand_color" value="#6366f1" style="width: 48px; height: 48px; border-radius: 10px; border: 1px solid var(--border); cursor: pointer; background: var(--bg-surface);">
                <span style="font-size: 0.75rem; color: var(--text-muted);">A full palette will be generated from this hex.</span>
            </div>
        </div>

        <div class="ads-card" x-show="currentStep === 4">
            <h2 style="font-size: 1.0625rem; font-weight: 600; color: white; margin-bottom: 0.75rem;">Features</h2>
            <div style="display: flex; flex-direction: column; gap: 0.75rem;">
                <label style="display: flex; align-items: flex-start; gap: 0.625rem; cursor: pointer; padding: 0.625rem; border-radius: var(--r-sm); border: 1px solid var(--border); background: var(--bg-surface);">
                    <input type="checkbox" name="enable_auth" value="yes" style="margin-top: 0.15rem; accent-color: var(--accent); width: 1rem; height: 1rem;">
                    <div>
                        <span style="font-weight: 500; font-size: 0.875rem; color: var(--text);">Google OAuth</span>
                        <p style="font-size: 0.75rem; color: var(--text-dim); margin-top: 0.1rem;">User authentication with Google sign-in</p>
                    </div>
                </label>
                <label style="display: flex; align-items: flex-start; gap: 0.625rem; cursor: pointer; padding: 0.625rem; border-radius: var(--r-sm); border: 1px solid var(--border); background: var(--bg-surface);">
                    <input type="checkbox" name="enable_database" value="yes" checked style="margin-top: 0.15rem; accent-color: var(--accent); width: 1rem; height: 1rem;">
                    <div>
                        <span style="font-weight: 500; font-size: 0.875rem; color: var(--text);">Database</span>
                        <p style="font-size: 0.75rem; color: var(--text-dim); margin-top: 0.1rem;">SQLite + SQLAlchemy models</p>
                    </div>
                </label>
            </div>
        </div>

        <div class="ads-card" x-show="currentStep === 5">
            <h2 style="font-size: 1.0625rem; font-weight: 600; color: white; margin-bottom: 0.25rem;">Pages</h2>
            <p style="font-size: 0.8125rem; color: var(--text-dim); margin-bottom: 0.75rem;">Page routes to pre-create (comma-separated).</p>
            <input type="text" name="pages" class="ads-input" placeholder="e.g. about, pricing, contact, features">

            <div style="margin-top: 1.25rem;">
                <h2 style="font-size: 1.0625rem; font-weight: 600; color: white; margin-bottom: 0.25rem;">Extra Dependencies</h2>
<p style="font-size: 0.8125rem; color: var(--text-dim); margin-bottom: 0.75rem;">Additional PyPI packages (comma-separated).</p>
                <input type="text" name="extra_deps" class="ads-input" placeholder="e.g. httpx, pandas, celery">
            </div>
        </div>

        <div class="ads-card" x-show="currentStep === 6">
            <h2 style="font-size: 1.0625rem; font-weight: 600; color: white; margin-bottom: 0.25rem;">Almost Done!</h2>
            <p style="font-size: 0.8125rem; color: var(--text-dim);">Review your answers on the next page, then generate.</p>
        </div>

        <div style="display: flex; justify-content: space-between; align-items: center; margin-top: 1.25rem;">
            <button type="button" @click="currentStep--" x-show="currentStep > 1" class="ads-btn ads-btn-ghost">
                <svg width="14" height="14" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7"/></svg>
                Back
            </button>
            <div style="display: flex; gap: 0.5rem;">
                <a href="/wizard" class="ads-btn ads-btn-ghost">Start Over</a>
                <button type="button" @click="currentStep++" x-show="currentStep < totalSteps" class="ads-btn ads-btn-primary">
                    Next
                    <svg width="14" height="14" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7"/></svg>
                </button>
                <button type="submit" x-show="currentStep === totalSteps" class="ads-btn ads-btn-cta ads-btn-lg">
                    Review &amp; Generate
                    <svg width="14" height="14" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7"/></svg>
                </button>
            </div>
        </div>
    </form>
    <div id="wizard-content" style="margin-top: 0.75rem;"></div>
</div>
{% endblock %}"""

files["wizard/preview.html"] = """{% extends "base.html" %}
{% block title %}Review Your Project{% endblock %}
{% block content %}
<div class="ads-page">
    <div style="margin-bottom: 1.5rem;">
        <span class="ads-badge">Step 3 of 4</span>
        <div class="ads-progress-track" style="margin-top: 0.75rem;">
            <div class="ads-progress-bar" style="width: 75%"></div>
        </div>
    </div>

    <h1 class="ads-heading">Review Your Project</h1>
    <p class="ads-sub">Make sure everything looks right before generating.</p>

    <div class="ads-card" style="margin-top: 1.5rem;">
        <dl style="display: flex; flex-direction: column; gap: 1rem;">
            <div>
                <dt class="ads-label" style="margin-bottom: 0.125rem;">Project Name</dt>
                <dd style="font-size: 1rem; font-weight: 600; color: white;">{{ data.name }}</dd>
            </div>
            <div>
                <dt class="ads-label" style="margin-bottom: 0.125rem;">Tagline</dt>
                <dd style="font-size: 0.875rem; color: var(--text);">{{ data.tagline or "?" }}</dd>
            </div>
            <div>
                <dt class="ads-label" style="margin-bottom: 0.125rem;">Brand Color</dt>
                <dd style="display: flex; align-items: center; gap: 0.5rem;">
                    <span style="width: 24px; height: 24px; border-radius: 6px; background: {{ data.color }}; box-shadow: 0 2px 6px rgba(0,0,0,0.3);"></span>
                    <span style="font-size: 0.875rem; color: var(--text);">{{ data.color }}</span>
                </dd>
            </div>
            <div>
                <dt class="ads-label" style="margin-bottom: 0.125rem;">Google OAuth</dt>
                <dd>{% if data.with_auth == 'yes' %}<span class="ads-badge ads-badge-green">Enabled</span>{% else %}<span class="ads-badge ads-badge-gray">Disabled</span>{% endif %}</dd>
            </div>
            <div>
<dt class="ads-label" style="margin-bottom: 0.125rem;">Database</dt>
                <dd>{% if data.with_db == 'yes' %}<span class="ads-badge ads-badge-green">Enabled</span>{% else %}<span class="ads-badge ads-badge-gray">Disabled</span>{% endif %}</dd>
            </div>
            <div>
                <dt class="ads-label" style="margin-bottom: 0.125rem;">Pages</dt>
                <dd style="font-size: 0.875rem; color: var(--text);">{{ data.pages or "?" }}</dd>
            </div>
            <div>
                <dt class="ads-label" style="margin-bottom: 0.125rem;">Extra Dependencies</dt>
                <dd style="font-size: 0.875rem; color: var(--text);">{{ data.deps or "?" }}</dd>
            </div>
            {% if data.scope %}
            <div>
                <dt class="ads-label" style="margin-bottom: 0.125rem;">Project Scope</dt>
                <dd style="font-size: 0.8125rem; color: var(--text-dim); background: var(--bg-surface); padding: 0.75rem; border-radius: var(--r-sm); max-height: 10rem; overflow-y: auto; white-space: pre-wrap; line-height: 1.5;">{{ data.scope[:500] }}{% if data.scope|length > 500 %}...{% endif %}</dd>
            </div>
            {% endif %}
        </dl>

        <div class="ads-hr"></div>

        <div style="display: flex; justify-content: space-between; align-items: center;">
            <a href="/wizard" class="ads-btn ads-btn-ghost">
                <svg width="14" height="14" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7"/></svg>
                Start Over
            </a>
            <div id="result">
                <button hx-post="/wizard/generate" hx-target="#result" hx-swap="innerHTML" hx-indicator="#gen-spinner" class="ads-btn ads-btn-cta ads-btn-lg">
                    <span id="gen-spinner" class="htmx-indicator" style="display: none;">Generating...</span>
                    <span>Generate Project</span>
                    <svg width="14" height="14" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7"/></svg>
                </button>
            </div>
        </div>
    </div>
</div>
{% endblock %}"""

files["wizard/success.html"] = """{% extends "base.html" %}
{% block title %}Project Generated!{% endblock %}
{% block content %}
<div class="ads-page" style="text-align: center; padding-top: 3rem;">
    <div style="margin-bottom: 1.5rem;">
        <span class="ads-badge ads-badge-green">Step 4 of 4 ? Done &#10003;</span>
        <div class="ads-progress-track" style="margin-top: 0.75rem;">
            <div class="ads-progress-bar" style="width: 100%; background: linear-gradient(135deg, #22c55e, #4ade80);"></div>
        </div>
    </div>

    <div style="width: 48px; height: 48px; border-radius: 12px; background: rgba(34,197,94,0.12); display: flex; align-items: center; justify-content: center; margin: 0 auto 1.25rem;">
        <svg width="24" height="24" fill="none" stroke="#4ade80" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"/></svg>
    </div>

    <h1 class="ads-heading" style="margin-bottom: 0.25rem;">Project Generated!</h1>
    <p class="ads-sub">Your scaffolded project is ready to download.</p>

    <div style="margin-top: 1.5rem;">
        <a href="/wizard/download/{{ project_name }}" download class="ads-btn ads-btn-primary ads-btn-lg" style="padding: 0.75rem 2rem; font-size: 0.9375rem;">
            <svg width="16" height="16" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"/></svg>
            Download {{ project_name }}.zip
        </a>
    </div>

    <div class="ads-card" style="text-align: left; margin-top: 2rem;">
<h3 style="font-size: 0.875rem; font-weight: 600; color: white; margin-bottom: 0.75rem;">Next Steps</h3>
        <ol style="padding-left: 1.25rem; display: flex; flex-direction: column; gap: 0.375rem;">
            <li style="font-size: 0.8125rem; color: var(--text-dim);">Unzip the downloaded project</li>
            <li style="font-size: 0.8125rem; color: var(--text-dim);">Run <code style="background: var(--bg-surface); padding: 0.125rem 0.375rem; border-radius: 4px; font-size: 0.75rem; color: var(--accent-light);">cp .env.example .env</code></li>
            <li style="font-size: 0.8125rem; color: var(--text-dim);">Run <code style="background: var(--bg-surface); padding: 0.125rem 0.375rem; border-radius: 4px; font-size: 0.75rem; color: var(--accent-light);">./scripts/build.sh</code> to install deps + build CSS</li>
            <li style="font-size: 0.8125rem; color: var(--text-dim);">Run <code style="background: var(--bg-surface); padding: 0.125rem 0.375rem; border-radius: 4px; font-size: 0.75rem; color: var(--accent-light);">uv run uvicorn app.main:app --reload</code></li>
        </ol>
    </div>

    <div style="margin-top: 1.5rem;">
        <a href="/wizard" class="ads-btn ads-btn-ghost">Create another project &rarr;</a>
    </div>
</div>
{% endblock %}"""

for name, content in files.items():
    p = T / name
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content.lstrip("\n"), encoding="utf-8")
    print(f"  Wrote {name} ({len(content)} chars)")

print(f"\nAll {len(files)} templates rewritten with dark design system.")
