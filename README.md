# SandboxDesktop

**The browser holds the full user interface. Programs run as Wayland micro-containers — local or remote — streamed into a web UI.**

SandboxDesktop is a personal, self-hosted **application-streaming workspace**. The entire UI is a
website (a Vue.js PWA you open in any browser). You sign in like any web app and talk to a **GraphQL**
backend; that backend is the only component with system access. The programs you run never touch your
local display server — each one runs inside its own **Wayland** micro-container, on your machine or on a
remote host, and **only the application's own content** is streamed back into the web UI over WebRTC.

Your interface is **yours**: each user gets a per-user, fully editable UI, customizable at three
overloadable levels — **Theme → Interface → Components** — and **plugins can change it**.

It is **not** a window manager and it does not embed a browser. It is closest in spirit to
[Selkies/Webtop](https://www.linuxserver.io/blog/webtop-4-0-wayland-is-here-engage-the-reality-engine)
(open, Wayland, WebRTC) and to [Shadow](https://shadow.tech) (PC streaming to any browser) — but
unlike either, every program is its **own per-application sandbox**, arranged inside a Vue workspace.

## Architecture at a glance

| Layer | Technology | Role |
|-------|-----------|------|
| **UI** | Vue 3 + Pinia (PWA) | Per-user, editable interface (Theme/Interface/Components); renders app surfaces; loads UI plugins. Runs in any browser. |
| **Backend** | Go + **GraphQL** (gqlgen) | Authenticated, privileged control plane: queries/mutations + subscriptions, internal authorization, container lifecycle, stream brokering, host abstraction. |
| **Hosts** | Podman/Docker (local) · SSH/Kubernetes (remote) | Interchangeable backends behind one interface. |
| **App container** | Headless **Wayland** compositor (Selkies/Smithay or sway) | One program per sandboxed container; **only its surface** is streamed via WebRTC. |
| **Backend plugins** | Isolated dynamic modules (**WASM**/WASI via Wasmtime) | Loaded in isolation, zero ambient authority, **Android-style declared permissions**, brokered access. |
| **Frontend plugins** | Curated **Module Federation** | Contribute/override UI behind a stable contract (signed + SRI + CSP). |

## Why these choices

This project deliberately re-founded its stack. The original pitch (React/Redux + Python/Flask/REST +
embedded CEF Chromium, on X11) was challenged technology by technology. The reasoning — and the
investigation into **Wayland over X11** and a comparison with **Shadow** — lives in the docs:

- **[docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)** — the full design, diagrams, technology challenge, and
  Wayland investigation.
- **[docs/LIMITATIONS.md](docs/LIMITATIONS.md)** — a deliberately critical counterweight: usage limits,
  the threat model, and where the design is in tension with its own goals.
- **[docs/adr/](docs/adr/)** — the architecture decision records:
  - [0001 — The UI is a pure web app](docs/adr/0001-ui-is-a-pure-web-app.md)
  - [0002 — Wayland only, no X11](docs/adr/0002-wayland-only-no-x11.md)
  - [0003 — Go core over Python/Flask](docs/adr/0003-go-core-over-python-flask.md)
  - [0004 — Vue + Pinia over React/Redux](docs/adr/0004-vue-pinia-over-react-redux.md)
  - [0005 — One program per micro-container](docs/adr/0005-one-program-per-micro-container.md)
  - [0006 — Local and remote hosts are interchangeable](docs/adr/0006-local-and-remote-hosts-interchangeable.md)
  - [0007 — Authenticated GraphQL backend](docs/adr/0007-authenticated-graphql-backend.md)
  - [0008 — Stream only the application content](docs/adr/0008-stream-only-application-content.md)
  - [0009 — Backend plugins: isolated dynamic modules, Android-style permissions](docs/adr/0009-backend-plugin-security-capability-model.md)
  - [0010 — Frontend plugins via curated Module Federation](docs/adr/0010-frontend-plugins-module-federation.md)
  - [0011 — Three-level customization with WordPress-style overrides](docs/adr/0011-three-tier-customization-overrides.md)
  - [0012 — Per-user editable UI as data](docs/adr/0012-per-user-editable-ui-as-data.md)

## Status

Pre-implementation. This repository currently holds the **architecture and decision records** only.
Roadmap: (P1) docs · (P2) PoC of one Wayland app, single-surface stream to a page · (P3) Go GraphQL
backend + per-user Vue workspace · (P4) plugin SDK (WASM backend plugins + Module Federation UI plugins).
