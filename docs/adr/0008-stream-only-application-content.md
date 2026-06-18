# ADR-0008 — Stream only the application content

- Status: Accepted
- Date: 2026-06-18

## Context

Streaming a full remote desktop (wallpaper, panels, other windows) wastes bandwidth when the user only
cares about one program. The goal is to keep bandwidth low by sending **only the application's own
content**.

## Decision

Stream **only the program's single surface** — never a desktop or other windows:

- Each program already runs alone in its own headless Wayland compositor (ADR-0005), so "the desktop"
  *is* that one app; the encoder captures its **single toplevel surface**.
- Use **damage tracking** — the compositor reports changed regions, and only those are encoded and sent.
  An idle app costs ~no bandwidth; a partially-updating app sends only its delta.
- **Adaptive** codec (H.264 / H.265 / AV1) and bitrate, with a low-bandwidth mode.

## Alternatives considered

- **Full virtual-desktop capture (Xvfb/whole screen):** simplest, but streams chrome and idle pixels the
  user never asked for. Rejected on bandwidth.
- **waypipe-style Wayland protocol forwarding ("stream commands, not pixels"):** tempting, but it does
  not fit. Unlike X11, **Wayland has no drawing-command protocol** — clients render their own pixels into
  shared-memory/`dmabuf` **buffers** and hand the compositor a finished frame. So there are no high-level
  commands to replay client-side; waypipe forwards the protocol *plus the buffer contents* (compressed
  lz4/zstd, and **video-encoded** for large/changing surfaces — i.e. it ships pixels too). Crucially it
  requires a **real Wayland compositor on the client**, which a **browser cannot be** — it breaks the
  "the UI is a website" goal (ADR-0001). It can be cheaper than a video codec only for small, static
  GUI updates, and is worse for animation/video. Kept as conceptual prior art for a hypothetical *native*
  client; not the browser transport. (The only true "render on the client" path in a browser is an app
  that is *actually a web app* running locally — out of scope here.)
- **Per-window capture via XDG `ScreenCast` portal + PipeWire:** the general per-window path; with our
  one-app-per-compositor model, single-surface capture is the default rather than a special case.

## Consequences

- Minimal bandwidth: only changed regions of one surface, adaptively encoded.
- The model is uniform — every container exposes exactly one surface to stream.
- Multi-window apps (a program opening several toplevels) need a policy (compose into one surface, or
  expose each as its own pane) — flagged for the PoC (P2).

## References

- waypipe: <https://gitlab.freedesktop.org/mstoeckl/waypipe>
- XDG ScreenCast portal / PipeWire: <https://flatpak.github.io/xdg-desktop-portal/docs/doc-org.freedesktop.portal.ScreenCast.html>
