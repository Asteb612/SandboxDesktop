# ADR-0014 — Native client: Chromium engine (CEF) + local Wayland compositor

- Status: Accepted
- Date: 2026-06-18
- Supersedes: [ADR-0001](0001-ui-is-a-pure-web-app.md) (pure web app, no embedded browser)
- Affects: [ADR-0008](0008-stream-only-application-content.md) (transport)

## Context

ADR-0001 made the UI a **pure web app served to any browser**, with apps streamed as WebRTC video. Two
things changed that:

1. **"Web app" was clarified to mean a native client** that embeds the **Chromium engine** to render the
   web UI, plus a local **Wayland** compositor and supporting tools — not a page in someone's browser.
   This is the project's original direction (it began as a CEF project).
2. We want to **stream the app's content, not always pixels** (cheaper bandwidth). That requires
   forwarding the app's **Wayland protocol + buffers** (waypipe-style) to a **Wayland compositor on the
   client** — which a browser cannot be.

## Decision

The client is a **native application** that:

- embeds the **Chromium engine via CEF** to render the **Shell UI** (Vue 3 + Pinia) — matching the
  project's origin and keeping the UI in web technology;
- runs a **local, nested Wayland compositor** (wlroots/Smithay-class, in the spirit of ChromeOS
  *Sommelier*) that composites both the CEF shell surface and the remote app surfaces, sharing GPU buffers
  **zero-copy via `linux-dmabuf`**; the shell defines layout, the compositor places app surfaces;
- runs a **waypipe client** (primary transport) and a **WebRTC decoder** (fallback), plus client-side
  input/clipboard/audio tools.

There is **no plain-browser client.** The native client is the only client.

## Alternatives considered

- **Pure PWA in any browser (ADR-0001):** maximal reach, zero install, but a browser cannot host a Wayland
  compositor, so it forces pixel-streaming for everything and forfeits the forwarding bandwidth win.
  Superseded.
- **Electron (Chromium + Node):** very mature Wayland/Ozone support and a large ecosystem, but heavier and
  bundles Node we do not need (the UI talks to a Go GraphQL backend). CEF chosen for a leaner embed that
  matches the project's history; Electron remains a viable fallback if CEF-on-Wayland blocks the PoC.
- **Tauri / system WebView:** lighter, but not guaranteed Chromium and weaker for embedding a custom
  compositor. Rejected ("use the Chromium engine").

## Consequences

- **Gains:** the forwarding transport becomes possible; local compositing is GPU-efficient (dmabuf);
  tighter OS integration (input, clipboard, audio, multi-window).
- **Costs:** loses "any device, no install" reach — the client must be installed and **maintained per
  platform**. **Risk:** CEF's Wayland/Ozone support is progressing but newer than Electron's; the P2 PoC
  must de-risk CEF-as-a-Wayland-client early (Electron is the fallback).
- The backend, GraphQL contract, plugin model, and customization model are unchanged; only the **client**
  and **transport** change.

## References

- CEF + Wayland progress: <https://www.phoronix.com/news/Chromium-CEF-Wayland-Progress>
- ChromeOS Sommelier (nested compositor, dmabuf): <https://chromium.googlesource.com/chromiumos/platform2/+/HEAD/vm_tools/sommelier/README.md>
- waypipe: <https://gitlab.freedesktop.org/mstoeckl/waypipe>
