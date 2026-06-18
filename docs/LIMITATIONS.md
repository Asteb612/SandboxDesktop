# SandboxDesktop — Limitations & Threat Model

> A deliberately **critical** companion to [ARCHITECTURE.md](ARCHITECTURE.md). The architecture doc
> argues *for* the design; this one argues *against* it. Read both. Nothing here is a blocker by itself,
> but several items are in direct tension with the project's stated goals ("the UI is a website",
> "very secure plugins"), and a few are showstoppers for specific use cases.

## TL;DR

- The project is, honestly, a **remote-desktop system with a web client** — not "apps built with web
  technology". It therefore inherits every remote-desktop limitation (latency, bandwidth, cost,
  accessibility) while *adding* the complexity of containers, a compositor, and an encoder per app.
- The **backend is a single, maximally-privileged point of compromise**. Most of the security model
  hangs on it being bug-free.
- The biggest contradiction with "very secure": **frontend plugins via Module Federation run untrusted
  code in the trusted app context.** "Curated + signed" is *trust the publisher*, not isolation.
- **Containers and WASM are not hard security boundaries.** The design treats stronger isolation
  (gVisor/Kata) as opt-in, i.e. the default is the weaker boundary — while the whole point is running
  *untrusted* programs.

---

## 1. Conceptual / usage limits

### 1.1 It is strictly worse than local apps, and worse than real web apps
The premise — "use the browser to hold the full UI" — is satisfied only for the *shell*. The actual
programs are native apps rendered remotely and shipped as **video**. So:
- Versus running the app **locally**: you add network latency, encode/decode, and bandwidth for zero
  functional gain on a machine that could just run it.
- Versus a real **web app**: a true web app runs in the browser (low latency, offline-capable, cheap to
  serve). Streaming a native app is a regression for anything that *could* have been a web app.

The sweet spot is narrow: native apps you *can't* run locally (wrong OS, need a remote GPU/dataset,
sandboxing untrusted binaries), for a few users on a good network.

### 1.2 Latency ceiling
WebRTC is excellent for video but interactive remoting has a floor. Best case is sub-250 ms glass-to-glass,
and congestion control reacts on the order of **seconds** when the link degrades — so typing, scrolling,
dragging, and drawing feel rubbery on anything but a strong, low-jitter connection. Terminals and
form-filling are tolerable; drawing/CAD/gaming/video-editing are painful.

### 1.3 Bandwidth and cost scale badly
- Streaming an app's pixels costs far more than serving a web app. "Only the app surface, damage-tracked"
  (ADR-0008) helps for *idle/static* UIs but does nothing for animation, scrolling, or video content —
  those pin the bitrate high continuously.
- **Per session you pay for: a container + a compositor + a hardware encoder + a media path.** GPU
  encoders are the real bottleneck and the real cost; CPU encoding is expensive and worse latency.
- When direct WebRTC NAT traversal fails, media goes through **TURN**, which **doubles bandwidth** and
  adds latency and server cost. Self-hosted SFU/relay tuning tops out around hundreds of concurrent
  streams per node — this does not cheaply become multi-tenant SaaS.

### 1.4 Integration gaps that wreck UX
A video surface is not a window. Expect hard problems with:
- **Accessibility** — a streamed surface is opaque pixels: screen readers, text scaling, high-contrast,
  and keyboard a11y do not work. This can be a legal/ethical non-starter for some deployments.
- **Clipboard & drag-and-drop** between host, browser, and apps; **file open/save** dialogs; uploading
  local files into a remote app.
- **IME / keyboard layouts**, global shortcuts colliding across browser ↔ shell ↔ app, focus and
  z-order, **multi-monitor**, HiDPI/scaling, text selection across apps.
- **Peripherals**: webcam/mic passthrough, USB, printers, smartcards.
- **Multi-window apps** — menus, tooltips, right-click context menus, and dialogs that pop *outside* the
  single captured toplevel. ADR-0008 flags this; it is genuinely unsolved and very common.

### 1.5 Offline & resilience
A PWA shell can cache, but streamed apps are **dead without the server/network** — no offline, and every
blip needs session reconnect and state recovery. State lives server-side; a backend restart can drop
every user's running apps.

---

## 2. Security problems

### 2.1 The backend is the crown jewel (single high-value target)
By design the Go backend is the **only** privileged component and brokers everything: it talks to the
**Docker/Podman socket**, **SSH**, and **Kubernetes**, and runs arbitrary user programs. Consequences:
- Access to the container socket is effectively **root on the host**. One backend RCE or a
  confused-deputy through a plugin capability ⇒ full host (and possibly remote-host) takeover.
- Centralizing privilege is good for *auditing* but makes the backend the most attractive target in the
  system, and the blast radius of any backend bug is total.
- **Mitigations the design must add (not optional):** never hand the raw container socket to the backend
  — front it with a narrow, rootless provisioning API; strict egress firewalls on hosts; per-user
  quotas; treat the backend as a hostile-input parser at every boundary.

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
The system's *raison d'être* is running **untrusted programs**, yet the default is namespace-only rootless
containers (shared kernel). Container escape via kernel vulnerabilities is a live threat, and
**gVisor/Kata are "opt-in"** — so the secure mode is the exception, not the default.
- **GPU passthrough** for hardware encode/accel exposes DRM/GPU drivers to the untrusted workload — a
  well-known escape vector — partially undermining the isolation.
- The per-app **compositor + encoder live next to the app** inside (or adjacent to) the same trust zone;
  an app that escapes its compositor may reach the stream/encoder.
- *Recommendation:* make gVisor/Kata (or microVMs) the **default** for user programs, add seccomp/AppArmor
  profiles, drop all capabilities, no host networking.

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
- *Recommendation:* for anything not 100% first-party, the **sandboxed-iframe + postMessage** model
  (deferred in ADR-0010) should be the default, not the future tier. Otherwise drop the "very secure"
  claim for the frontend.

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
  storage. This is a subsystem, not a field.

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
1. Make **strong isolation the default** for user programs (microVM/gVisor) and never expose the raw
   container socket to the backend.
2. **Sandbox frontend plugins (iframe) by default** — Module Federation only for audited first-party code.

## Sources
- GraphQL DoS / complexity / field-authz: <https://www.wiz.io/academy/api-security/graphql-api-security-risks> · <https://portswigger.net/web-security/graphql> · <https://markaicode.com/graphql-api-dos-vulnerabilities-2025/>
- WASM/WASI sandbox limits (side channels, escapes, resource exhaustion): <https://aquilax.ai/blog/webassembly-wasm-security-risks> · <https://instatunnel.my/blog/the-wasm-breach-escaping-backend-webassembly-sandboxes>
- Module Federation security (runtime remote code, CSP relaxation, shared-dep supply chain): <https://github.com/webpack/webpack/discussions/16230>
- WebRTC scaling, TURN cost, IP leaks, latency: <https://antmedia.io/webrtc-scalability/> · <https://www.nanocosmos.net/blog/webrtc-latency/>
- Container vs WASM isolation in practice: <https://arxiv.org/pdf/2411.03344>
