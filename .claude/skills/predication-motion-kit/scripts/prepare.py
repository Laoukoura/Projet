#!/usr/bin/env python3
"""Étape 1 : analyse du rush. Usage : KIT_CFG=config.json python3 prepare.py
Produit dans le dossier courant : sil.txt (pauses), a16.wav (voix pour l'alignement),
audio.m4a (bande-son finale), face_check.png (2 images pour vérifier le cadrage)."""
import json,os,subprocess
C=json.load(open(os.environ.get("KIT_CFG","config.json")))
V=C["raw_video"]; S=float(C.get("start",0.9))
dur=float(subprocess.check_output(["ffprobe","-v","error","-show_entries","format=duration","-of","csv=p=0",V]))
print("durée du rush :",round(dur,2),"s  (mettre \"end\" un peu avant)")
log=subprocess.run(["ffmpeg","-v","info","-i",V,"-vn","-af","silencedetect=noise=-26dB:d=0.18","-f","null","-"],capture_output=True,text=True).stderr
vals=[l.split(": ")[1].split()[0] for l in log.splitlines() if "silence_start:" in l or "silence_end:" in l]
open("sil.txt","w").write("\n".join(vals)+"\n")
subprocess.run(["ffmpeg","-v","error","-y","-i",V,"-vn","-ac","1","-ar","16000","a16.wav"],check=True)
E=float(C.get("end",dur))
subprocess.run(["ffmpeg","-v","error","-y","-i",V,"-vn","-ss",str(S),"-t",f"{E-S:.3f}","-c:a","aac","-b:a","192k","audio.m4a"],check=True)
for i,t in enumerate([dur*0.2,dur*0.6]):
    subprocess.run(["ffmpeg","-v","error","-y","-ss",str(t),"-i",V,"-frames:v","1","-vf","scale=300:-1",f"fc{i}.png"],check=True)
subprocess.run(["ffmpeg","-v","error","-y","-i","fc0.png","-i","fc1.png","-filter_complex","hstack","face_check.png"],check=True)
print("ok : sil.txt, a16.wav, audio.m4a, face_check.png")
