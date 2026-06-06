p = r"app\templates\wizard\preview.html"
c = open(p, encoding="utf-8").read()
old = "Project Scope"
new = """Requirements Summary"""
# Find the {% endif %} after Project Scope and insert after it
pos = c.find(old)
if pos > 0:
    # Find the endif closing the scope block
    endif_pos = c.find("{% endif %}", pos)
    if endif_pos > 0:
        endif_pos += len("{% endif %}")
        insert_block = """
            {% if scope_compiled %}
            <div>
                <dt class="ads-label" style="margin-bottom: 0.125rem;">Compiled Scope Document</dt>
                <dd style="position: relative;">
                    <pre style="font-size: 0.75rem; color: var(--text-dim); background: var(--bg-surface); padding: 1rem; border-radius: var(--r-sm); max-height: 24rem; overflow-y: auto; white-space: pre-wrap; line-height: 1.6; border: 1px solid var(--border); font-family: ui-monospace, SFMono-Regular, monospace;">{{ scope_compiled }}</pre>
                    <a href="/wizard/export-markdown" download="scope.md" style="position: absolute; top: 0.625rem; right: 0.625rem; display: inline-flex; align-items: center; gap: 0.375rem; padding: 0.375rem 0.75rem; border-radius: var(--r-sm); background: var(--accent); color: white; font-size: 0.75rem; font-weight: 500; text-decoration: none;">
                        <svg width="14" height="14" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4"/></svg>
                        Export .md
                    </a>
                </dd>
            </div>
            {% endif %}
            {% if answers %}
            <div>
                <details style="border: 1px solid var(--border); border-radius: var(--r-sm); padding: 0.75rem;">
                    <summary style="cursor: pointer; font-size: 0.8125rem; font-weight: 500; color: var(--text-muted);">Requirements Summary</summary>
                    <div style="margin-top: 0.75rem; display: flex; flex-direction: column; gap: 0.625rem;">
                    {% for key, value in answers.items() %}
                        <div>
                            <span style="font-size: 0.6875rem; font-weight: 600; color: var(--text-muted); text-transform: uppercase;">{{ key }}</span>
                            <p style="font-size: 0.8125rem; color: var(--text); margin: 0.125rem 0 0; white-space: pre-wrap;">{{ value[:200] }}{% if value|length > 200 %}...{% endif %}</p>
                        </div>
                    {% endfor %}
                    </div>
                </details>
            </div>
            {% endif %}"""
        c = c[:endif_pos] + insert_block + c[endif_pos:]
        open(p, "w", encoding="utf-8").write(c)
        print("OK - inserted compiled scope + answers after Project Scope block")
    else:
        print("endif not found after Project Scope")
else:
    print("Project Scope not found in preview.html")
