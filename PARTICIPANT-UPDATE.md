# JKS Interactive 3.0.1 — Participant experience

## Source audit
3.0 had an audience renderer, automatic reconnect/polling, local voting receipts and backend duplicate-vote rejection. The visual layout remained largely the previous version. The status was based on a presence heartbeat, not a successful presentation-state refresh. Submitting a competition vote did not lock its button while the request was outstanding. The live preview used a separate phase-selection expression.

## Changes
- Shared branded audience shell for the editor preview, operator preview and actual `/join` route. Existing per-slide mobile artwork, logo position, title/message, fonts and colour remain in use.
- Waiting, countdown (live progress, group, pause state), 1–7 voting (or configured scale), server-acknowledged confirmation, next-group waiting and results screens. A loading screen, connection footer and retry control are present independently of the phase.
- Connection state reflects successful state fetches, not presence heartbeats; offline status, timed requests (where supported), automatic polling and WebSocket reconnect remain active. Inputs are disabled while reconnecting and while a submission is pending. A failed submission does not show a success confirmation. The existing server-side duplicate checks remain unchanged; identity remains browser-based.
- Activity controls share the shell and reject stale activity tokens. The live phone preview uses the same current-slide selector as participants. Preview votes are not sent.
- Asset version updated to 3.0.1. No Worker, storage or migration changes.

## Verification
`npm test`: all seven suites passed, including new `tests/participant.mjs`, which executes the participant rendering and click handlers with VM DOM stubs. It covers all competition phases, mobile content, duplicate in-flight clicks, stale round rejection, receipt persistence in local storage, failed submission, offline/recovery and activity scoping. Existing backend tests still cover server-side validation and concurrent requests. `tests/participant-browser.py` was attempted, but Chromium returned `net::ERR_BLOCKED_BY_ADMINISTRATOR` when navigating to the intercepted test URL. It is included for running on a machine without that restriction; browser interaction, visual layout, physical devices and actual Cloudflare deployment have not been verified.

## Deploy and check
Replace `public/app.js` and `public/index.html` together, or use the complete ZIP. Deploy to staging first, then refresh open tabs. On a rehearsal copy, open the editor Phone view and compare it against the actual join URL. Start a round, wait for voting, submit a rating, refresh during voting to check the receipt, switch off internet and restore it, close the round, and move to a standard slide. No existing live data should be reset to install this frontend update. Existing V3.0 release limitations still apply.
