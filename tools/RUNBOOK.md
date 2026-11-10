# GrowLimo Apps — nightly shorts runbook

Two vertical 1080×1920 shorts every night, one per app, posted to that app's Instagram page:

| App | Instagram page | vidIQ platformAccountId | Play Store link |
|---|---|---|---|
| Earth Map | @earthmaplivesatellite | 29231600796473915 | https://play.google.com/store/apps/details?id=com.earthmap.satelliteview |
| Bluetooth Auto Connect | @bluetooth_auticonnect | 29599495256321483 | https://play.google.com/store/apps/details?id=com.bluetooth.autoconnect |

The main page @emma_wa8son gets nothing until it is renamed (owner decision).

## 0. Setup (every run — the workspace starts empty)
1. `add_repo growlimomiraj/growlimo-videos` with **push** access, clone to `/home/claude/growlimo-videos`, `bash tools/setup.sh` (Kokoro TTS + Python deps).
2. Read `tools/used_places.txt` and `tools/bt_scenarios_used.txt` so nothing repeats.
3. Built-in browser on the owner's PC (`desktop-gs1buou`): load the `built-in-browser` skill first. Flow project: https://flow.google.com/u/3/project/ab0de2c0-b6e4-4db9-a41d-d4eb76ce1f4c (Omni 1.2 Flash, 9:16, 720p, 8 s). Note the credit balance shown in Flow before generating.
4. Browser downloads land in `C:\Users\GrowLimo - Umair\Downloads`. Stage files from there with `device_stage_files` (the scheduled task has that folder attached). If it is not reachable, use `C:\Users\GrowLimo - Umair\flow videos`, and if neither works, stop and report.

Credit plan per night: Earth Map ≈ 48 (one night prompt ×2), Bluetooth ≈ 72 (hook 8 s + extend 8 s + CTA 8 s). If the balance is below 130, make only the Earth Map video with ×1 (24). If it is below 30, generate nothing and report that the credits are exhausted.

## A. Earth Map — horror Street View short (`tools/horror/`)
Formula (≈33 s): hook text "Never open this street at 3 AM 😨" → smooth zoom from space to the place (real Google Earth stills) → red pin + label → dive → real daytime Street View ("By day, it looks completely normal.") → glitch → night Flow scene, framed as a Street View 360° turn, with a creepy reveal and a jump scare → end card "Explore every street on Earth… if you dare", Google Play badge, "Link in bio". There is a small "Dramatization" tag on the night scene. Voice: Kokoro `bm_george` at 0.92.

1. **Pick the place**: the first entry in `tools/horror/places.json` whose slug is not in `used_places.txt`.
2. **Capture the zoom stack (Google Earth, built-in browser)**:
   - `resize_window` 1080×1920 on the tab. Open https://earth.google.com/web/ and click **Explore Earth**. Under View > Basemap settings, choose **Clean** (no labels).
   - Search the place and close the info panel. Make the view top-down: tilt 0 (use the 2D button if it is tilted) and north up. Scroll in at screen centre until the URL distance is about 200 m with the place near the centre. Note its pixel position in the 1080×1920 frame; this is `target_px`, and you can find it from a full-scale `computer zoom`.
   - Inject `tools/horror/earth_capture.js` with `javascript_tool`, then `await snap('L0',1500)`.
   - Repeat until the URL distance exceeds 2e7: `computer scroll` **down 10** at screen centre (take a screenshot first), then `await snap('L<n>',7000)`. That gives about 16–17 levels.
   - `await exportMosaic('<slug>_zoomstack', SHOTS, 6)`. It returns the distances: put them in `config.json` as `levels_d`, in order.
   - Street View: click the pegman (bottom right), wait about 8 s for the blue lines, then click a blue line on the street. If the map pans instead, find the line again and click again. Wait 10 s, then `window.SV=[]; await snap('SV0',1500); SV.push(SHOTS.pop()); await exportMosaic('<slug>_sv', SV, 1)`. Clear the canvas-drawn arrows with `sv_crop_x/sv_crop_w`, which crops to the upper part. Then `resize_window desktop`.
   - Google Earth renders only about 1 fps in this browser. **Never record it with MediaRecorder**; that is why we use stills.
3. **Night scene (Flow)**: text-to-video, ×2, with this prompt: *"Vertical 9:16 footage that looks exactly like a real Google Street View panorama captured at night: camera on a pole about 2.5 m high, perfectly stationary, slowly and smoothly rotating 360 degrees at constant speed, wide-angle street-view lens. Location: <place night description from places.json>, 3 a.m., thin fog, one flickering light, completely empty, no people, no cars. Photorealistic, real camera noise, cold blue night tones with sickly yellow light, deeply unsettling. No text, no captions, no subtitles, no music; only quiet ambient wind."* Download both results at 720p: the Download media button, then 720p. Use page scripting to click it if needed.
4. **Stage** `<slug>_zoomstack.jpg`, `<slug>_sv.jpg` and the two `.mp4` files from Downloads. Split the mosaic into `lv/L0..Ln.png` (1080×1920 tiles, 6 per row) and `lv/SV0.png`. Write `config.json`; the Doyers Street example is in `tools/horror/config.example.json`. Lines: l1 "This is <Name>.", l2 from places.json, l3 "By day, it looks completely normal.", l4 "But someone opened Street View here at three a.m. and turned around.", l5 "Explore every street on Earth, if you dare. Earth Map, free on Google Play. Link in bio." Set `captions` to the word-index splits, 2–3 words per chunk.
5. **Build** in a work dir containing all of `tools/horror/*`, `icon.png` (Earth Map icon), `lv/`, `in/` and `config.json`: `python3 vo.py && python3 zoom.py && python3 build_video.py && python3 timeline.py && python3 audio.py && ./finish.sh out.mp4`.
6. **QC**: extract about 10 frames and look at them. Check the zoom has no black gaps, the captions are readable, the night scene shows the creepy reveal and the end card is clean. Check loudness is about -14 LUFS and the file is under 100 MB. Fix and rebuild if anything is wrong.

## B. Bluetooth Auto Connect — UGC presenter short (`tools/ugc/`)
Formula (≈30 s): a real-looking person has a relatable Bluetooth problem (hook) → shows the app → it auto-connects (phone-style "Connected" notifications) → CTA "It's free on Google Play. Link's in my bio." → blue end card with Google Play and "Link in bio". Captions are word tiles, with keywords on blue tiles. A different person and setting every night, e.g. car, gym with earbuds, home speaker party, office headset call, road trip, morning run. Log each one in `tools/bt_scenarios_used.txt`.

1. **Flow**:
   - Clip 1: text-to-video, 8 s, hook line in quotes for lip-sync.
   - Extend: in the scene editor, Add clip > Extend, set the length to 8 s with the slider and arrow keys, then add the second line.
   - Clip 3 (CTA): in Ingredients mode, use a still of the same person as reference. Grab the still in the Flow page by drawing a frame of the clip's `flow-content.google/video/...` URL to a canvas. Upload it by hooking `HTMLInputElement.prototype.click` and setting the file with `DataTransfer` before clicking **Upload media**.
   - After an extend, select the **extended** version in the scene's history before downloading. The download must be about 16 s; check the size (about 5–6 MB).
2. **Edit**: adapt `tools/ugc/make.py`. Set the `SEG` cut list, the `R` caption regions and the `NTS` notifications from the speech regions of the new clips. Use the RMS-threshold speech-region detection, 20 ms frames at -30 dB from peak. Keep the music from `music.py`, render with `render_ov.py`, and `loudnorm` to -14 LUFS.
3. **QC** the same way as A.

## C. Publish (both)
1. Copy to `videos/<app>/<YYYY-MM-DD>-<app>-<slug>.mp4`, commit ending with the attribution trailer, and push.
2. `vidiq_video_upload(url=https://raw.githubusercontent.com/growlimomiraj/growlimo-videos/main/videos/...)`, then `vidiq_instagram_publish_reel(platformAccountId, videoUrl, caption, isAiGenerated=true)`. Poll the same `containerId` every ~20 s until it shows PUBLISHED. Never create a second container for the same video.
3. Comment the Play Store link from the page's own account in the built-in browser. Switch profiles with More > Switch profiles. In the comment box, type then press Return, reload, and confirm the comment is there. Pinning is mobile-only, so remind the owner.
4. Append the slug to `used_places.txt` or `bt_scenarios_used.txt`, commit and push.

## Gotchas learned (2026-11-11 run)
- Browser-pane downloads land in Downloads as `<guid>.tmp` files (not the real filename). List the folder, pick the newest `.tmp` by mtime/size, and stage it. Do one download at a time so you know which is which. Don't `navigate` the Earth tab right after `exportMosaic` — the download can be lost; stage it first.
- After re-injecting `earth_capture.js` on a static view, nothing redraws: hover the mouse over the canvas once before `snap`, otherwise you get a blank frame. In Street View, hover near the bottom (cropped area) so the cursor ring isn't in the shot.
- Stop the zoom stack at the first level ≥ ~1.8e7 m; an extra level (~3.7e7) aligns badly and leaves a dark rectangle over the globe. `zoom.py` now starts at P0=1.0 and fades levels in from 45% coverage.
- Flow flagged "mannequin figures" as sexual content (refunded). Use "a tall dark shadowy silhouette" instead.
- Extend length slider: press Right one key per action (a `repeat` count overshoots). Check `input[type=range]` value = 8.

## Rules
- Never post a video that failed QC. Post nothing rather than something broken, and report why.
- No real people's names or likenesses in the Flow prompts. No gore. Keep the horror to the level of Halloween props and shadowy figures.
- Do not sign in to anything or enter passwords. If Flow, Instagram or Google Earth shows a sign-in page, stop and report.
- If the PC or the browser can't be reached, report that and end.
