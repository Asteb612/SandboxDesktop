# ADR-0002 — Wayland only, no X11

- Status: Accepted
- Date: 2026-06-18

## Context

Programs run inside containers; their surfaces are forwarded/streamed to the client. The container needs
a display server. The original project targeted X11. The system runs **untrusted programs**, so the
display server's isolation properties are a security concern, not just a rendering detail. The question
of *reverting to X11* was explicitly re-evaluated (see below).

## Decision

Use **Wayland at the system level**, both inside app containers and as the client's local compositor
(ADR-0014). **No system-wide X11 and no shared XWayland.** The **only** sanctioned X11 surface is
**XWayland running inside a single app's own container** for a legacy X11-only program — because that app
is alone in its sandbox, X11's lack of isolation cannot be used to snoop anything else.

## Alternatives considered

- **Revert to X11 system-wide (re-evaluated 2026):** rejected on two grounds. **(1) Security:** any X11
  client can read all input and every other client's window contents — disqualifying for untrusted
  programs. **(2) Ecosystem:** X.Org is **maintenance-only** (since 2024); Fedora 43 and Ubuntu 25.10
  dropped X11 sessions; **GNOME 50** (Mar 2026) ships with zero X11 code; KDE Plasma 6 defaults to
  Wayland; **RHEL 10** removed the Xorg server keeping only XWayland; critical X.Org CVEs surfaced in
  20-year-old code in 2025. The one real draw — mature browser remote-display via **xpra** — still
  inherits X11's no-isolation model. Building new on X11 means building on a sunsetting base.
- **X11 (Xvfb + KasmVNC) per container:** isolates via the container, but pins us to a dying protocol and
  recreates the isolation Wayland gives for free. Rejected.
- **Shared/system XWayland:** reopens the cross-app X11 snooping hole. Rejected.
- **Wayland-only + per-container XWayland for legacy apps (chosen):** keeps the isolation model and rides
  the ecosystem trajectory, while still allowing legacy X11 apps in a confined way.

## Consequences

- **Security:** per-client surface isolation — apps cannot snoop each other's input/output.
- **Efficiency:** the native client's local Wayland compositor + waypipe forwarding (ADR-0014, ADR-0008)
  delivers "render on the client" bandwidth savings without X11.
- **Future-proof:** aligned with where the entire desktop-Linux ecosystem now is.
- **Cost:** legacy X11-only apps require a per-container XWayland shim; system-wide X11 features are out.

## References

- GNOME 50 drops X11: <https://www.theregister.com/software/2026/03/19/gnome-50-debuts-with-x11-axed-wayland-front-and-center/>
- RHEL 10 Wayland/Xorg plans (XWayland only): <https://www.redhat.com/en/blog/rhel-10-plans-wayland-and-xorg-server>
- xpra (X11 remote apps + HTML5, considered/rejected): <https://github.com/Xpra-org/xpra>
- Webtop 4.1, "X11 is dead / what is Selkies": <https://www.linuxserver.io/blog/webtop-4-1-x11-is-dead-and-what-is-selkies-anyway>
