# SandboxDesktop — Limitations & Threat Model

> A deliberately **critical** companion to [ARCHITECTURE.md](ARCHITECTURE.md). The architecture doc
> argues *for* the design; this one argues *against* it. Read both. Nothing here is a blocker by itself,
> but several items are in direct tension with the project's stated goals ("very secure plugins",
> per-app sandboxing), and a few are showstoppers for specific use cases.

## TL;DR

- The project is, honestly, a **remote-application system** — a native client (CEF + local Wayland
  compositor) presenting per-app sandboxes. It inherits remote-app limitations (latency, bandwidth, cost,
  accessibility) while *adding* the complexity of containers, a compositor per app, and now a **native
  client to build and maintain per platform** (ADR-0014 — which trades away the earlier "any device, no
  install" reach). Wayland forwarding (vs always-video) softens the bandwidth/latency hit for typical
  GUIs but not for animation/video.
- The **backend is a single, maximally-privileged point of compromise**. Most of the security model
  hangs on it being bug-free.
- The biggest contradiction with "very secure" was **frontend plugins via Module Federation running
  untrusted code in the trusted app context** — now mitigated with **Hardened JS / SES** (ADR-0016).
- Concrete mitigations for every item below are collected in **[SECURITY.md](SECURITY.md)**; tools to
  build on are in **[TOOLING.md](TOOLING.md)**.

---

## 1. Conceptual / usage limits

### 1.1 It is still a remote-app system, and it is no longer "the browser"
The UI is now a **native client** embedding Chromium (ADR-0014), not a page in any browser. That sharpens
two trade-offs:
- **You gave up the web's reach.** No "open a URL on any device" — the client must be installed and
  **maintained per platform** (Linux/macOS/Windows), and it depends on **CEF-on-Wayland**, which is newer
  and less proven than Electron's (a real P2 risk; Electron is the fallback).
- **The programs are still remote.** Versus running an app **locally**, you add network latency and a
  forward/encode step for no functional gain on a machine that could just run it. Versus a real **web
  app**, anything that *could* be a web app is better off as one. Forwarding (not video) means the app now
  renders on the client (real surfaces, better than opaque video), which narrows — but does not close —
  the gap.

The sweet spot is narrow: native apps you *can't* run locally (wrong OS, remote GPU/dataset, sandboxing
untrusted binaries), for a few trusted users on a good network, who will install a client.

### 1.2 Latency ceiling
Interactive remoting has a floor regardless of transport. On the **WebRTC fallback**, best case is
sub-250 ms glass-to-glass and congestion control reacts in **seconds** when the link degrades. **Wayland
forwarding** avoids re-encoding for static GUIs (better for typing/scrolling) but every frame still makes
a network round trip, and forwarded `dmabuf` buffers for large surfaces are heavy. Terminals and
form-filling are tolerable; drawing/CAD/gaming/video-editing remain painful on anything but a strong,
low-jitter link.

### 1.3 Bandwidth and cost scale badly
- Forwarding (ADR-0008) helps *static/idle* GUIs, but animation, scrolling, and video pin bandwidth high —
  and there it falls back to video encoding anyway, with the same costs as below.
- **Per session you still pay for: a container + a compositor + (on the fallback) a hardware encoder + a
  transport path.** GPU encoders are the real bottleneck and cost; CPU encoding is expensive and worse
  latency.
- When direct NAT traversal fails, the WebRTC fallback goes through **TURN**, which **doubles bandwidth**
  and adds cost. Self-hosted relay tuning tops out around hundreds of concurrent streams per node — this
  does not cheaply become multi-tenant SaaS.

### 1.4 Integration gaps that wreck UX
A forwarded/streamed surface is not a fully native window. Expect hard problems with:
- **Accessibility** — even forwarded surfaces don't carry an accessibility tree across the boundary by
  default, so screen readers, text scaling, and keyboard a11y of the *remote app* don't work (the CEF
  shell itself is accessible). On the WebRTC fallback it's pure opaque pixels. This can be a legal/ethical
  non-starter for some deployments.
- **Clipboard & drag-and-drop** between host, browser, and apps; **file open/save** dialogs; uploading
  local files into a remote app.
- **IME / keyboard layouts**, global shortcuts colliding across browser ↔ shell ↔ app, focus and
  z-order, **multi-monitor**, HiDPI/scaling, text selection across apps.
- **Peripherals**: webcam/mic passthrough, USB, printers, smartcards.
- **Multi-window apps** — menus, tooltips, right-click context menus, and dialogs that pop *outside* the
  single captured toplevel. ADR-0008 flags this; it is genuinely unsolved and very common.

### 1.5 Offline & resilience
The native shell launches offline, but the apps it shows are **dead without the server/network** — no
offline use, and every blip needs session reconnect and state recovery. State lives server-side; a
backend restart can drop every user's running apps.

---

## 2. Security problems

### 2.1 The backend is the crown jewel (single high-value target)
By design the Go backend is the **only** privileged component and brokers everything: it talks to the
**Docker/Podman socket**, **SSH**, and **Kubernetes**, and runs arbitrary user programs. Consequences:
- Access to the container socket is effectively **root on the host**. One backend RCE or a
  confused-deputy through a plugin capability ⇒ full host (and possibly remote-host) takeover.
- Centralizing privilege is good for *auditing* but makes the backend the most attractive target in the
  system, and the blast radius of any backend bug is total.
- **Mitigations — now adopted ([ADR-0013](adr/0013-strong-isolation-by-default.md)):** the backend no
  longer holds a raw container socket — it calls a narrow, least-privilege provisioning API; per-user
  quotas and default-deny egress are part of that contract. Still required: treat the backend as a
  hostile-input parser at every boundary.

### 2.2 GraphQL is a broad, easy-to-misuse attack surface
- **Complexity/depth DoS:** a single nested query can fan out to thousands of resolver/DB/container
  operations; real outages have come from exactly this. IP/session rate-limiting is insufficient.
  *Required:* query depth + complexity limits, timeouts, persisted/allow-listed queries,
  **resource-based** rate limiting.
- **Mutation amplification:** a batched/loop `launch(app)` can spawn many containers ⇒ resource-exhaustion
  DoS unless hard per-user quotas exist.
- **Field-level authz is the classic GraphQL footgun.** One endpoint, so *every field/resolver* must
  enforce authorization. ADR-0007's directive approach is good — but a resolver added without the
  directive silently exposes data, and directives don't protect against object-level (BOLA/IDOR) bugs.
- **Introspection** as recon, **injection** through resolver arguments (e.g. a capability path argument
  enabling path traversal, or args reaching a host shell), and **subscriptions** that authenticate only
  at WS-init and then run long-lived (token revocation and re-authorization mid-stream are easy to miss).

### 2.3 Containers are not a security boundary by default
The system's *raison d'être* is running **untrusted programs**. The original default (namespace-only
rootless containers, shared kernel) was too weak — container escape via kernel vulnerabilities is a live
threat. **Resolved ([ADR-0013](adr/0013-strong-isolation-by-default.md)):** strong isolation
(microVM/gVisor/Kata) is now the **default**, with seccomp/dropped-caps/no-host-net as the floor; plain
rootless is an explicit downgrade for trusted images only. Remaining caveats:
- **GPU passthrough** for hardware encode/accel still exposes DRM/GPU drivers to the untrusted workload —
  a well-known escape vector. Keep encode off the host where possible and use the strongest isolation
  tier.
- The per-app **compositor + encoder live next to the app** inside (or adjacent to) the same trust zone;
  an app that escapes its compositor may reach the stream/encoder.

### 2.4 WASM is not the airtight sandbox it's marketed as
ADR-0009 leans hard on WASM/WASI for "isolated dynamic libraries". Real, current caveats:
- **Side channels:** Spectre/transient-execution attacks can read host memory across the WASM boundary;
  defenses (Swivel-style hardening, MPK/CHERI) are not universal.
- **Runtime escapes happen:** linear-memory and JIT bugs have produced real escapes; a Wasmer flaw let
  modules bypass WASI filesystem restrictions. Wasmtime is solid but not infallible.
- **Resource exhaustion:** WASI lacks fine-grained quotas by default — a module can starve CPU/IO/entropy
  (DoS). You must configure fuel/epoch interruption and memory limits explicitly.
- **The host-function/WIT boundary is the real attack surface.** Capability security is only as correct
  as the `ResourceManager` broker; a too-coarse capability ("net: host X") still allows SSRF/exfiltration
  within scope (confused deputy). Bugs in the host functions = escape.

### 2.5 Frontend plugins are the weakest link — and contradict "very secure"
This is the most important finding. ADR-0010 loads plugins via **Module Federation**, i.e. **untrusted
remote code running in the main app's origin** with full DOM and same-origin privileges. Such a plugin can
read the user's session/GraphQL token, act as the user, keylog, phish, and exfiltrate.
- **Signing + SRI verify integrity, not behavior.** A signed-but-malicious (or later-compromised) plugin
  runs with full privilege. SRI can't help when the remote is *meant* to update.
- **Module Federation typically forces you to relax CSP/CORS**, weakening the app's own defenses.
- **Runtime-shared singletons** (Pinia, the GraphQL client) sourced from remotes are a supply-chain hole:
  one poisoned remote can corrupt shared state for the whole app.
- **"Curation" is a single human gate** — it doesn't scale and is the only thing standing between a user
  and a hostile plugin. That is *publisher trust*, not the capability isolation the backend plugins get.
- *Mitigation ([SECURITY.md](SECURITY.md) §2.5, **[ADR-0016](adr/0016-harden-frontend-plugins-ses.md)**):*
  keep curated federation but add **Hardened JavaScript (SES) Compartments** per plugin (the MetaMask
  Snaps model) so a plugin only gets explicitly granted capabilities, plus cosign signing + SRI + a
  capability bridge; **ShadowRealm/iframe** for the untrusted tier. This bounds a bad plugin to its
  granted capabilities rather than the whole UI — but SES is hardening, not an absolute boundary.

### 2.6 UI-as-data is an injection surface
The per-user layout document (ADR-0012) is **data rendered into the UI**. If documents can reference
arbitrary components, pass arbitrary props, or embed markup/expressions — and especially if they're ever
**shared between users** — that's stored-XSS / template-injection. Component refs must be allow-listed and
props schema-validated and sanitized.

### 2.7 WebRTC exposure
- **ICE candidate gathering leaks IP addresses** (client and server), a deanonymization vector.
- Media flows **browser ↔ container directly**, so containers must be network-reachable by clients,
  widening exposure; signaling/SDP tampering and DTLS-SRTP misconfig are risks.
- Self-hosting **TURN** securely (short-lived rotating credentials) is fiddly and easy to get wrong
  (open relays get abused).

### 2.8 Identity, multi-tenancy, and tokens
- "Built-in accounts to start" means DIY password storage, brute-force protection, and session management
  — all easy to get wrong. Prefer OIDC from day one.
- **Tenant isolation** of layout docs, capabilities, and live streams must be airtight; one IDOR lets a
  user reach another's session or stream.
- **Capability tokens** need a real lifecycle: scoping, expiry, revocation, replay protection, and secure
  storage. *Mitigation:* **Biscuit** offline-attenuable capability tokens
  (**[ADR-0015](adr/0015-capability-tokens-biscuit.md)**, SECURITY §2.8) + short TTL + revocation list.

### 2.9 Supply chain & abuse platform
- Trust chain for **app container images** (who builds/signs them? base-image CVEs), the **WASM
  toolchain**, and **npm deps** (host app + every federated remote) — each is a poisoning vector.
- A system that runs arbitrary programs and reaches remote hosts is an attractive **abuse platform**
  (cryptomining, C2, open proxy). Exposing it to the internet without egress controls, quotas, and
  monitoring is a liability.

---

## 3. What the architecture gets right (for balance)
- **Wayland over X11** for per-client isolation is the correct call (ADR-0002).
- A **single privileged broker + capability model** is a sound shape *if* implemented carefully.
- **WASM** for backend plugins is genuinely better than native in-process `.so`.
- Keeping **media out-of-band** from the control plane is the right separation.

## 4. Honest verdict
SandboxDesktop is a reasonable **personal / small-team, trusted-user** remote-app workspace on a good
network. It is **not**, as currently specified, a "very secure" platform for **untrusted multi-tenant**
use, and it is a poor fit where **low latency, low bandwidth, offline, or accessibility** matter. The two
changes that would most close the gap between the stated goals and reality:
1. ✅ **Adopted ([ADR-0013](adr/0013-strong-isolation-by-default.md)):** strong isolation is the default
   for user programs (microVM/gVisor) and the backend no longer holds the raw container socket.
2. ✅ **Addressed ([ADR-0016](adr/0016-harden-frontend-plugins-ses.md)):** frontend plugins are confined
   with Hardened JS / SES Compartments (+ signing/SRI/CSP), with ShadowRealm/iframe for the untrusted
   tier — bounding a bad plugin to its granted capabilities.

Concrete mitigations for all of §2 are in **[SECURITY.md](SECURITY.md)**; reusable tools in
**[TOOLING.md](TOOLING.md)**.

## Sources
- GraphQL DoS / complexity / field-authz: <https://www.wiz.io/academy/api-security/graphql-api-security-risks> · <https://portswigger.net/web-security/graphql> · <https://markaicode.com/graphql-api-dos-vulnerabilities-2025/>
- WASM/WASI sandbox limits (side channels, escapes, resource exhaustion): <https://aquilax.ai/blog/webassembly-wasm-security-risks> · <https://instatunnel.my/blog/the-wasm-breach-escaping-backend-webassembly-sandboxes>
- Module Federation security (runtime remote code, CSP relaxation, shared-dep supply chain): <https://github.com/webpack/webpack/discussions/16230>
- WebRTC scaling, TURN cost, IP leaks, latency: <https://antmedia.io/webrtc-scalability/> · <https://www.nanocosmos.net/blog/webrtc-latency/>
- Container vs WASM isolation in practice: <https://arxiv.org/pdf/2411.03344>
