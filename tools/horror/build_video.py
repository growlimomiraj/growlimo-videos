import cv2, numpy as np, subprocess, os, json
CFG=json.load(open('config.json')); W,H,FPS=1080,1920,30
def writer(name):
    return subprocess.Popen(f"ffmpeg -v error -y -f rawvideo -pix_fmt bgr24 -s {W}x{H} -r {FPS} -i - -c:v libx264 -crf 15 -preset veryfast -pix_fmt yuv420p {name}",shell=True,stdin=subprocess.PIPE)
rng=np.random.default_rng(7)
yy,xx=np.mgrid[0:H,0:W].astype(np.float32)
vig=1-0.55*np.clip(((xx-W/2)/(W*0.62))**2+((yy-H/2)/(H*0.6))**2,0,1)**1.3
vig=vig[...,None]
# ---------- SV daytime push (3.2s) ----------
sv=cv2.imread(CFG.get('sv_image','lv/SV0.png')).astype(np.float32)
SX,SW=CFG.get('sv_crop_x',175),CFG.get('sv_crop_w',731)
p=writer('seg_sv.mp4'); n=int(3.2*FPS)
for f in range(n):
    x=f/(n-1); e=x*x*(3-2*x)
    cw=SW-81*e; ch=cw*16/9; cx=SX+SW/2+20*e; cy=0+ch/2+40*e
    M=np.array([[W/cw,0,-(cx-cw/2)*W/cw],[0,H/ch,-(cy-ch/2)*H/ch]],np.float32)
    img=cv2.warpAffine(sv,M,(W,H),flags=cv2.INTER_LANCZOS4)
    img=cv2.addWeighted(img,1.25,cv2.GaussianBlur(img,(0,0),2.2),-0.25,0)
    if f<6: img=img*(f/6)+255*(1-f/6)   # come out of the white flash
    p.stdin.write(np.clip(img,0,255).astype(np.uint8).tobytes())
p.stdin.close(); p.wait()
last_sv=img.copy()
# ---------- night: skA (0-8) + skB (1.0-5.0), graded ----------
def frames(path,t0,t1):
    cap=cv2.VideoCapture(path); fps=cap.get(cv2.CAP_PROP_FPS); out=[]; i=0
    while True:
        ok,fr=cap.read()
        if not ok: break
        t=i/fps; i+=1
        if t0<=t<t1: out.append(fr)
    return out,fps
CL=[frames(c['file'],c['t0'],c['t1']) for c in CFG['night']]
tl=[]
for fr,fps in CL:
    d=len(fr)/fps
    for f in range(int(round(d*FPS))): tl.append(fr[min(len(fr)-1,int(f/FPS*fps))])
n=len(tl)
SCARE=n-int(0.95*FPS)   # scare starts ~0.95s before end of night segment
def grade(fr,f):
    img=cv2.resize(fr,(W,H),interpolation=cv2.INTER_LANCZOS4).astype(np.float32)
    img=cv2.addWeighted(img,1.35,cv2.GaussianBlur(img,(0,0),2.0),-0.35,0)
    g=img.mean(2,keepdims=True); img=g+(img-g)*0.78          # desaturate a bit
    img=img*np.array([1.08,0.98,0.90])                         # cold (BGR)
    img=np.clip((np.clip(img,0,255)/255)**1.12*255*0.95,0,255)                 # crush
    fl=1-0.10*(rng.random()<0.06)-0.05*np.sin(f*0.9)**8         # flicker
    img=img*vig*fl
    img+=rng.normal(0,7,(H,W,1)).astype(np.float32)             # grain
    return img
p=writer('seg_night.mp4'); prev=None
for f,fr in enumerate(tl):
    img=grade(fr,f)
    if f>=SCARE:
        k=(f-SCARE)/FPS
        z=1+0.42*min(1,k/0.12)                                  # punch zoom
        sx=rng.normal(0,14*max(0,1-k)); sy=rng.normal(0,14*max(0,1-k))
        M=cv2.getRotationMatrix2D((W/2+sx,H*0.40+sy),rng.normal(0,0.8),z)
        img=cv2.warpAffine(img,M,(W,H))
        red=np.array([0.55,0.55,1.6]); img=img*red if k<0.5 else img*(red*0.5+0.5)
        if k<0.07: img=img*0+255
        if k>0.8: img*=max(0,1-(k-0.8)/0.15)
    p.stdin.write(np.clip(img,0,255).astype(np.uint8).tobytes())
    if f==0: first_night=img.copy()
p.stdin.close(); p.wait()
print('night frames',n,'scare at',SCARE/FPS)
json.dump({'night_dur':n/FPS,'scare_in_night':SCARE/FPS},open('night_meta.json','w'))
# ---------- glitch 0.5s ----------
p=writer('seg_glitch.mp4'); n=int(0.5*FPS)
for f in range(n):
    x=f/(n-1); base=last_sv if x<0.5 else first_night
    img=base.copy()
    for _ in range(14):   # block displacement
        y0=int(rng.integers(0,H-80)); h=int(rng.integers(10,120)); dx=int(rng.normal(0,90))
        img[y0:y0+h]=np.roll(img[y0:y0+h],dx,axis=1)
    sh=int(12+30*np.sin(np.pi*x)); out=img.copy(); out[...,2]=np.roll(img[...,2],sh,1); out[...,0]=np.roll(img[...,0],-sh,1)
    noise=rng.random((H//4,W//4,1)).astype(np.float32)*255; noise=cv2.resize(noise,(W,H),interpolation=cv2.INTER_NEAREST)[...,None]
    a=0.25+0.45*np.sin(np.pi*x); out=out*(1-a)+noise*a
    if abs(x-0.5)<0.09: out*=0.1
    p.stdin.write(np.clip(out,0,255).astype(np.uint8).tobytes())
p.stdin.close(); p.wait()
# ---------- black 0.3s + end background 6.8s ----------
p=writer('seg_black.mp4')
for f in range(int(0.3*FPS)): p.stdin.write(np.zeros((H,W,3),np.uint8).tobytes())
p.stdin.close(); p.wait()
bg=cv2.GaussianBlur(grade(tl[int(len(tl)*0.3)],0),(0,0),22)*0.45
p=writer('seg_end.mp4'); n=int(6.9*FPS)
for f in range(n):
    x=f/(n-1); M=cv2.getRotationMatrix2D((W/2,H/2),0,1.05+0.05*x)
    img=cv2.warpAffine(bg,M,(W,H))*min(1,f/8)+rng.normal(0,5,(H,W,1))
    p.stdin.write(np.clip(img,0,255).astype(np.uint8).tobytes())
p.stdin.close(); p.wait()
open('list.txt','w').write(''.join(f"file '{s}'\n" for s in ['seg_zoom.mp4','seg_sv.mp4','seg_glitch.mp4','seg_night.mp4','seg_black.mp4','seg_end.mp4']))
subprocess.run("ffmpeg -v error -y -f concat -safe 0 -i list.txt -c copy base.mp4",shell=True,check=True)
for s in ['seg_zoom.mp4','seg_sv.mp4','seg_glitch.mp4','seg_night.mp4','seg_black.mp4','seg_end.mp4']:
    print(s,subprocess.run(f"ffprobe -v error -show_entries format=duration -of csv=p=0 {s}",shell=True,capture_output=True,text=True).stdout.strip())
