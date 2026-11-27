# JKS Interactive V3.0.6 — mobile and competition workflow

See [V3.0.6-VERIFICATION.md](V3.0.6-VERIFICATION.md) for changes, tests and deployment checklist.

**Upgrade:** replace the repository root with this archive's contents (not a nested folder). Keep the Worker name, EVENTS Durable Object binding and ADMIN_PASSWORD unchanged. Rehearse with a duplicate first and export a design backup. Existing competition scores remain in their Durable Object; presentation exports deliberately omit votes.

**Groups:** select a competition slide, then click Competition groups. Select the competition in the dialog. Existing competition groups initially inherit the legacy roster; first edit makes an independent copy. New competitions start with a copied roster. Each competition has a separate rating scale, duration, results and CSV export.

**Results:** add a Results slide and choose Competition to display in its Content properties, or select the source in Live control. Publish after all groups in that competition have finished. Two result slides can publish different competitions. Private scores are under Scores in Live control.

---

# JKS Interactive — V3.0.3 (candidate)

A Cloudflare Worker with Durable Object storage and a static browser application for dual-screen presentations, interactive slides and audience voting. The Worker/project name is still `interactive-presentation`. JKS accent: `#ff5521`.

## Upgrade safely

This is a substantial upgrade to V2.4. Read `RELEASE-CHECKLIST.md` before using it for a live event. All included Node test suites passed; a full real-browser/hardware run was blocked in the development environment. **Treat this as a release candidate until you rehearse on your own devices.**

- Keep the existing V2.4 Git commit and ZIP. Do not delete or recreate the production Durable Object. Code rollback after using new slide types or new state is not a guaranteed data rollback.
- Prefer testing first on a separate staging Worker (change `name` in a staging copy of `wrangler.jsonc` only). It will have separate storage. Configure its own `ADMIN_PASSWORD` secret, then test the checklist. Do not copy the secret into GitHub.
- For production, use the original `wrangler.jsonc` from this package unchanged. Replace repository contents (including `public/`, `worker.js`, `package.json`, `tests/`, and `tools/`), commit and deploy with the existing GitHub integration. The Worker name, `EVENTS` binding, `EventRoom` class and migration tag are unchanged. The existing session uses the same storage namespace and `main` room name. Existing presentations should load without resetting their designs or votes; simulated migration was tested.
- Refresh **all** editor, controller, TV and participant browsers with Ctrl+F5 after deployment. Do not operate a mixture of old and V3.0.3 clients.
- After loading the existing presentation, export a JSON design backup from the editor or library. This is a design backup (not a backup of live scores). Export the competition results separately as CSV when needed.

Cloudflare build command: `npm install` (or existing equivalent). Deploy command: `npx wrangler deploy`. Repository root: `/`. Keep `ADMIN_PASSWORD` configured as a Worker secret. No additional R2/D1 binding is required.

## New in V3.0.3: independent participant screens

Select a slide in the editor, choose **Phone · 9:16** (or **Both → Edit phone**), then open **Content → What should participants see?**. Choose Automatic, Waiting screen, Share join QR code, Custom information, or Games finished. Optional phone screen headline and message are independent of TV text and of the competition mobile title/question. Use **Configured phone screen** in the preview phase selector to view the idle screen on an interactive slide; choose the other phases to preview interaction states. Changes are saved by the existing save/autosave flow. The TV slide type and design are unchanged.

Automatic shows the join QR on a Join session slide, and otherwise uses the original waiting/interaction behavior. Explicit idle modes override non-active content; active countdowns and response collection always take precedence. Live control → participant preview → Follows TV 1/TV 2 chooses the idle phone source when TVs differ. Use **Finish games** in Live control to show the closing screen persistently, including for new arrivals. This does not change the TVs or votes. It is rejected if a round/activity is open. Use **Reopen games** to clear it; a deliberately started new round/activity also clears it. This is explicit rather than inferring the end from one competition, because other games may follow. A slide with Games finished mode still shows that screen when followed, even after the global end flag is cleared. The global closing screen uses the current phone background, with default closing copy unless the followed slide is set to Games finished.

See `V3.0.3-PHONE-SCREENS.md` for focused verification and acceptance steps. The existing restriction on saving during an active round remains unchanged in this update.

## Routes

| Route | Purpose |
|---|---|
| `/library` | Manage presentations, search, sort, duplicate, archive/restore, import/export, rehearsal copies |
| `/admin` | Edit original presentation (`main`) |
| `/control` | Live controller |
| `/tv/1`, `/tv/2` | Display outputs |
| `/join` | Participant interface |

For another presentation, append `?p=<presentation-id>` to its routes. The library provides correct links automatically. QR codes are generated locally from the session's actual join URL. The same link is used throughout an event.

## Workflow

1. Open Presentations. Edit JKS Christmas or create a new deck. Use Duplicate to reuse a design, Rehearse to create an isolated copy with empty vote history, or Archive to hide a presentation from the active library without deleting its session.
2. In the editor, use the fixed slide sidebar, TV/phone/Both views and right-side tabs. Drag slides to reorder. Drag the logo or text block on the canvas; double-click title/subtitle to edit. Use numeric inputs for exact positions. The Elements tab adds independent text/image layers on the TV, including layer order, lock, visibility, copy/paste and position/size. The phone has its own background, logo, typography and content position. Extra free-form mobile layers are not supported.
3. Add a slide from the type gallery. Configure content and, for an interactive type, its prompt/options/duration as applicable. QR position and size are editable. Open Presentation theme in the editor toolbar to configure shared TV and phone backgrounds, logos and their placement, title/body fonts, sizes and colors, voting colors, and transitions. New slides inherit theme fields. Existing slides keep their original design until you link an individual property group or explicitly opt in to link all existing slides. Changing a linked field on a slide detaches that field without affecting other slides. Use theme re-links its property group. Join slides retain their individual vertical text position to avoid QR overlap. Use the selected slide as a starting point if desired. Media library reuses uploaded images from the current presentation; WOFF2 fonts can be uploaded if you have permission to embed them.
4. Edits autosave after a short delay. Undo/Redo are local to the editing session, with limited history; explicit Save and JSON backup export remain available. On conflicting edits, the server rejects the stale save rather than overwriting another editor's work. Export the draft and reload. Local IndexedDB recovery is best-effort; do not rely on it as your only backup. Keyboard shortcuts: Ctrl/Cmd+S, Ctrl/Cmd+Z, Ctrl/Cmd+Shift+Z or Ctrl/Cmd+Y, Ctrl/Cmd+D, Delete (when not typing). Logo dragging retains its existing resize handle and numeric fields.
5. Use Present to open the setup dialog and display links. In Live control, set the timeline target to Both TVs, TV 1 or TV 2; click a thumbnail to send it live. Previous/Next affect the selected screen target; Both TVs moves them together using TV 1 as reference. Sync to TV 1 explicitly links both outputs. There are no old dropdowns or Apply buttons. The timeline, two previews, phone preview, notes and contextual controls share a fixed desktop workspace; only the panels scroll when required. Smaller displays use a scrolling responsive layout. The controller displays heartbeat-based connection estimates and the number of recently active browser IDs, not a verified headcount. The TV browser can toggle fullscreen with F. Blackout hides both TVs without stopping the round; Restore returns them to the live slide. Presenter notes are private to the authenticated controller.
6. For a competition slide, show it on a TV, then start the next group. Default duration is 60 seconds, default rating maximum 7. Countdown opens voting automatically; close manually by default or configure an automatic close. The controller can pause/resume, restart a running timer, cancel, skip a group or explicitly redo a completed group (deletes that group's votes only). Leaving an active round requires confirmation; the server checks that the round hasn't changed. If the competition stays visible on the other TV, the round continues. Otherwise leaving a countdown cancels it, leaving voting closes it and keeps received votes. Separate competition slides keep separate vote ledgers and share the presentation's group names/order. Only one competition/activity can accept responses at a time. The public leaderboard stays hidden until you reveal or publish it. A Results slide displays the last explicitly published competition scores. Export the currently selected competition's scores using CSV. The controller sound button enables a short local timer-expiry tone after user interaction.
7. Poll, Rating, Word cloud, Q&A: display the slide, open responses, close responses and reveal results. Each browser ID can submit once per activity; reset to repeat with fresh responses. Q&A results are unmoderated; review privately before revealing. Word cloud aggregates case-insensitive exact responses, not semantic variants. Standalone countdown has no voting. Audience responses are browser-ID based and do not verify the identity of guests.
8. Linked video (experimental): enter a direct HTTPS MP4/WebM URL you have permission to display. It is played muted, full-screen on the TVs, using a shared timestamp and periodic drift correction. Browser support, network buffering, autoplay and exact synchronisation are not guaranteed. Test on the actual displays. A Restart video control resets its shared start. Instant/fade/slide entry transitions are available.

## Stream Deck (experimental, Windows)

The optional `tools/stream-deck.ps1` script calls the same authenticated control API. Copy the script to a local folder, then run in Windows PowerShell:

```powershell
powershell.exe -NoProfile -File "C:\JKS\stream-deck.ps1" -Configure
```

Enter your actual HTTPS `/control` link (including `?p=` for a non-main deck) and administrator password. It stores the credentials encrypted by Windows DPAPI for the current Windows user in `%LOCALAPPDATA%\JKS-Interactive\stream-deck.xml`. Keep that file private. Make Windows shortcuts that invoke:

```powershell
powershell.exe -NoProfile -File "C:\JKS\stream-deck.ps1" -Action Next
```

Actions: `Next`, `Previous`, `Blackout`, `Restore`, `Start`, `Close`, `Pause`, `Resume`. Bind the shortcuts with a Stream Deck Open/launcher action. The script refuses next/previous while an activity is active; use the browser for confirmation and overrides. PowerShell and Stream Deck hardware were not available for testing here. Follow your organisation's script execution policies; don't disable security policies just to run this launcher.

## Storage, limits and security

The original compressed inline image storage model is retained to avoid a disruptive storage migration. Per-presentation edit payload limit: 12,000,000 JSON characters (roughly 12 MB for ASCII, including base64 assets and fonts). Source image upload limit: 50 MB, optimised before saving. TV background up to 1920×1080, phone background up to 1080×1920; logos use smaller targets. Up to 100 slides, 100 groups, 30 additional TV layers per slide, 8 uploaded WOFF2 fonts (1 MB source each). Fonts are included in the presentation storage limit. Media reuse copies data, so it does not remove that overall limit. Large projects may need R2/object storage in a later migration. No sensitive/confidential information should be placed in public slides or questions; anyone with a session link can access its audience content. The admin secret is required for editing/control/library/private result APIs. Guest presence is approximate, and one-vote-per-browser is not identity verification.

The server sends lightweight WebSocket invalidations and clients fetch updates. Polling remains a fallback. Vote-only changes do not cause public displays to refetch large images; the controller still receives private vote counts through polling. These changes were tested using simulated storage, not a Cloudflare production load test.

## Local verification

Node 22 was used in development. `npm test` runs syntax checks and six Node suites (original library/navigation, upgrade, activities, migration/80 simulated votes, static rendering). No Wrangler install is needed for those tests. For Cloudflare local development, install dependencies and use `npm run dev`; configure `ADMIN_PASSWORD` in a local `.dev.vars` file that is not committed. For the optional actual-browser test, install Playwright Python (`pip install playwright`, then `python -m playwright install chromium`) and run `python tests/browser.py`. This launches a disposable in-memory local server; it does not touch your real deployment. The test was attempted here but browser navigation was blocked by the environment. The supplied test is a starting smoke test, not a claim of full UI coverage. The local server is deliberately not a real Durable Object or WebSocket emulator.

See `RELEASE-CHECKLIST.md` for the completed checks, partial implementations and physical-device test plan. Keep the old deployment available until the candidate passes that rehearsal.


## 3.0.1 participant update
See [PARTICIPANT-UPDATE.md](PARTICIPANT-UPDATE.md) for the changes, verification and live rehearsal checklist. This patch changes the audience frontend without changing the Worker or data format.

## V3.0.7
Competition rating endpoints are numbered. During a running or paused countdown, Live control offers **Open voting now**, with a group-specific confirmation. See V3.0.7-CHANGES.md.

## V3.0.9 – Text effects

See [V3.0.9-TEXT-EFFECTS.md](V3.0.9-TEXT-EFFECTS.md) for controls and verification. Run `python tests/text-effects-dom.py` for the focused Chromium tests (requires Playwright and Chromium).
