from pathlib import Path
p = Path('app/templates/base.html')
c = p.read_text(encoding='utf-8')
c = c.replace('    </style>\n</head>', '    </style>\n    {% block extra_head %}{% endblock %}\n</head>')
p.write_text(c, encoding='utf-8')
print("Added extra_head block to base.html")
