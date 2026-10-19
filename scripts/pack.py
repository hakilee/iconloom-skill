#!/usr/bin/env python3
"""Render authored icon packs from one style contract, independent of source families."""
import argparse,json,re
from pathlib import Path
import xml.etree.ElementTree as E
from generate import render,geometry,number,PALETTES
from geometry_audit import contours
from materials import plan
from construction import verify as verify_construction
from keylines import apply as apply_keylines

NS='http://www.w3.org/2000/svg'
E.register_namespace('',NS)

def style_config(style):
    if not isinstance(style,dict) or set(style)-{'mode','palette','stroke_width','relief','light','dark','grid','line_contrast'}:raise ValueError('Unsupported style field')
    if style.get('grid') not in (None,'keyline-16'):raise ValueError('Unknown grid preset')
    if style.get('line_contrast') not in (None,'by-role'):raise ValueError('Unknown line contrast mode')
    mode=style.get('mode','layered')
    if mode not in ('layered','outline','duotone'):raise ValueError('mode must be layered, outline or duotone')
    number(style.get('stroke_width',.8),.35,1.5);number(style.get('relief',.18),0,.3)
    palette=style.get('palette','sky');colors=PALETTES.get(palette) if isinstance(palette,str) else palette
    if not isinstance(colors,list) or len(colors)!=3 or any(not isinstance(c,str) or not re.fullmatch('#[a-fA-F0-9]{6}',c) for c in colors):raise ValueError('Invalid palette')
    defaults={'light':dict(ink='#26334D',accent='#6C87CA',detail='#FFFFFF'),'dark':dict(ink='#DBE5FF',accent='#86A8FA',detail='#202124')}
    themes={}
    for theme in ('light','dark'):
        custom=style.get(theme,{})
        if not isinstance(custom,dict) or set(custom)-{'ink','accent','detail'}:raise ValueError('Unsupported theme token')
        themes[theme]={**defaults[theme],**custom}
        if any(not isinstance(v,str) or not re.fullmatch('#[a-fA-F0-9]{6}',v) for v in themes[theme].values()):raise ValueError('Invalid theme color')
    return mode,themes

def normalize(icon,style):
    if set(icon)-{'name','label','meaning','scenario','recognition','shapes','layout','construction'}:raise ValueError('Unsupported icon field')
    name=icon['name']
    if not isinstance(name,str) or not re.fullmatch('[a-z][a-z0-9-]{0,63}',name):raise ValueError('Invalid icon name')
    if not isinstance(icon['shapes'],list) or not 1<=len(icon['shapes'])<=24:raise ValueError('Use 1–24 shapes')
    cleaned=[];roles=[];metadata=[]
    for raw in icon['shapes']:
        shape=dict(raw);role=shape.pop('role','body');meta={'id':shape.pop('id',f'p{len(cleaned)}'),'parent':shape.pop('parent',None)}
        if not isinstance(meta['id'],str) or not re.fullmatch('[a-z][a-z0-9-]{0,63}',meta['id']):raise ValueError('Invalid shape id')
        if role not in ('body','accent','surface','line'):raise ValueError('Invalid shape role')
        geometry(dict(name=name,shapes=[shape]))
        line=style.get('mode','layered')=='outline' or role=='line'
        if style.get('mode','layered')!='layered' or role=='line':
            if set(shape)&{'gradient','relief','edge','paint','edge_opacity','edge_cutout','edge_tone','edge_width'}:raise ValueError('Surface attributes require layered fills')
        for key in ('r','width','height'):
            if key in shape and shape[key]<=0:raise ValueError('Zero-sized shape')
        if shape['tag']=='ellipse' and (shape['rx']<=0 or shape['ry']<=0):raise ValueError('Zero-sized ellipse')
        if shape['tag']=='rect' and 'ry' in shape and shape['ry']!=shape.get('rx',shape['ry']):raise ValueError('Pack rectangles use equal corner radii')
        if shape['tag']=='rect' and 'ry' in shape:shape.setdefault('rx',shape['ry'])
        if shape['tag']=='path' and not line and not shape['d'].rstrip().endswith('Z'):raise ValueError('Filled paths must close explicitly')
        # The pack helper intentionally supports inspectable absolute M/L/Q/C/Z
        # curves; general SVG authoring can handle other syntax outside this helper.
        points=[q for c in contours(shape) for q in c]
        if not points:raise ValueError('Empty shape')
        pad=style.get('stroke_width',.8)/2 if line else 0
        if min(min(x,y) for x,y in points)-pad<.5 or max(max(x,y) for x,y in points)+pad>15.5:raise ValueError('Shape/stroke outside safe bounds: '+name)
        cleaned.append(shape);roles.append(role);metadata.append(meta)
    return cleaned,roles,metadata

def prepare(icon,style,strict=False):
    mode,_=style_config(style);style={**style,'mode':mode}
    shapes,roles,metadata=normalize(icon,style)
    if mode=='layered' and not strict:
        expanded=[]
        for shape,role,meta in zip(shapes,roles,metadata):
            paths=re.findall(r'M[^M]+',shape.get('d','')) if role=='line' and shape['tag']=='path' else []
            if len(paths)>1 and not meta.get('parent'):
                expanded.extend(({**shape,'d':d.strip()},role,{**meta,'id':meta['id']+'-s'+str(j)}) for j,d in enumerate(paths))
            else:expanded.append((shape,role,meta))
        shapes,roles,metadata=map(list,zip(*expanded))
    if mode=='outline' and 'surface' in roles:raise ValueError('Outline mode has no filled surface')
    if strict:
        r=icon.get('recognition',{})
        if set(r)!={'silhouette','cue','confusable','difference','cue_ids'}:raise ValueError('Strict packs require a recognition plan')
        if any(not isinstance(r[k],str) or not r[k].strip() for k in ('silhouette','cue','confusable','difference')):raise ValueError('Empty recognition rationale')
        if not isinstance(r['cue_ids'],list) or not r['cue_ids'] or not set(r['cue_ids'])<={m['id'] for m in metadata}:raise ValueError('Recognition cues must reference real shapes')
        if style.get('stroke_width',.8)<.75:raise ValueError('Strict native-size strokes must be at least .75')
    shapes,layout_notes=apply_keylines(shapes,roles,metadata,style,icon.get('layout'))
    shapes,roles,parents,notes=plan(shapes,roles,metadata,style,strict)
    notes=layout_notes+notes+verify_construction(icon.get('construction'),shapes,roles,metadata,parents,style)
    return shapes,roles,metadata,parents,notes

def render_icon(icon,style,theme,strict=False):
    mode,themes=style_config(style)
    shapes,roles,meta,parents,notes=prepare(icon,style,strict);tokens=themes[theme]
    prefix=f'{icon["name"]}-{theme}'
    material_nodes={};defs=None
    if mode=='layered':
        filled_indices=[i for i,r in enumerate(roles) if r!='line']
        filled=[shapes[i] for i in filled_indices]
        if not filled:raise ValueError('layered mode needs a filled component')
        root=E.fromstring(render(dict(name=icon['name'],label=icon.get('label',icon['name']),palette=style.get('palette','sky'),relief=style.get('relief',.18),shapes=filled),theme))
        defs=root.find('{'+NS+'}defs')
        groups=[e for e in root if e.tag=='{'+NS+'}g']
        for i,g in zip(filled_indices,groups):material_nodes[i]=g;root.remove(g)
    else:
        root=E.Element('{'+NS+'}svg',dict(width='16',height='16',viewBox='0 0 16 16',fill='none',role='img',**{'aria-labelledby':prefix+'-title'}))
        E.SubElement(root,'{'+NS+'}title',id=prefix+'-title').text=icon.get('label',icon['name'])
        if any(p is not None for p in parents):defs=E.SubElement(root,'{'+NS+'}defs')
    root.set('data-profile','pack-'+mode)
    def primitive(i):
        shape,role=shapes[i],roles[i]
        if mode=='layered' and role!='line':return material_nodes[i]
        tag,attrs=geometry(dict(name=icon['name'],opacity=1,shapes=[shape]))[0]
        a=dict(attrs);a.pop('opacity',None)
        line=mode=='outline' or role=='line'
        color=tokens['accent'] if role in ('accent','surface') else tokens['ink']
        if line:
            if mode!='outline' and role=='line':color=tokens['ink'] if style.get('line_contrast')=='by-role' and parents[i] is None else tokens['detail']
            a.update(fill='none',stroke=color,opacity=str(shape.get('opacity',1)),**{'stroke-width':str(style.get('stroke_width',.8)),'stroke-linecap':'round','stroke-linejoin':'round','data-part':'line'})
        else:a.update(fill=color,opacity=str(shape.get('opacity',1)),**{'data-part':'solid'})
        return E.Element('{'+NS+'}'+tag,a)
    for i in range(len(shapes)):
        if parents[i] is not None:continue
        node=primitive(i);children=[j for j,p in enumerate(parents) if p==i]
        if not children:
            root.append(node);continue
        # The material's edge is painted once, after its contained surface/details.
        # Parent geometry is in world coordinates: rotated parents do not rotate children twice.
        outer=E.SubElement(root,'{'+NS+'}g',{'data-material':meta[i]['id']})
        edges=[]
        if mode=='layered':
            outer.set('opacity',node.attrib.pop('opacity','1'))
            for child in list(node):
                if child.get('data-part')=='edge':node.remove(child);edges.append(child)
        outer.append(node)
        clip_id=prefix+'-material-'+meta[i]['id']
        clip=E.SubElement(defs,'{'+NS+'}clipPath',id=clip_id,clipPathUnits='userSpaceOnUse')
        tag,attrs=geometry(dict(name=icon['name'],shapes=[shapes[i]]))[0]
        attrs.pop('opacity',None)
        if 'fill-rule' in attrs:attrs['clip-rule']=attrs['fill-rule']
        E.SubElement(clip,'{'+NS+'}'+tag,attrs)
        clipped=E.SubElement(outer,'{'+NS+'}g',{'clip-path':'url(#'+clip_id+')','data-part':'contained'})
        for j in children:
            if roles[j]!='line':clipped.append(primitive(j))
        if edges:
            edge_group=E.SubElement(outer,'{'+NS+'}g')
            if node.get('transform'):edge_group.set('transform',node.get('transform'))
            edge_group.extend(edges)
        line_children=[j for j in children if roles[j]=='line']
        if line_children:
            # Keep semantic detail contrast independent of translucent material opacity.
            # Exclude the material edge from the line mask so caps cannot cover its border.
            mask_id=clip_id+'-interior'
            mask=E.SubElement(defs,'{'+NS+'}mask',id=mask_id,maskUnits='userSpaceOnUse',x='0',y='0',width='16',height='16',**{'mask-type':'luminance'})
            E.SubElement(mask,'{'+NS+'}'+tag,{**attrs,'fill':'white'})
            width=shapes[i].get('edge_width',1) if mode=='layered' and shapes[i].get('edge',True) else 0
            if width:E.SubElement(mask,'{'+NS+'}'+tag,{**attrs,'fill':'none','stroke':'black','stroke-width':str(width),'stroke-linejoin':'round'})
            line_group=E.SubElement(root,'{'+NS+'}g',{'mask':'url(#'+mask_id+')','data-part':'material-detail'})
            for j in line_children:line_group.append(primitive(j))
    E.indent(root)
    return E.tostring(root,encoding='unicode')+'\n'

def build(spec):
    if set(spec)-{'name','brief','style','strict','icons'}:raise ValueError('Unsupported pack field')
    icons=spec['icons'];style_config(spec['style'])
    strict=spec.get('strict',False)
    if not isinstance(strict,bool):raise ValueError('strict must be boolean')
    if not isinstance(icons,list) or not icons:raise ValueError('Empty pack')
    if len({s['name'] for s in icons})!=len(icons):raise ValueError('Duplicate icon name')
    if strict:
        signatures=[json.dumps([{k:v for k,v in sh.items() if k not in ('id','parent','opacity','relief','gradient')} for sh in s['shapes']],sort_keys=True) for s in icons]
        if len(set(signatures))!=len(signatures):raise ValueError('Duplicate icon geometry in a strict pack')
    return {f'{s["name"]}-{t}.svg':render_icon(s,spec['style'],t,strict) for s in icons for t in ('light','dark')}

def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--spec',type=Path,required=True);ap.add_argument('--out',type=Path,required=True);ap.add_argument('--audit',type=Path);args=ap.parse_args()
    spec=json.loads(args.spec.read_text());files=build(spec)
    args.out.mkdir(parents=True,exist_ok=True)
    for name,data in files.items():(args.out/name).write_text(data)
    if args.audit:
        rows=[dict(name=s['name'],rules=prepare(s,spec['style'],spec.get('strict',False))[-1]) for s in spec['icons']]
        args.audit.parent.mkdir(parents=True,exist_ok=True);args.audit.write_text(json.dumps(rows,ensure_ascii=False,indent=2)+'\n')
    print(f'{spec["name"]}: {len(files)} SVGs; style {spec["style"].get("mode","layered")}')
if __name__=='__main__':main()
