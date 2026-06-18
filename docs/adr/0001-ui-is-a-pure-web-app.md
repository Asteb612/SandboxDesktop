# ADR-0001 — The UI is a pure web app (no embedded browser)

- Status: Accepted
- Date: 2026-06-18

## Context

The project goal is to "use the possibilities of the browser to hold the full user interface." The
first attempt embedded Chromium via **CEF** and shipped a desktop binary. CEF/Electron bundle a whole
Chromium (~80–150 MB installers, ~150–300 MB RAM) and tie the UI to a specific engine and a desktop
install.

## Decision

The UI is a **pure web application** — a Vue 3 PWA served over HTTP, opened in **any browser**. No
embedded browser engine (no CEF, no Electron, no Tauri/WebView wrapper).

## Alternatives considered

- **CEF / Electron (embedded Chromium):** heavy, engine-locked, requires a desktop install. Rejected —
  contradicts "the UI is a website."
- **Tauri (native OS WebView + Rust):** much lighter than CEF, but still a native window wrapper we do
  not need; the workspace is reachable from any device without installation if it is just a web app.
- **Pure web app (chosen):** lightest, device-agnostic, installable as a PWA, and the most literal
  reading of the goal.

## Consequences

- The workspace runs on any device with a modern browser; nothing to install.
- We rely on browser capabilities (WebRTC, WebCodecs, service workers) rather than native APIs.
- Any "desktop window" feel must be achieved within the page (PWA install, fullscreen) — acceptable.
