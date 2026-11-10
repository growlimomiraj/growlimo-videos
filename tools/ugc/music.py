import numpy as np, scipy.io.wavfile as wf
from scipy.signal import lfilter, butter
SR=48000; T=40; bpm=118; beat=60/bpm; n=int(SR*T); out=np.zeros((n,2))
rng=np.random.default_rng(7)
def env(L,a=0.01,r=0.3):
    t=np.arange(L)/SR; e=np.minimum(t/a,1)*np.exp(-t/r); return e
def note(f,dur,amp,r=0.6):
    L=int(dur*SR); t=np.arange(L)/SR
    s=(np.sin(2*np.pi*f*t)+0.35*np.sin(4*np.pi*f*t+0.3)+0.12*np.sin(6*np.pi*f*t))*env(L,0.008,r)
    return s*amp
chords=[[50,54,57,61],[47,50,54,57],[43,47,50,54],[45,49,52,55]]  # Am7 Fmaj7 Cmaj7 G
m2f=lambda m:440*2**((m-69)/12)
bar=4*beat
for b in range(int(T/bar)+1):
    ch=chords[b%4]; t0=b*bar
    for k in range(8):  # plucked eighths arpeggio
        m=ch[[0,2,1,3,2,1,3,2][k]]+12; i=int((t0+k*beat/2)*SR)
        s=note(m2f(m),0.5,0.085,0.16); L=min(len(s),n-i)
        if L>0: pan=0.35+0.3*(k%2); out[i:i+L,0]+=s[:L]*(1-pan); out[i:i+L,1]+=s[:L]*pan
    for m in ch[:3]:
        i=int(t0*SR); s=note(m2f(m-12),bar,0.05,1.6); L=min(len(s),n-i)
        if L>0: out[i:i+L]+=s[:L,None]
    i=int(t0*SR); s=note(m2f(ch[0]-24),bar,0.16,0.9); L=min(len(s),n-i)
    if L>0: out[i:i+L]+=s[:L,None]
for q in range(int(T/beat)):
    i=int(q*beat*SR)
    L=int(0.25*SR); t=np.arange(L)/SR; kick=np.sin(2*np.pi*(50+90*np.exp(-t*30))*t)*np.exp(-t*12)*0.35
    L2=min(L,n-i); out[i:i+L2]+=kick[:L2,None]
    for h in (0.5,):
        j=int((q+h)*beat*SR); Lh=int(0.05*SR); hat=rng.standard_normal(Lh)*np.exp(-np.arange(Lh)/SR*90)*0.05
        bb,aa=butter(2,7000/(SR/2),'high'); hat=lfilter(bb,aa,hat); L3=min(Lh,n-j)
        if L3>0: out[j:j+L3]+=hat[:L3,None]
    if q%2==1:
        Ls=int(0.18*SR); sn=rng.standard_normal(Ls)*np.exp(-np.arange(Ls)/SR*22)*0.09
        bb,aa=butter(2,[1500/(SR/2),6000/(SR/2)],'band'); sn=lfilter(bb,aa,sn); L4=min(Ls,n-i)
        if L4>0: out[i:i+L4]+=sn[:L4,None]
out/=np.abs(out).max()*1.1
wf.write('music.wav',SR,(out*32767).astype(np.int16))
