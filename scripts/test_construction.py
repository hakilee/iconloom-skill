import copy
from pack import prepare,build

def main():
 s={'mode':'duotone','stroke_width':1,'grid':'keyline-16'}
 icon={'name':'joint','layout':{'fit':'preserve','keyline':'square'},'shapes':[
 {'id':'body','tag':'rect','x':3,'y':4,'width':6,'height':8,'rx':1},
 {'id':'arm','tag':'path','role':'line','d':'M8 8 L13 8'}],
 'construction':{'joins':[['body','arm']]}}
 shapes,roles,meta,parents,notes=prepare(icon,s)
 assert shapes[0]['x']==3 and shapes[1]['d']=='M8 8 L13 8'
 assert any(n['rule']=='declared-joint' for n in notes)
 for d in ['M9.5 8 L13 8','M10 8 L13 8']:
  bad=copy.deepcopy(icon);bad['shapes'][1]['d']=d
  try:prepare(bad,s)
  except ValueError as e:assert 'joint' in str(e)
  else:raise AssertionError('Tangent or disconnected arm accepted')
 gap=copy.deepcopy(icon);gap['shapes'][1]['d']='M11 5 L11 11';gap['construction']={'gaps':[{'parts':['body','arm'],'min':1}]}
 assert prepare(gap,s)[-1][-1]['passed']
 gap['shapes'][1]['d']='M9.75 5 L9.75 11'
 try:prepare(gap,s)
 except ValueError as e:assert 'gap' in str(e)
 else:raise AssertionError('Narrow gap accepted')
 for con in [{'joins':[['body','missing']]},{'joins':[['body','body']]},{'gaps':[{'parts':['body','arm'],'min':0}]},{'joins':'bad'},{'unknown':[]}]:
  bad=copy.deepcopy(icon);bad['construction']=con
  try:prepare(bad,s)
  except ValueError:pass
  else:raise AssertionError('Invalid relationship accepted')
 bad=copy.deepcopy(icon);bad['layout']['fit']='stretch'
 try:prepare(bad,s)
 except ValueError:pass
 else:raise AssertionError('Unknown fitting mode accepted')
 # Constraints annotate source semantics but never alter SVG rendering.
 plain=copy.deepcopy(icon);plain.pop('construction')
 assert build({'name':'p','style':s,'icons':[icon]})==build({'name':'p','style':s,'icons':[plain]})
 # Preserve mode must keep native coordinates, not recenter or rescale them.
 assert notes[0]['scale']==1 and notes[0]['translation']==[0,0]
 print('PASS: connected/point-contact/detached parts, meaningful gaps, 6 invalid inputs, exact coordinate preservation, non-mutating construction checks')
if __name__=='__main__':main()
