#!/usr/bin/env python3
"""Deterministic, standard-library SVG authoring with shared theme geometry."""
import argparse, json, math, re
from pathlib import Path
import xml.etree.ElementTree as E

ROOT = Path(__file__).resolve().parents[1]
PALETTES = json.loads((ROOT/'references/palettes.json').read_text())
ATTRS = {
 'circle': {'cx','cy','r'}, 'ellipse': {'cx','cy','rx','ry'},
 'rect': {'x','y','width','height','rx','ry'}, 'path': {'d','fill-rule'},
}

def number(v, low, high):
    if isinstance(v,bool) or not isinstance(v,(int,float)) or not math.isfinite(v) or not low <= v <= high:
        raise ValueError(f'Expected finite number in [{low}, {high}], got {v!r}')
    return v

def base_form(kind):
    forms = {
      'petal': ('ellipse',dict(cx=8,cy=5.1,rx=2.25,ry=3.45)),
      'disc': ('circle',dict(cx=8,cy=5.2,r=3)),
      'leaf': ('path',dict(d='M8 1.3 C11.5 3.4 11.8 7.8 8 9.5 C4.2 7.8 4.5 3.4 8 1.3Z')),
      'capsule': ('rect',dict(x=6.6,y=1.5,width=2.8,height=13,rx=1.4)),
      'tile': ('rect',dict(x=5.2,y=1.8,width=5.6,height=5.6,rx=1.3)),
      'arc': ('path',dict(d='M2 8 C2 2.24 8.96 -0.16 13 3.56 C14.4 4.76 12.8 6.92 11.4 5.84 C8.96 4.04 5.36 5.36 5.36 8 C5.36 10 2 10 2 8Z')),
    }
    if kind not in forms: raise ValueError(f'Unknown form: {kind}; use {list(forms)} or custom shapes')
    tag, a = forms[kind]
    return dict(tag=tag,**a)

def geometry(spec):
    if 'shapes' in spec:
        raw=spec['shapes']
        if not isinstance(raw,list) or not 1<=len(raw)<=24: raise ValueError('Use 1–24 custom shapes')
    else:
        n=spec.get('count',5)
        if isinstance(n,bool) or not isinstance(n,int) or not 3<=n<=8: raise ValueError('count must be integer 3–8')
        phase=number(spec.get('phase',0),-360,360)
        # Full centered capsules are undirected; half-circle spacing prevents duplicates.
        sweep=180 if spec.get('form','petal')=='capsule' else 360
        raw=[dict(base_form(spec.get('form','petal')),rotate=round(phase+i*sweep/n,4),opacity=spec.get('opacity',[0.85,0.6,0.8,0.65][i%4])) for i in range(n)]
    result=[]
    for shape in raw:
        tag=shape.get('tag'); allowed=ATTRS.get(tag)
        if allowed is None or set(shape)-allowed-{'tag','rotate','opacity','gradient','relief','edge','paint','edge_opacity','edge_cutout','edge_tone','edge_width'}: raise ValueError(f'Unsupported shape: {shape}')
        a={}
        for key in sorted(allowed):
            if key not in shape: continue
            v=shape[key]
            if key=='fill-rule':
                if v not in ('evenodd','nonzero'): raise ValueError('Invalid fill rule')
            elif key=='d':
                if not isinstance(v,str) or not re.fullmatch(r'[MmZzLlHhVvCcSsQqTtAa0-9eE.,+\s-]+',v): raise ValueError('Invalid path characters')
            else:
                number(v,0 if key in {'r','rx','ry','width','height'} else -32,32)
            a[key]=str(v)
        required={'circle':{'cx','cy','r'},'ellipse':{'cx','cy','rx','ry'},'rect':{'x','y','width','height'},'path':{'d'}}[tag]
        if not required<=a.keys(): raise ValueError(f'Missing geometry attributes for {tag}')
        if 'rotate' in shape: a['transform']=f"rotate({number(shape['rotate'],-360,360)} 8 8)"
        a['opacity']=str(number(shape.get('opacity',spec.get('opacity',0.72)),0.35,1))
        result.append((tag,a))
    return result

def mix_hex(a,b,t):
    return '#'+''.join(f'{round(int(a[i:i+2],16)*(1-t)+int(b[i:i+2],16)*t):02X}' for i in (1,3,5))

def render(spec, theme):
    name=spec['name']
    if not isinstance(name,str) or not re.fullmatch('[a-z][a-z0-9-]{0,63}',name): raise ValueError('name must be a lowercase slug beginning with a letter')
    palette=spec.get('palette','sky')
    colors=PALETTES.get(palette) if isinstance(palette,str) else palette
    if not isinstance(colors,list) or len(colors)!=3 or not all(isinstance(c,str) and re.fullmatch('#[0-9a-fA-F]{6}',c) for c in colors): raise ValueError('palette must be a token name or three #RRGGBB colors')
    prefix=f'{name}-{theme}'
    r=E.Element('svg',{'xmlns':'http://www.w3.org/2000/svg','width':'16','height':'16','viewBox':'0 0 16 16','fill':'none','role':'img','aria-labelledby':prefix+'-title'})
    E.SubElement(r,'title',id=prefix+'-title').text=spec.get('label',name)
    defs=E.SubElement(r,'defs')
    # Independent local gradients and composited layers preserve petal direction.
    for index,(tag,attributes) in enumerate(geometry(spec)):
        a=dict(attributes)
        opacity=a.pop('opacity')
        transform=a.pop('transform',None)
        layer_id=f'{prefix}-layer-{index}'
        raw=spec.get('shapes',[{}]*24)[index] if 'shapes' in spec else {}
        direction=raw.get('gradient',spec.get('gradient',[0.15,0,0.85,1]))
        if not isinstance(direction,list) or len(direction)!=4:
            raise ValueError('gradient must contain four object-bounding-box coordinates')
        direction=[number(v,-2,3) for v in direction]
        gradient=E.SubElement(defs,'linearGradient',dict(id=layer_id+'-paint',x1=str(direction[0]),y1=str(direction[1]),x2=str(direction[2]),y2=str(direction[3]),gradientUnits='objectBoundingBox'))
        E.SubElement(gradient,'stop',{'stop-color':colors[0]})
        if palette=='sunbeam':
            E.SubElement(gradient,'stop',{'offset':'0.43','stop-color':'#FFE236'})
        E.SubElement(gradient,'stop',{'offset':'1','stop-color':colors[1]})
        clip=E.SubElement(defs,'clipPath',{'id':layer_id+'-clip','clipPathUnits':'userSpaceOnUse'})
        clip_a=dict(a)
        if 'fill-rule' in a: clip_a['clip-rule']=a['fill-rule']
        E.SubElement(clip,tag,clip_a)
        strength=raw.get('relief',spec.get('relief',0.16 if theme=='dark' else 0.07))
        number(strength,0,0.3)
        if strength and theme=='dark':
            # A narrow rim was hidden by the inset outline. Broader interior light
            # remains visible beyond it; inverse rotation keeps the light coherent.
            angle=math.radians(raw.get('rotate',0))
            dx=1.4*math.cos(angle)+.9*math.sin(angle)
            dy=-1.4*math.sin(angle)+.9*math.cos(angle)
            blur=1.1
            strength=min(.3,strength*1.5)
        else:dx,dy,blur=0,.55,.32
        if strength:
            f=E.SubElement(defs,'filter',{'id':layer_id+'-inset','x':'-50%','y':'-50%','width':'200%','height':'200%','color-interpolation-filters':'sRGB'})
            # SourceAlpha minus the shifted alpha produces an INNER edge only.
            E.SubElement(f,'feOffset',{'in':'SourceAlpha','dx':str(round(dx,5)),'dy':str(round(dy,5)),'result':'shift'})
            E.SubElement(f,'feGaussianBlur',{'in':'shift','stdDeviation':str(blur),'result':'blur'})
            E.SubElement(f,'feComposite',{'in':'SourceAlpha','in2':'blur','operator':'out','result':'rim'})
            E.SubElement(f,'feFlood',{'flood-color':'#FFFFFF','flood-opacity':str(strength),'result':'tint'})
            E.SubElement(f,'feComposite',{'in':'tint','in2':'rim','operator':'in','result':'light'})
            merge=E.SubElement(f,'feMerge')
            E.SubElement(merge,'feMergeNode',{'in':'SourceGraphic'})
            E.SubElement(merge,'feMergeNode',{'in':'light'})
        cutout=raw.get('edge_cutout')
        if cutout is not None:
            if not isinstance(cutout,str) or not re.fullmatch(r'[MmZzLlHhVvCcSsQqTtAa0-9eE.,+\s-]+',cutout): raise ValueError('Invalid edge cutout path')
            mask=E.SubElement(defs,'mask',{'id':layer_id+'-join','maskUnits':'userSpaceOnUse','x':'0','y':'0','width':'16','height':'16','mask-type':'luminance'})
            E.SubElement(mask,'rect',{'x':'0','y':'0','width':'16','height':'16','fill':'white'})
            E.SubElement(mask,'path',{'d':cutout,'fill':'black'})
        layer=E.SubElement(r,'g',{'opacity':opacity,'data-layer':str(index)})
        if transform:layer.set('transform',transform)
        fill=dict(a,fill=f'url(#{layer_id}-paint)',**{'data-part':'fill'})
        if strength:fill['filter']=f'url(#{layer_id}-inset)'
        for flag in ('edge','paint'):
            if flag in raw and not isinstance(raw[flag],bool): raise ValueError(flag+' must be boolean')
        if raw.get('paint',True): E.SubElement(layer,tag,fill)
        edge_opacity=number(raw.get('edge_opacity',1),0,1)
        edge_tone=number(raw.get('edge_tone',0),0,1)
        edge_width=number(raw.get('edge_width',1),0,1)
        if raw.get('edge',True) and edge_width:
            edge=E.SubElement(layer,tag,dict(a,opacity=str(edge_opacity),fill='none',stroke='#FFFFFF' if theme=='light' else mix_hex(colors[2],colors[1],edge_tone),**{'stroke-width':str(edge_width),'stroke-linejoin':'round','clip-path':f'url(#{layer_id}-clip)','data-part':'edge'}))
            if cutout is not None:edge.set('mask',f'url(#{layer_id}-join)')
    E.indent(r)
    return E.tostring(r,encoding='unicode')+'\n'

def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--spec',type=Path,required=True);ap.add_argument('--out',type=Path,required=True);args=ap.parse_args()
    data=json.loads(args.spec.read_text()); specs=data if isinstance(data,list) else [data]
    if not specs: raise ValueError('Empty spec list')
    names=[s['name'] for s in specs]
    if len(names)!=len(set(names)): raise ValueError('Duplicate icon names')
    files=[(f"{s['name']}-{t}.svg",render(s,t)) for s in specs for t in ('light','dark')]
    args.out.mkdir(parents=True,exist_ok=True)
    for name,svg in files: (args.out/name).write_text(svg)
    print(f'Generated {len(files)} SVGs from {len(specs)} designs')
if __name__=='__main__': main()
