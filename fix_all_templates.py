from pathlib import Path

P = Path('app/templates')

# ============================================================
# PART 1: Patch base.html ? inject ads-* design tokens + dark nav
# ============================================================
base = (P / 'base.html').read_text(encoding='utf-8').lstrip('\ufeff')

# The tokens + overrides to inject into <head>
TOKENS = """
    <style>
    /* === ADS Design Tokens (dark glass) === */
    :root {
        --bg: #0f1117;
        --bg-surface: rgba(255,255,255,0.03);
        --bg-card: rgba(255,255,255,0.025);
        --text: #e2e4ea;
        --text-dim: rgba(255,255,255,0.55);
        --text-muted: rgba(255,255,255,0.35);
        --accent: #6366f1;
        --accent-light: #a5b4fc;
        --accent-glow: rgba(99,102,241,0.35);
        --gradient: linear-gradient(135deg, #6366f1, #8b5cf6);
        --border: rgba(255,255,255,0.08);
        --r: 12px;
        --r-sm: 8px;
    }
    body { background: var(--bg) !important; color: var(--text) !important; }
    .ads-page { max-width: 640px; margin: 0 auto; padding: 2.5rem 1.5rem 3rem; }
    .ads-heading { font-size: 1.75rem; font-weight: 700; color: white; margin-bottom: 0.25rem; letter-spacing: -0.02em; }
    .ads-sub { font-size: 0.9rem; color: var(--text-dim); margin-bottom: 1.5rem; }
    .ads-card { background: var(--bg-card); border: 1px solid var(--border); border-radius: var(--r); padding: 1.25rem; margin-bottom: 1rem; }
    .ads-input { width: 100%; padding: 0.7rem 0.875rem; background: var(--bg-surface); color: var(--text); border: 1px solid var(--border); border-radius: var(--r-sm); font-size: 0.875rem; outline: none; transition: border-color 0.15s; }
    .ads-input:focus { border-color: var(--accent); }
    .ads-input::placeholder { color: var(--text-muted); }
    .ads-btn { display: inline-flex; align-items: center; gap: 0.4rem; padding: 0.55rem 1.1rem; border-radius: var(--r-sm); font-weight: 600; font-size: 0.875rem; text-decoration: none; cursor: pointer; border: none; transition: all 0.15s; }
    .ads-btn-lg { padding: 0.7rem 1.4rem; font-size: 0.9375rem; }
    .ads-btn-primary { background: var(--gradient); color: white; }
    .ads-btn-primary:hover { transform: translateY(-1px); box-shadow: 0 4px 16px var(--accent-glow); }
    .ads-btn-cta { background: linear-gradient(135deg, #22c55e, #16a34a); color: white; box-shadow: 0 4px 16px rgba(34,197,94,0.25); }
    .ads-btn-cta:hover { transform: translateY(-1px); box-shadow: 0 6px 20px rgba(34,197,94,0.4); }
    .ads-btn-ghost { background: var(--bg-surface); color: var(--text-dim); border: 1px solid var(--border); }
    .ads-btn-ghost:hover { background: rgba(255,255,255,0.06); color: white; }
    .ads-badge { display: inline-flex; align-items: center; padding: 0.25rem 0.7rem; border-radius: 20px; font-size: 0.7rem; font-weight: 600; background: rgba(99,102,241,0.12); color: var(--accent-light); letter-spacing: 0.02em; }
    .ads-badge-gray { background: rgba(255,255,255,0.05); color: var(--text-muted); }
    .ads-badge-green { background: rgba(34,197,94,0.12); color: #4ade80; }
    .ads-progress-track { height: 4px; background: rgba(255,255,255,0.06); border-radius: 2px; overflow: hidden; }
    .ads-progress-bar { height: 100%; background: var(--gradient); border-radius: 2px; transition: width 0.3s; }
    .ads-hr { height: 1px; background: var(--border); margin: 1.25rem 0; }
.ads-label { font-size: 0.65rem; font-weight: 600; color: var(--text-muted); text-transform: uppercase; letter-spacing: 0.08em; }
    .gradient-text { background: var(--gradient); -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text; }
    /* Dark nav override */
    nav { background: rgba(15,17,23,0.9) !important; backdrop-filter: blur(12px) !important; border-color: var(--border) !important; }
    nav a { color: var(--text-dim) !important; }
    nav a:hover { color: white !important; }
    footer { background: rgba(15,17,23,0.8) !important; border-color: var(--border) !important; color: var(--text-muted) !important; }
    footer * { color: inherit !important; }
    </style>
"""

if '<!-- ADS_TOKENS -->' not in base:
    base = base.replace('    {% block extra_head %}', '    <!-- ADS_TOKENS -->\n' + TOKENS + '\n    {% block extra_head %}')
    (P / 'base.html').write_text(base, encoding='utf-8')
    print("[1/2] Patched base.html with ads-* tokens")
else:
    print("[1/2] base.html already has tokens, skipping")

# ============================================================
# PART 2: Rewrite scope.html to use ads-* classes (match others)
# ============================================================
scope_new = r'''{% extends "base.html" %}
{% block title %}New Project ? Scope{% endblock %}
{% block content %}
<div class="ads-page" x-data="{ fileName: '', fileContent: '', dragOver: false }">
    <div style="margin-bottom: 1.5rem;">
        <span class="ads-badge">Step 1 of 4: Scope</span>
        <div class="ads-progress-track" style="margin-top: 0.75rem;">
            <div class="ads-progress-bar" style="width: 25%"></div>
        </div>
    </div>

    <h1 class="ads-heading">Describe your project</h1>
    <p class="ads-sub">Paste a scope document, upload a file, or just type what you're building.</p>

    <div class="ads-card">
        <form hx-post="/wizard/save-scope" hx-target="#wizard-feedback" hx-swap="innerHTML" hx-encoding="multipart/form-data">

            <label class="ads-label" style="margin-bottom: 0.5rem; display: block;">Upload Scope File <span style="color: var(--text-muted); font-weight: 400; text-transform: none;">(optional ? .txt, .md)</span></label>
            <div
                style="border: 1.5px dashed var(--border); border-radius: var(--r-sm); padding: 1.5rem; text-align: center; background: var(--bg-surface); transition: all 0.2s; cursor: pointer; position: relative;"
                :style="dragOver ? 'border-color: var(--accent); background: rgba(99,102,241,0.06);' : ''"
                @dragover.prevent="dragOver = true"
                @dragleave.prevent="dragOver = false"
                @drop.prevent="dragOver = false; if ($event.dataTransfer.files[0]) { fileName = $event.dataTransfer.files[0].name; readFile($event.dataTransfer.files[0]); }"
                @click="$refs.fileInput.click()"
            >
                <input type="file" name="scope_file" accept=".txt,.md,.text" x-ref="fileInput" style="display: none"
                    @change="if ($event.target.files[0]) { fileName = $event.target.files[0].name; readFile($event.target.files[0]); }">
                <div x-show="!fileName">
                    <svg style="width: 28px; height: 28px; color: var(--text-muted); margin-bottom: 0.5rem;" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12"/>
                    </svg>
                    <p style="color: var(--text-dim); font-size: 0.875rem; margin: 0;">Drop or <span style="color: var(--accent-light); font-weight: 500;">click to browse</span></p>
                    <p style="color: var(--text-muted); font-size: 0.75rem; margin: 0.25rem 0 0;">Supports .txt and .md files</p>
                </div>
                <div x-show="fileName" x-cloak style="display: none;">
<div style="display: inline-flex; align-items: center; gap: 0.625rem;">
                        <svg style="width: 20px; height: 20px; color: #4ade80;" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"/>
                        </svg>
                        <span style="font-size: 0.875rem; font-weight: 500; color: white;" x-text="fileName"></span>
                        <button type="button" @click.stop="fileName = ''; fileContent = ''; $refs.fileInput.value = ''" style="color: var(--text-muted); background: none; border: none; cursor: pointer; padding: 2px;">
                            <svg style="width: 14px; height: 14px;" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/></svg>
                        </button>
                    </div>
                </div>
            </div>

            <label class="ads-label" style="margin: 1.25rem 0 0.5rem; display: block;">Or Type Your Scope <span style="color: var(--text-muted); font-weight: 400; text-transform: none;">(optional if file uploaded)</span></label>
            <textarea name="scope" rows="8" class="ads-input" style="resize: vertical; font-family: ui-monospace, SFMono-Regular, monospace; font-size: 0.8125rem; line-height: 1.5;"
                placeholder="Example: A task management app for remote teams. Users can create projects, assign tasks, set deadlines, and track progress with a Kanban board view."></textarea>

            <div style="margin-top: 1.5rem;">
                <button type="submit" class="ads-btn ads-btn-primary ads-btn-lg">
                    Next: Answer Questions
                    <svg width="14" height="14" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7"/></svg>
                </button>
            </div>
        </form>
    </div>
    <div id="wizard-feedback" style="margin-top: 0.75rem;"></div>
</div>

<script>
function readFile(file) {
    const reader = new FileReader();
    reader.onload = e => {
        const ta = document.querySelector('textarea[name="scope"]');
        if (ta) ta.value = e.target.result;
    };
    reader.readAsText(file);
}
</script>
{% endblock %}
'''

(P / 'wizard' / 'scope.html').write_text(scope_new.lstrip('\ufeff'), encoding='utf-8')
print("[2/2] Rewrote wizard/scope.html with ads-* tokens")
print("\nDone. Ctrl+Shift+R on all pages to see the consistent dark theme.")
