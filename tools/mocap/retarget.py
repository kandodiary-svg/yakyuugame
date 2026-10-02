import numpy as np
from bvh import *
LG=dict(th=0.47,sh=0.45,ua=0.31,fa=0.29)
def euler_YXZ(M):
    # three.js Euler 'YXZ' from rotation matrix (columns X,Y,Z): 
    m=M;x=np.arcsin(-np.clip(m[1,2],-1,1))
    if abs(m[1,2])<0.9999: y=np.arctan2(m[0,2],m[2,2]);z=np.arctan2(m[1,0],m[1,1])
    else: y=np.arctan2(-m[2,0],m[0,0]);z=0
    return x,y,z
def Ry(th):
    c,s=np.cos(th),np.sin(th);return np.array([[c,0,s],[0,1,0],[-s,0,c]])
def retarget(P,idx,yaw=0.0,mirror=False,keep_xz=False,xz0=None):
    """P: dict name->(N,3) world pos. idx: frame indices. returns dict of arrays in game coords."""
    g=lambda n:np.array([P[n][i] for i in idx])
    # yaw about Y, then map (x,y,z)->(x,y,-z)
    Rm=Ry(yaw)
    def T(a):
        a=a@Rm.T;a=a*np.array([1,1,-1]);
        if mirror:a=a*np.array([-1,1,1])
        return a
    J={n:T(g(n)) for n in ['Hips','Neck','LeftArm','RightArm','LeftForeArm','RightForeArm','LeftHand','RightHand','LeftLeg','RightLeg','LeftFoot','RightFoot','LeftUpLeg','RightUpLeg','LeftToeBase','RightToeBase','Head']}
    if mirror: # swap L/R
        for a,b in [('LeftArm','RightArm'),('LeftForeArm','RightForeArm'),('LeftHand','RightHand'),('LeftLeg','RightLeg'),('LeftFoot','RightFoot'),('LeftUpLeg','RightUpLeg'),('LeftToeBase','RightToeBase')]:
            J[a],J[b]=J[b],J[a]
    n0=len(idx)
    legM=np.mean(np.linalg.norm(J['LeftUpLeg']-J['LeftLeg'],axis=1)+np.linalg.norm(J['LeftLeg']-J['LeftFoot'],axis=1))
    armM=np.mean(np.linalg.norm(J['RightArm']-J['RightForeArm'],axis=1)+np.linalg.norm(J['RightForeArm']-J['RightHand'],axis=1))
    sl=(LG['th']+LG['sh'])*0.985/legM; ar=(LG['ua']+LG['fa'])*0.97/armM
    ground=min(J['LeftFoot'][:,1].min(),J['RightFoot'][:,1].min())
    out=[]
    hips=J['Hips']
    xz0=hips[0,[0,2]] if xz0 is None else xz0
    prev=None
    res=dict(pel=[],rx=[],ry=[],rz=[],hL=[],hR=[],fL=[],fR=[],eL=[],eR=[])
    for i in range(n0):
        h=hips[i]
        Y=J['Neck'][i]-h;Y/=np.linalg.norm(Y)
        X=J['RightArm'][i]-J['LeftArm'][i];X=X-Y*np.dot(X,Y);X/=np.linalg.norm(X)
        Z=np.cross(X,Y);Z/=np.linalg.norm(Z)
        M=np.stack([X,Y,Z],1)
        rx,ry,rz=euler_YXZ(M)
        if prev is not None:
            while ry-prev>np.pi:ry-=2*np.pi
            while ry-prev<-np.pi:ry+=2*np.pi
        prev=ry
        pel=np.array([(h[0]-xz0[0])*sl,(h[1]-ground)*sl+0.12-0.0,(h[2]-xz0[1])*sl])
        # game body transform for shoulders
        sh={}
        for s,name in [(-1,'L'),(1,'R')]:
            loc=np.array([0.19*s,0.57,0.0]);
            # body matrix = T(pel)*Ry(ry)*Rx(rx)*Rz(rz)  (three YXZ order)
            cx,sx=np.cos(rx),np.sin(rx);cy,sy=np.cos(ry),np.sin(ry);cz,sz=np.cos(rz),np.sin(rz)
            RY=np.array([[cy,0,sy],[0,1,0],[-sy,0,cy]]);RX=np.array([[1,0,0],[0,cx,-sx],[0,sx,cx]]);RZ=np.array([[cz,-sz,0],[sz,cz,0],[0,0,1]])
            sh[name]=pel+RY@RX@RZ@loc
        res['pel'].append(pel);res['rx'].append(rx);res['ry'].append(ry);res['rz'].append(rz)
        for name,hn,en,an in [('L','LeftHand','LeftForeArm','LeftArm'),('R','RightHand','RightForeArm','RightArm')]:
            hand=sh[name]+ar*(J[hn][i]-J[an][i]);elb=sh[name]+ar*(J[en][i]-J[an][i])
            res['h'+name].append(hand);res['e'+name].append(elb)
        for name,fn in [('L','LeftFoot'),('R','RightFoot')]:
            f=J[fn][i];fx=pel[0]+sl*(f[0]-h[0]);fz=pel[2]+sl*(f[2]-h[2]);fy=max(0.08,(f[1]-ground)*sl+0.08)
            res['f'+name].append(np.array([fx,fy,fz]))
    return {k:np.array(v) for k,v in res.items()},dict(sl=sl,ar=ar,legM=legM,armM=armM)
