import cv2, numpy as np, json, subprocess, os, sys
CFG=json.load(open('config.json'))
D=CFG['levels_d']
N=len(D); W,H=1080,1920
L=[cv2.imread(f'lv/L{i}.png').astype(np.float32) for i in range(N)]
# --- align consecutive levels: find finer level i inside coarser i+1
off=[(0.0,0.0)]*N
for i in range(N-1):
    s=D[i]/D[i+1]
    small=cv2.resize(L[i],(int(W*s),int(H*s)),interpolation=cv2.INTER_AREA)
    # use central part of small template for robustness
    th,tw=small.shape[:2]; cy,cx=th//2,tw//2; hh,hw=int(th*0.35),int(tw*0.35)
    tpl=small[cy-hh:cy+hh,cx-hw:cx+hw]
    res=cv2.matchTemplate(L[i+1],tpl,cv2.TM_CCOEFF_NORMED)
    _,mx,_,loc=cv2.minMaxLoc(res)
    # template center in coarse coords
    tcx=loc[0]+hw; tcy=loc[1]+hh
    ox,oy=tcx-W/2, tcy-H/2
    if mx<0.35 or abs(ox)>150 or abs(oy)>150: ox,oy=0.0,0.0
    off[i]=(ox,oy); print(i,'score',round(mx,3),'off',round(ox,1),round(oy,1))
# level geometry in L16 pixel units
k=[d/D[-1] for d in D]
c=[None]*N; c[N-1]=np.array([W/2,H/2])
for i in range(N-2,-1,-1): c[i]=c[i+1]+np.array(off[i])*k[i+1]
def X_of(i,u,v): return c[i]+(np.array([u,v])-[W/2,H/2])*k[i]
TGT=X_of(0,*CFG['target_px'])      # the place, in L0 pixels
# feather mask
fm=np.ones((H,W),np.float32); fe=int(0.10*W)
ramp=np.linspace(0,1,fe)
fm[:,:fe]*=ramp; fm[:,-fe:]*=ramp[::-1]; fm[:fe,:]*=ramp[:,None]; fm[-fe:,:]*=ramp[::-1][:,None]
def render(C,P):
    out=np.zeros((H,W,3),np.float32)
    # base: coarsest level that covers screen fully
    order=[i for i in range(N) if k[i]/P>=0.22]
    base=None
    for i in range(N):
        if k[i]/P>=1.0: base=i; break
    if base is None: base=N-1
    lv=[base]+[i for i in sorted(order,reverse=True) if i<base]
    for idx,i in enumerate(lv):
        sc=k[i]/P
        # screen = (X - C)/P + center ; X = c_i + (u - W/2)*k_i
        t=(c[i]-C)/P + np.array([W/2,H/2]) - np.array([W/2,H/2])*sc
        M=np.array([[sc,0,t[0]],[0,sc,t[1]]],np.float32)
        img=cv2.warpAffine(L[i],M,(W,H),flags=cv2.INTER_CUBIC if sc>1 else cv2.INTER_AREA,borderMode=cv2.BORDER_CONSTANT)
        if idx==0: out=img
        else:
            a=cv2.warpAffine(fm,M,(W,H),flags=cv2.INTER_LINEAR)
            # fade in finer level as it grows (avoid popping tiny patch)
            g=np.clip((sc-0.22)/0.25,0,1)
            a=(a*g)[...,None]; out=out*(1-a)+img*a
    return out
FPS=30
def chainC(P):
    lp=np.log(P)
    if P>=k[N-1]: return c[N-1].copy()
    if P<=k[0]: return c[0].copy()
    for i in range(N-1):
        if k[i]<=P<=k[i+1]:
            f=(np.log(k[i+1])-lp)/(np.log(k[i+1])-np.log(k[i]))
            return c[i+1]*(1-f)+c[i]*f
def ease(x): return x*x*(3-2*x)
frames=[]
# phase A: zoom from globe to L0 (6.0s), log-scale with smootherstep
TA=6.0; nA=int(TA*FPS)
P0,P1=1.25,k[0]*1.0
for f in range(nA):
    x=f/(nA-1); e=x*x*x*(x*(6*x-15)+10)
    lp=np.log(P0)+(np.log(P1)-np.log(P0))*e
    P=np.exp(lp)
    # center: follow chain; use target-weighted path: C = TGT + (c16 - TGT)*(P/P0)^(..) -> keep target at its screen place smoothly
    C=chainC(P)
    frames.append((C,P))
# phase B: hold & slow push toward Doyers (3.6s)
TB=3.6; nB=int(TB*FPS); Cend=frames[-1][0]
for f in range(nB):
    x=f/(nB-1); e=ease(x)
    P=k[0]*(1-0.18*e); C=Cend*(1-0.55*e)+TGT*0.55*e
    frames.append((C,P))
# phase C: dive (0.6s) fast zoom toward target
TC=0.6; nC=int(TC*FPS); Cb,Pb=frames[-1]
for f in range(nC):
    x=(f+1)/nC; e=x*x*x
    P=Pb*np.exp(-np.log(5)*e); C=Cb*(1-e)+TGT*e
    frames.append((C,P))
pin=[[float(v) for v in ((TGT-np.array(C))/P+np.array([W/2,H/2]))] for C,P in frames]
json.dump({'nA':nA,'nB':nB,'nC':nC,'pin':pin},open('zoom_meta.json','w'))
import sys
if '--meta' in sys.argv: sys.exit(0)
os.makedirs('zf',exist_ok=True)
p=subprocess.Popen(f"ffmpeg -v error -y -f rawvideo -pix_fmt bgr24 -s {W}x{H} -r {FPS} -i - -c:v libx264 -crf 15 -preset veryfast -pix_fmt yuv420p seg_zoom.mp4",shell=True,stdin=subprocess.PIPE)
prev=None
for n,(C,P) in enumerate(frames):
    img=render(np.array(C),P)
    if n>=nA+nB:  # dive: radial zoom blur
        x=(n-nA-nB+1)/nC; acc=img.copy()
        for s in (1.03,1.06,1.10,1.15):
            M=cv2.getRotationMatrix2D((W/2,H/2),0,1+(s-1)*x*2); acc+=cv2.warpAffine(img,M,(W,H))
        img=acc/5; img=img*(1-0.7*x**2)+255*0.7*x**2
    p.stdin.write(np.clip(img,0,255).astype(np.uint8).tobytes())
p.stdin.close(); p.wait()
print('frames',len(frames),'dur',len(frames)/FPS)
