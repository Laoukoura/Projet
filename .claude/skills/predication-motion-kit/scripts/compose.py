#!/usr/bin/env python3
"""Étape 5 : composition finale (base étalonnée + calques + sphères + particules + son).
Usage : KIT_CFG=config.json python3 compose.py /mnt/user-data/outputs/ma_video.mp4"""
import json,os,subprocess,sys
A=os.path.join(os.path.dirname(os.path.abspath(__file__)),"..","assets")
C=json.load(open(os.environ.get("KIT_CFG","config.json")))
m=json.load(open("bp.json"))
with open("states.txt","w") as f:
    for k in range(len(m)-1): f.write(f"file 'st/{k:04d}.png'\nduration {m[k+1]-m[k]:.4f}\n")
    f.write(f"file 'st/{len(m)-2:04d}.png'\n")
P="";specs=[(120,0.0,55),(300,3.1,70),(780,1.7,48),(940,5.2,62),(520,7.4,40),(60,9.0,66)]
for i,(x,ph,sp) in enumerate(specs):
    P+=f";[q{i}][p{i}]overlay=x='{x}+30*sin(t*0.8+{i})':y='1980-mod(t*{sp}+{ph*sp},2100)':shortest=1[q{i+1}]"
SPLIT=("[4:v]format=rgba,split=6[r0][r1][r2][r3][r4][r5];[r0]colorchannelmixer=aa=0.9,scale=26:26[p0];[r1]colorchannelmixer=aa=0.7[p1];"
"[r2]colorchannelmixer=aa=0.8,scale=20:20[p2];[r3]colorchannelmixer=aa=0.6[p3];[r4]colorchannelmixer=aa=0.9,scale=16:16[p4];[r5]colorchannelmixer=aa=0.6,scale=30:30[p5]")
FC=("[1:v]fps=30,format=rgba[ov];[0:v][ov]overlay=0:0:eof_action=repeat[b];[2:v]format=rgba,colorchannelmixer=aa=0.75[a2];[3:v]format=rgba,colorchannelmixer=aa=0.8[a3];"
"[b][a2]overlay=x='870+18*sin(t*0.7)':y='-40+22*cos(t*0.5)':shortest=1[c];[c][a3]overlay=x='-30+15*cos(t*0.6)':y='1330+25*sin(t*0.45)':shortest=1[q0];"+SPLIT+P+";[q6]format=yuv420p[v]")
T=float(C["end"])-float(C.get("start",0.9))
subprocess.run(["ffmpeg","-v","error","-y","-i","base.mp4","-f","concat","-safe","0","-i","states.txt","-loop","1","-i",f"{A}/sA.png","-loop","1","-i",f"{A}/sB.png",
  "-loop","1","-i",f"{A}/dot.png","-i","audio.m4a","-filter_complex",FC,"-map","[v]","-map","5:a","-t",f"{T:.2f}","-c:v","libx264","-preset","superfast","-crf","20",
  "-c:a","copy","-movflags","+faststart",sys.argv[1]],check=True)
print("ok :",sys.argv[1])
