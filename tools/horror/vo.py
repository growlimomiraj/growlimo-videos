import json, numpy as np, soundfile as sf
from kokoro_onnx import Kokoro
import os
TTS=os.environ.get('TTS_DIR','/home/claude/tts')
K=Kokoro(f'{TTS}/kokoro-dur.onnx',f'{TTS}/voices-v1.0.bin')
SR=24000; HOP=600
CFG=json.load(open('config.json')); V=CFG.get('voice',['bm_george',0.92]); LINES={k:[V[0],V[1],t] for k,t in CFG['lines'].items()}
out={}
for key,(voice,speed,text) in LINES.items():
    lang='en-us' if voice[0]=='a' else 'en-gb'
    ph=K.tokenizer.phonemize(text,lang); toks=K.tokenizer.tokenize(ph)
    style=K.voices[voice][len(toks)]
    a,d=K.sess.run(None,{'tokens':[[0,*toks,0]],'style':style,'speed':np.array([speed],dtype=np.float32)})
    a=a.reshape(-1).astype(np.float32); d=d.reshape(-1).astype(float)
    lead=d[0]*HOP/SR; tail=d[-1]*HOP/SR
    seg=a[int(lead*SR):len(a)-int(max(0,tail-0.05)*SR)]
    sf.write(f'vo_{key}.wav',seg,SR)
    # word timing by phoneme spaces
    kept=[c for c in ph if c in K.tokenizer.vocab]; t=0; starts=[0.0]
    for c,dd in zip(kept,d[1:-1]):
        t+=dd*HOP/SR
        if c==' ': starts.append(t)
    out[key]=dict(dur=len(seg)/SR,words=text.split(),starts=starts[:len(text.split())])
json.dump(out,open('vo.json','w'),indent=0)
for k,v in out.items(): print(k,round(v['dur'],2),len(v['words']),len(v['starts']))
