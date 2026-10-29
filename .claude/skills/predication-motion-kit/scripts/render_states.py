import json,re,os,sys,math
import numpy as np
from PIL import Image,ImageDraw,ImageFont,ImageFilter
W,H=1080,1920
FD="/usr/share/fonts/truetype/google-fonts"
if not os.path.exists(f"{FD}/Poppins-Bold.ttf"):  # polices embarquées dans le skill
    FD=os.path.join(os.path.dirname(os.path.abspath(__file__)),"..","assets","fonts")
def F(n,s):
    return ImageFont.truetype(f"{FD}/{n}",s)
BOLD="Poppins-Bold.ttf"; MED="Poppins-Medium.ttf"; SEMI="Poppins-Bold.ttf"
def KF(s):
    f=ImageFont.truetype(f"{FD}/Lora-Italic-Variable.ttf",s)
    try: f.set_variation_by_name("Medium Italic")
    except Exception: pass
    return f
CFG=json.load(open(os.environ.get("KIT_CFG","config.json")))
END=float(CFG["end"]); START=float(CFG.get("start",0.9))
TXT=[sc["text"] for sc in CFG["scenes"]]
KEY=set(k.lower() for k in CFG.get("key_words",[]))
SIGTXT=CFG.get("signature","Une vie au cœur de l'impact")
CAPY=int(CFG.get("caption_y",1500))
FLAT_LABELS=CFG.get("flat_labels",["jan","fév","mar","avr","mai","juin"])
WT=[tuple(x) for x in json.load(open("wt.json"))]
def first(i,word=None,nth=0):
    c=[t for t,si,w in WT if si==i and (word is None or w.lower().startswith(word.lower()))]
    if len(c)<=nth: raise SystemExit(f"Ancre introuvable : scène {i}, mot '{word}' (n°{nth})")
    return c[nth]
N=len(TXT)
B=[START]+[round(first(i)-0.15,2) for i in range(1,N)]+[END]
def A(spec):
    """'S3' = début de la scène 3 ; 'S3:parce' = mot commençant par 'parce' ; 'S3:si#1' = 2e occurrence ; 'END'."""
    if spec=="END": return END
    sc,_,w=spec[1:].partition(":"); i=int(sc)
    if not w: return B[i]
    w,_,n=w.partition("#")
    return first(i,w,int(n or 0))-0.1
HEAD=[(A(h["from"]),A(h["to"]),h["kicker"],h["title"]) for h in CFG.get("heads",[])]
GFX=[(A(g["from"]),A(g["to"]),g["kind"],g.get("kicker",""),g["title"]) for g in CFG.get("gfx",[])]
PILLS=[]
for g in CFG.get("gfx",[]):
    if g["kind"]=="pills":
        PILLS=[(p["label"],A(p["at"])+0.1) for p in g["pills"]]
FLASH=sorted(set([x for x in B[1:-1]]+[g[0] for g in GFX]+[h[0] for h in HEAD]))
def clean(w): return re.sub(r"[.,:;!?…~«»]","",w).lower()
# groups: up to 3 words / 20 chars, break after key word or punctuation
GROUPS=[]  # list of (scene, [idx in WT])
cur=[];curs=None
for k,(t,i,w) in enumerate(WT):
    if curs is not None and (i!=curs or len(cur)>=3 or sum(len(WT[j][2]) for j in cur)+len(w)>20):
        GROUPS.append(cur); cur=[]
    cur.append(k); curs=i
    if re.search(r"[.,:?!]$",w): GROUPS.append(cur); cur=[]; curs=None
if cur: GROUPS.append(cur)
# ---------- drawing helpers
def fit(text,fontname,size,maxw,d):
    while size>30:
        f=F(fontname,size)
        if d.textlength(text,font=f)<=maxw: return f
        size-=4
    return F(fontname,size)
def shadow_text(img,xy,text,font,fill,anchor="mm",blur=10,salpha=170,stroke=0):
    lay=Image.new("RGBA",img.size,(0,0,0,0)); d=ImageDraw.Draw(lay)
    d.text(xy,text,font=font,fill=(0,0,0,salpha),anchor=anchor,stroke_width=stroke+4,stroke_fill=(0,0,0,salpha))
    lay=lay.filter(ImageFilter.GaussianBlur(blur)); img.alpha_composite(lay)
    ImageDraw.Draw(img).text(xy,text,font=font,fill=fill,anchor=anchor)
def grad_layer():
    a=np.zeros((H,W,4),np.uint8)
    y=np.arange(H)[:,None]
    top=np.clip((560-y)/560,0,1)**1.4*210
    bot=np.clip((y-1250)/670,0,1)**1.3*230
    a[...,3]=np.maximum(top,bot).astype(np.uint8).repeat(W,1)
    return Image.fromarray(a,"RGBA")
GRAD=grad_layer()
def sphere(r,blur=0):
    s=2*r+40; yy,xx=np.mgrid[0:s,0:s]-s/2
    d=np.sqrt(xx**2+yy**2)/r
    hx,hy=-0.35*r,-0.4*r; dh=np.sqrt((xx-hx)**2+(yy-hy)**2)/r
    base=np.array([95,8,22.]); hi=np.array([205,45,62.]); edge=np.array([35,2,8.])
    k=np.clip(1-dh/1.3,0,1)[...,None]**1.6
    col=edge+(base-edge)*np.clip(1-d**3,0,1)[...,None]
    col=col+(hi-col)*k
    alpha=np.clip((1-d)*r/2,0,1)*255
    im=Image.fromarray(np.dstack([np.clip(col,0,255),alpha]).astype(np.uint8),"RGBA")
    if blur: im=im.filter(ImageFilter.GaussianBlur(blur))
    return im
def gfx_bg():
    yy,xx=np.mgrid[0:H,0:W]
    d=np.sqrt(((xx-W*0.5)/W)**2+((yy-H*0.42)/H)**2)
    c1=np.array([62,10,22.]); c0=np.array([10,3,6.])
    t=np.clip(d/0.75,0,1)[...,None]
    col=c1+(c0-c1)*t
    im=Image.fromarray(np.dstack([col,np.full((H,W),255)]).astype(np.uint8),"RGBA")
    for (x,y,r,b) in [(90,300,170,0),(960,1180,210,6),(180,1420,90,3),(1000,240,120,10)]:
        sp=sphere(r,b); im.alpha_composite(sp,(x-sp.width//2,y-sp.height//2))
    return im
GBG=None
def draw_headline(img,kicker,title,el):
    d=ImageDraw.Draw(img)
    ka=int(255*min(1,el/0.25)); y=175+int((1-min(1,el/0.25))*20)
    shadow_text(img,(W//2,y),kicker,KF(46),(236,200,205,ka),blur=8,salpha=int(150*ka/255))
    y=237; idx=0
    for ln in title.split("\n"):
        f=fit(ln,BOLD,86,900,d); ws=ln.split(" ")
        tw=d.textlength(ln,font=f); x=W/2-tw/2
        for w in ws:
            e=el-0.12-idx*0.09; idx+=1
            ww=d.textlength(w,font=f)
            if e>0:
                p=min(1,e/0.18); sc=1+0.35*(1-p)**2 - (0.06*math.sin(p*math.pi) if p<1 else 0)
                fs=max(10,int(f.size*sc)); f2=F(BOLD,fs)
                shadow_text(img,(x+ww/2,y+44),w,f2,(255,255,255,int(255*min(1,p*1.6))),blur=12,salpha=int(180*p))
            x+=ww+d.textlength(" ",font=f)
        # underline sweep under last line
        y+=f.size*1.08
    if el>0.15+idx*0.09:
        p=min(1,(el-0.15-idx*0.09)/0.3); L=int(260*p)
        ImageDraw.Draw(img).rounded_rectangle((W//2-L//2,int(y+30),W//2+L//2,int(y+38)),radius=4,fill=(226,52,70,235))
def outline_text(img,center,text,size,width=4,col=(245,225,228,255)):
    lines=text.split("\n"); d=ImageDraw.Draw(img)
    f=F(BOLD,size); lh=size*1.05; y0=center[1]-lh*len(lines)/2+lh/2
    for i,ln in enumerate(lines):
        f2=fit(ln,BOLD,size,960,d)
        m1=Image.new("L",img.size,0); ImageDraw.Draw(m1).text((center[0],y0+i*lh),ln,font=f2,fill=255,anchor="mm",stroke_width=width,stroke_fill=255)
        m2=Image.new("L",img.size,0); ImageDraw.Draw(m2).text((center[0],y0+i*lh),ln,font=f2,fill=255,anchor="mm")
        m=Image.fromarray(np.clip(np.array(m1,np.int16)-np.array(m2,np.int16),0,255).astype(np.uint8))
        glow=Image.new("RGBA",img.size,(225,60,80,0)); glow.putalpha(m.filter(ImageFilter.GaussianBlur(14)).point(lambda v:min(255,v*2)))
        img.alpha_composite(glow)
        lay=Image.new("RGBA",img.size,col); lay.putalpha(m); img.alpha_composite(lay)
def glass_card(img,box,kind,prog):
    lay=Image.new("RGBA",img.size,(0,0,0,0)); d=ImageDraw.Draw(lay)
    d.rounded_rectangle(box,radius=34,fill=(255,255,255,26),outline=(255,255,255,70),width=3)
    img.alpha_composite(lay)
    x0,y0,x1,y1=box
    if kind=="flat":
        pts=[(0,.55),(.2,.52),(.4,.56),(.6,.53),(.8,.55),(1,.54)]; col=(240,232,234,255)
        labels=FLAT_LABELS
    elif kind=="wave":
        pts=[(0,.5),(.12,.2),(.25,.75),(.38,.3),(.5,.8),(.62,.25),(.75,.7),(.88,.35),(1,.6)]; col=(232,58,72,255); labels=None
    elif kind=="down":
        pts=[(0,.25),(.25,.3),(.45,.42),(.6,.5),(.8,.68),(1,.8)]; col=(232,58,72,255); labels=None
    else:
        pts=[(0,.85),(.25,.8),(.45,.7),(.6,.55),(.8,.33),(1,.12)]; col=(64,222,128,255); labels=None
    P=[(x0+40+(x1-x0-80)*u,y0+30+(y1-y0-60)*v) for u,v in pts]
    # partial polyline by prog
    n=len(P)-1; L=prog*n; seg=[P[0]]
    for i in range(n):
        if L>=i+1: seg.append(P[i+1])
        elif L>i:
            f=L-i; seg.append((P[i][0]+(P[i+1][0]-P[i][0])*f,P[i][1]+(P[i+1][1]-P[i][1])*f)); break
    gl=Image.new("RGBA",img.size,(0,0,0,0)); g=ImageDraw.Draw(gl)
    if len(seg)>1: g.line(seg,fill=col[:3]+(200,),width=18,joint="curve")
    img.alpha_composite(gl.filter(ImageFilter.GaussianBlur(12)))
    d=ImageDraw.Draw(img)
    if len(seg)>1: d.line(seg,fill=col,width=8,joint="curve")
    ex,ey=seg[-1]; d.ellipse((ex-12,ey-12,ex+12,ey+12),fill=col)
    if labels:
        lf=F(MED,26)
        for (px,py),lb in zip(P,labels):
            d.ellipse((px-7,py-7,px+7,py+7),fill=(255,255,255,200))
            d.text((px,y1-26),lb,font=lf,fill=(255,255,255,140),anchor="mm")
def wrap(text,font,maxw,d):
    out=[];cur=""
    for w in text.split():
        t=(cur+" "+w).strip()
        if d.textlength(t,font=font)<=maxw: cur=t
        else: out.append(cur); cur=w
    if cur: out.append(cur)
    return out
def draw_gfx(img,g,t):
    global GBG
    if GBG is None: GBG=gfx_bg()
    img.alpha_composite(GBG)
    s,e,kind,kicker,title=g; el=t-s; prog=el/0.9
    a=int(255*min(1,prog*3)); d=ImageDraw.Draw(img)
    if kind=="outline":
        shadow_text(img,(W//2,560),kicker,KF(54),(240,205,210,a),blur=8)
        sc=1+0.25*max(0,1-el/0.35)**2
        outline_text(img,(W//2,860),title,int((230 if "\n" not in title else 190)*sc),width=5)
    elif kind=="verse":
        lay=Image.new("RGBA",img.size,(0,0,0,0)); dl=ImageDraw.Draw(lay)
        dl.rounded_rectangle((80,420,1000,1230),radius=40,fill=(255,255,255,24),outline=(255,255,255,70),width=3)
        img.alpha_composite(lay)
        # open book icon
        cx,cy=W//2,520
        d.line([(cx-70,cy+30),(cx,cy+42),(cx+70,cy+30)],fill=(232,58,72,255),width=6)
        d.polygon([(cx-70,cy-20),(cx-4,cy-8),(cx-4,cy+36),(cx-70,cy+24)],outline=(255,230,232,255),width=5)
        d.polygon([(cx+70,cy-20),(cx+4,cy-8),(cx+4,cy+36),(cx+70,cy+24)],outline=(255,230,232,255),width=5)
        qf=KF(64); n=int(len(title)*min(1,el/max(0.5,(e-s)*0.75)))
        lines=wrap(title,qf,800,d); shown=0; y=720
        d.text((120,620),"«",font=F(BOLD,120),fill=(226,52,70,200),anchor="lm")
        for ln in lines:
            part=ln[:max(0,n-shown)]; shown+=len(ln)+1
            if part: shadow_text(img,(W//2,y),part,qf,(255,255,255,255),blur=8)
            y+=88
        if n>=len(title): d.text((950,y-40),"»",font=F(BOLD,120),fill=(226,52,70,200),anchor="rm")
        shadow_text(img,(W//2,1180),kicker.upper(),F(BOLD,40),(240,205,210,a),blur=6)
    elif kind=="pills":
        shadow_text(img,(W//2,360),kicker,KF(50),(240,205,210,a),blur=8)
        f=fit(title,BOLD,92,960,d); shadow_text(img,(W//2,445),title,f,(255,255,255,a),blur=12)
        cur=max([i for i,(_,pt) in enumerate(PILLS) if pt<=t] or [-1])
        for i,(lab,pt) in enumerate(PILLS):
            if t<pt-0.05: continue
            p=min(1,(t-pt+0.05)/0.2); y=600+i*170; wpx=int(640*(0.7+0.3*p))
            box=(W//2-wpx//2,y,W//2+wpx//2,y+120)
            lay=Image.new("RGBA",img.size,(0,0,0,0)); dl=ImageDraw.Draw(lay)
            if i==cur:
                dl.rounded_rectangle(box,radius=60,fill=(214,40,60,int(235*p)))
                glow=lay.filter(ImageFilter.GaussianBlur(22)); img.alpha_composite(glow)
            else:
                dl.rounded_rectangle(box,radius=60,fill=(255,255,255,28),outline=(255,255,255,90),width=3)
            img.alpha_composite(lay)
            shadow_text(img,(W//2,y+60),lab,F(BOLD,int(62*(0.8+0.2*p))),(255,255,255,int(255*p)),blur=6)
    elif kind=="target":
        shadow_text(img,(W//2,330),kicker,KF(52),(240,205,210,a),blur=8)
        f=fit(title,BOLD,110,960,d); shadow_text(img,(W//2,425),title,f,(255,255,255,a),blur=12)
        cx,cy=W//2,830
        for k,(r,col) in enumerate([(270,(255,230,232)),(200,(214,40,60)),(130,(255,230,232)),(60,(214,40,60))]):
            p=max(0,min(1,(el-k*0.1)/0.25))
            if p<=0: continue
            rr=int(r*(0.5+0.5*(1-(1-p)**3)))
            lay=Image.new("RGBA",img.size,(0,0,0,0)); dl=ImageDraw.Draw(lay)
            if k==3: dl.ellipse((cx-rr,cy-rr,cx+rr,cy+rr),fill=col+(int(255*p),))
            else: dl.ellipse((cx-rr,cy-rr,cx+rr,cy+rr),outline=col+(int(255*p),),width=14)
            if k==1: img.alpha_composite(lay.filter(ImageFilter.GaussianBlur(16)))
            img.alpha_composite(lay)
        q=max(0,min(1,(el-0.55)/0.3))
        if q>0:
            q=1-(1-q)**3; tx=cx+int(700*(1-q)); ty=cy-int(700*(1-q))
            sh=int(6*math.sin(el*60)*max(0,1-(el-0.85)/0.3)) if el>0.85 else 0
            tx+=sh
            dd=ImageDraw.Draw(img)
            dd.line([(tx,ty),(tx+230,ty-230)],fill=(255,255,255,255),width=12)
            dd.polygon([(tx,ty),(tx+48,ty-14),(tx+14,ty-48)],fill=(255,255,255,255))
            dd.polygon([(tx+230,ty-230),(tx+270,ty-210),(tx+250,ty-250),(tx+210,ty-270)],fill=(214,40,60,255))
    elif kind=="shield":
        shadow_text(img,(W//2,330),kicker,KF(54),(240,205,210,a),blur=8)
        f=fit(title,BOLD,100,960,d); shadow_text(img,(W//2,420),title,f,(255,255,255,a),blur=12)
        sc=min(1,el/0.35); sc=1-(1-sc)**3; cx,cy,R=W//2,800,int(260*(0.6+0.4*sc))
        pts=[(cx,cy-R),(cx+R*0.85,cy-R*0.62),(cx+R*0.78,cy+R*0.15),(cx,cy+R),(cx-R*0.78,cy+R*0.15),(cx-R*0.85,cy-R*0.62)]
        lay=Image.new("RGBA",img.size,(0,0,0,0)); dl=ImageDraw.Draw(lay)
        dl.polygon(pts,fill=(200,30,50,int(150*sc))); img.alpha_composite(lay.filter(ImageFilter.GaussianBlur(30)))
        lay=Image.new("RGBA",img.size,(0,0,0,0)); dl=ImageDraw.Draw(lay)
        dl.polygon(pts,fill=(120,12,28,int(230*sc)),outline=(255,225,228,int(255*sc)),width=8)
        img.alpha_composite(lay)
        cp=max(0,min(1,(el-0.35)/0.4))
        c=[(cx-R*0.38,cy+R*0.0),(cx-R*0.08,cy+R*0.3),(cx+R*0.42,cy-R*0.3)]
        if cp>0:
            if cp<0.4: seg=[c[0],(c[0][0]+(c[1][0]-c[0][0])*cp/0.4,c[0][1]+(c[1][1]-c[0][1])*cp/0.4)]
            else:
                q=(cp-0.4)/0.6; seg=[c[0],c[1],(c[1][0]+(c[2][0]-c[1][0])*q,c[1][1]+(c[2][1]-c[1][1])*q)]
            ImageDraw.Draw(img).line(seg,fill=(255,255,255,255),width=30,joint="curve")
    else:
        shadow_text(img,(W//2,330),kicker,KF(50),(240,205,210,a),blur=8)
        f=fit(title,BOLD,92,960,d)
        shadow_text(img,(W//2,415),title,f,(255,255,255,a),blur=12)
        glass_card(img,(80,520,1000,1080),kind,min(1,prog*1.25))
def draw_caption(img,words,graphic):
    # words: list of (word, visible_alpha)
    d=ImageDraw.Draw(img)
    lines=[];cur=[]
    for w,a in words:
        if clean(w) in KEY:
            if cur: lines.append(cur); cur=[]
            lines.append([(w,a,True)])
        else: cur.append((w,a,False))
    if cur: lines.append(cur)
    y=CAPY if not graphic else 1290
    for ln in lines:
        big=ln[0][2]; f=F(BOLD,76) if big else F(BOLD,50)
        txt=" ".join(clean(w) if not big else clean(w) for w,_,_ in ln)
        tw=d.textlength(txt,font=f); x=W/2-tw/2
        for w,a,_ in ln:
            ww=clean(w)
            col=(255,255,255,a) if not big else (255,92,108,a)
            shadow_text(img,(x,y),ww,f,col,anchor="lm",blur=7,salpha=int(a*0.75))
            x+=d.textlength(ww+" ",font=f)
        y+=f.size*1.12
SIG=(END-1.6,END)
def render_state(t):
    img=Image.new("RGBA",(W,H),(0,0,0,0))
    g=next((g for g in GFX if g[0]<=t<g[1]),None)
    if g: draw_gfx(img,g,t)
    else:
        img.alpha_composite(GRAD)
        h=next((h for h in HEAD if h[0]<=t<h[1]),None)
        if h: draw_headline(img,h[2],h[3],t-h[0])
    # caption: current group
    gi=None
    for k,G in enumerate(GROUPS):
        if WT[G[0]][0]<=t: gi=k
    if gi is not None:
        G=GROUPS[gi]; end=WT[GROUPS[gi+1][0]][0] if gi+1<len(GROUPS) else END
        if t<end+0.0:
            ws=[(WT[j][2], 255 if WT[j][0]<=t-0.08 else (150 if WT[j][0]<=t else 0)) for j in G]
            ws=[(w,a) for w,a in ws if a>0 and not w.startswith('~')]
            if ws: draw_caption(img,ws,bool(g))
    if SIG[0]<=t:
        a=int(255*min(1,(t-SIG[0])/0.3)); d=ImageDraw.Draw(img)
        shadow_text(img,(W//2,1745),SIGTXT,KF(38),(240,205,210,a),blur=6)
    fl=[x for x in FLASH if 0<=t-x<0.22]
    if fl:
        dt=t-fl[-1]; lay=Image.new("RGBA",img.size,(255,240,242,int(120*(1-dt/0.22)))); img.alpha_composite(lay)
    return img
def breakpoints():
    T={B[0],B[-1]}
    for t,_,_ in WT: T|={t,t+0.08}
    for h in HEAD: T|={h[0]+k*0.045 for k in range(26)}|{h[1]}
    for x in FLASH: T|={x,x+0.07,x+0.14,x+0.22}
    for _,pt in PILLS: T|={pt-0.05+k*0.05 for k in range(5)}
    for g in GFX:
        T|={g[0]+k*0.06 for k in range(14)}|{g[1]}
        if g[2]=='verse': T|={g[0]+k*0.1 for k in range(int((g[1]-g[0])/0.1))}
    T|={SIG[0]+k*0.1 for k in range(4)}
    return sorted(x for x in T if B[0]<=x<=B[-1])
if __name__=="__main__":
    bp=breakpoints()
    # merge tiny intervals (<1 frame)
    m=[bp[0]]
    for x in bp[1:]:
        if x-m[-1]>=1/30: m.append(x)
    m[-1]=B[-1]
    a,b=int(sys.argv[1]),int(sys.argv[2])
    os.makedirs("st",exist_ok=True)
    for k in range(a,min(b,len(m)-1)):
        render_state(m[k]+0.001).save(f"st/{k:04d}.png",compress_level=1)
    json.dump(m,open("bp.json","w")); print(len(m)-1,"states total; done",a,b)
