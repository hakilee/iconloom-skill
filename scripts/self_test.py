#!/usr/bin/env python3
"""Exercise subprocess reproducibility and structural failures with no dependencies."""
import json,subprocess,sys,tempfile
from pathlib import Path
import generate,validate
from pack import build
from quality_check import examples_check

def main():
    specs=[dict(name='petal-check',form='petal',count=5,palette='bloom'),dict(name='arc-check',form='arc',count=3,palette='lagoon'),dict(name='custom-check',palette='mint',shapes=[dict(tag='circle',cx=8,cy=8,r=6),dict(tag='circle',cx=8,cy=10,r=4)])]
    with tempfile.TemporaryDirectory() as tmp:
        root=Path(tmp);spec=root/'designs.json';spec.write_text(json.dumps(specs));expected=None
        for i in range(3):
            out=root/str(i)
            subprocess.run([sys.executable,str(Path(__file__).with_name('generate.py')),'--spec',str(spec),'--out',str(out)],check=True,capture_output=True)
            actual={p.name:p.read_bytes() for p in out.glob('*.svg')}
            if expected is None:expected=actual
            assert actual==expected,'Subprocess output drift'
            subprocess.run([sys.executable,str(Path(__file__).with_name('validate.py')),str(out)],check=True,capture_output=True)
        for bad in [dict(name='../escape'),dict(name='bad',count=0),dict(name='bad',opacity=float('nan')),dict(name='bad',shapes=[dict(tag='image',href='external')])]:
            try:generate.render(bad,'light')
            except (ValueError,KeyError):pass
            else:raise AssertionError('Invalid input accepted')
        broken=root/'broken.svg';broken.write_text(generate.render(specs[0],'light').replace('-paint)','-missing)'))
        assert validate.check(broken)[0],'Broken reference accepted'
        pair=root/'pair';pair.mkdir()
        for theme in ('light','dark'):
            s=generate.render(specs[2],theme)
            if theme=='dark':s=s.replace('r="6"','r="5"')
            (pair/f'custom-check-{theme}.svg').write_text(s)
        result=subprocess.run([sys.executable,str(Path(__file__).with_name('validate.py')),str(pair)],capture_output=True)
        assert result.returncode==1,'Theme mismatch accepted'
        narrow=root/'narrow.svg'
        narrow_spec=dict(name='narrow',shapes=[dict(tag='rect',x=3,y=3,width=10,height=10,rx=2,edge_width=.6)])
        valid=generate.render(narrow_spec,'light');narrow.write_text(valid)
        assert not validate.check(narrow)[0],'Documented narrow edge rejected'
        light_geometry=validate.check(narrow)[1]
        narrow.write_text(generate.render(narrow_spec,'dark'))
        assert light_geometry==validate.check(narrow)[1]
        narrow.write_text(generate.render(narrow_spec,'dark').replace('stroke-width="0.6"','stroke-width="0.5"'))
        assert light_geometry!=validate.check(narrow)[1],'Narrow-edge theme mismatch missed'
        for width in ('0','-0.5','1.1','nan','invalid'):
            narrow.write_text(valid.replace('stroke-width="0.6"','stroke-width="'+width+'"'))
            assert validate.check(narrow)[0],'Invalid edge width accepted: '+width
        narrow.write_text(valid.replace('clip-path="url(#narrow-light-layer-0-clip)"',''))
        assert validate.check(narrow)[0],'Unclipped edge accepted'
        example_root=root/'public';examples=example_root/'examples'
        (examples/'abstract/svg').mkdir(parents=True);(examples/'svg').mkdir();(examples/'specs').mkdir()
        (examples/'abstract/specs.json').write_text(json.dumps([specs[2]]))
        for theme in ('light','dark'):
            (examples/'abstract/svg'/f'custom-check-{theme}.svg').write_text(generate.render(specs[2],theme))
        pack=dict(name='sample',style=dict(mode='outline'),icons=[dict(name='box',shapes=[dict(tag='rect',x=3,y=3,width=10,height=10,rx=2)])])
        source=examples/'specs/box.json';source.write_text(json.dumps(pack))
        files=build(pack)
        for name,svg in files.items():(examples/'svg'/name).write_text(svg)
        assert examples_check(example_root)['passed']
        output=examples/'svg/box-dark.svg';original=output.read_text()
        output.write_text(original.replace('width="16"','width="17"'))
        assert examples_check(example_root)['changed_files']==['svg/box-dark.svg']
        output.unlink()
        assert examples_check(example_root)['changed_files']==['svg/box-dark.svg']
        output.write_text(original)
        extra=examples/'svg/extra.svg';extra.write_text(original)
        assert examples_check(example_root)['changed_files']==['svg/extra.svg']
        extra.unlink();source.unlink()
        assert not examples_check(example_root)['passed'],'Missing source examples accepted'
    for bad in [dict(name='bad', gradient=[0,1,2]), dict(name='bad', relief=.9), dict(name='bad',gradient=[0,float('nan'),1,1])]:
        try:generate.render(bad,'light')
        except ValueError:pass
        else:raise AssertionError('Invalid surface parameter accepted')
    import xml.etree.ElementTree as ET
    ns={'s':'http://www.w3.org/2000/svg'}
    tree=ET.fromstring(generate.render(specs[0],'dark'))
    layers=tree.findall('s:g',ns)
    gradients=tree.findall('s:defs/s:linearGradient',ns)
    assert len(layers)==len(gradients)
    assert all(g.get('gradientUnits')=='objectBoundingBox' for g in gradients)
    for layer in layers:
        fill,edge=list(layer)
        assert edge.get('stroke-width')=='1' and edge.get('clip-path')
        assert all(fill.get(k)==edge.get(k) for k in validate.GEOMETRY-{"opacity"})
    print('PASS: 3 subprocess repeats, 3 shape cases, local-gradient/inset-edge invariants, 9 negative checks; narrow edges, edge-only theme mismatch, 6 invalid edges; public example drift, missing/extra SVGs and missing sources')
if __name__=='__main__':main()
