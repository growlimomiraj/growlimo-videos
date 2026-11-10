import sys, os, asyncio
from playwright.async_api import async_playwright
# usage: render_ov.py total_seconds fps workers
T=float(sys.argv[1]); FPS=int(sys.argv[2]); W=int(sys.argv[3])
N=int(round(T*FPS)); os.makedirs('ov',exist_ok=True)
async def worker(pw,k):
    b=await pw.chromium.launch(executable_path='/usr/bin/google-chrome',args=['--allow-file-access-from-files'])
    p=await b.new_page(viewport={'width':1080,'height':1920})
    await p.goto('file://'+os.path.abspath('overlay.html')); await p.wait_for_timeout(600)
    last=None
    for i in range(k,N,W):
        t=i/FPS
        await p.evaluate(f'render({t})')
        await p.screenshot(path=f'ov/{i:05d}.png',omit_background=True)
    await b.close()
async def main():
    async with async_playwright() as pw:
        await asyncio.gather(*[worker(pw,k) for k in range(W)])
asyncio.run(main())
