#!/usr/bin/env python3
"""Validate safe local SVG structure and theme geometry, not aesthetic similarity."""
import argparse,re,sys,json
from pathlib import Path
import xml.etree.ElementTree as E
ALLOWED={'svg','title','desc','defs','linearGradient','stop','g','path','circle','ellipse','rect','clipPath','filter','feOffset','feGaussianBlur','feComposite','feFlood','feMerge','feMergeNode','mask'}
SHAPES={'path','circle','ellipse','rect'}
GEOMETRY={'d','cx','cy','r','rx','ry','x','y','width','height','transform','opacity','fill-rule','clip-rule'}
def check(path,profile="agent"):
    errors=[]
    try:r=E.parse(path).getroot()
    except E.ParseError as e:return [str(e)],None
    if r.tag!='{http://www.w3.org/2000/svg}svg':errors.append('Missing SVG namespace/root')
    if r.get('viewBox')!='0 0 16 16' or r.get('width')!='16' or r.get('height')!='16':errors.append('Expected native 16×16')
    ids=[e.get('id') for e in r.iter() if e.get('id')]
    if len(ids)!=len(set(ids)):errors.append('Duplicate IDs')
    for e in r.iter():
        tag=e.tag.split('}')[-1]
        if tag not in ALLOWED:errors.append('Unsupported element '+tag)
        for k,v in e.attrib.items():
            if k.lower().startswith('on') or k in {'style','href','{http://www.w3.org/1999/xlink}href'}:errors.append('Active/external attribute '+k)
            if 'url(' in v and not re.fullmatch(r'url\(#[A-Za-z0-9_-]+\)',v):errors.append('Nonlocal URL')
            for ref in re.findall(r'url\(#([^)]*)\)',v):
                if ref not in ids:errors.append('Unresolved ID '+ref)
    geometry=[]
    # Clip geometry is structural too: theme-only clip changes alter the visible icon.
    for clip in r.iter():
        if clip.tag.split('}')[-1]in {'clipPath','mask'}:
            geometry.append((clip.tag.split('}')[-1],[(c.tag.split('}')[-1],sorted((k,v) for k,v in c.attrib.items() if k in GEOMETRY or k in {'fill','stroke','stroke-width','stroke-linejoin'})) for c in clip]))
    def visible(e,depth=0):
        tag=e.tag.split('}')[-1]
        if tag in {'defs','title','desc'}:return
        if tag in SHAPES|{'g'}:
            geometry.append((depth,tag,sorted((k,v) for k,v in e.attrib.items() if k in GEOMETRY)))
        if tag in SHAPES:
            if profile=='pack':
                geometry.append(('paint-role',e.get('data-part'),[(k,e.get(k)) for k in ('stroke-width','stroke-linecap','stroke-linejoin')]))
            elif e.get('data-part')=='edge':
                try:width=float(e.get('stroke-width',''))
                except (ValueError,TypeError):width=0
                if not 0<width<=1 or not e.get('clip-path'):errors.append('Expected silhouette-clipped edge with stroke width in (0, 1]')
                geometry.append(('edge-style',width,e.get('stroke-linejoin')))
            elif not e.get('fill','').startswith('url(#'):errors.append('Expected tonal gradient fill')
        for child in e:visible(child,depth+1)
    visible(r)
    if not geometry:errors.append('No visible geometry')
    return errors,geometry

def main():
    ap=argparse.ArgumentParser();ap.add_argument('directory',type=Path);ap.add_argument('--profile',choices=['agent','pack'],default='agent');args=ap.parse_args();files=sorted(args.directory.glob('*.svg'));issues={};geometries={}
    for p in files:
        err,geo=check(p,args.profile);geometries[p.name]=geo
        if err:issues[p.name]=err
    for p in files:
        if p.name.endswith('-light.svg'):
            dark=p.name.replace('-light.svg','-dark.svg')
            if dark not in geometries:issues.setdefault(p.name,[]).append('Missing dark pair')
            elif geometries[p.name]!=geometries[dark]:issues.setdefault(p.name,[]).append('Theme geometry mismatch')
        elif p.name.endswith('-dark.svg'):
            if p.name.replace('-dark.svg','-light.svg') not in geometries:issues.setdefault(p.name,[]).append('Missing light pair')
        else:issues.setdefault(p.name,[]).append('Expected theme suffix')
    result={'files':len(files),'passed':bool(files) and not issues,'issues':issues};print(json.dumps(result,indent=2));sys.exit(0 if result['passed'] else 1)
if __name__=='__main__':main()
