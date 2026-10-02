import sys,json;sys.path.insert(0,'.')
from retarget import *
import numpy as np
def clip(name,tA,tN,tB,dA,dB,fps=60,hand='R'):
    J,d,ft=parse(name+'.bvh');P,_=fk(J,d)
    ts=[]
    for i in range(int(dA*fps)): ts.append(tA+(tN-tA)*i/(dA*fps))
    for i in range(int(dB*fps)+1): ts.append(tN+(tB-tN)*i/(dB*fps))
    names=list(P.keys())
    def at(k,t):
        fi=t/ft;i=int(fi);f=fi-i;return P[k][i]*(1-f)+P[k][i+1]*f
    PP={k:np.array([at(k,t) for t in ts]) for k in names}
    best=None
    for yaw in np.linspace(-np.pi,np.pi,72,endpoint=False):
        res,info=retarget(PP,list(range(len(ts))),yaw=yaw)
        # forward means hand z at nadir large, and hips-to-shoulder facing: choose max of lowest hand z
        j=int(dA*fps);hz=max(res['hL'][j][2],res['hR'][j][2])
        if best is None or hz>best[0]:best=(hz,yaw,res)
    hz,yaw,res=best
    print(name,'yaw',round(yaw,2),'nadir hand z',round(hz,2))
    # recentre xz on first frame pel
    cx,cz=res['pel'][0][0],res['pel'][0][2]
    for k in ['pel','hL','hR','fL','fR','eL','eR']:res[k][:,0]-=cx;res[k][:,2]-=cz
    return res,len(ts),int(dA*fps)
if __name__=='__main__':
    res,n,j=clip('64_26',2.0,2.67,3.3,0.3,0.35)
    for i in [0,j//2,j,j+10,n-1]:
        print(i,'pel',res['pel'][i].round(2),'rx',round(res['rx'][i],2),'hL',res['hL'][i].round(2),'hR',res['hR'][i].round(2),'fL',res['fL'][i].round(2),'fR',res['fR'][i].round(2))
