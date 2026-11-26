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

## Gotchas learned (2026-11-12 run)
- Word timings: Hugging Face / OpenAI model hosts are blocked, so faster-whisper can't download. `pip install pocketsphinx --break-system-packages` works offline (bundled model): `Decoder(samprate=16000)`, then `seg()` gives `word, start_frame/100, end_frame/100`. Good enough for caption timing.
- UGC render: copy `bluetooth_icon.png` to `icon.png` in the work dir, or the notification and end-card icons render blank.
- Single-pass loudnorm landed at -15.2 LUFS on the UGC mix; use two-pass (`print_format=json`, then `measured_*` + `linear=true`) to hit ~-14.
- Before generating night scenes, check Downloads/Flow for unused clips of the same place (the 11-11 run left two Winchester clips; reused them, 0 credits).
- Earth zoom stack: 10 ticks gave only ~1.65× per level near the ground; 13 ticks (10+3) gives ~2.17×. Batch at most 3 levels per browser_batch (50 s limit).
- Browser-pane screenshots lag one action behind on Earth/Flow; take a second screenshot or read state with JS before clicking.

## Rules
- Never post a video that failed QC. Post nothing rather than something broken, and report why.
- No real people's names or likenesses in the Flow prompts. No gore. Keep the horror to the level of Halloween props and shadowy figures.
- Do not sign in to anything or enter passwords. If Flow, Instagram or Google Earth shows a sign-in page, stop and report.
- If the PC or the browser can't be reached, report that and end.

## Gotchas learned (2026-11-13 run)
- Earth: you can skip search and go straight to a top-down view with `navigate https://earth.google.com/web/@<lat>,<lon>,<alt>a,220d,35y,0h,0t,0r` (wait ~15 s, hover once). Any `navigate` reloads the page, so re-inject `earth_capture.js` after it. A Street View pano can't be opened by URL (it drops back to space); use pegman + click a blue line, then `left_click_drag` to turn/tilt.
- 13 ticks per level from 220 m gave 16 levels (L15 ≈ 1.98e7) with match scores ≥0.82 except L0 (0.38, still fine). 2 levels per browser_batch fits the 50 s limit; 3 can time out (the snap still lands, check `SHOTS`).
- Downloads: Flow clips and blob JPEGs first land as `<guid>.tmp`, later renamed (`<Title>…_<8hex>.mp4`, `<name>.jpg`). Staging the `.tmp` works; match by size.
- Flow pane size can change mid-run (800×600 → 480×360); prefer `find` refs or take a fresh screenshot before coordinate clicks. Extend popup covers the prompt box: press Escape after setting the slider, then type.
- Reference still for the CTA: the scene thumbnails are `<img>` 720×1280 frames that `fetch()` fine from the Flow page — `REFB = await (await fetch(img.src)).blob()`, then the `HTMLInputElement.prototype.click` hook. Restore the original `click` afterwards.
- BT tonight used 4 gens (hook 8 s, extend 8 s, B-roll 8 s, one CTA clip with both the app line and "free on Google Play / link in bio") = 96 credits; make.py adapted to 3 sources (a, b, c). pocketsphinx `Segment` uses `start_frame`/`end_frame`.
- The extend line got cut off at 16.0 s ("Every single…"); keep extend lines short (≤ 6 s of speech).

## Gotchas learned (2026-11-14 run)
- Some places have NO Street View coverage on the property (Waverly Hills: private land, blue lines only on distant side streets). Fallback that worked: a tilted 3D Earth view of the facade as the "daytime" shot — `navigate @<lat>,<lon>,200a,300d,35y,0h,72t,0r` (camera south of a south-facing facade), wait ~30 s for tiles, re-inject `earth_capture.js`, snap `SV0` and set `sv_crop_x: 0, sv_crop_w: 1080` (full frame; the canvas has no UI to crop).
- Zoom stack from 450 m start (13 ticks/level) reached 2.47e7 at L14 — globe looked clean, match scores 0.75–0.92.
- Flow downloads: right-click a tile → Download → use `find "Original size"` and click that ref (submenu position varies). A download from the scene editor's top download button silently failed once; re-download from the grid tile (the stacked/extended tile gives the 16 s file, ~6.6 MB).
- "Add to prompt" on a video tile attaches the *video* (switches to 15 s video-to-video) — remove it. For the CTA reference still, open the scene editor and `fetch()` the first 720×1280 timeline `<img>` (y≈507), then use the `HTMLInputElement.prototype.click` hook + Upload media. Grid `<video>` previews are tainted / fetch-blocked.
- The Ingredients CTA clip came back with **burned-in subtitles** at ~74–80 % height despite "no subtitles". Fixed in make.py with zoom 1.38 and a top-anchored crop (`TOP={'c'}`). Check every Flow clip for burned text.
- Extend 8 s = 24 credits (4 s = 12). Credits used tonight: 48 (Earth ×2) + 24 hook + 24 B-roll + 24 extend + 24 CTA = 144.

## Gotchas learned (2026-11-16 run)
- Earth search box: the first click only opens the dropdown; type after it is focused. Pick the place result, read its lat/lon from the URL, then `navigate @lat,lon,40a,450d,35y,0h,0t,0r`. Clean basemap is under View > Basemap settings > Clean.
- 450 m start, 13 ticks/level → 15 levels (L14 ≈ 2.2e7), match scores 0.86–0.97 (L0 0.68). 2 levels per browser_batch fits.
- Street View drags: a 600 px drag turns ~27°. In a batch, a drag that changes the URL aborts the batch ("Page navigated during drag"), so drag one call at a time. A drag can also hop to the next pano; check the view before snapping.
- Lizzie Borden House: "an axe leaning by the door" was swapped for "a rocking chair moving on its own" to stay clear of violence filters; the silhouette-in-window still read well.
- Scene-editor timeline `<img>`s were only 54×96 data URIs this time. The 720×1280 still at the top scene strip (first `img` with naturalWidth 720 and y<60) was the current scene's first frame and worked as the CTA reference.
- BT used 3 gens (hook 8 s + extend 8 s + CTA 8 s = 72). No B-roll: the extend clip's dead air (she looks at her phone, ~8.3–11 s) served as the B-roll under "Then I found this app 👇". Final cut ≈21 s. Local make.py: SEG a/a/a/c/c with B-roll at index 1 (music gain + whoosh indices moved to starts[1]).
- Caption chunker splits "that | connects them" (18 chars > 17); add a PAIR ('that','connects') so the last-word merge keeps it as one tile.

## Gotchas learned (2026-11-17 run)
- Credits were 112 (< 130) → Earth Map only, night ×1 (24). One clip is enough: reuse the reveal as the second night piece (`skA` 0–8 s, then `skA` 2.8–4.6 s ending on the window) so the scare lands on the silhouette.
- Hilltop places: a URL `a` below the real ground makes Earth clamp to `10d`. Use the ground altitude Earth reports (Bran: `1190a` worked for the start view). After the first scroll the reference altitude snaps to the real ground (~782 m), so L0's `450d` is really ~858 m above that ground — put the corrected value in `levels_d[0]` (match score then 0.69).
- 13 ticks/level from that start reached 2.0e7 at L13 (14 levels), scores 0.69–0.96.
- Street View: the blue dots around attractions are user photo spheres. The courtyard sphere at Bran had unblurred tourists — skip those. A park sphere below the castle (no people) worked: drag down to tilt up (tilt ~113), `sv_crop_x: 0, sv_crop_w: 1080` (no arrows to crop).
- The Earth tab's pane frame changed mid-run (800×1422 → 514×914); take a fresh full screenshot before coordinate clicks.
- Instagram web: the first `type` after clicking the comment ref can miss (page scrolls). Click the box by coordinate, confirm `document.activeElement` is the TEXTAREA, then type + Return.

## Gotchas learned (2026-11-18 run)
- Credits were 110 (< 130) → Earth Map only, night ×1 (24); 86 left after. The owner then asked for the Bluetooth short anyway (hook 8 s + extend 8 s + CTA 8 s = 72), leaving **14 credits — below the 30 floor, so no new clips until the 4 Dec reset** unless he tops up.
- Islands: start the zoom stack at `1500d` (whole island in frame, `navigate @lat,lon,10a,1500d,35y,0h,0t,0r`, ~30 s for tiles). 13 ticks/level → 13 levels to 1.6e7, then one 7-tick level to 2.45e7 (globe in space). Match scores 0.91–0.99. Mosaic is only ~5 MB (ocean compresses); that's fine.
- Ocean near coasts renders as dark "halos" (real imagery) vs flat lighter blue (generic ocean); it shows as faint soft edges for <1 s mid-zoom. Acceptable.
- Hashima Street View: pegman at 900d shows Google trek lines inside the island; clicking a west-side lane opened a June-2013 sphere (no people) with a staircase in a ruined block. `sv_crop_x 175 / w 731` clears the arrows. A Google Earth survey popup appeared on entering SV — close it with the X.
- Prompt "a tall dark shadowy silhouette standing motionless in a dark doorway" gave a clean reveal at 4.4–6.0 s; night = skA 0–8.05 + skA 4.0–5.8.
- Used l3 "By day, it's just an empty ruin." (the stock "completely normal" line doesn't fit a ruin) and l2 without a year ("Then one day, everyone left.") because digits break the Kokoro word-timing split; the year went in `pin_sub`.
- BT morning-run: the app window was sometimes hidden (`document.visibilityState === 'hidden'`), so screenshots were stale. Work from `find`/`read_page` refs and `javascript_tool` instead: read the slider with `input[type=range]`, check the prompt with `[contenteditable=true]`, progress with `/\d+%/`. If a real right-click opens no menu, dispatch `pointerdown`/`mousedown`/`contextmenu` on the tile's `<img>`; then click the `Download` and `Original size` refs.
- CTA reference still, no canvas needed: cut a frame from the downloaded clip with ffmpeg, push it to `tools/ugc/refs/`, then in the Flow page `fetch()` the raw.githubusercontent URL (allowed), wrap it in a `File`, hook `HTMLInputElement.prototype.click`, click Add ingredients > Upload media. The image lands as a grid tile; open its context menu > **Add to prompt** (on an image this adds an "Ingredient image"; check `img[alt="Ingredient image"]`). Close the picker with Escape and restore `click`.
- The extend line was cut at 16.0 s again ("…for me auto–"). Found a clean dip with a 10 ms RMS profile and cut after "connects them." Keep extend lines to ~8 words, with the action first (5 s of phone tapping made good B-roll).
- Captions: give `R` one region per 2–3 word phrase using the pocketsphinx word times; the syllable interpolation over a whole sentence drifts. Edit script saved as `tools/ugc/make_morning_run_2026-11-18.py`. Final ≈18 s, -14.5 LUFS.

## Gotchas learned (2026-11-19 run)
- Credits were 64 (< 130) → Earth Map only, night ×1 (24); 40 left after. Bluetooth skipped.
- The browser pane was hidden most of the run, and Earth screenshots came back flat grey. Workaround: `tabs_select` the Earth tab, then take a screenshot after a click (that sometimes repaints). Or preview what the canvas shows: draw the captured frame to a 540×960 canvas, download it as `<name>.jpg`, stage it and Read it. A named blob download keeps its real filename after ~5–10 s, with no `.tmp`.
- The Greyfriars ground is ~88 m. Starting at `75a,450d` puts L0 at ~437 m real distance (`levels_d[0]` corrected). 13 ticks/level → 15 levels to 2.23e7, match scores 0.77–0.97.
- A Google Earth survey popup covered the pegman (bottom right ~(600,1373) in the 800×1422 frame). Close it with its X first. The pegman shows Trekker lines inside the kirkyard; clicking one opened a user photo sphere (Apr 2025) with two distant people. One 600 px left-drag (heading 27°) faced wall tombs with no people. `sv_crop_x 175 / w 731`.
- The basemap reverted to labels after the pegman/SV session, but the zoom stack (captured right after setting Clean and one navigate) stayed clean. Check L0 for labels before scrolling.
- Night: "a tall dark hooded silhouette standing motionless far away between the graves" gave a figure in view 0.5–5.5 s; night = skA 0–8.0 + skA 2.2–4.2 (the figure is centred at ~4.0 s, so the scare lands on it). Config saved as `tools/horror/config_greyfriars_2026-11-19.json`.
- Instagram was on @bluetooth_auticonnect; switched with ☰ More (left, ~(28,515)) → Switch profiles → earthmaplivesatellite.

## Gotchas learned (2026-11-20 run)
- Credits were 64 again at the start (< 130) → Earth Map only, night ×1 (24); 40 left after. Bluetooth skipped.
- Browser downloads (Flow mp4 and named blob JPEGs) all stayed as `<guid>.tmp` this time, never renamed. Listing Downloads is ~25k tokens per call, so do every download first and list once; match the `.tmp` by the byte size `exportMosaic`/`preview` return.
- Earth screenshots: grey unless you `tabs_select` the tab right before; the first screenshot after an action is often grey, the second one is real.
- Catacombs start `navigate @48.83388,2.33237,62a,450d,35y,0h,0t,0r` → Earth reported `551a,10d` (camera ~541 m, ground ~75 m); used `levels_d[0]=480` (score 0.75). 13 ticks/level → 15 levels to 2.48e7, scores 0.67–0.90. Clean basemap was already set.
- Pegman: the first click on the Street View hint's X toggled pegman mode off; click pegman again, wait 8 s, click the line. SV at 11 Place Denfert-Rochereau (Oct 2025) faced roadworks; four 600 px left drags (heading ~110°) faced the Denfert RER station with no clear people.
- Night prompt with "tunnel entrance lined with ancient stacked skulls like a museum ossuary … a tall dark shadowy silhouette standing motionless deep in the tunnel" passed the filter; figure visible 2.5–5.5 s. night = skA 0–8.04 + skA 3.0–5.0. Config saved as `tools/horror/config_catacombs-paris_2026-11-20.json`. Final 31.1 s, -14.3 LUFS, 45.6 MB.
- Instagram was already on @earthmaplivesatellite (nav "Profile" image alt shows the active account).

## Gotchas learned (2026-11-21 run)
- Credits were 64 again (< 130) → Earth Map only, night ×1 (24); 40 left after. Bluetooth skipped.
- Earth search results live in shadow DOM (find/get_page_text see nothing) — skip search and `navigate @lat,lon,...` directly. Bhangarh palace: `@27.0964,76.2859,350a,800d` (ground ≈ 426 m, so L0 real distance = 1150−426 ≈ 724 m; `levels_d[0]=724.35`). 13 ticks/level → L13 = 1.70e7, then one 7-tick level → L14 = 2.59e7. Scores 0.79–0.98.
- Grey screenshots: a reliable preview without Downloads is `peekbig()` — draw `_ocv` to a 360-px canvas, return its dataURL padded to ~110k chars in a standalone `javascript_tool` call (no screenshot in the same batch). The oversize result is saved to a tool-results .txt file instead of entering context; decode the base64 locally and Read it. (A batch that also contains a screenshot gets truncated inline instead — expensive.) Screenshots of the Earth UI did work right after opening the View menu.
- Clean basemap: View menu (~(130,11) in the 800×1422 frame) → Basemap settings → Clean radio (~(212,558)) → X.
- No official Street View at Bhangarh; the blue dots are photo spheres. Clicking one inside the palace (~(396,596) at 900d) opened a sphere looking north over ruined walls and hills, no people. `sv_crop_x 0 / w 1080`.
- Night prompt with "a tall dark shadowy silhouette standing motionless in a dark stone archway" gave two hooded figures in archways 4.2–5.4 s. The scare covers the last 0.95 s of the second piece, so end the piece ~0.4 s after the figure is fully in view: night = skA 0–8.04 + skA 3.6–5.4. Final 30.9 s, -14.3 LUFS, 43.4 MB.
- Instagram web was already on @earthmaplivesatellite.

## Gotchas learned (2026-11-22 run)
- Credits were 64 again (< 130) → Earth Map only, night ×1 (24); 40 left after. Bluetooth skipped.
- Centralia: `navigate @40.8043,-76.3404,450a,450d,35y,0h,0t,0r` (ground ≈ 446 m, so `levels_d[0]=454`). 13 ticks/level → L14 = 2.31e7, scores 0.83–0.96. Clean basemap was already set. Pin on the Locust Ave / Park St crossing (`target_px [290,990]`).
- Street View without the pegman: View menu (~(130,11)) → **Show Street View** (~(180,120)) draws the blue lines; preview them with `peekbig`, then click a line. Locust Ave pano faces north up the empty road; the canvas-drawn "Locust Ave" label sits at y ≈ 1230+ in the 1080×1920 frame, so `sv_crop_x 215 / w 650` (crop height 1155) clears it.
- l2 avoids digits ("for over sixty years"); the year went in `pin_sub`. l3 "By day, it's just an empty ghost town."
- Night prompt with "a tall dark shadowy silhouette standing motionless far down the road in the smoke" gave the figure 6.0–8.0 s (fully in view ~6.4); night = skA 0–8.04 + skA 5.0–6.9. Final 31.0 s, -14.2 LUFS, 43.6 MB. Config saved as `tools/horror/config_centralia_2026-11-22.json`.
- Flow credit balance: click the `PRO` chip (top right) and read "NN Google Flow credits" from the panel text.
- Instagram /reel/ links redirect to the /reels/ feed; the comment icon opens a small panel with "Add a comment…" (a contenteditable DIV, not a TEXTAREA). Verify on /p/<shortcode>/ after posting.

## Gotchas learned (2026-11-23 run)
- Credits were 64 again (< 130) → Earth Map only, night ×1 (24); 40 left after. Bluetooth skipped.
- Fast way to get a place's lat/lon without the shadow-DOM search box: `preview_start https://earth.google.com/web/search/<query>` (e.g. `Proctor's+Ledge+Memorial,+Salem,+MA`), wait ~20 s, read `location.href` → `@42.5176374,-70.9090035,4.8a,...`. Then `navigate @lat,lon,5a,450d,35y,0h,0t,0r`. Ground ≈ 5 m, so `levels_d[0]=450`. 13 ticks/level → L14 = 2.29e7 (15 levels). Clean basemap was already set.
- The flow-tile download came through as a `.tmp` (4.5 MB) next to the mosaic `.tmp` (11.4 MB); the SV JPEG stayed a `.tmp` too (not renamed after 12 s), so a second Downloads listing was needed.
- Street View: View menu → Show Street View drew the line on Pope St; a click opened "8 Pope St" (Jul 2025) facing north up an ordinary street (parked cars, plates blurred). Turning left faced a private house close-up with its number — avoided. `sv_crop_x 165 / w 740` clears the canvas "Pope St" label and arrows.
- `display: {"three":"3"}` also rewrites "three hundred" → "3 hundred"; avoid "three" anywhere except "three a.m." (used "Centuries ago, …" for l2, year in `pin_sub`).
- Night prompt with "a circle of small candles burning on the grass, crows on a wooden fence, and a tall dark shadowy silhouette standing motionless under the bare trees" passed; figure in view 3.0–5.5 s. night = skA 0–8.04 + skA 3.0–4.9. Final 31.0 s, -14.3 LUFS, 44.3 MB. Config saved as `tools/horror/config_salem_2026-11-23.json`.
- Instagram web was already on @earthmaplivesatellite; the /p/ page comment box was a TEXTAREA this time.

## Gotchas learned (2026-11-24 run)
- Credits were 64 again (< 130) → Earth Map only, night ×1 (24); 40 left after. Bluetooth skipped.
- Flow settings chip already read "Video · 720p · 8s · 9:16 x1" with Omni 1.2 Flash; typed the prompt via the `What do you want to create?` textbox ref and clicked the `arrow_forward` ref. Started generation first, then did Earth while it rendered (done in < 5 min).
- `earth_capture.js` can be injected after a `navigate` with `eval(await (await fetch('https://raw.githubusercontent.com/growlimomiraj/growlimo-videos/main/tools/horror/earth_capture.js')).text())` (fetch is allowed from the Earth page).
- Highgate: search URL gave `@51.5669188,-0.1467755,94.9a`; `navigate @…,95a,450d,35y,0h,0t,0r` (ground snapped to ~99 m → `levels_d[0]=446`). 13 ticks/level → L14 = 2.28e7 (15 levels), scores 0.70–0.95. Clean basemap was already set. `target_px [540,960]` (West Cemetery entrance courtyard on Swain's Lane).
- Street View: navigate `600d`, View → Show Street View, click the Swain's Lane line by the gate → "83 Swain's Ln" (Sep 2024), facing north up the lane past the cemetery gate pier, no people. `sv_crop_x 175 / w 731` (crop height 1299) clears the arrows (they start at y≈1350).
- Night prompt with "Victorian cemetery avenue lined with ivy-covered stone tombs and a tall Egyptian-style stone gateway, and a tall dark shadowy silhouette standing motionless at the far end of the path" passed; the figure is in the gateway at 0–1.5 s and again 6.75–8.0 s (the 360° turn comes back to it). Skipped the spoiler start: night = skA 1.8–8.04 + skA 6.5–8.04. Final 28.8 s, -14.0 LUFS, 42.3 MB. Config saved as `tools/horror/config_highgate_2026-11-24.json`.
- l2 "In the nineteen seventies, crowds hunted a vampire here." (no digits); year in `pin_sub`.
- Instagram web was already on @earthmaplivesatellite; /p/ comment box was a TEXTAREA.

## Gotchas learned (2026-11-25 run)
- Credits were 64 again (< 130) → Earth Map only, night ×1 (24); 40 left after. Bluetooth skipped.
- **Sedlec was the last entry in `places.json`** — add new places before the next Earth Map run.
- Labels sneaked into the capture even though Basemap settings showed **Clean** selected (the first stack had "Kostnice Sedlec", house numbers and POI dots; browser screenshots did NOT show them). Fix: View → Basemap settings → click Exploration, then Clean again, close, then snap. Always `peekbig()` L0 before scrolling the stack.
- `preview_start` with an Earth URL re-used the existing Earth tab (navigated it) instead of opening a new one.
- Show Street View via View menu / Ctrl+Shift+V did nothing this time (screenshots were grey, clicks blind). The pegman (bottom bar, ~(600,1374) in the 800×1422 frame) worked: blue Trekker lines around the chapel; a click at (329,711) opened a cemetery pano. One 600 px drag right = heading 0→332; a 300 px drag back = 346, which hid a distant visitor. `sv_crop_x 300 / w 731`.
- Sedlec: search URL `@49.9617385,15.2881713,223.66a`; `navigate @…,224a,450d` → Earth reported `714.36a,9.96d` (camera 724, ground 224 → `levels_d[0]=500.2`). 13 ticks/level → L14 = 2.55e7 (15 levels), scores 0.77–0.95. `target_px [548,900]`.
- Pin label "📍 Sedlec Ossuary, Czech Republic" overflowed the right edge; keep `pin` ≤ ~27 chars ("📍 Sedlec Ossuary, Czechia").
- Night prompt with "small Gothic chapel courtyard … chandelier and garlands made of skulls and bones like a museum ossuary lit by candles, old gravestones … a tall dark shadowy silhouette standing motionless in the open chapel doorway" passed; figure in the doorway 3.5–6.5 s. night = skA 0–8.04 + skA 3.4–5.4. Final 31.1 s, -14.3 LUFS, 42.8 MB. Config saved as `tools/horror/config_sedlec_2026-11-25.json`.
- Instagram web was already on @earthmaplivesatellite (post page shows View insights / Boost reel); /p/ comment box was a TEXTAREA.

## Gotchas learned (2026-11-26 run)
- Credits were 64 again (< 130) → Earth Map only, night ×1 (24); 40 left after. Bluetooth skipped.
- `places.json` had run out; added 7 new places (island-of-dolls, hill-of-crosses, bodie, kolmanskop, hoia-baciu, craco, hellfire-club). The file is now pretty-printed JSON (`_note` + `places` list).
- Flow prompt box: the `find` textbox ref click didn't focus it; click the box by coordinate (~(330,551) in the 800×600 frame), confirm `document.activeElement` is the contenteditable DIV, then type.
- Earth `navigate` sometimes sits at `@0,0,0a,0d` with no `#earth-canvas` for 40+ s; a second `navigate` plus `tabs_select` and ~40 s wait loaded it.
- Island of the Dolls: search URL gave `@19.29038075,-99.09689245,2235.9a` (ground ≈ 2236 m, `levels_d[0]=450`). 13 ticks/level → L14 = 2.29e7 (15 levels), scores 0.83–0.97. `target_px [540,960]`. No Street View at the island; pegman at ~2200d showed a blue line on the canal road ~500 m south — clicking it opened a Sep 2014 photo sphere on a canal (trees, water lilies, no people). `sv_crop_x 175 / w 731`.
- The globe → L13 fade showed a visible darker rectangle (L13 exposure ≠ L14 near the limb). `zoom.py` now colour-matches each finer level to its parent with a low-frequency gain map (blurred parent/child ratio), applied fully until the level reaches screen scale and fading out by sc=1.6. Rectangle gone.
- Night prompt with "a tiny overgrown island in the dark still canals of Xochimilco, an old wooden shack and a wooden pier, hundreds of old weathered dolls tied to the tree branches and fences like Halloween props, and a tall dark shadowy silhouette standing motionless among the trees behind the shack" passed; the camera pole is visible at 0–0.8 s, figures in view 2.0–5.0 s. night = skA 1.0–8.04 + skA 3.2–5.1. Final 30.0 s, -14.3 LUFS, 42.0 MB. Config saved as `tools/horror/config_island-of-dolls_2026-11-26.json`.
- Instagram web was already on @earthmaplivesatellite; the `find "comment"` textbox ref focused the TEXTAREA.

## Gotchas learned (2026-11-27 run)
- Credits were 64 again (< 130) → Earth Map only, night ×1 (24); 40 left after. Bluetooth skipped.
- Earth `navigate` landed on the "Overview | Home | Plans…" splash with no `#earth-canvas` for ~60 s, twice; a screenshot of the tab seemed to wake it, then it loaded. Keep waiting (and screenshot) rather than re-navigating.
- Hill of Crosses: search URL gave `@56.0153357,23.4163579,106.1a`; `navigate @…,106a,450d` (camera 556 m, ground ~110 m → `levels_d[0]=446`). 13 ticks/level → L14 = 2.27e7 (15 levels). `target_px [630,960]`. Clean basemap was already set (toggled Exploration → Clean anyway; L0 peek clean).
- Pegman at 600d drew blue lines on the hill paths; a click at (533,707) in the 800×1422 frame opened a photo sphere among the crosses (no people, no canvas arrows) → `sv_crop_x 0 / w 1080`.
- Night prompt with "…crosses and rosaries… a narrow path between them, and a tall dark shadowy silhouette standing motionless far up the path among the crosses" passed; the figure is small on the path only at 0.8–2.6 s. Put the spoiler last: night = skA 2.6–8.04 + skA 0.4–2.4. Final 28.5 s, -14.0 LUFS, 39.4 MB. Config saved as `tools/horror/config_hill-of-crosses_2026-11-27.json`.
- Instagram web was on @bluetooth_auticonnect; switched with ☰ (~(28,523)) → Switch profiles → earthmaplivesatellite. /p/ comment box was a TEXTAREA.
