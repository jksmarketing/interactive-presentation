# JKS Events — v1
A responsive, single-event presentation and audience voting application, built for Cloudflare Workers with static assets and a SQLite-backed Durable Object. No separate server or D1 database required.

## Deploy from GitHub
1. Create a private GitHub repository and upload the **contents** of this folder (wrangler.jsonc must be at the repository root).
2. In Cloudflare, open Workers & Pages, create a Worker using the Git repository integration, and select the repository. This is a **Worker**, not a static Pages project.
3. Use `npm install` as the build command if requested, and `npx wrangler deploy` as the deploy command. Root directory: repository root. The Durable Object binding and migration are declared in wrangler.jsonc.
4. In the deployed Worker's Settings > Variables and Secrets, add a secret named `ADMIN_PASSWORD` with a long unique password. Alternatively run `npx wrangler secret put ADMIN_PASSWORD` locally. Never commit the password.
5. Open the Worker URL or add a custom domain in Settings > Domains & Routes. Visit /admin and sign in.

## Routes
- `/admin`: edit slides, upload artwork and logos, adjust colours, title size and alignment; edit group names; save.
- `/control`: choose a slide for each TV, apply together, sync both to the first selection, start/reset a 60-second timer, open/close votes and reveal rankings.
- `/tv/1`, `/tv/2`: fullscreen using browser F11. Keep each URL open on its own TV browser or connected computer.
- `/join`: mobile voting; generate a QR code for the final HTTPS URL using your preferred QR generator.

## Event rehearsal
1. Save slides in /admin. Open both TV URLs and the controller in separate browsers/tabs.
2. Choose slide 1 for TV 1 and slide 2 for TV 2; click Apply independent slides. Select slide 3 for TV 1 then click Sync both to TV 1 selection.
3. Select a group, start timer, open voting manually after the presentation. Test from two independent phones. Close voting. Repeat for each group, then reveal results.
4. Check reconnection by refreshing both TVs and switching a phone between Wi-Fi and cellular. Test from the actual venue. Reset votes before the real event.

## Local development
Node 20+; run `npm install`, create a local `.dev.vars` file containing `ADMIN_PASSWORD=your-local-password`, then `npm run dev`. Do not commit `.dev.vars`. `npm run check` checks JS syntax.

## Scope and limitations
- Single reusable event, not a multi-event dashboard. Slide editing uses title/subtitle fields and fixed logo positioning, not arbitrary drag-and-drop objects. Import a complete 1920x1080 design as background and leave title/subtitle blank for exact designs.
- Images stored in event state: maximum 2 MB per uploaded image and ~12 MB combined JSON; compressed JPEG/WebP recommended. State broadcasts include slide images, so keep assets small and rehearse on venue Wi-Fi.
- Voting is anonymous and limited to one vote per browser identifier per group. Clearing site data or switching browsers can bypass this; no identity verification or own-group exclusion.
- The timer does not automatically open voting. Results are hidden on public screens until manually revealed. TV transitions use a shared timestamp with approximate client clock offset; network and device latency can cause small differences.
- Public routes expose presentation content and are intended for nonconfidential event slides. Admin edits/control require a password. For stronger security, use additional access controls and rate limiting before broadly public deployment.
- Syntax checked and backend smoke-tested with a mock storage runtime if indicated in delivery notes; real Cloudflare deployment and actual TVs require rehearsal.
