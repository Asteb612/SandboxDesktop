# SandboxDesktop — Tooling: build on, don't reinvent

> Concrete, existing projects to reuse for each layer, so the project assembles proven components instead
> of rebuilding them. **Reuse** = adopt as a dependency/base; **Reference** = study/borrow the approach;
> **Build** = the genuinely novel glue we must write. Pairs with [ARCHITECTURE.md](ARCHITECTURE.md) and
> [SECURITY.md](SECURITY.md).

## Native client (ADR-0014)

| Tool | Role | Use |
|------|------|-----|
| **CEF** (Chromium Embedded Framework) | Embed the Chromium engine to render the Vue UI | **Reuse** (primary; powers Steam/OBS/Spotify) |
| **Electron** | Chromium + Node shell with mature Wayland/Ozone | **Reference / fallback** if CEF-on-Wayland blocks P2 |
| **Smithay** (Rust) / **wlroots** (C) | Build the client's **nested Wayland compositor** | **Reuse** (Smithay preferred — chosen by XFCE; pairs with Rust/Pion) |
| **ChromeOS Sommelier** | Nested compositor that composites external surfaces with a Chromium UI via dmabuf | **Reference** (the exact pattern we need) |
| **waypipe** | Forward a single app's Wayland protocol + buffers to the client (primary transport) | **Reuse** |
| **wayland-rs / wayland-protocols** | Wayland protocol bindings, `linux-dmabuf`, surface delegation | **Reuse** |

## Per-app container (ADR-0005, ADR-0008)

| Tool | Role | Use |
|------|------|-----|
| **Cage** / **Gabbia** | Single-app kiosk Wayland compositor — exactly "one program, one surface" | **Reuse** as the in-container compositor |
| **Selkies** (Smithay + GStreamer WebRTC) | Headless-Wayland-in-container → WebRTC | **Reuse / reference** for the WebRTC **fallback** path |
| **GStreamer** (`webrtcbin`, VAAPI) | Capture/encode the single surface; hardware encode | **Reuse** |
| **XWayland** | Legacy X11-only apps, confined to their own container (ADR-0002) | **Reuse** (only sanctioned X11 surface) |

## Backend / orchestrator (ADR-0003, ADR-0007)

| Tool | Role | Use |
|------|------|-----|
| **gqlgen** (Go) | Schema-first GraphQL: queries/mutations/subscriptions | **Reuse** |
| **Pion** (pure-Go WebRTC) | Negotiate/relay the WebRTC fallback from Go; integrates with GStreamer | **Reuse** |
| **coder/websocket** or **gorilla/websocket** | Subscriptions / signaling transport | **Reuse** |
| **Ory Kratos/Hydra**, **Keycloak**, **Zitadel**, **dex** | Identity + OIDC (don't roll your own auth) | **Reuse** (pick one) |

## Sandboxing & provisioning (ADR-0013)

| Tool | Role | Use |
|------|------|-----|
| **Sysbox** (Nestybox) | Rootless runc that runs system workloads with userns; strong default isolation, no host root | **Reuse** (default tier) |
| **Kata Containers** + **Firecracker** / Cloud Hypervisor | microVM isolation (~100–200 ms boot) for untrusted apps | **Reuse** (strong tier) |
| **gVisor** | User-space kernel sandbox | **Reuse** (alt strong tier) |
| **Google Agent Sandbox** (CNCF, K8s) | Declarative API for isolated sandbox pods (gVisor default + Kata) | **Reference** for the provisioning-API design |
| **Podman REST API** (rootless) | The local provisioning backend behind our narrow API (no raw socket) | **Reuse** |
| **netavark / Cilium / nftables** | Default-deny per-sandbox egress firewall | **Reuse** |

## Plugins (ADR-0009, ADR-0010)

| Tool | Role | Use |
|------|------|-----|
| **Extism** | Plugin framework over WASM: PDK, host functions, runtime limiters/timers, host-controlled HTTP | **Reuse** (backend logic plugins) |
| **wazero** (pure-Go WASM runtime) | Zero-CGo WASM host inside the Go backend | **Reuse** (Extism can run on it) |
| **Wasmtime** | Industrial WASM runtime (fuel/epoch/memory limits) | **Reuse / alt** |
| **Vite Module Federation** (`@originjs/vite-plugin-federation`) | Runtime-load curated UI plugins | **Reuse** (frontend plugins) |
| **SES / Hardened JS** (Endo, **LavaMoat**) | Confine UI-plugin JS to granted capabilities (MetaMask Snaps model) | **Reuse** (see SECURITY + ADR-0016) |

## Frontend (ADR-0004, ADR-0011, ADR-0012)

| Tool | Role | Use |
|------|------|-----|
| **Vue 3 + Pinia + Vite** | Shell UI + state + build | **Reuse** |
| **Lit** | Web Components / Shadow DOM for the Component tier | **Reuse** |
| **Style Dictionary** | Build design tokens → CSS custom properties (Theme tier) | **Reuse** |
| **Gridstack.js** | Drag-drop dashboard layout (Interface edit mode) | **Reuse** |
| **@jsonforms/vue** or **FormKit** | Schema-driven prop editors for the registry | **Reuse** |

## Security infrastructure (SECURITY.md)

| Tool | Role | Use |
|------|------|-----|
| **Biscuit** (Eclipse) | Offline-attenuable, public-key capability tokens (the permission model) | **Reuse** (see ADR-0015) |
| **coturn** | Self-hosted TURN with time-limited credentials | **Reuse** |
| **Sigstore / cosign** | Sign + verify plugin and container artifacts | **Reuse** |
| **gqlgen complexity** + **query-cost-analysis** | GraphQL depth/cost limiting | **Reuse** |
| **SPIFFE/SPIRE** | Workload identity between backend ↔ provisioning ↔ sandboxes | **Reference / reuse** |

## What we still build (the novel glue)

- The **StreamBroker** logic that negotiates *forwarding vs WebRTC* per app and wires waypipe ↔ local
  compositor ↔ layout.
- The **layout-document ↔ compositor placement** binding (shell layout drives surface geometry).
- The **capability/permission model** end-to-end: manifest → user grant → Biscuit token → `ResourceManager`
  enforcement → Extism/provisioning host functions.
- The **three-tier customization** resolver and component registry.
- The **least-privilege provisioning API** contract over Sysbox/Kata/Podman.
