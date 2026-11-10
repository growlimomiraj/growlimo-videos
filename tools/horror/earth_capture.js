// Paste into the Google Earth tab with javascript_tool (built-in browser, viewport emulated 1080x1920).
// Google Earth in the app's browser renders ~1 fps and canvas.captureStream() barely delivers frames,
// so we read the WebGL back buffer right after each draw (microtask after drawElements/drawArrays).
(() => {
  const c = document.getElementById('earth-canvas');
  const gl = c.getContext('webgl'); window._gl = gl;
  const W = c.width, H = c.height;
  window._buf = new Uint8Array(W * H * 4);
  window._ocv = document.createElement('canvas'); _ocv.width = W; _ocv.height = H;
  window._octx = _ocv.getContext('2d'); window._img = _octx.createImageData(W, H);
  window._frames = 0; window._sched = false; window._capOn = true;
  const P = WebGLRenderingContext.prototype;
  for (const m of ['drawElements', 'drawArrays']) {
    const o = P[m]; if (o.__h) continue;
    const h = function (...a) { const r = o.apply(this, a); if (this === window._gl && window._capOn && !window._sched) { window._sched = true; queueMicrotask(window._read); } return r; };
    h.__h = 1; P[m] = h;
  }
  window._read = function () {
    window._sched = false; const gl = window._gl;
    const fb = gl.getParameter(gl.FRAMEBUFFER_BINDING); gl.bindFramebuffer(gl.FRAMEBUFFER, null);
    gl.readPixels(0, 0, W, H, gl.RGBA, gl.UNSIGNED_BYTE, window._buf); gl.bindFramebuffer(gl.FRAMEBUFFER, fb);
    const src = window._buf, dst = window._img.data, row = W * 4;
    for (let y = 0; y < H; y++) dst.set(src.subarray((H - 1 - y) * row, (H - y) * row), y * row);
    window._octx.putImageData(window._img, 0, 0); window._frames++;
  };
  window.SHOTS = window.SHOTS || [];
  // snap(label, waitMs): wait for tiles to settle, then copy the latest frame. URL holds "...,<dist>d,..."
  window.snap = async function (label, wait) {
    await new Promise(r => setTimeout(r, wait || 7000));
    const f = window._frames; for (let i = 0; i < 20 && window._frames === f; i++) await new Promise(r => setTimeout(r, 250));
    const cv = document.createElement('canvas'); cv.width = _ocv.width; cv.height = _ocv.height; cv.getContext('2d').drawImage(_ocv, 0, 0);
    const u = location.href.split('/@')[1].split('/')[0]; window.SHOTS.push({ label, cv, u }); return [label, window.SHOTS.length, u];
  };
  // exportMosaic(name, shots, cols): one JPEG download (goes to the Downloads folder)
  window.exportMosaic = async function (name, shots, cols) {
    const m = document.createElement('canvas'); const rows = Math.ceil(shots.length / cols);
    m.width = W * cols; m.height = H * rows; const x = m.getContext('2d'); x.fillStyle = '#000'; x.fillRect(0, 0, m.width, m.height);
    shots.forEach((s, i) => x.drawImage(s.cv, (i % cols) * W, Math.floor(i / cols) * H));
    const b = await new Promise(r => m.toBlob(r, 'image/jpeg', 0.93));
    const a = document.createElement('a'); a.href = URL.createObjectURL(b); a.download = name + '.jpg'; document.body.appendChild(a); a.click(); a.remove();
    return [name, b.size, shots.map(s => s.label + '|' + s.u.split(',')[3])];
  };
  return [W, H];
})();
