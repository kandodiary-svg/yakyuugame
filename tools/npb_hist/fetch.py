import re,subprocess,json,sys,time
from concurrent.futures import ThreadPoolExecutor
TEAMS=['g','t','db','c','s','d','h','f','m','e','l','b']
YEARS=[2022,2023,2024,2025]
def get(u):
    for _ in range(3):
        r=subprocess.run(['curl','-s','-m','30',u],capture_output=True)
        if r.returncode==0 and len(r.stdout)>2000:return r.stdout.decode('utf-8','ignore')
        time.sleep(1)
    return ''
import unicodedata
FOLD=str.maketrans({'髙':'高','﨑':'崎','德':'徳','邉':'辺','邊':'辺','澤':'沢','國':'国','齋':'斎','齊':'斉','濵':'浜','濱':'浜','嶋':'島','﨏':'迫','廣':'広','櫻':'桜','淺':'浅','實':'実','眞':'真','惠':'恵','榮':'栄'})
def norm(n):
    return unicodedata.normalize('NFKC',re.sub(r'[\s\u3000\*\+]','',n)).translate(FOLD)
def rows(h):
    out=[]
    for r in re.findall(r'<tr[^>]*>(.*?)</tr>',h,re.S):
        cells=[re.sub(r'<[^>]+>','',c).strip() for c in re.findall(r'<t[dh][^>]*>(.*?)</t[dh]>',r,re.S)]
        out.append(cells)
    return out
def job(a):
    y,t,k=a
    h=get(f'https://npb.jp/bis/{y}/stats/id{k}1_{t}.html')
    return a,rows(h)
jobs=[(y,t,k) for y in YEARS for t in TEAMS for k in ('b','p')]
res={}
with ThreadPoolExecutor(6) as ex:
    for a,r in ex.map(job,jobs):res[a]=r
B={};P={}
miss=[a for a,r in res.items() if len(r)<5]
print('missing',miss)
for (y,t,k),rs in res.items():
    for c in rs:
        if k=='b':
            if len(c)<24 or not c[2].isdigit():continue
            n=norm(c[1]);v=[int(x) for x in (c[2],c[3],c[4],c[6],c[7],c[8],c[9],c[11],c[13],c[17],c[20])] if False else None
            # cols: 0 mark,1 name,2 G,3 PA,4 AB,5 R,6 H,7 2B,8 3B,9 HR,10 TB,11 RBI,12 SB,13 CS,14 SH,15 SF,16 BB,17 IBB,18 HBP,19 K
            try:v=[int(c[i]) for i in (2,3,4,6,7,8,9,12,16,19)]
            except:continue
            B.setdefault(n,{})
            old=B[n].get(y)
            B[n][y]=[a+b for a,b in zip(old,v)] if old else v
        else:
            if len(c)<24:continue
            if not c[1].isdigit():continue
            n=norm(c[0])
            try:
                ipS=c[12]
                v=[int(c[1]),ipS,int(c[4]),int(c[5]),int(c[13]),int(c[14]),int(c[15]),int(c[18]),int(c[22])]
            except:continue
            P.setdefault(n,{})
            old=P[n].get(y)
            if old:
                def addip(a,b):
                    ia,fa=a.split('.') if '.' in a else (a,'0');ib,fb=b.split('.') if '.' in b else (b,'0')
                    tot=(int(ia)+int(ib))*3+int(fa)+int(fb);return f'{tot//3}.{tot%3}'
                P[n][y]=[old[0]+v[0],addip(old[1],v[1])]+[a+b for a,b in zip(old[2:],v[2:])]
            else:P[n][y]=v
json.dump({'B':B,'P':P},open('hist.json','w'),ensure_ascii=False)
print(len(B),len(P))
