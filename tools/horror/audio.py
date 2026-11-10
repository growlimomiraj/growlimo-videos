import numpy as np, soundfile as sf, json, subprocess, os
from scipy.signal import butter, lfilter, fftconvolve, resample_poly
TM=json.load(open('timings.json')); SR=48000; T=TM['total']; N=int(T*SR)
rng=np.random.default_rng(11)
L=np.zeros(N); R=np.zeros(N)
def bp(x,lo,hi,o=2): b,a=butter(o,[lo/(SR/2),hi/(SR/2)],'band'); return lfilter(b,a,x)
def lp(x,f,o=2): b,a=butter(o,f/(SR/2)); return lfilter(b,a,x)
def hp(x,f,o=2): b,a=butter(o,f/(SR/2),'high'); return lfilter(b,a,x)
def add(sig,t,g=1.0,pan=0.0):
    i=int(t*SR); n=min(len(sig),N-i)
    if n<=0: return
    L[i:i+n]+=sig[:n]*g*(1-max(0,pan)); R[i:i+n]+=sig[:n]*g*(1+min(0,pan))
tt=np.arange(N)/SR
def env_pts(pts):
    xs=[p[0] for p in pts]; ys=[p[1] for p in pts]; return np.interp(tt,xs,ys)
# --- drone bed
dr=(np.sin(2*np.pi*41.2*tt)+0.7*np.sin(2*np.pi*41.9*tt+1)+0.35*np.sin(2*np.pi*61.7*tt)+0.25*np.sin(2*np.pi*82.4*tt*(1+0.002*np.sin(tt*0.7))))
dr+=lp(rng.standard_normal(N),180)*3
dr*=0.11*(0.75+0.25*np.sin(2*np.pi*0.13*tt))
de=env_pts([(0,0),(1.0,0.8),(TM['t_zoom']-0.6,1.0),(TM['t_zoom'],0.4),(TM['t_gl'],0.55),(TM['t_night'],1.0),(TM['scare']-1.2,1.3),(TM['scare']-0.35,0.0),(TM['scare'],0),(TM['t_black'],0),(TM['t_end']+0.1,0.7),(T-0.9,0.8),(T,0)])
add(dr*de,0,1.0)
# high eerie tone in night section
hi=np.sin(2*np.pi*1720*tt)*0.5+np.sin(2*np.pi*1733*tt)*0.5
add(hi*0.012*env_pts([(TM['t_night'],0),(TM['t_night']+2,1),(TM['scare']-1.5,1.5),(TM['scare']-0.35,0),(T,0)]),0)
# --- space whoosh rising into city (0-6s) and dive whoosh
def whoosh(dur,f0,f1,g):
    n=int(dur*SR); x=rng.standard_normal(n); out=np.zeros(n); seg=1024
    for j in range(0,n,seg):
        fr=f0*(f1/f0)**(j/n); out[j:j+seg]=bp(x[j:j+seg],fr,min(fr*2.2,20000),1)
    e=np.sin(np.linspace(0,np.pi,n))**1.5; return out*e*g
add(whoosh(5.6,150,2500,0.16),0.3,1,0.1)
add(whoosh(0.8,400,9000,0.35),TM['t_zoom']-0.7,1,-0.1)
# impact boom at street view drop
def boom(g=0.9,f=48,d=1.4):
    n=int(d*SR); t=np.arange(n)/SR; s=np.sin(2*np.pi*(f+60*np.exp(-t*18))*t)*np.exp(-t*3.2)
    s+=lp(rng.standard_normal(n),300)*np.exp(-t*9)*2; return s*g
add(boom(0.75),TM['t_zoom'])
# daytime city ambience 10.2-13.4
amb=bp(rng.standard_normal(int(3.3*SR)),300,3000)*0.05; amb*=np.minimum(1,np.arange(len(amb))/SR/0.3)
add(amb,TM['t_sv'])
# glitch 13.4-13.9
n=int(0.5*SR); g=np.zeros(n)
for j in range(0,n,int(0.035*SR)):
    blk=rng.standard_normal(int(0.035*SR))*(0.3+0.7*rng.random())
    if rng.random()<0.4: blk=np.sign(np.sin(2*np.pi*rng.integers(80,900)*np.arange(len(blk))/SR))*0.5
    g[j:j+len(blk)]=blk[:n-j]
add(hp(g,200)*0.22,TM['t_gl'])
add(boom(0.35,60,0.6),TM['t_night'])
# night clip ambience (Flow audio)
parts=[]
for c in TM['night_clips']:
    subprocess.run(f"ffmpeg -v error -y -i '{c['file']}' -ac 1 -ar {SR} /tmp/_n.wav",shell=True,check=True)
    x,_=sf.read('/tmp/_n.wav'); parts.append(x[int(c['t0']*SR):int(c['t1']*SR)])
amb=np.concatenate(parts); amb=amb/np.abs(amb).max()*0.30
nd=TM['t_black']-TM['t_night']; sc=TM['scare']-TM['t_night']
amb*=np.interp(np.arange(len(amb))/SR,[0,0.3,sc-0.4,sc,nd],[0,1,1,0,0])
add(amb,TM['t_night'])
# heartbeat accelerating 19 -> 24.6
t=TM['scare']-6.0; bpm=62
while t<TM['scare']-0.45:
    for off,gg in [(0,1.0),(0.17,0.7)]:
        n=int(0.18*SR); s=np.sin(2*np.pi*55*np.arange(n)/SR)*np.exp(-np.arange(n)/SR*28)
        add(s*0.55*gg,t+off)
    t+=60/bpm; bpm=min(150,bpm*1.09)
# SCARE sting at 24.967
ts=TM['scare']; n=int(1.8*SR); st=np.zeros(n); tq=np.arange(n)/SR
for fq in [233,247,262,277,370,392,523,554,740]:
    st+=np.sign(np.sin(2*np.pi*fq*tq*(1+0.01*np.sin(tq*30))))*0.12
st=lp(st,5000)+hp(rng.standard_normal(n),1500)*0.5
st*=np.exp(-tq*1.6)*np.minimum(1,tq/0.008)
add(st*0.75,ts); add(boom(1.0,40,1.8),ts); add(st*0.4,ts+0.02,1,0.6)
# end swell (reverse cymbal-ish) into end card
n=int(1.4*SR); sw=hp(rng.standard_normal(n),3000)*np.linspace(0,1,n)**3*0.25
add(sw,TM['t_end']-1.4+0.05)
# low piano-ish note on end card
for k,(fq,tt0) in enumerate([(110,TM['t_end']+0.2),(103.8,TM['t_end']+2.2),(98,TM['t_end']+4.2)]):
    n=int(2.4*SR); q=np.arange(n)/SR; s=(np.sin(2*np.pi*fq*q)+0.4*np.sin(2*np.pi*2*fq*q)+0.2*np.sin(2*np.pi*3.01*fq*q))*np.exp(-q*1.6)
    add(s*0.12,tt0)
# --- voice: EQ + room reverb
vo=json.load(open('vo.json')); ST=TM['ST']
ir_n=int(1.6*SR); ir=rng.standard_normal(ir_n)*np.exp(-np.arange(ir_n)/SR*4.5); ir=lp(ir,4000); ir/=np.abs(ir).sum()**0.5*8
V=np.zeros(N)
for k,t0 in ST.items():
    x,sr=sf.read(f'vo_{k}.wav'); x=resample_poly(x,SR,sr)
    x=hp(x,70); x=x+0.35*lp(x,220)                 # warmth
    i=int(t0*SR); n=min(len(x),N-i); V[i:i+n]+=x[:n]
V=V/np.abs(V).max()*0.9
wet=fftconvolve(V,ir)[:N]; wet=wet/np.abs(wet).max()*0.25
# duck bed under voice
from scipy.ndimage import maximum_filter1d, uniform_filter1d
h=int(0.02*SR); rms=np.array([np.sqrt(np.mean(V[i:i+h]**2)) for i in range(0,N,h)])
act=uniform_filter1d(maximum_filter1d((rms>0.03).astype(float),20),12); duck=np.repeat(1-0.45*act,h)[:N]
L*=duck; R*=duck
L+=V+wet; R+=V+wet*0.9
mix=np.stack([L,R],1); mix=mix/np.abs(mix).max()*0.97
sf.write('mix.wav',mix,SR)
print('ok',mix.shape[0]/SR)
