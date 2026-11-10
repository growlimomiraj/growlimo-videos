# Builds tl.js (overlay timeline) and timings.json (audio) from config.json + vo.json + zoom/night meta.
import json
CFG=json.load(open('config.json')); vo=json.load(open('vo.json'))
zm=json.load(open('zoom_meta.json')); nm=json.load(open('night_meta.json'))
FPS=30
t_zoom=(zm['nA']+zm['nB']+zm['nC'])/FPS          # 10.2
t_pin=[zm['nA']/FPS,(zm['nA']+zm['nB'])/FPS]       # 6.0 - 9.6
t_sv=t_zoom; t_gl=t_sv+3.2; t_night=t_gl+0.5; t_black=t_night+nm['night_dur']; t_end=t_black+0.3
scare=t_night+nm['scare_in_night']
total=t_end+6.9
ST={'l1':1.4,'l2':t_pin[0]-0.1,'l3':t_sv+0.3,'l4':t_night+0.5,'l5':t_end+0.2}
HL={w.lower() for w in CFG.get('highlight',[])}
caps=[]
for k in ['l1','l2','l3','l4']:
    w=vo[k]['words']; s=vo[k]['starts']; d=vo[k]['dur']; i=0
    splits=CFG['captions'][k]           # word indices where each caption chunk ends
    for j in splits:
        a=ST[k]+s[i]-0.05; b=ST[k]+(s[j] if j<len(s) else d)
        words=[CFG.get('display',{}).get(w[x].lower(),w[x]).rstrip(',') for x in range(i,j)]
        hl=[n for n,x in enumerate(range(i,j)) if w[x].lower().strip(',.') in HL]
        caps.append(dict(t0=round(a,3),t1=round(b,3),words=words,hl=hl)); i=j
for i in range(len(caps)-1):
    if caps[i+1]['t0']-caps[i]['t1']<0.35: caps[i]['t1']=caps[i+1]['t0']
pin=[[round(x,1),round(y,1)] for x,y in zm['pin']]
TL=dict(caps=caps,pin=pin,pinT=t_pin,pinSubT=ST['l2']+vo['l2']['starts'][-2] if len(vo['l2']['starts'])>2 else t_pin[0]+1.5,
        hook=[0.1,3.6],night=[t_night,t_black],scare=scare,end=t_end,total=total,
        T=CFG['texts'])
open('tl.js','w').write('TL='+json.dumps(TL,ensure_ascii=False)+';')
json.dump(dict(ST=ST,t_zoom=t_zoom,t_sv=t_sv,t_gl=t_gl,t_night=t_night,t_black=t_black,t_end=t_end,scare=scare,total=total,
               night_clips=CFG['night']),open('timings.json','w'),indent=1)
print('total',round(total,2),'scare',round(scare,2))
for c in caps: print(c['t0'],c['t1'],' '.join(x.upper() if n in c['hl'] else x for n,x in enumerate(c['words'])))
