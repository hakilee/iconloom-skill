#!/usr/bin/env python3
"""Exercise scene ownership, native width budget and recognition-plan failures."""
import copy,tempfile
from pathlib import Path
import xml.etree.ElementTree as E
from pack import build,prepare
from validate import check
N={'s':'http://www.w3.org/2000/svg'}
def main():
 spec=dict(name='material-probe',strict=True,style=dict(mode='layered',stroke_width=.85),icons=[dict(name='probe',recognition=dict(silhouette='case',cue='stripe',confusable='tile',difference='handle and stripe',cue_ids=['stripe']),shapes=[dict(id='body',tag='rect',x=3,y=3,width=10,height=10,rx=2,rotate=8),dict(id='stripe',role='surface',parent='body',tag='rect',x=9,y=2,width=2,height=12,rx=1,opacity=.4),dict(id='detail',role='line',parent='body',tag='path',d='M4 7 L12 7'),dict(id='part',tag='rect',x=1.5,y=5,width=1.2,height=6,rx=.6)])])
 shapes,roles,meta,parents,notes=prepare(spec['icons'][0],spec['style'],True)
 assert shapes[3]['edge_width']==0
 assert parents==[None,0,0,None]
 assert shapes[1]['edge'] is False and shapes[1]['relief']==0
 files=build(spec)
 with tempfile.TemporaryDirectory() as td:
  gs=[]
  for n,text in files.items():
   p=Path(td)/n;p.write_text(text);err,g=check(p,'pack');assert not err,err;gs.append(g)
   r=E.fromstring(text);mat=r.find("s:g[@data-material='body']",N)
   assert mat is not None
   contained=mat.find("s:g[@data-part='contained']",N)
   assert len(contained)==1
   assert r.find("s:g[@data-part='material-detail']",N) is not None
   assert list(mat)[-1].find(".//*[@data-part='edge']") is not None
   assert r.find("s:defs/s:clipPath[@id='probe-"+('dark' if '-dark' in n else 'light')+"-material-body']/s:rect",N).get('transform')=='rotate(8 8 8)'
  assert gs[0]==gs[1]
 negatives=0
 def fail(change):
  nonlocal negatives
  s=copy.deepcopy(spec);change(s)
  try:build(s)
  except (ValueError,TypeError):negatives+=1
  else:raise AssertionError('Invalid material plan accepted')
 fail(lambda s:s['icons'][0].pop('recognition'))
 fail(lambda s:s['icons'][0]['recognition'].update(cue_ids=['absent']))
 fail(lambda s:s['icons'][0]['shapes'][1].update(parent='stripe'))
 fail(lambda s:s['icons'][0]['shapes'][1].update(parent='absent'))
 fail(lambda s:s['icons'][0]['shapes'][1].pop('parent'))
 fail(lambda s:s['icons'][0]['shapes'][1].update(id='body'))
 fail(lambda s:s['icons'][0]['shapes'][3].update(width=.6))
 fail(lambda s:s['style'].update(stroke_width=.4))
 duplicate=copy.deepcopy(spec['icons'][0]);duplicate['name']='probe-duplicate'
 fail(lambda s:s['icons'].append(duplicate))
 # No shape-name dispatch: renamed scene produces the same plans and geometry.
 renamed=copy.deepcopy(spec['icons'][0]);renamed['name']='different-subject'
 assert prepare(renamed,spec['style'],True)==prepare(spec['icons'][0],spec['style'],True)
 # Legacy inference is deterministic and only applies to largely contained material.
 legacy=copy.deepcopy(spec['icons'][0]);legacy.pop('recognition')
 for sh in legacy['shapes']:sh.pop('parent',None);sh.pop('id',None)
 legacy['shapes'][1].update(role='body',edge=False,x=9,y=3,height=10)
 sh,ro,me,pa,no=prepare(legacy,spec['style'],False)
 assert ro[1]=='surface' and pa[1]==0 and pa[3] is None
 print(f'PASS: contained paint order, rotated parent clip, narrow-part color budget, theme geometry, {negatives} invalid plans, subject-name invariance, legacy inference')
if __name__=='__main__':main()
