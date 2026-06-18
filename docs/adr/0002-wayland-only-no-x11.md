# ADR-0002 — Wayland only, no X11

- Status: Accepted
- Date: 2026-06-18

## Context

Programs run inside containers and are streamed to the browser. The container needs a display server.
The original project targeted X11. The system is designed to run **untrusted user modules**, so the
display server's isolation properties are a security concern, not just a rendering detail.

## Decision

Use **Wayland exclusively** inside app containers. **No X11, and no XWayland fallback.** Legacy
X11-only applications are an explicit non-goal.

## Alternatives considered

- **X11 (e.g. Xvfb + KasmVNC):** any X11 client can read all input and all other clients' window
  contents — unacceptable for untrusted modules. Being retired in comparable projects (Webtop dropped
  it). Rejected.
- **Wayland + XWayland fallback:** would support legacy apps but reopens the X11 isolation hole and adds
  runtime weight. Rejected to keep the security model intact and the stack lean.
- **Wayland only (chosen).**

## Consequences

- **Security:** per-client surface isolation — apps cannot snoop each other's input/output.
- **Streaming:** Wayland damage tracking enables encoding only changed regions, pairing well with
  WebRTC/GStreamer for low-latency GPU frames (the Selkies model).
- **Maturity:** aligns with Selkies/Webtop 4.x (headless Wayland via Rust/Smithay → browser).
- **Cost:** X11-only legacy apps cannot run. Accepted as a deliberate non-goal.

## References

- Webtop 4.1, "X11 is dead / what is Selkies": <https://www.linuxserver.io/blog/webtop-4-1-x11-is-dead-and-what-is-selkies-anyway>
- Selkies: <https://github.com/selkies-project/selkies>
