#!/usr/bin/env python3
"""Sample compiled blueprint fill geometry; no image libraries or browser required.
Not a style score. Pixel grid approximation excludes strokes, colors and filters.
"""
import argparse,json,math,re
from pathlib import Path
from compose import compile_spec

RES=128

def contours(s):
    tag=s['tag']
    if tag in ('circle','ellipse'):
        rx=s.get('r',s.get('rx'));ry=s.get('r',s.get('ry'))
        polys=[[(s['cx']+rx*math.cos(i*math.tau/96),s['cy']+ry*math.sin(i*math.tau/96)) for i in range(96)]]
    elif tag=='rect':
        x,y,w,h=s['x'],s['y'],s['width'],s['height'];r=min(s.get('rx',0),w/2,h/2)
        if not r:polys=[[(x,y),(x+w,y),(x+w,y+h),(x,y+h)]]
        else:
            poly=[]
            for cx,cy,start in [(x+w-r,y+r,-90),(x+w-r,y+h-r,0),(x+r,y+h-r,90),(x+r,y+r,180)]:
                for i in range(17):
                    a=math.radians(start+i*90/16);poly.append((cx+r*math.cos(a),cy+r*math.sin(a)))
            polys=[poly]
    elif tag=='path':
        tokens=re.findall(r'[A-Za-z]|[-+]?(?:\d*\.\d+|\d+)(?:[eE][-+]?\d+)?',s['d'])
        polys=[];poly=[];i=0;current=None
        def pair(i):return float(tokens[i]),float(tokens[i+1])
        while i<len(tokens):
            command=tokens[i];i+=1
            if command=='M':
                if poly:polys.append(poly)
                current=pair(i);i+=2;poly=[current]
            elif command=='L':current=pair(i);i+=2;poly.append(current)
            elif command in ('Q','C'):
                p0=current;p1=pair(i);p2=pair(i+2);i+=4
                if command=='C':p3=pair(i);i+=2
                for j in range(1,33):
                    t=j/32;u=1-t
                    if command=='Q':p=tuple(u*u*p0[k]+2*u*t*p1[k]+t*t*p2[k] for k in (0,1))
                    else:p=tuple(u**3*p0[k]+3*u*u*t*p1[k]+3*u*t*t*p2[k]+t**3*p3[k] for k in (0,1))
                    poly.append(p)
                current=p
            elif command=='Z':
                if poly:polys.append(poly);poly=[]
            else:raise ValueError('Audit supports compiled M/L/Q/C/Z paths only, got '+command)
        if poly:polys.append(poly)
    else:raise ValueError('Unknown shape')
    a=math.radians(s.get('rotate',0));c=math.cos(a);sn=math.sin(a)
    return [[(8+(x-8)*c-(y-8)*sn,8+(x-8)*sn+(y-8)*c) for x,y in p] for p in polys]

def raster(polys):
    result=set();step=16/RES
    for y in range(RES):
        py=(y+.5)*step;xs=[]
        for poly in polys:
            for i,(x1,y1) in enumerate(poly):
                x2,y2=poly[i-1]
                if (y1>py)!=(y2>py):xs.append(x1+(py-y1)*(x2-x1)/(y2-y1))
        xs.sort()
        for x1,x2 in zip(xs[::2],xs[1::2]):
            lo=max(0,math.ceil(x1/step-.5));hi=min(RES,math.ceil(x2/step-.5))
            result.update(y*RES+x for x in range(lo,hi))
    return result

def components(cells,diagonal=False):
    pending=set(cells);groups=[]
    while pending:
        start=pending.pop();group={start};todo=[start]
        while todo:
            p=todo.pop();x=p%RES;y=p//RES
            neighbors=([p-1] if x else [])+([p+1] if x<RES-1 else [])+([p-RES] if y else [])+([p+RES] if y<RES-1 else [])
            if diagonal:
                neighbors += [p+dy*RES+dx for dx,dy in [(-1,-1),(-1,1),(1,-1),(1,1)] if 0<=x+dx<RES and 0<=y+dy<RES]
            for q in neighbors:
                if q in pending:pending.remove(q);group.add(q);todo.append(q)
        groups.append(group)
    return groups

def audit(s):
    compiled=compile_spec(s) if 'family' in s else s
    polys=[contours(p) for p in compiled['shapes']]
    points=[q for p in polys for c in p for q in c]
    bbox=[min(p[0] for p in points),min(p[1] for p in points),max(p[0] for p in points),max(p[1] for p in points)]
    layers=[raster(p) for p,shape in zip(polys,compiled['shapes']) if shape.get('paint',True)]
    union=set().union(*layers);background=set(range(RES*RES))-union
    holes=[c for c in components(background,diagonal=True) if not any(p%RES in (0,RES-1) or p//RES in (0,RES-1) for p in c)]
    area=(16/RES)**2
    graph=[(i,j,len(layers[i]&layers[j])*area) for i in range(len(layers)) for j in range(i+1,len(layers)) if len(layers[i]&layers[j])*area>=.25]
    reached={0}
    while True:
        nxt=reached|{j for i,j,_ in graph if i in reached}|{i for i,j,_ in graph if j in reached}
        if nxt==reached:break
        reached=nxt
    result=dict(name=compiled['name'],bbox=[round(x,4) for x in bbox],fill_area=round(len(union)*area,4),fill_components=len(components(union)),hole_areas=sorted(round(len(c)*area,4) for c in holes),strong_overlap_graph_connected=len(reached)==len(layers),overlap_edges=graph)
    errors=[]
    if min(bbox[:2])<.5 or max(bbox[2:])>15.5:errors.append('Less than 0.5 units of outer margin')
    if result['fill_components']!=1:errors.append('Disconnected fill components')
    if not result['strong_overlap_graph_connected']:errors.append('A layer has only weak/tangent connections')
    if 'family' in s:
        expected=1 if s['family'] in ('capsule-knot','pinwheel-knot') else 0
        if len(holes)!=expected:errors.append(f'Expected {expected} intentional holes, found {len(holes)}')
    result['issues']=errors;result['passed']=not errors
    return result

def main():
    p=argparse.ArgumentParser();p.add_argument('spec',type=Path);p.add_argument('--out',type=Path);args=p.parse_args()
    raw=json.loads(args.spec.read_text());rows=raw if isinstance(raw,list) else [raw]
    result=dict(resolution=RES,scope='Sampled fill topology, not rendered edge/surface quality',passed=True,results=[audit(s) for s in rows]);result['passed']=all(r['passed'] for r in result['results'])
    text=json.dumps(result,ensure_ascii=False,indent=2)+'\n'
    if args.out:args.out.write_text(text)
    else:print(text)
    raise SystemExit(0 if result['passed'] else 1)
if __name__=='__main__':main()
