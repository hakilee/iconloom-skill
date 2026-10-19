#!/usr/bin/env python3
"""Compile bounded reference-family blueprints to new SVG geometry (stdlib only)."""
import argparse, json, math
from pathlib import Path
from generate import render, number

# Bounds are jointly tested. Increasing them requires new visual/topology calibration.
FAMILIES = {
 'interlocking-tiles': dict(palette='violet', a=(2.95,3.2,3.1), b=(3.85,4.05,3.95)),
 'capsule-knot': dict(palette='coral', a=(3.55,3.9,3.75), b=(2.45,2.65,2.55)),
 'tile-weave': dict(palette='lavender', a=(2.8,3.1,2.95), b=(3.6,4.1,3.85)),
 'pinwheel-knot': dict(palette='apricot', a=(5.8,6.15,6.0), b=(1.25,1.5,1.4)),
 'lens-network': dict(palette='sky', a=(2.95,3.2,3.1), b=(3.35,3.6,3.45)),
 'lobed-orbit': dict(palette='lagoon', a=(3.65,3.95,3.8), b=(1.55,1.8,1.7)),
}

def f(v): return format(round(v,5),'.5f').rstrip('0').rstrip('.') or '0'
def pt(p): return ' '.join(f(v) for v in p)
def rounded_polygon(points, inset):
    """Quadratic corner rounding with a bounded distance along each incident edge."""
    corners=[]
    for i,p in enumerate(points):
        prev,nxt=points[i-1],points[(i+1)%len(points)]
        def cut(q):
            d=math.dist(p,q);t=min(inset/d,.45)
            return (p[0]+(q[0]-p[0])*t,p[1]+(q[1]-p[1])*t)
        corners.append((cut(prev),p,cut(nxt)))
    d='M'+pt(corners[0][0])
    for i,(a,p,b) in enumerate(corners):
        if i:d+=' L'+pt(a)
        d+=' Q'+pt(p)+' '+pt(b)
    return d+' Z'
def diamond(cx,cy,r,corner=1.25,**kw):
    return dict(tag='path',d=rounded_polygon([(cx,cy-r),(cx+r,cy),(cx,cy+r),(cx-r,cy)],corner),**kw)
def rect(cx,cy,w,h,r,**kw):
    return dict(tag='rect',x=cx-w/2,y=cy-h/2,width=w,height=h,rx=r,**kw)
def circle(cx,cy,r,**kw):return dict(tag='circle',cx=cx,cy=cy,r=r,**kw)
def ellipse_path(cx,cy,r):
    k=.5522847498307936*r
    return f'M{f(cx+r)} {f(cy)} C{f(cx+r)} {f(cy+k)} {f(cx+k)} {f(cy+r)} {f(cx)} {f(cy+r)} C{f(cx-k)} {f(cy+r)} {f(cx-r)} {f(cy+k)} {f(cx-r)} {f(cy)} C{f(cx-r)} {f(cy-k)} {f(cx-k)} {f(cy-r)} {f(cx)} {f(cy-r)} C{f(cx+k)} {f(cy-r)} {f(cx+r)} {f(cy-k)} {f(cx+r)} {f(cy)} Z'

def compile_spec(s):
    allowed={'name','label','family','palette','spread','weight','phase','meaning'}
    if set(s)-allowed:raise ValueError('Blueprint fields not allowed: '+str(set(s)-allowed))
    family=s['family'];cfg=FAMILIES.get(family)
    if cfg is None:raise ValueError('Unknown family: '+str(family))
    spread=number(s.get('spread',0),-1,1);weight=number(s.get('weight',0),-1,1)
    phase=number(s.get('phase',0),-12,12)
    def param(key,t):
        lo,hi,mid=cfg[key];return mid+t*(hi-mid if t>=0 else mid-lo)
    a,b=param('a',spread),param('b',weight)
    parts=[]
    if family=='interlocking-tiles':
        # Rear pair is deliberately unoutlined. Do not thicken every seam alike.
        for x,y in [(8,8-a),(8,8+a)]:parts.append(diamond(x,y,b,1.25,opacity=.6,edge=False))
        for x,y in [(8+a,8),(8-a,8)]:parts.append(diamond(x,y,b+.35,1.4,opacity=.8,edge_cutout=diamond(8,8,1.95,1.2)['d']))
        # Suppress hidden side seams inside the shared junction; draw the junction once.
        parts.append(diamond(8,8,1.95,1.2,opacity=.8))
    elif family=='capsule-knot':
        # Four off-center capsules; radius and distance preserve an open center.
        length=7.4+.3*spread
        for i in [0,2,1,3]:
            parts.append(rect(8,8-a,length,2*b,b,rotate=90*i,opacity=.9 if i%2==0 else .7,edge_tone=.65 if i%2 else 0))
        # Source-family continuity contour. It has no fill and cannot plug the hole.
        parts.append(circle(8,8,4.05,opacity=.86,paint=False,relief=0,edge_tone=.6))
    elif family=='tile-weave':
        parts.append(rect(8,8,12.5,b,1.05,opacity=.67,relief=0))
        for x,y in [(8-a,8-a),(8-a,8+a),(8+a,8-a),(8+a,8+a)]:
            parts.append(diamond(x,y,2.95+.1*weight,1.3,opacity=.5,relief=0))
        parts.append(rect(8,8,b,12.5,1.05,opacity=.67,relief=0))
    elif family=='pinwheel-knot':
        # Rounded sector/blade, parametrically built; no imported source path.
        end=(8+a-.2,8-a+1.8);tip=(9.54,8.12)
        length=math.dist(end,tip);u=((tip[0]-end[0])/length,(tip[1]-end[1])/length)
        c2=(end[0]-.85*u[0],end[1]-.85*u[1])
        blade=f'M8.16 {f(8-a+1.5)} Q8.16 {f(8-a+.65)} 8.85 {f(8-a+.3)} Q{f(8+a*.55)} {f(8-a-.5)} {f(8+a-.7)} {f(8-a+.3)} C{f(8+a+.55)} {f(8-a+.68)} {pt(c2)} {pt(end)} L9.54 8.12 C9.04 8.62 8.16 8.27 8.16 7.56 Z'
        for i in [0,2]:parts.append(dict(tag='path',d=blade,rotate=i*90,opacity=.8))
        ring=diamond(8,8,5.45,1.0,opacity=.78)
        ring['d']+=' '+ellipse_path(8,8,b);ring['fill-rule']='evenodd'
        parts.append(ring)
        for i in [1,3]:parts.append(dict(tag='path',d=blade,rotate=i*90,opacity=.8))
    elif family=='lens-network':
        parts.append(circle(8,8,a+b-.12,opacity=.95,edge=False,relief=0))
        parts.append(circle(8,8,b-.3,opacity=.72,edge_opacity=.8,relief=0))
        for i in [3,1,0,2]:
            parts.append(circle(8,8-a,b,rotate=i*90,opacity=.78 if i%2 else .6,edge_opacity=.8,relief=0))
    elif family=='lobed-orbit':
        length=5.9
        for i in [0,2,4,6,1,3,5,7]:
            parts.append(rect(8,8-a,2*b,length,b,rotate=i*45,opacity=.9 if i%2==0 else .6))
        parts.append(diamond(8,8,3.95,1.4,opacity=.6))
    for part in parts:
        part['rotate']=round(part.get('rotate',0)+phase,5)
        part['gradient']=[.25,0,.65,1]
    out=dict(name=s['name'],label=s.get('label',s['name']),palette=s.get('palette',cfg['palette']),shapes=parts)
    # Validate the actual renderer input before writing any files.
    render(out,'light');render(out,'dark')
    return out

def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--spec',type=Path,required=True);ap.add_argument('--out',type=Path,required=True);args=ap.parse_args()
    raw=json.loads(args.spec.read_text());raw=raw if isinstance(raw,list) else [raw]
    if not raw or len({s['name'] for s in raw})!=len(raw):raise ValueError('Empty batch or duplicate names')
    from geometry_audit import audit
    checks=[audit(s) for s in raw]
    failures=[r for r in checks if not r['passed']]
    if failures:raise ValueError('Blueprint topology preflight failed: '+json.dumps(failures))
    compiled=[compile_spec(s) for s in raw]
    files=[(s['name']+'-'+t+'.svg',render(s,t)) for s in compiled for t in ('light','dark')]
    dest=args.out/'svg';dest.mkdir(parents=True,exist_ok=True)
    for name,data in files:(dest/name).write_text(data)
    (args.out/'topology.json').write_text(json.dumps(checks,ensure_ascii=False,indent=2)+'\n')
    (args.out/'compiled-specs.json').write_text(json.dumps(compiled,ensure_ascii=False,indent=2)+'\n')
    print(f'Compiled {len(raw)} blueprints; generated {len(files)} SVGs')
if __name__=='__main__':main()
