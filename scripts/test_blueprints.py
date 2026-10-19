#!/usr/bin/env python3
"""Check supported parameter corners, topology, and renderer failure detection."""
import itertools,json,tempfile,xml.etree.ElementTree as E
from pathlib import Path
from compose import FAMILIES,compile_spec
from geometry_audit import audit
from generate import render
from validate import check

def main():
    reports=[]
    for family in FAMILIES:
        for spread,weight,phase in itertools.product((-1,1),(-1,1),(-12,12)):
            s=dict(name='boundary',family=family,spread=spread,weight=weight,phase=phase)
            r=audit(s);reports.append(dict(family=family,spread=spread,weight=weight,phase=phase,**r))
        reports.append(dict(family=family,**audit(dict(name='default',family=family))))
    assert all(r['passed'] for r in reports),json.dumps([r for r in reports if not r['passed']],indent=2)
    rejected=0
    for extra in [dict(spread=1.01),dict(weight=-1.01),dict(phase=13),dict(spread=True),dict(weight=float('nan')),dict(shapes=[]),dict(family='unknown')]:
        try:compile_spec(dict(dict(name='invalid',family='tile-weave'),**extra))
        except (ValueError,KeyError):rejected+=1
        else:raise AssertionError('Accepted invalid blueprint: '+str(extra))
    # A disconnected layer and a tangent connection must not pass just because XML is valid.
    bad=dict(name='disconnected',shapes=[dict(tag='circle',cx=4,cy=8,r=2),dict(tag='circle',cx=12,cy=8,r=2)])
    assert not audit(bad)['passed']
    bad['shapes'][1]['cx']=8
    assert not audit(bad)['passed']
    # Removing the pinwheel's structural ring disconnects its blades.
    broken=compile_spec(dict(name='broken',family='pinwheel-knot'));del broken['shapes'][2]
    assert not audit(broken)['passed']
    with tempfile.TemporaryDirectory() as tmp:
        tmp=Path(tmp);s=compile_spec(dict(name='clip-test',family='pinwheel-knot'))
        light=tmp/'light.svg';dark=tmp/'dark.svg'
        light.write_text(render(s,'light'));dark.write_text(render(s,'dark'))
        assert check(light)[1]==check(dark)[1]
        tree=E.parse(dark);ns={'s':'http://www.w3.org/2000/svg'}
        hole=next(c for c in tree.findall('s:defs/s:clipPath/s:path',ns) if c.get('clip-rule')=='evenodd')
        hole.set('clip-rule','nonzero');tree.write(dark,encoding='unicode')
        assert check(light)[1]!=check(dark)[1],'Clip-only theme mismatch missed'
    print(json.dumps(dict(passed=True,boundary_and_default_cases=len(reports),invalid_blueprints_rejected=rejected,geometry_faults_rejected=3,clip_only_mismatch_detected=True,results=reports),indent=2))
if __name__=='__main__':main()
