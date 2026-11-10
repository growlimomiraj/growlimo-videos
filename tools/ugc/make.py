import subprocess, json, re, numpy as np, scipy.io.wavfile as wf, os
from scipy.signal import resample_poly, butter, lfilter
from scipy.ndimage import maximum_filter1d, uniform_filter1d
os.chdir('/home/claude/ugcbt'); FPS=30
def run(c): subprocess.run(c,shell=True,check=True)
# (src,in,out,zoom,blur,keep_audio)
SEG=[('a',0.38,4.75,1.00,0,1),('a',9.55,14.55,1.08,0,1),('b',0.30,3.20,1.00,0,0),('b',5.20,7.00,1.00,0,0),
     ('c',0.20,7.60,1.00,0,1),('d',0.90,7.95,1.00,0,1),('d',7.95,8.04,1.00,1,0)]
END_HOLD=2.8
os.makedirs('seg',exist_ok=True); starts=[]; t=0
for k,(s,a,b,z,bl,au) in enumerate(SEG):
    starts.append(t); d=b-a
    vf=f"scale={int(1080*z)}:{int(1920*z)}:flags=lanczos,crop=1080:1920,unsharp=5:5:0.6,fps={FPS},setsar=1"
    if bl: vf+=f",tpad=stop_mode=clone:stop_duration={END_HOLD},gblur=sigma=18"
    run(f"ffmpeg -v error -y -ss {a} -t {d} -i in/{s}.mp4 -vf '{vf}' -an -c:v libx264 -crf 14 -preset veryfast -pix_fmt yuv420p seg/v{k}.mp4")
    t+=d+(END_HOLD if bl else 0)
TOTAL=t
open('seg/list.txt','w').write(''.join(f"file 'v{k}.mp4'\n" for k in range(len(SEG))))
run("ffmpeg -v error -y -f concat -safe 0 -i seg/list.txt -c copy base.mp4")
SR=48000
def load(f):
    sr,x=wf.read(f); x=x.astype(float)/32768
    if x.ndim>1: x=x.mean(1)
    return resample_poly(x,SR,sr) if sr!=SR else x
for s in 'abcd': run(f"ffmpeg -v error -y -i in/{s}.mp4 -ac 1 -ar {SR} in/{s}48.wav")
src={s:load(f'in/{s}48.wav') for s in 'abcd'}
N=int((TOTAL+0.1)*SR); voice=np.zeros(N)
for k,(s,a,b,z,bl,au) in enumerate(SEG):
    if not au: continue
    x=src[s][int(a*SR):int(b*SR)].copy(); f=int(0.015*SR); x[:f]*=np.linspace(0,1,f); x[-f:]*=np.linspace(1,0,f)
    i=int(starts[k]*SR); voice[i:i+len(x)]+=x[:N-i]
voice=voice/np.abs(voice).max()*0.92
sr,mus=wf.read('music.wav'); mus=mus.astype(float)/32768; mus=mus[:N] if len(mus)>=N else np.pad(mus,((0,N-len(mus)),(0,0)))
h=int(0.02*SR); rms=np.array([np.sqrt(np.mean(voice[i:i+h]**2)) for i in range(0,N,h)])
act=uniform_filter1d(maximum_filter1d((rms>0.02).astype(float),25),15)
g=np.repeat(0.30-0.21*act,h)[:N]
# hook: music starts low and swells at the B-roll (problem -> solution)
i2=int(starts[2]*SR); g[:i2]*=0.55
b0,b1=int(starts[2]*SR),int(starts[4]*SR); g[b0:b1]=np.maximum(g[b0:b1],0.55)
endi=int(starts[-1]*SR); g[endi:]=np.linspace(g[endi],0.45,len(g)-endi)
fo=int(1.2*SR); g[-fo:]*=np.linspace(1,0,fo)
mix=np.stack([voice,voice],1)+mus*g[:,None]
rng=np.random.default_rng(2)
def whoosh(t,amp=0.18):
    L=int(0.45*SR); n=rng.standard_normal(L); e=np.sin(np.linspace(0,np.pi,L))**2; out=np.zeros(L)
    for j in range(0,L,512):
        fc=600+5000*(j/L); bb,aa=butter(2,[fc/(SR/2),min(fc*1.6,20000)/(SR/2)],'band'); out[j:j+512]=lfilter(bb,aa,n[j:j+512])
    i=int(t*SR)-L//2; s=out*e*amp/np.abs(out).max(); mix[i:i+L]+=s[:,None]
def ding(t,amp=0.14):
    L=int(0.5*SR); tt=np.arange(L)/SR; s=(np.sin(2*np.pi*1318*tt)+0.6*np.sin(2*np.pi*1975*tt))*np.exp(-tt*9)*amp
    i=int(t*SR); mix[i:i+L]+=s[:,None]
def buzz(t,amp=0.12):
    L=int(0.32*SR); tt=np.arange(L)/SR; s=np.sign(np.sin(2*np.pi*140*tt))*np.exp(-tt*6)*amp; bb,aa=butter(2,900/(SR/2)); s=lfilter(bb,aa,s)
    i=int(t*SR); mix[i:i+L]+=s[:,None]
def o(s,t):
    for k,(ss,a,b,z,bl,au) in enumerate(SEG):
        if ss==s and a-0.05<=t<=b+0.05 and not bl: return starts[k]+max(0,t-a)
    raise Exception((s,t))
BAD=[o('a',2.55),starts[1]-0.05]
NTS=[dict(t0=o('b',2.15),t1=starts[4]-0.1,title='Car Audio connected',sub='Auto-connected in 0.8s'),
     dict(t0=o('c',3.05),t1=o('c',4.30),title='Car Audio connected',sub='Remembered device'),
     dict(t0=o('c',4.30),t1=o('c',5.15),title='Earbuds connected',sub='Remembered device'),
     dict(t0=o('c',5.15),t1=o('c',7.30),title='Speaker connected',sub='Remembered device'),]
for n in NTS: n['y']=110
buzz(BAD[0]); whoosh(starts[2]); whoosh(starts[-1]+0.05,0.2)
for n in NTS: ding(n['t0']+0.05)
mix=np.clip(mix/np.abs(mix).max()*0.95,-1,1); wf.write('mix.wav',SR,(mix*32767).astype(np.int16))
# captions: (src, word timings by region)
R=[('a',[(0.56,2.16,"Every single time I get in my car,"),(2.38,4.58,"my phone just refuses to connect to the stereo.")]),
   ('a',[(9.70,10.32,"Settings,"),(10.74,11.24,"Bluetooth,"),(11.78,12.50,"tap the car,"),(12.70,13.06,"wait…"),(13.60,14.44,"every single day.")]),
   ('c',[(0.38,2.08,"It's called Bluetooth Auto Connect."),(2.68,3.88,"It remembers my car,"),(4.26,5.82,"my earbuds, my speaker,"),(6.10,7.40,"and connects them automatically.")]),
   ('d',[(2.30,3.44,"It's free on Google Play."),(4.44,5.26,"Link's in my bio."),(6.12,7.68,"Honestly, I'm never going back.")])]
HL={'refuses','connect','stereo','day','app','bluetooth','auto','earbuds','speaker','automatically','free','google','play','bio','never'}
PAIR={('google','play.'),('my','bio.'),('auto','connect.'),('my','car,'),('my','phone'),('my','earbuds,'),('my','speaker,'),('the','stereo.'),('the','car,'),('every','single'),('single','day.'),('connects','them'),('in','my')}
def syl(w):
    w=re.sub('[^a-z0-9]','',w.lower()); return max(1,len(re.findall('[aeiouy]+',w))-(1 if w.endswith('e') and len(w)>3 else 0))
caps=[]
for s,regs in R:
    for a,b,txt in regs:
        ws=txt.split(); sy=np.array([syl(w)+0.6 for w in ws]); cum=np.concatenate([[0],np.cumsum(sy)])/sy.sum(); wt=[a+(b-a)*c for c in cum]
        toks=[];i=0
        while i<len(ws):
            if i+1<len(ws) and (ws[i].lower(),ws[i+1].lower()) in PAIR: toks.append([i,i+1]); i+=2
            else: toks.append([i]); i+=1
        ch=[];cur=[]
        for tk in toks:
            L=len(' '.join(ws[j] for j in cur+tk))
            if cur and (L>17 or len(cur)+len(tk)>3): ch.append(cur);cur=[]
            cur=cur+tk
        if cur: ch.append(cur)
        if len(ch)>1 and len(ch[-1])==1 and len(' '.join(ws[j] for j in ch[-2]+ch[-1]))<=18: last=ch.pop(); ch[-1]+=last
        for c in ch:
            t0=o(s,wt[c[0]]); t1=o(s,min(wt[c[-1]+1],b))
            words=[re.sub(r'[,.]$','',ws[j]) for j in c]
            hl=[i for i,j in enumerate(c) if re.sub('[^a-z0-9]','',ws[j].lower()) in HL or (s=='c' and re.sub('[^a-z0-9]','',ws[j].lower())=='car')]
            caps.append(dict(t0=round(t0-0.04,3),t1=round(t1,3),words=words,hl=hl))
# bridge text over the B-roll (not spoken)
caps.append(dict(t0=round(starts[2]+0.05,3),t1=round(o('b',2.1),3),words=['Then','I','found','this','app 👇'],hl=[4]))
caps.sort(key=lambda c:c['t0'])
for i in range(len(caps)-1):
    if caps[i+1]['t0']-caps[i]['t1']<0.4: caps[i]['t1']=caps[i+1]['t0']
    caps[i]['t1']=min(caps[i]['t1'],caps[i+1]['t0'])
TL=dict(caps=caps,nts=[{**n,'t0':round(n['t0'],3),'t1':round(n['t1'],3)} for n in NTS],bad=[round(x,3) for x in BAD],end=round(starts[-1]+0.12,3))
open('tl.js','w').write('TL='+json.dumps(TL,ensure_ascii=False)+';')
json.dump(dict(TOTAL=TOTAL,starts=starts),open('meta.json','w'))
print('TOTAL',round(TOTAL,2),[round(x,2) for x in starts])
for c in caps: print(c['t0'],c['t1'],' '.join(w.upper() if i in c['hl'] else w for i,w in enumerate(c['words'])))
