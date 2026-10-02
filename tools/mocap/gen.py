import sys,json;sys.path.insert(0,'.')
from retarget import *
from scipy.signal import find_peaks
def pack(res,idx_range):
    rows=[]
    for i in idx_range:
        r=[*res['pel'][i],res['rx'][i],res['ry'][i],res['rz'][i],*res['hL'][i],*res['hR'][i],*res['fL'][i],*res['fR'][i],*res['eL'][i],*res['eR'][i]]
        rows.append([round(float(x),3) for x in r])
    return rows
def run_cycle(name,ta,tb,M=24):
    J,d,ft=parse(name+'.bvh');P,_=fk(J,d);fps=1/ft
    h=P['Hips'];trav=h[-1]-h[0];trav[1]=0;dirv=trav/np.linalg.norm(trav)
    ang=np.arctan2(dirv[2],dirv[0]);yaw=ang+np.pi/2
    ia,ib=int(ta/ft),int(tb/ft)
    # remove linear travel within [ia,ib]
    v=(h[ib]-h[ia])/(ib-ia);v[1]=0
    P2={k:p.copy() for k,p in P.items()}
    for k in P2:
        for i in range(len(d)):P2[k][i]=P2[k][i]-v*(i-ia)
    # resample frames with linear interp
    idxs=[ia+(ib-ia)*m/M for m in range(M+1)]
    # build interpolated P at fractional idx
    def interp(k,fi):
        i=int(np.floor(fi));f=fi-i;return P2[k][i]*(1-f)+P2[k][min(i+1,len(d)-1)]*f
    names=['Hips','Neck','LeftArm','RightArm','LeftForeArm','RightForeArm','LeftHand','RightHand','LeftLeg','RightLeg','LeftFoot','RightFoot','LeftUpLeg','RightUpLeg','LeftToeBase','RightToeBase','Head']
    PP={k:np.array([interp(k,fi) for fi in idxs]) for k in names}
    res,info=retarget(PP,list(range(M+1)),yaw=yaw)
    # xz of pelvis: recenter to mean
    cx=res['pel'][:M,0].mean();cz=res['pel'][:M,2].mean()
    for k in ['pel','hL','hR','fL','fR','eL','eR']:
        res[k][:,0]-=cx;res[k][:,2]-=cz
    # loop closure
    for k in ['pel','hL','hR','fL','fR','eL','eR']:
        dlt=res[k][0]-res[k][M]
        for m in range(M+1):
            w=max(0,(m/M-0.6)/0.4);w=w*w*(3-2*w);res[k][m]=res[k][m]+dlt*w
    for k in ['rx','ry','rz']:
        dlt=res[k][0]-res[k][M]
        for m in range(M+1):
            w=max(0,(m/M-0.6)/0.4);w=w*w*(3-2*w);res[k][m]=res[k][m]+dlt*w
    sp=np.linalg.norm(v)*fps*info['sl']  # m/s game scale
    dur=(ib-ia)*ft
    return dict(n=M,dur=round(dur,3),speed=round(float(sp),2),D=round(float(sp*dur),3),d=pack(res,range(M)))
out={}
out['sprint']=run_cycle('143_01',0.04,0.40)
out['jog']=run_cycle('09_01',0.01,0.66)
print({k:(v['dur'],v['speed'],v['D']) for k,v in out.items()})
# swing
J,d,ft=parse('124_07.bvh');P,_=fk(J,d)
t0=1.9;t1=3.9;fps=60
idx=[int(round((t0+i/fps)/ft)) for i in range(int((t1-t0)*fps))]
dv=(P['LeftFoot'][int(3.0/ft)]-P['LeftFoot'][int(1.9/ft)]);ang=np.arctan2(dv[2],dv[0]);yaw=ang-np.pi
res,info=retarget(P,idx,yaw=yaw)
out['swing']=dict(t0=t0,fps=fps,d=pack(res,range(len(idx))))
json.dump(out,open('mc_data.json','w'),separators=(',',':'))
import os;print('bytes',os.path.getsize('mc_data.json'))
for k,v in out.items():
    if k!='swing':
        a=np.array(v['d']);print(k,'pel y range',a[:,1].min(),a[:,1].max(),'fL y max',a[:,10].max(),'hand z range',a[:,8].min(),a[:,8].max(),'rx mean',a[:,3].mean())

# ---- pitching tracks ----
def pitch_track(name,rel,pre=1.5,post=0.9,fps=60):
    J,d,ft=parse(name+'.bvh');P,_=fk(J,d)
    t0=rel-pre;idx=[int(round((t0+i/fps)/ft)) for i in range(int((pre+post)*fps))]
    i0=idx[0];irel=int(round(rel/ft))
    dv=P['Hips'][int(round((rel+0.5)/ft))]-P['Hips'][i0];ang=np.arctan2(dv[2],dv[0]);yaw=ang+np.pi/2
    res,info=retarget(P,idx,yaw=yaw)
    # pivot foot (right) at rubber at start
    off=np.array([0.14-res['fR'][0][0],0,0.0-res['fR'][0][2]])
    for k in ['pel','hL','hR','fL','fR','eL','eR']:res[k]=res[k]+off
    return dict(t0=round(t0,3),fps=fps,rel=pre,d=pack(res,range(len(idx))))
out['p0']=pitch_track('124_01',3.72)
out['p1']=pitch_track('124_02',3.37)
json.dump(out,open('mc_data.json','w'),separators=(',',':'))
print('bytes',os.path.getsize('mc_data.json'))
a=np.array(out['p0']['d'])
for i in [0,30,60,90,120,143]:print(i,'pel',a[i,:3],'hR',a[i,9:12],'fL',a[i,12:15],'fR',a[i,15:18])

# ---- fielding: ground-ball scoop (64_26 Picking up Ball) ----
from scoop import clip
res,n,j=clip('26_09',1.3,2.2,3.0,0.3,0.35)
out['scoop']=dict(t0=0,fps=60,rel=0.3,d=pack(res,range(n)))
json.dump(out,open('mc_data.json','w'),separators=(',',':'))
print('bytes',os.path.getsize('mc_data.json'))
