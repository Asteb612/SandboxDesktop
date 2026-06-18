# SandboxDesktop

**A native client renders the full UI with the Chromium engine and a local Wayland compositor. Programs run as Wayland micro-containers — local or remote — and their content is forwarded to the client.**

SandboxDesktop is a personal, self-hosted **application workspace**. The UI is built in web technology
(Vue 3) and rendered by an embedded **Chromium engine (CEF)** inside a **native client** — the project's
original CEF direction, now with a clear architecture. The client also runs a **local Wayland
compositor**, so each program's surface can be **forwarded (waypipe-style) and rendered locally** instead
of always streaming pixels. You sign in like any web app and talk to a **GraphQL** backend; that backend
is the only component with system access. Each program runs inside its own strongly-isolated **Wayland**
micro-container, on your machine or a remote host, and **only that program's content** is delivered.

Your interface is **yours**: each user gets a per-user, fully editable UI, customizable at three
overloadable levels — **Theme → Interface → Components** — and **plugins can change it**.

It is **not** a window manager. It draws on [waypipe](https://gitlab.freedesktop.org/mstoeckl/waypipe)
(single-app Wayland forwarding), ChromeOS [Sommelier](https://chromium.googlesource.com/chromiumos/platform2/+/HEAD/vm_tools/sommelier/README.md)
(compositing external surfaces with a Chromium UI), and [Selkies/Webtop](https://www.linuxserver.io/blog/webtop-4-0-wayland-is-here-engage-the-reality-engine)
(the WebRTC fallback) — but every program is its **own per-application sandbox**.

## Architecture at a glance

| Layer | Technology | Role |
|-------|-----------|------|
| **Client** | Native app: **CEF (Chromium)** + local **Wayland** compositor | Renders the Vue UI; composites forwarded app surfaces (zero-copy dmabuf); waypipe client + WebRTC fallback. No plain-browser client. |
| **UI** | Vue 3 + Pinia (in CEF) | Per-user, editable interface (Theme/Interface/Components); loads UI plugins. |
| **Backend** | Go + **GraphQL** (gqlgen) | Authenticated, privileged control plane: queries/mutations + subscriptions, internal authorization, lifecycle, transport brokering, host abstraction. |
| **Hosts** | Provisioning API → Podman/Docker (local) · SSH/Kubernetes (remote) | Interchangeable backends; backend holds **no raw container socket**. |
| **App container** | Headless **Wayland** compositor, **strong isolation by default** | One program per sandbox; surface **forwarded (waypipe)**, WebRTC pixel-streaming as fallback. |
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
- **[docs/SECURITY.md](docs/SECURITY.md)** — concrete mitigations for each threat (SES-hardened plugins,
  Biscuit capability tokens, strong-isolation provisioning, GraphQL hardening, coturn, signing).
- **[docs/TOOLING.md](docs/TOOLING.md)** — existing projects to build on per layer (reuse vs reference vs
  build), so the project assembles proven components instead of reinventing them.
- **[docs/adr/](docs/adr/)** — the architecture decision records:
  - [0001 — The UI is a pure web app](docs/adr/0001-ui-is-a-pure-web-app.md) *(superseded by 0014)*
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
  - [0013 — Strong isolation by default; broker the container socket](docs/adr/0013-strong-isolation-by-default.md)
  - [0014 — Native client: Chromium engine (CEF) + local Wayland compositor](docs/adr/0014-native-client-cef-local-wayland.md) *(supersedes 0001)*
  - [0015 — Capability tokens via Biscuit](docs/adr/0015-capability-tokens-biscuit.md)
  - [0016 — Harden frontend plugins with Hardened JavaScript (SES)](docs/adr/0016-harden-frontend-plugins-ses.md)

## Status

Pre-implementation. This repository currently holds the **architecture and decision records** only.
Roadmap: (P1) docs · (P2) PoC — native CEF client + local Wayland compositor forwarding one containerized
app (waypipe), WebRTC fallback · (P3) Go GraphQL backend + per-user Vue shell in CEF · (P4) plugin SDK
(WASM backend plugins + Module Federation UI plugins).
