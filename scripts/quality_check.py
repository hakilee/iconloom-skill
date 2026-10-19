#!/usr/bin/env python3
"""Detect drift from the reviewed regression batch; never rewrite the accepted baseline."""
import argparse,hashlib,json,subprocess,sys
from pathlib import Path
from compose import compile_spec
from generate import render
from pack import build

ROOT=Path(__file__).resolve().parents[1]
def baseline_check(baseline):
    actual={}
    for blueprint in baseline['blueprints']:
        compiled=compile_spec(blueprint)
        for theme in ('light','dark'):
            name=f"{compiled['name']}-{theme}.svg"
            if name in actual:raise ValueError('Duplicate baseline output: '+name)
            actual[name]=hashlib.sha256(render(compiled,theme).encode()).hexdigest()
    expected=baseline['sha256']
    changed=[name for name in sorted(actual.keys()|expected.keys()) if actual.get(name)!=expected.get(name)]
    return dict(passed=not changed,designs=len(baseline['blueprints']),files=len(actual),changed_files=changed)

def examples_check(root=ROOT):
    """Replay public source specs against checked-in SVGs, including missing/extra files."""
    expected={}
    def add(directory,name,svg):
        path=directory+'/'+name
        if path in expected:raise ValueError('Duplicate example output: '+path)
        expected[path]=hashlib.sha256(svg.encode()).hexdigest()
    try:
        abstract=json.loads((root/'examples/abstract/specs.json').read_text())
        if not isinstance(abstract,list) or not abstract:raise ValueError('Missing abstract example specs')
        for spec in abstract:
            for theme in ('light','dark'):
                add('abstract/svg',spec['name']+'-'+theme+'.svg',render(spec,theme))
        sources=sorted((root/'examples/specs').glob('*.json'))
        if not sources:raise ValueError('Missing object example specs')
        for source in sources:
            for name,svg in build(json.loads(source.read_text())).items():add('svg',name,svg)
    except (OSError,ValueError,TypeError,KeyError) as error:
        return dict(passed=False,error=str(error))
    actual={p.relative_to(root/'examples').as_posix():hashlib.sha256(p.read_bytes()).hexdigest()
            for p in (root/'examples').rglob('*.svg')}
    changed=[name for name in sorted(expected.keys()|actual.keys()) if expected.get(name)!=actual.get(name)]
    return dict(passed=not changed,files=len(expected),changed_files=changed)

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--out',type=Path)
    ap.add_argument('--baseline-only',action='store_true')
    args=ap.parse_args()
    result={'baseline':baseline_check(json.loads((ROOT/'references/quality-baseline.json').read_text()))}
    fixture=json.loads((ROOT/'references/quality-pack-baseline.json').read_text())
    actual={s['name']+'/'+n:hashlib.sha256(t.encode()).hexdigest() for s in fixture['packs'] for n,t in build(s).items()}
    changed=[n for n in sorted(actual.keys()|fixture['sha256'].keys()) if actual.get(n)!=fixture['sha256'].get(n)]
    result['pack_baseline']={'passed':not changed,'files':len(actual),'changed_files':changed}
    result['examples']=examples_check()
    if not args.baseline_only:
        checks={}
        for script in ['test_blueprints.py','self_test.py','test_pack.py','test_materials.py','test_keylines.py','test_construction.py']:
            p=subprocess.run([sys.executable,str(ROOT/'scripts'/script)],capture_output=True,text=True)
            entry={'passed':p.returncode==0}
            if p.returncode:entry['diagnostics']=(p.stdout+p.stderr)[-12000:]
            elif script=='test_blueprints.py':entry['summary']={k:v for k,v in json.loads(p.stdout).items() if k!='results'}
            else:entry['summary']=p.stdout.strip()
            checks[script]=entry
        result['checks']=checks
    result['passed']=all(result[k]['passed'] for k in ('baseline','pack_baseline','examples')) and all(c['passed'] for c in result.get('checks',{}).values())
    result['scope']='Output drift and mechanical invariants; not a visual similarity score.'
    text=json.dumps(result,ensure_ascii=False,indent=2)+'\n'
    if args.out:
        args.out.parent.mkdir(parents=True,exist_ok=True);args.out.write_text(text)
    print(text)
    return 0 if result['passed'] else 1
if __name__=='__main__':raise SystemExit(main())
