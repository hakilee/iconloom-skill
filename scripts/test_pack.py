#!/usr/bin/env python3
"""Pack contracts, theme geometry, stroke containment and isolated runtime checks."""
import copy,json,tempfile,shutil,subprocess,sys
from pathlib import Path
from pack import build
from validate import check
ROOT=Path(__file__).resolve().parents[1]
def main():
    spec=dict(name='probe',brief='A panel with a separate handle',style=dict(mode='layered'),icons=[dict(name='probe',shapes=[dict(tag='rect',x=3,y=5,width=10,height=8,rx=2),dict(tag='path',role='line',d='M5 3 L11 3')])])
    with tempfile.TemporaryDirectory() as td:
        td=Path(td)
        for mode in ('layered','outline','duotone'):
            spec['style']['mode']=mode;files=build(spec);geo=[]
            assert files==build(spec)
            for n,svg in files.items():
                p=td/n;p.write_text(svg);errors,g=check(p,'pack');assert not errors,errors;geo.append(g)
            assert geo[0]==geo[1]
        bad=[]
        def invalid(change):
            s=copy.deepcopy(spec);change(s)
            try:build(s)
            except (ValueError,KeyError,TypeError):bad.append(True)
            else:raise AssertionError('Invalid input was accepted')
        invalid(lambda s:s['style'].update(mode='unknown'))
        invalid(lambda s:s['style'].update(stroke_width=0))
        invalid(lambda s:s['style'].update(light={'ink':'url(https://example.com)'}))
        invalid(lambda s:s['icons'].append(copy.deepcopy(s['icons'][0])))
        invalid(lambda s:s['icons'][0].update(name='../escape'))
        invalid(lambda s:s['icons'][0]['shapes'][0].update(width=0))
        invalid(lambda s:s['icons'][0]['shapes'][1].update(d='M0.6 3 L11 3'))
        invalid(lambda s:s['icons'][0]['shapes'][0].update(tag='path',d='M3 3 L5 5'))
        invalid(lambda s:s['icons'][0]['shapes'][1].update(d='M3 3 H11'))
        invalid(lambda s:s['icons'][0]['shapes'][0].update(gradient=[0,0,1,1]))
        # Real theme stroke mismatch must be detected, independently of color.
        files=build(spec)
        a=td/'a.svg';b=td/'b.svg';a.write_text(files['probe-light.svg']);b.write_text(files['probe-dark.svg'].replace('stroke-width="0.8"','stroke-width="1.1"'))
        assert check(a,'pack')[1]!=check(b,'pack')[1]
        isolated=td/'isolated';(isolated/'scripts').mkdir(parents=True);(isolated/'references').mkdir()
        for n in ('pack.py','generate.py','geometry_audit.py','compose.py','materials.py','keylines.py','construction.py'):
            shutil.copy(ROOT/'scripts'/n,isolated/'scripts'/n)
        shutil.copy(ROOT/'references/palettes.json',isolated/'references/palettes.json')
        inp=td/'spec.json';inp.write_text(json.dumps(spec))
        subprocess.run([sys.executable,str(isolated/'scripts/pack.py'),'--spec',str(inp),'--out',str(td/'isolated-output')],check=True,capture_output=True)
        assert {p.name:p.read_text() for p in (td/'isolated-output').glob('*.svg')}==files
    print('PASS: 3 style modes, deterministic pairs, 10 invalid inputs, stroke mismatch, source-free runtime')
if __name__=='__main__':main()
