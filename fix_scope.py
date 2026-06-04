from pathlib import Path

html = """{% extends "base.html" %}
{% block title %}New Project - Scope{% endblock %}
{% block content %}
<div class="ads-page" x-data="{
    fileName: '',
    fileContent: '',
    dragOver: false,
    scopeText: '',
    async handleFile(file) {
        this.fileName = file.name;
        this.fileContent = await file.text();
    },
    async handleDrop(e) {
        this.dragOver = false;
        if (e.dataTransfer.files.length > 0) await this.handleFile(e.dataTransfer.files[0]);
    }
}">
    <div style="margin-bottom: 1.5rem;">
        <span class="ads-badge">Step 1 of 4: Scope</span>
        <div class="ads-progress-track" style="margin-top: 0.75rem;">
            <div class="ads-progress-bar" style="width: 25%"></div>
        </div>
    </div>

    <h1 class="ads-heading">Describe Your Project</h1>
    <p class="ads-sub">Paste a scope document, upload a file, or type what you're building.</p>

    <div class="ads-card" style="margin-top: 1.5rem;">
        <form hx-post="/wizard/save-scope" hx-target="#wizard-feedback" hx-swap="innerHTML" hx-encoding="multipart/form-data">
            <div style="margin-bottom: 1.5rem;">
                <label style="display: block; font-size: 0.8125rem; font-weight: 500; color: var(--text); margin-bottom: 0.5rem;">Upload Scope File <span style="color: var(--text-muted);">(optional - .txt, .md)</span></label>
                <div
                    style="border: 1.5px dashed var(--border); border-radius: var(--r); padding: 1.75rem 1.25rem; text-align: center; cursor: pointer; background: var(--bg-surface); transition: all 0.2s;"
                    :style="dragOver ? 'border-color: var(--accent); background: var(--accent)' + '10' : ''"
                    @dragover.prevent="dragOver = true"
                    @dragleave.prevent="dragOver = false"
                    @drop.prevent="handleDrop($event)"
                    @click="$refs.fileInput.click()"
                >
                    <input type="file" name="scope_file" accept=".txt,.md,.text" x-ref="fileInput"
                        style="display: none;"
                        @change="if ($event.target.files[0]) handleFile($event.target.files[0])">
                    <div x-show="!fileName">
                        <svg style="width: 28px; height: 28px; color: var(--text-muted); margin: 0 auto 0.5rem; display: block;" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12"/>
                        </svg>
                        <p style="font-size: 0.875rem; color: var(--text-dim); margin: 0 0 0.15rem;">Drag a file here or <span style="color: var(--accent-light); font-weight: 500;">browse</span></p>
                        <p style="font-size: 0.75rem; color: var(--text-muted); margin: 0;">Supports .txt and .md files</p>
                    </div>
                    <div x-show="fileName" x-cloak style="display: flex; align-items: center; justify-content: center; gap: 0.75rem;">
                        <svg style="width: 20px; height: 20px; color: #22c55e; flex-shrink: 0;" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"/>
                        </svg>
                        <span style="font-size: 0.875rem; font-weight: 500; color: var(--text);" x-text="fileName"></span>
<button type="button" @click="fileName = ''; fileContent = ''" style="background: none; border: none; color: var(--text-muted); cursor: pointer; padding: 0.2rem;" title="Remove">
                            <svg style="width: 14px; height: 14px;" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/></svg>
                        </button>
                    </div>
                </div>
            </div>

            <div style="margin-bottom: 1.5rem;">
                <label for="scope" style="display: block; font-size: 0.8125rem; font-weight: 500; color: var(--text); margin-bottom: 0.5rem;">Or Type Your Scope <span style="color: var(--text-muted);">(optional if file uploaded)</span></label>
                <textarea id="scope" name="scope" rows="7" class="ads-input"
                    style="resize: vertical; font-family: ui-monospace, SFMono-Regular, monospace; font-size: 0.8125rem; line-height: 1.6;"
                    placeholder="Example: A task management app for remote teams. Users can create projects, assign tasks, set deadlines, and track progress with a Kanban board view."></textarea>
            </div>

            <div style="display: flex; justify-content: flex-end;">
                <button type="submit" class="ads-btn ads-btn-primary">
                    Next: Answer Questions
                    <svg width="14" height="14" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7"/></svg>
                </button>
            </div>
        </form>
    </div>
    <div id="wizard-feedback" style="margin-top: 0.75rem;"></div>
</div>
{% endblock %}"""

p = Path('app/templates/wizard/scope.html')
p.write_text(html, encoding='utf-8')
print(f"Wrote {len(html)} chars to wizard/scope.html")
