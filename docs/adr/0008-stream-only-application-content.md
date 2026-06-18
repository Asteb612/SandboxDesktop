# ADR-0008 — Stream only the application content

- Status: Accepted (transport updated by [ADR-0014](0014-native-client-cef-local-wayland.md))
- Date: 2026-06-18

## Context

Delivering a full remote desktop (wallpaper, panels, other windows) wastes bandwidth when the user only
cares about one program. The goal is to keep bandwidth low by delivering **only the application's own
content**. The native client (ADR-0014) runs a **local Wayland compositor**, which changes what is
possible: the app's Wayland protocol can be *forwarded* and rendered on the client, not only streamed as
pixels.

## Decision

Deliver **only the program's single surface** — never a desktop or other windows — via two transports:

- **Primary — Wayland forwarding (waypipe-style).** Forward the app's **Wayland protocol + buffers**
  (`dmabuf`, compressed; optional VAAPI video for large/changing surfaces) to the client's local
  compositor, which renders them (zero-copy via `linux-dmabuf`). Cheaper than continuous video for typical
  GUIs. **Note:** Wayland has *no drawing-command protocol* — clients render their own pixels into
  buffers — so this forwards *buffers*, not X11-style commands; it is still far lighter than full-desktop
  video for static UIs.
- **Fallback — WebRTC single-surface pixel-streaming.** Damage-tracked, adaptive H.264/H.265/AV1 with a
  low-bandwidth mode, for animation/video-heavy surfaces or paths where forwarding is unavailable.

Each program runs alone in its own headless Wayland compositor (ADR-0005), so "the desktop" *is* that one
app — one surface to forward or capture.

## Alternatives considered

- **Full virtual-desktop capture (whole screen):** simplest, but ships chrome and idle pixels. Rejected.
- **WebRTC pixels as the *only* transport (the pre-native-client design):** correct while the client was a
  browser (ADR-0001), but a browser cannot host a Wayland compositor. Now that the client is native
  (ADR-0014), forwarding is available and cheaper for most GUIs — so WebRTC becomes the *fallback*, not
  the only path.
- **Per-window capture via XDG `ScreenCast` portal + PipeWire:** a general per-window capture path; with
  one-app-per-compositor, single-surface capture is the default for the WebRTC fallback.

## Consequences

- Minimal bandwidth for typical GUIs (forward buffers/deltas); video only when it actually pays off.
- Two transports to build and a policy to pick between them (see ADR/roadmap); the StreamBroker negotiates.
- **waypipe caveat:** video-encoding per rotating buffer can flicker; hardware (VAAPI) encode is
  format/size sensitive — to validate in the PoC.
- Multi-window apps (several toplevels) need a policy (forward each as its own surface, or compose) —
  flagged for the PoC (P2).

## References

- waypipe: <https://gitlab.freedesktop.org/mstoeckl/waypipe>
- XDG ScreenCast portal / PipeWire: <https://flatpak.github.io/xdg-desktop-portal/docs/doc-org.freedesktop.portal.ScreenCast.html>
