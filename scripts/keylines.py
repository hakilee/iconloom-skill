"""Optional 16-unit keylines: uniform geometry fitting, unchanged stroke tokens.

Bounds are sampled geometric paint bounds, not a perceptual or pixel-coverage score.
Clipped children do not determine the outer silhouette. No subject-name branches.
"""
import copy,math,re
from geometry_audit import contours
from generate import number

BOXES={'square':(2,2,14,14),'circle':(1.5,1.5,14.5,14.5),
       'horizontal':(1,3,15,13),'vertical':(3,1,13,15),'free':(1,1,15,15)}

def bounds(shapes,roles,metadata,style):
    boxes=[]
    for s,r,m in zip(shapes,roles,metadata):
        if m.get('parent') or r=='surface':continue
        points=[p for c in contours(s) for p in c]
        pad=style.get('stroke_width',.8)/2 if r=='line' or style.get('mode')=='outline' else 0
        boxes.append((min(x for x,y in points)-pad,min(y for x,y in points)-pad,
                      max(x for x,y in points)+pad,max(y for x,y in points)+pad))
    if not boxes:raise ValueError('Keyline layout needs a visible outer shape')
    return (min(b[0] for b in boxes),min(b[1] for b in boxes),max(b[2] for b in boxes),max(b[3] for b in boxes))

def move_shape(raw,scale,dx,dy):
    s=copy.deepcopy(raw);a=math.radians(s.get('rotate',0))
    # Existing rotate is around (8,8). Move in its inverse frame so every
    # component receives exactly the same WORLD-space scale and translation.
    lx=dx*math.cos(a)+dy*math.sin(a);ly=-dx*math.sin(a)+dy*math.cos(a)
    def point(x,y):return (round(8+(x-8)*scale+lx,8),round(8+(y-8)*scale+ly,8))
    if s['tag'] in ('circle','ellipse'):s['cx'],s['cy']=point(s['cx'],s['cy'])
    elif s['tag']=='rect':s['x'],s['y']=point(s['x'],s['y'])
    for key in ('r','rx','ry','width','height'):
        if key in s:s[key]=round(s[key]*scale,8)
    def path(d):
        tokens=re.findall(r'[A-Za-z]|[-+]?(?:\d*\.\d+|\d+)(?:[eE][-+]?\d+)?',d)
        out=[];i=0
        while i<len(tokens):
            command=tokens[i];i+=1
            if command not in ('M','L','Q','C','Z'):raise ValueError('Keylines support absolute M/L/Q/C/Z paths')
            out.append(command)
            for _ in range({'M':1,'L':1,'Q':2,'C':3,'Z':0}[command]):
                x,y=point(float(tokens[i]),float(tokens[i+1]));i+=2
                out.extend((format(x,'.8g'),format(y,'.8g')))
        return ' '.join(out)
    for key in ('d','edge_cutout'):
        if key in s:s[key]=path(s[key])
    return s

def apply(shapes,roles,metadata,style,layout=None):
    layout={} if layout is None else layout
    if not isinstance(layout,dict) or set(layout)-{'keyline','offset','reason','fit'}:raise ValueError('Invalid layout fields')
    fit=layout.get('fit','contain')
    if fit not in ('contain','preserve'):raise ValueError('fit must be contain or preserve')
    if style.get('grid')!='keyline-16':
        if layout:raise ValueError('Icon layout requires style.grid=keyline-16')
        return shapes,[]
    requested=layout.get('keyline','auto')
    if requested not in (*BOXES,'auto'):raise ValueError('Unknown keyline')
    offset=layout.get('offset',[0,0])
    if not isinstance(offset,list) or len(offset)!=2:raise ValueError('Optical offset needs two numbers')
    for v in offset:number(v,-.5,.5)
    if any(offset) and (not isinstance(layout.get('reason'),str) or not layout['reason'].strip()):
        raise ValueError('Optical offset requires a visual reason')
    before=bounds(shapes,roles,metadata,style);w=before[2]-before[0];h=before[3]-before[1]
    if min(w,h)<=0:raise ValueError('Empty silhouette')
    key=requested
    if key=='auto':
        key='horizontal' if w/h>1.25 else 'vertical' if w/h<.8 else 'square'
        # A dominant round primitive can suggest the circle keyline. A square
        # bbox alone cannot distinguish a disc from a square or a complex symbol.
        for s,r,m in zip(shapes,roles,metadata):
            if key=='square' and not m.get('parent') and s['tag']=='circle' and 2*s['r']>=.9*max(w,h):key='circle'
    target=BOXES[key];tw=target[2]-target[0];th=target[3]-target[1]
    if fit=='preserve':
        result=[move_shape(s,1,*offset) for s in shapes] if any(offset) else copy.deepcopy(shapes)
        after=bounds(result,roles,metadata,style)
        if min(after[:2])<1-1e-6 or max(after[2:])>15+1e-6:raise ValueError('Preserved geometry violates the 1-unit safe margin')
        return result,[dict(rule='keyline-16-preserve',keyline=key,target=list(target),scale=1,
            translation=offset,reason=layout.get('reason',''),before=list(before),after=list(after),
            outside_keyline=any((after[0]<target[0],after[1]<target[1],after[2]>target[2],after[3]>target[3])),
            scope='Authored coordinates retained; keyline is a guide, safe margin is enforced')]
    def scaled(factor):return [move_shape(s,factor,0,0) for s in shapes]
    # Fixed-width strokes make simple bbox multiplication inaccurate. Solve
    # scale with stroke extents included, reserving .01 units for sampling error.
    lo,hi=0.,8.
    for _ in range(40):
        mid=(lo+hi)/2;b=bounds(scaled(mid),roles,metadata,style)
        if b[2]-b[0]<=tw-.02 and b[3]-b[1]<=th-.02:lo=mid
        else:hi=mid
    factor=lo
    if not .5<=factor<=2:raise ValueError('Keyline fit needs excessive scale; author near the target size')
    b=bounds(scaled(factor),roles,metadata,style)
    dx=8-(b[0]+b[2])/2+offset[0];dy=8-(b[1]+b[3])/2+offset[1]
    result=[move_shape(s,factor,dx,dy) for s in shapes]
    after=bounds(result,roles,metadata,style)
    if min(after[:2])<1-1e-6 or max(after[2:])>15+1e-6:raise ValueError('Optical offset violates the 1-unit safe margin')
    return result,[dict(rule='keyline-16',keyline=key,requested=requested,target=list(target),
        scale=round(factor,6),translation=[round(dx,6),round(dy,6)],offset=offset,reason=layout.get('reason',''),
        before=[round(v,5) for v in before],after=[round(v,5) for v in after],
        margins=[round(after[0],5),round(after[1],5),round(16-after[2],5),round(16-after[3],5)],
        scope='Sampled outer geometry with fixed-width stroke extents; no automatic optical proof')]
