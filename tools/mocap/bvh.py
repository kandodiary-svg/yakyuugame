import numpy as np,re
def rot(axis,a):
    c,s=np.cos(a),np.sin(a);N=len(a);R=np.zeros((N,3,3));R[:,:,:]=np.eye(3)
    if axis=='X':R[:,1,1]=c;R[:,1,2]=-s;R[:,2,1]=s;R[:,2,2]=c
    elif axis=='Y':R[:,0,0]=c;R[:,0,2]=s;R[:,2,0]=-s;R[:,2,2]=c
    else:R[:,0,0]=c;R[:,0,1]=-s;R[:,1,0]=s;R[:,1,1]=c
    return R
def parse(path):
    toks=open(path).read().split('\n');J=[];stack=[];i=0;ft=1/120
    while i<len(toks):
        l=toks[i].strip();i+=1
        if l.startswith(('ROOT','JOINT')):
            J.append({'name':l.split()[1],'parent':stack[-1] if stack else None,'off':None,'ch':[]});stack.append(len(J)-1)
        elif l.startswith('End Site'):stack.append(None)
        elif l.startswith('OFFSET'):
            if stack[-1] is not None:J[stack[-1]]['off']=np.array(list(map(float,l.split()[1:4])))
        elif l.startswith('CHANNELS'):
            p=l.split();J[stack[-1]]['ch']=p[2:]
        elif l=='}':stack.pop()
        elif l.startswith('Frame Time'):ft=float(l.split(':')[1])
        elif l.startswith('Frames'):nf=int(l.split(':')[1])
        elif l=='MOTION':break
    # find motion data
    while not toks[i].strip().startswith('Frame Time'):i+=1
    ft=float(toks[i].split(':')[1]);i+=1
    data=np.array([list(map(float,t.split())) for t in toks[i:] if t.strip()])
    return J,data,ft
def fk(J,data):
    N=len(data);pos={};R={};col=0
    for j,jt in enumerate(J):
        ch=jt['ch'];vals={}
        for c in ch:vals[c]=data[:,col];col+=1
        Rl=np.tile(np.eye(3),(N,1,1))
        for c in ch:
            if c.endswith('rotation'):Rl=Rl@rot(c[0],np.deg2rad(vals[c]))
        off=jt['off'] if jt['off'] is not None else np.zeros(3)
        loc=np.tile(off,(N,1))
        if 'Xposition' in vals:loc=loc+np.stack([vals['Xposition'],vals['Yposition'],vals['Zposition']],1)
        p=jt['parent']
        if p is None:R[j]=Rl;pos[j]=loc
        else:R[j]=R[p]@Rl;pos[j]=pos[p]+np.einsum('nij,nj->ni',R[p],loc)
    return {J[j]['name']:pos[j] for j in pos},{J[j]['name']:R[j] for j in R}
