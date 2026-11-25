# Interactive Presentation — consolidated update
A responsive, single-event presentation and audience voting application, built for Cloudflare Workers with static assets and a SQLite-backed Durable Object. No separate server or D1 database required.

## Deploy from GitHub
1. Create a private GitHub repository and upload the **contents** of this folder (wrangler.jsonc must be at the repository root).
2. In Cloudflare, open Workers & Pages, create a Worker using the Git repository integration, and select the repository. This is a **Worker**, not a static Pages project.
3. Use `npm install` as the build command if requested, and `npx wrangler deploy` as the deploy command. Root directory: repository root. The Durable Object binding and migration are declared in wrangler.jsonc.
4. In the deployed Worker's Settings > Variables and Secrets, add a secret named `ADMIN_PASSWORD` with a long unique password. Alternatively run `npx wrangler secret put ADMIN_PASSWORD` locally. Never commit the password.
5. Open the Worker URL or add a custom domain in Settings > Domains & Routes. Visit /admin and sign in.

## Routes
- `/admin`: edit slides, upload artwork and logos, adjust colours, title size and alignment; edit group names; save.
- `/control`: choose a slide for each TV, apply together, sync both to the first selection, start/reset a 60-second timer with automatic voting, open/close votes and reveal rankings.
- `/tv/1`, `/tv/2`: fullscreen using browser F11. Keep each URL open on its own TV browser or connected computer.
- `/join`: mobile voting; generate a QR code for the final HTTPS URL using your preferred QR generator.

## Event rehearsal
1. Save slides in /admin. Open both TV URLs and the controller in separate browsers/tabs.
2. Choose slide 1 for TV 1 and slide 2 for TV 2; click Apply independent slides. Select slide 3 for TV 1 then click Sync both to TV 1 selection.
3. Select a group, start presentation and verify voting opens automatically after 60 seconds. Test from two independent phones. Close voting. Repeat for each group, then reveal results.
4. Check reconnection by refreshing both TVs and switching a phone between Wi-Fi and cellular. Test from the actual venue. Reset votes before the real event.

## Local development
Node 20+; run `npm install`, create a local `.dev.vars` file containing `ADMIN_PASSWORD=your-local-password`, then `npm run dev`. Do not commit `.dev.vars`. `npm run check` checks JS syntax.

## Scope and limitations
- Single reusable event, not a multi-event dashboard. Slide editing uses title/subtitle fields and fixed logo positioning, not arbitrary drag-and-drop objects. Import a complete 1920x1080 design as background and leave title/subtitle blank for exact designs.
- Images stored in event state: source images up to 50 MB are automatically optimised in the browser; ~12 MB combined JSON limit remains. State broadcasts include slide images, so keep assets small and rehearse on venue Wi-Fi.
- Voting is anonymous and limited to one vote per browser identifier per group. Clearing site data or switching browsers can bypass this; no identity verification or own-group exclusion.
- The timer automatically opens voting; the administrator closes voting manually. Results are hidden on public screens until manually revealed. TV transitions use a shared timestamp with approximate client clock offset; network and device latency can cause small differences.
- Public routes expose presentation content and are intended for nonconfidential event slides. Admin edits/control require a password. For stronger security, use additional access controls and rate limiting before broadly public deployment.
- JavaScript syntax checked; real Cloudflare deployment and actual TVs require rehearsal.

## Version 1.2 — slide-specific competition
In Editor, select a slide and set Properties > Slide type to Standard slide or 60-second competition / voting, then save. Existing slides with “60 Sekunden” in their titles are initially recognised as competition slides; other existing slides default to Standard. In Live control, apply the desired slides to the TVs, choose the displayed competition slide and group, and start the presentation. Voting opens automatically after 60 seconds. Only TVs displaying the selected competition slide show its timer/voting/results overlay. End competition / return to slide clears the overlay immediately. Navigating both TVs away from that competition slide closes voting and cancels the timer automatically; if one TV remains on it, the competition stays active for that TV. Votes remain stored until explicitly reset. All competition slides share the existing event-wide groups and results. Slide selections still require Apply/Sync. Syntax and simulated backend transitions tested; physical TVs and live Cloudflare deployment not tested.

## V1.3 participant design
Each slide supports separate mobile background, logo, title, message, voting question and text colour. Preview waiting, countdown, voting, submitted and results in the editor without casting votes. Save presentation to publish. The participant view follows the active competition slide, otherwise TV 1. Portrait uploads are resized to fit 1080 × 1920 and compressed to 250 KB where necessary; the existing 12 MB presentation limit remains. No storage migration or new Cloudflare bindings.

## V1.4 — Join QR slide
Add a slide, choose QR code / Join session, set title and subtitle, and save. The QR encodes the current website origin plus /join, and appears in TV and editor previews. Use the controller to show it on either or both TVs. No external QR service or new Cloudflare binding is needed. Existing slides are unchanged.

## V1.5
Slide types now immediately refresh the editor, show type-specific guidance, and preview competition stages on TV and phone. Preview only: start the real timer in Live control after saving.

## V1.6 – Layout and scoring
Per-slide TV text block position, width, alignment, font and subtitle size; independent TV/mobile logo width and X/Y position; mobile font, title/body size, alignment and vertical content position. Numeric voting is now 1–7, validated on the Worker, with averages and bars scaled to seven. Existing votes retain their numeric values: reset test votes before your real event. QR and timer positions remain fixed. Fonts are system fonts (availability varies by device). Save changes before presenting.

## V1.7 workspace
The editor now has independent slide navigation and property panes, a fitted TV/phone/both preview, content/appearance/typography/logo tabs, and a top-toolbar competition groups dialog. The backend and storage schema are unchanged from V1.6. Save presentation to persist edits. Desktop workspace recommended.

## V1.8 — Guided competition

Groups run in configured order. Display a competition slide, confirm Start for the next group, then wait for automatic voting. Confirm Close voting to complete the group. The next group is prepared but its timer does not start automatically. Navigation and editing are locked during active rounds. Restart or cancel is available only during countdown, with confirmation. Reveal results after all groups finish. Reset all votes is in Competition tools and clears progress. Existing votes are preserved; older completed rounds are inferred from saved votes (except the active countdown/voting round). Reset test votes before the real event. Refresh every connected browser after deployment because voting now includes the competition reset epoch.

Backend state-machine tests used a simulated Durable Object storage and clock expiry; live browser and Cloudflare deployment are not verified. The group sequence is shared across competition slides.

## V1.9 — Direct editing
Drag a slide thumbnail above or below another to reorder it. The selected slide stays selected. Drag the logo on the TV or phone canvas; use its bottom-right handle to resize, or arrow keys to nudge its position. Save presentation to persist changes. Existing logo coordinates and slide IDs are reused; live screen assignments are preserved by ID when saving. Desktop mouse drag is supported for slide ordering; existing up/down buttons remain available.

## V2.0
Editable numeric typography and logo values, synchronized with existing sliders and direct logo manipulation. Numeric values commit on Enter or change; existing storage unchanged.

### V2.1 — Slide navigation
The editor restores the slide rail scroll position after rendering and scrolls only as needed to keep the selected thumbnail visible, including after slide reordering. No backend or storage changes.

## V2.2 — JKS Interactive
- New presentation library at `/library`. Existing presentation remains in the original `main` Durable Object and retains its original URLs. No data migration or new bindings required.
- New presentations are created in independent Durable Objects. Their editor, controller, display links and QR join URLs include `?p=<presentation-id>`. Open the links from the selected deck's editor/controller, not from a different deck. Each deck has independent slides, groups, timers and votes.
- Use the Light/Dark button in the application header. Preference is saved locally in the browser. Presentation artwork is unchanged.
- Existing manual save, slide drag ordering, logo dragging, numeric layout inputs, mobile preview and guided competition remain available.
- Presentations can be renamed via the editor's existing title field and Save. Delete/duplicate whole presentations and authenticated audience access are not implemented. Existing audience URLs remain publicly accessible to anyone with the link.
- Run `npm run check` and `node tests/library.mjs` for syntax and simulated storage checks. Physical browser and Cloudflare tests remain necessary.
