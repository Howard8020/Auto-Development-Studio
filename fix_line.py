lines = open('_wire_scope_upload.py', encoding='utf-8').readlines()
fixed = [l for l in lines if not ('python -c' in l and 'ast.parse' in l) and not ('git add -A' in l) and not ('git push' in l) and not ('git diff' in l)]
open('_wire_scope_upload.py', 'w', encoding='utf-8').writelines(fixed)
print('Fixed')
