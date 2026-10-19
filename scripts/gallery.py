#!/usr/bin/env python3
"""Write a self-contained browser preview at 16, 32 and 128 pixels."""
import argparse,base64,html
from pathlib import Path
ap=argparse.ArgumentParser();ap.add_argument('directory',type=Path);ap.add_argument('--out',type=Path,required=True);a=ap.parse_args()
rows=[]
for p in sorted(a.directory.glob('*-light.svg')):
    name=p.name[:-10];cells=[]
    for theme in ['light','dark']:
        q=a.directory/(name+'-'+theme+'.svg')
        uri='data:image/svg+xml;base64,'+base64.b64encode(q.read_bytes()).decode()
        cells.append('<div class="'+theme+'">'+''.join(f'<img alt="{html.escape(name)} {theme} {s}px" width="{s}" height="{s}" src="{uri}">' for s in (16,32,128))+'</div>')
    rows.append('<article><h2>'+html.escape(name)+'</h2>'+''.join(cells)+'</article>')
a.out.parent.mkdir(parents=True,exist_ok=True)
a.out.write_text('''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width"><title>Iconloom · QA</title><style>body{margin:32px;background:#ededed;color:#252525;font:14px system-ui}main{display:grid;grid-template-columns:repeat(auto-fit,minmax(290px,1fr));gap:16px}article{background:white;padding:16px;border-radius:14px}h2{font-size:15px}.light,.dark{display:flex;align-items:center;justify-content:space-around;padding:12px;min-height:132px}.light{background:#fafafa}.dark{background:#181818}img{display:block}</style><h1>Iconloom</h1><p>Native SVG · 16 / 32 / 128 px · light and dark surfaces</p><main>'''+''.join(rows)+'</main></html>')
print(a.out)
