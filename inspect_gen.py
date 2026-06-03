# Step 1: Show us what's in generate_project.py
gen = open('scripts/generate_project.py', encoding='utf-8').read()
# Find all function definitions
import re
funcs = re.findall(r'^(def \w+.*)', gen, re.MULTILINE)
print('Functions found:')
for f in funcs:
    print(f'  {f}')
# Show last 30 lines
lines = gen.split('\n')
print(f'\n--- Last 30 lines (total: {len(lines)}) ---')
for l in lines[-30:]:
    print(l)
