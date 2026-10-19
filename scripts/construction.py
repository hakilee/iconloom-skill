"""Sample declared mechanical joints and meaningful gaps before rendering.

128x128 binary geometry, independent of theme/name. Not a semantic, visibility,
contrast or analytic topology proof. Relationships must be authored correctly.
"""
import math,re
from geometry_audit import contours,raster,RES
from generate import number

STEP=16/RES

def segment_distance(p,a,b):
    dx=b[0]-a[0];dy=b[1]-a[1];den=dx*dx+dy*dy
    t=max(0,min(1,((p[0]-a[0])*dx+(p[1]-a[1])*dy)/den)) if den else 0
    return math.hypot(p[0]-a[0]-t*dx,p[1]-a[1]-t*dy)

def mask(shape,line,width):
    paths=contours(shape)
    if not line:return raster(paths)
    chunks=[{**shape,'d':d} for d in re.findall(r'M[^M]+',shape['d'])] if shape['tag']=='path' else [shape]
    segs=[]
    for chunk in chunks:
        closed=chunk['tag']!='path' or chunk['d'].rstrip().endswith('Z')
        segs.extend((a,b) for ps in contours(chunk) for a,b in zip(ps,ps[1:]+(ps[:1] if closed else [])))
    points=[p for ps in paths for p in ps];pad=width/2
    xs=range(max(0,int((min(x for x,y in points)-pad)/STEP)),min(RES,math.ceil((max(x for x,y in points)+pad)/STEP)))
    ys=range(max(0,int((min(y for x,y in points)-pad)/STEP)),min(RES,math.ceil((max(y for x,y in points)+pad)/STEP)))
    return {y*RES+x for y in ys for x in xs if any(segment_distance(((x+.5)*STEP,(y+.5)*STEP),a,b)<=pad for a,b in segs)}

def boundary(cells):
    return [((p%RES+.5)*STEP,(p//RES+.5)*STEP) for p in cells if any(q not in cells for q in (p-1,p+1,p-RES,p+RES))]

def verify(spec,shapes,roles,metadata,parents,style):
    if spec is None:return []
    if not isinstance(spec,dict) or set(spec)-{'joins','gaps'}:raise ValueError('Invalid construction fields')
    ids={m['id']:i for i,m in enumerate(metadata)};cache={};notes=[]
    def cells(i):
        if i not in cache:
            cache[i]=mask(shapes[i],roles[i]=='line' or style.get('mode')=='outline',style.get('stroke_width',.8))
            if parents[i] is not None:cache[i]&=cells(parents[i])
        return cache[i]
    def pair(value):
        if not isinstance(value,list) or len(value)!=2 or any(not isinstance(v,str) or v not in ids for v in value) or value[0]==value[1]:raise ValueError('Construction pair needs two different shape ids')
        return [cells(ids[v]) for v in value]
    for key in ('joins','gaps'):
        if not isinstance(spec.get(key,[]),list) or len(spec.get(key,[]))>24:raise ValueError('Use up to 24 construction relations per kind')
    for relation in spec.get('joins',[]):
        a,b=pair(relation);overlap=a&b
        robust=any(p%RES<RES-1 and {p,p+1,p+RES,p+RES+1}<=overlap for p in overlap)
        area=len(overlap)*STEP*STEP
        if not robust or area<.125:raise ValueError('Weak or disconnected joint: '+' / '.join(relation))
        notes.append(dict(rule='declared-joint',parts=relation,overlap_area=round(area,4),passed=True))
    for relation in spec.get('gaps',[]):
        if not isinstance(relation,dict) or set(relation)!={'parts','min'}:raise ValueError('Gap needs parts and min')
        threshold=number(relation['min'],.5,3);a,b=pair(relation['parts'])
        if not a or not b:raise ValueError('Gap references empty geometry')
        distance=0 if a&b else max(0,min(math.dist(p,q) for p in boundary(a) for q in boundary(b))-STEP*math.sqrt(2))
        if distance<threshold:raise ValueError('Insufficient declared gap: '+' / '.join(relation['parts'])+f' ({distance:.3f} < {threshold})')
        notes.append(dict(rule='declared-gap',parts=relation['parts'],sampled_gap=round(distance,4),minimum=threshold,passed=True))
    return notes
