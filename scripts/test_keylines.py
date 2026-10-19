"""Grid invariants: constant stroke, aspect ratio, rotated ownership and safety."""
import copy,math,tempfile
from pathlib import Path
from keylines import apply,bounds,move_shape,BOXES
from geometry_audit import contours
from pack import build,prepare
from validate import check

def main():
    # Rotation-aware transform must be the same world-space similarity for every point.
    for shape in [dict(tag='rect',x=5,y=3,width=3,height=8,rx=1,rotate=37),
                  dict(tag='ellipse',cx=7,cy=6,rx=2,ry=3,rotate=-26),
                  dict(tag='path',d='M4 3 C9 2 12 7 10 12 L4 12 Z',rotate=19)]:
        moved=move_shape(shape,1.2,.25,-.2)
        a=[p for c in contours(shape) for p in c];b=[p for c in contours(moved) for p in c]
        assert len(a)==len(b)
        assert max(math.dist(q,(8+(p[0]-8)*1.2+.25,8+(p[1]-8)*1.2-.2)) for p,q in zip(a,b))<1e-6
    # Clipped child extending beyond a parent must not change silhouette fitting.
    body=dict(tag='rect',x=3,y=4,width=9,height=8,rx=2,rotate=15)
    child=dict(tag='rect',x=2,y=4,width=4,height=8,rx=1)
    sh=[body,child];roles=['body','surface'];meta=[{'id':'body'},{'id':'shine','parent':'body'}]
    sty=dict(mode='layered',grid='keyline-16',stroke_width=.85)
    assert bounds(sh,roles,meta,sty)==bounds([body],['body'],[{'id':'body'}],sty)
    for key in BOXES:
        result,notes=apply(sh,roles,meta,sty,{'keyline':key});b=notes[0]['after'];target=BOXES[key]
        assert min(b[:2])>=1 and max(b[2:])<=15
        assert abs(b[0]+b[2]-16)<1e-4 and abs(b[1]+b[3]-16)<1e-4
        assert b[2]-b[0]<=target[2]-target[0] and b[3]-b[1]<=target[3]-target[1]
    _,notes=apply(sh,roles,meta,sty,{'keyline':'square','offset':[.25,-.2],'reason':'visual balance'})
    b=notes[0]['after']
    assert abs((b[0]+b[2])/2-8.25)<1e-4 and abs((b[1]+b[3])/2-7.8)<1e-4
    assert notes[0]['reason']=='visual balance'
    invalids=[{'keyline':'unknown'},{'offset':[.6,0],'reason':'x'},{'offset':[.2,0]},
              {'offset':[float('nan'),0],'reason':'x'},{'offset':'bad'},{'unexpected':True}]
    for layout in invalids:
        try:apply(sh,roles,meta,sty,layout)
        except ValueError:pass
        else:raise AssertionError('Invalid grid layout accepted')
    try:apply(sh,roles,meta,sty,{'keyline':'free','offset':[.5,0],'reason':'test'})
    except ValueError:pass
    else:raise AssertionError('Unsafe offset accepted')
    spec=dict(name='grid-test',style=sty,icons=[dict(name='panel',shapes=[
        dict(id='panel',tag='rect',x=3,y=3,width=9,height=9,rx=2),
        dict(id='line',tag='path',d='M5 7 L10 7',role='line',parent='panel')])])
    with tempfile.TemporaryDirectory() as td:
        for mode in ('layered','outline','duotone'):
            s=copy.deepcopy(spec);s['style']['mode']=mode
            if mode=='outline':s['icons'][0]['shapes'][1].pop('parent')
            files=build(s);geometry=[]
            for name,text in files.items():
                p=Path(td)/name;p.write_text(text);errors,g=check(p,'pack');assert not errors,errors;geometry.append(g)
                assert 'stroke-width="0.85"' in text
                assert 'scale(' not in text
            assert geometry[0]==geometry[1]
            icon=s['icons'][0];old=copy.deepcopy(icon);old['name']='another-subject'
            assert prepare(icon,s['style'])[:4]==prepare(old,s['style'])[:4]
    print('PASS: similarity transforms, rotated shapes, clipped-child bounds, 5 keylines, 7 invalid layouts, 3 modes, fixed strokes, theme equality, subject-name independence')

if __name__=='__main__':main()
