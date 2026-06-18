# SandboxDesktop

**The browser holds the full user interface. Programs run as Wayland micro-containers — local or remote — streamed into a web UI.**

SandboxDesktop is a personal, self-hosted **application-streaming workspace**. The entire UI is a
website (a Vue.js PWA you open in any browser). The programs you run never touch your local display
server — each one runs inside its own **Wayland** micro-container, on your machine or on a remote
host, and is streamed back into the web UI over WebRTC.

It is **not** a window manager and it does not embed a browser. It is closest in spirit to
[Selkies/Webtop](https://www.linuxserver.io/blog/webtop-4-0-wayland-is-here-engage-the-reality-engine)
(open, Wayland, WebRTC) and to [Shadow](https://shadow.tech) (PC streaming to any browser) — but
unlike either, every program is its **own per-application sandbox**, arranged inside a Vue workspace.

## Architecture at a glance

| Layer | Technology | Role |
|-------|-----------|------|
| **UI** | Vue 3 + Pinia (PWA) | The full interface — launches apps, arranges their streams, plugin UIs. Runs in any browser. |
| **Core** | Go | Control plane: WebSocket event API, container lifecycle, stream brokering, host abstraction. |
| **Hosts** | Podman/Docker (local) · SSH/Kubernetes (remote) | Interchangeable backends behind one interface. |
| **App container** | Headless **Wayland** compositor (Selkies/Smithay or sway) | One program per sandboxed container, streamed via WebRTC. |
| **Plugins** | Python sidecars | Extend the core with system access; register via capability tokens. |

## Why these choices

This project deliberately re-founded its stack. The original pitch (React/Redux + Python/Flask/REST +
embedded CEF Chromium, on X11) was challenged technology by technology. The reasoning — and the
investigation into **Wayland over X11** and a comparison with **Shadow** — lives in the docs:

- **[docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)** — the full design, diagrams, technology challenge, and
  Wayland investigation.
- **[docs/adr/](docs/adr/)** — the architecture decision records:
  - [0001 — The UI is a pure web app](docs/adr/0001-ui-is-a-pure-web-app.md)
  - [0002 — Wayland only, no X11](docs/adr/0002-wayland-only-no-x11.md)
  - [0003 — Go core over Python/Flask](docs/adr/0003-go-core-over-python-flask.md)
  - [0004 — Vue + Pinia over React/Redux](docs/adr/0004-vue-pinia-over-react-redux.md)
  - [0005 — One program per micro-container](docs/adr/0005-one-program-per-micro-container.md)
  - [0006 — Local and remote hosts are interchangeable](docs/adr/0006-local-and-remote-hosts-interchangeable.md)

## Status

Pre-implementation. This repository currently holds the **architecture and decision records** only.
Roadmap: (P1) docs · (P2) PoC of one Wayland app streamed to a page · (P3) Go core + Vue workspace ·
(P4) Python plugin SDK.
