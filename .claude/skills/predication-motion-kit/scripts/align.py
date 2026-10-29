import numpy as np,re,json
from scipy.io import wavfile
from scipy.signal import butter,sosfiltfilt,find_peaks
import os,types
_C=json.load(open(os.environ.get('KIT_CFG','config.json')))
render=types.SimpleNamespace(TXT=[s['text'] for s in _C['scenes']]); END=float(_C['end'])
sr,x=wavfile.read("a16.wav"); x=x.astype(float)/32768
sos=butter(4,[300,2500],btype="band",fs=sr,output="sos"); y=sosfiltfilt(sos,x)
hop=160; n=len(y)//hop
e=np.sqrt(np.array([np.mean(y[i*hop:(i+1)*hop]**2) for i in range(n)]))
db=20*np.log10(e+1e-9)
k=np.hanning(9);k/=k.sum(); s=np.convolve(db,k,mode="same")
floor=np.percentile(s,15); voiced=s>floor+12
pk,_=find_peaks(s,distance=9,prominence=3.5)
nuc=np.array([p*0.01 for p in pk if voiced[p]])
# speech chunks: voiced runs separated by >=0.16s unvoiced
t=np.arange(n)*0.01; runs=[];st=None;last=None
for i,v in enumerate(voiced):
    if v:
        if st is None: st=i
        elif i-last>16: runs.append((st,last)); st=i
        last=i
if st is not None: runs.append((st,last))
sl=[float(v) for v in open("sil.txt").read().split()]
chunks=[];prev=0.0
for a,b in zip(sl[0::2],sl[1::2]):
    if a-prev>0.12: chunks.append((prev,a))
    prev=b
if END-prev>0.12: chunks.append((prev,END))
# words
words=[];sent=[]
for si,txt in enumerate(render.TXT):
    for w in txt.replace(":","").split():
        words.append((si,w))
def syl(w):
    w=w.lower(); w=re.sub(r"[^a-zàâäéèêëîïôöûùüœç'-]","",w)
    if w in("i","for","you","pray"): return 1
    parts=[p for p in re.split(r"[-']",w) if p]
    c=0
    for p in parts:
        g=len(re.findall(r"[aeiouyàâäéèêëîïôöûùüœ]+",p))
        if g>1 and re.search(r"(e|es|ent)$",p) and not p.endswith(("ée","ées")): g-=1
        c+=max(g,1 if re.search(r"[aeiouyàâäéèêëîïôöûùüœ]",p) else 0)
    return max(c,1)
S=[syl(w) for _,w in words]
punct=[bool(re.search(r"[.,?!:]$",w)) for _,w in words]
cn=[int(((nuc>=a-0.03)&(nuc<=b+0.03)).sum()) for a,b in chunks]
print("words",len(words),"syl",sum(S),"nuclei",len(nuc),"in chunks",sum(cn),"chunks",len(chunks))
rate=sum(cn)/sum(S)
W=len(words);C=len(chunks);INF=1e18
cs=np.concatenate([[0],np.cumsum(S)])
D=np.full((C+1,W+1),INF);P=np.zeros((C+1,W+1),int);D[0,0]=0
for c in range(1,C+1):
    for j in range(0,W+1):
        best=INF;arg=0
        for i in range(max(0,j-25),j+1):
            if D[c-1,i]>=INF: continue
            sy=(cs[j]-cs[i])*rate
            cost=(sy-cn[c-1])**2/(1+0.3*cn[c-1])
            if j==i: cost=cn[c-1]**2*2+4   # empty chunk
            else:
                # boundary at end of chunk: prefer punctuation
                cost+= -1.5 if punct[j-1] else 0.8
            v=D[c-1,i]+cost
            if v<best: best=v;arg=i
        D[c,j]=best;P[c,j]=arg
# backtrack
assign=[];j=W
for c in range(C,0,-1):
    i=P[c,j]; assign.append((c-1,i,j)); j=i
assign.reverse()
WT=[None]*W
for c,i,j in assign:
    if j==i: continue
    a,b=chunks[c]; nn=[v for v in nuc if a-0.03<=v<=b+0.03]
    tot=cs[j]-cs[i]
    for k in range(i,j):
        if k==i: WT[k]=a; continue
        f=(cs[k]-cs[i])/tot
        if len(nn)>=2:
            pos=f*len(nn); q=min(int(pos),len(nn)-1)
            tt=nn[q]-0.06
            WT[k]=max(tt,WT[k-1]+0.08)
        else: WT[k]=a+(b-a)*f
json.dump([(WT[k],words[k][0],words[k][1]) for k in range(W)],open("wt.json","w"),ensure_ascii=False)
for c,i,j in assign: print(f"{chunks[c][0]:6.2f}-{chunks[c][1]:6.2f} n={cn[c]:2d} s={cs[j]-cs[i]:2d} | "+" ".join(w for _,w in words[i:j]))
