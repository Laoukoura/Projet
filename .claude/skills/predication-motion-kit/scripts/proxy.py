#!/usr/bin/env python3
"""Étape 3 : étalonnage + recadrage du rush, scène par scène (coupes à l'image près).
Usage : KIT_CFG=config.json python3 proxy.py 0 1 2 3   (3 à 6 scènes par appel, ~4K lent)
        KIT_CFG=config.json python3 proxy.py concat      (assemble base.mp4)"""
import subprocess,sys,os,json
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault("KIT_CFG","config.json")
C=json.load(open(os.environ["KIT_CFG"]))
FR=C.get("framing",{}); MODE=FR.get("mode","full")
GR={"normal":"eq=contrast=1.12:brightness=-0.07:saturation=0.78",
    "bright":"eq=contrast=1.06:brightness=0.03:saturation=0.85:gamma=1.18"}[C.get("grade","normal")]
TAIL=GR+",colorbalance=rs=0.10:gs=-0.03:bs=0.06:rm=0.05:bm=0.03,vignette=PI/3.6,fps=30,format=yuv420p"
def vf(i):
    if MODE=="inset":
        zs=FR.get("zooms",[0.80,0.88]); z=zs[i%len(zs)]; w=int(1080*z)//2*2; top=FR.get("top",260)
        return (f"split[m][bg];[bg]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,boxblur=40:3,eq=brightness=-0.2[bb];"
                f"[m]scale={w}:-2[mm];[bb][mm]overlay=(W-w)/2:{top},"+TAIL)
    zs=FR.get("zooms",[1.0,1.10]); z=zs[i%len(zs)]; w=int(1080*z)//2*2
    fy=FR.get("face_y",0.40); pad=int(FR.get("pad_top",0))
    if pad:
        return (f"scale={w}:-2,split[m][bg];[bg]scale={w}:ih+{pad},boxblur=40:2,eq=brightness=-0.12[bb];[bb][m]overlay=0:{pad},"
                f"crop=1080:1920:(iw-1080)/2:'max(0,min(ih-1920,(ih-{pad})*{fy}+{pad}-960))',"+TAIL)
    return f"scale={w}:-2,crop=1080:1920:(iw-1080)/2:'max(0,min(ih-1920,ih*{fy}-960))',"+TAIL
if sys.argv[1]=="concat":
    import render_states as R
    open("plist.txt","w").write("".join(f"file 'p{i:02d}.mp4'\n" for i in range(len(R.B)-1)))
    subprocess.run(["ffmpeg","-v","error","-y","-f","concat","-safe","0","-i","plist.txt","-c","copy","base.mp4"],check=True)
    print("base.mp4 :",subprocess.check_output(["ffprobe","-v","error","-show_entries","format=duration","-of","csv=p=0","base.mp4"]).decode().strip(),"s"); sys.exit()
import render_states as R
for i in map(int,sys.argv[1:]):
    s,e=R.B[i],R.B[i+1]
    subprocess.run(["ffmpeg","-v","error","-y","-ss",str(s),"-i",C["raw_video"],"-frames:v",str(round(e*30)-round(s*30)),
      "-an","-vf",vf(i),"-c:v","libx264","-preset","ultrafast","-crf","14",f"p{i:02d}.mp4"],check=True); print("ok",i,flush=True)
