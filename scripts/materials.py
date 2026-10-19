"""Common scene roles, width budgets and legacy parent inference (stdlib)."""
import copy,math
from geometry_audit import contours,raster,RES

def footprint(shape):return raster(contours(shape))
def feature_width(shape):
    if shape['tag']=='circle':return 2*shape['r']
    if shape['tag']=='ellipse':return 2*min(shape['rx'],shape['ry'])
    if shape['tag']=='rect':return min(shape['width'],shape['height'])
    polys=contours(shape)
    area=len(raster(polys))*(16/RES)**2
    perimeter=sum(math.dist(p[i-1],p[i]) for p in polys for i in range(len(p)))
    return 2*area/perimeter if perimeter else 0

def cell(p):
    x,y=(int(v*RES/16) for v in p)
    return y*RES+x if 0<=x<RES and 0<=y<RES else -1

def line_coverage(shape,cells):
    points=[p for c in contours(shape) for p in c]
    # Include line segments, not just endpoints, so a line across a hole is not contained.
    samples=[]
    for poly in contours(shape):
        for a,b in zip(poly,poly[1:]):
            n=max(1,math.ceil(math.dist(a,b)*16))
            samples.extend((a[0]+(b[0]-a[0])*i/n,a[1]+(b[1]-a[1])*i/n) for i in range(n+1))
    samples=samples or points
    return sum(cell(p) in cells for p in samples)/max(1,len(samples))

def plan(shapes,roles,metadata,style,strict=False):
    """No icon-name branches. Surface inference only for legacy unoutlined fills."""
    shapes=copy.deepcopy(shapes);roles=list(roles);parents=[None]*len(shapes);notes=[]
    masks={i:footprint(s) for i,s in enumerate(shapes) if roles[i]!='line' and style.get('mode')!='outline'}
    ids={m['id']:i for i,m in enumerate(metadata)}
    if len(ids)!=len(metadata):raise ValueError('Duplicate shape id')
    for i,(s,role,m) in enumerate(zip(shapes,roles,metadata)):
        explicit=m.get('parent')
        if explicit:
            if explicit not in ids or ids[explicit]>=i:raise ValueError('Parent must be a preceding filled material')
            j=ids[explicit]
            if roles[j] in ('line','surface') or style.get('mode')=='outline':raise ValueError('Parent is not a material')
            if role not in ('surface','line'):raise ValueError('Only surfaces and interior lines have parents')
            parents[i]=j
        elif role=='surface':raise ValueError('Surface needs an explicit parent')
        elif style.get('mode')=='layered' and not strict:
            candidates=[]
            for j in range(i):
                if roles[j] in ('line','surface') or not masks.get(j):continue
                coverage=line_coverage(s,masks[j]) if role=='line' else len(masks.get(i,set())&masks[j])/max(1,len(masks.get(i,set())))
                if (role=='line' or s.get('edge') is False) and coverage>=.90:
                    if role!='line' and len(masks[j])<len(masks[i])*1.15:continue
                    candidates.append((len(masks[j]),j))
            if candidates:
                j=min(candidates)[1];parents[i]=j
                if role!='line':roles[i]='surface'
                notes.append(dict(shape=m['id'],rule='inferred-contained-'+roles[i],parent=metadata[j]['id']))
        if parents[i] is not None:
            parent=masks[parents[i]]
            coverage=line_coverage(s,parent) if roles[i]=='line' else len(masks.get(i,set())&parent)/max(1,len(masks.get(i,set())))
            if coverage<.5:raise ValueError('Child has too little overlap with its parent')
        if style.get('mode')=='layered' and roles[i]!='line':
            width=feature_width(s)
            if roles[i]=='surface':
                s['edge']=False;s['relief']=0
                notes.append(dict(shape=m['id'],rule='surface-in-parent-before-edge'))
            else:
                # A stroke of W clipped inside consumes W/2 from each side.
                # Reserve >=.9 units of color. Very narrow parts become unoutlined.
                edge=0 if width<1.4 else min(1,max(0,round(width-.9,4)))
                if s.get('edge',True):s['edge_width']=min(s.get('edge_width',1),edge)
                if width<2 and 'opacity' not in s:s['opacity']=.9
                if edge<1:notes.append(dict(shape=m['id'],rule='reserve-color-core',feature_width=round(width,4),stroke_width=edge))
                if strict and width<.85:raise ValueError('Filled part is too thin at 16px; use a structural line or broader silhouette')
    return shapes,roles,parents,notes
