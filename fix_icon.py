import re
with open('scripts/generate_project.py','r',encoding='utf-8') as f: c=f.read()
t='    (out / "app" / "static" / "css").mkdir(parents=True, exist_ok=True)'
r=t+'''
    (out / "app" / "static" / "img").mkdir(parents=True, exist_ok=True)
    icon_svg = f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">
  <rect width="100" height="100" rx="20" fill="{color}"/>
  <path d="M30 50 L50 30 L70 50 L50 70 Z" fill="white"/>
</svg>"""
    (out / "app" / "static" / "img" / "icon.svg").write_text(icon_svg)'''
c=c.replace(t,r,1)
with open('scripts/generate_project.py','w',encoding='utf-8') as f: f.write(c)
print('Done')
