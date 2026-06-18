# SandboxDesktop — Security solutions

> Concrete mitigations and tools for each problem raised in [LIMITATIONS.md](LIMITATIONS.md) §2. This is
> the "how we defend it" companion to the threat model. Tools are listed in [TOOLING.md](TOOLING.md).

## Threat → mitigation map

| # | Problem (LIMITATIONS §2) | Mitigation | Tool / mechanism |
|---|--------------------------|-----------|------------------|
| 2.1 | Backend is a maximally-privileged target | No raw container socket; least-privilege **provisioning API**; workload identity; treat all input as hostile | Sysbox/Kata behind a provisioning daemon (Google Agent Sandbox model), **SPIFFE/SPIRE**, ADR-0013 |
| 2.2 | GraphQL DoS + field-authz | Depth + **complexity/cost limits**, timeouts, **persisted/trusted documents**, introspection **off in prod**, resource-based rate limiting, per-user mutation quotas; authz as **schema directives + default-deny** | `gqlgen` complexity, `query-cost-analysis`, ADR-0007 |
| 2.3 | Containers aren't a hard boundary | **Strong isolation by default** (microVM/gVisor/Kata); seccomp/AppArmor; drop caps; no host net; keep GPU encode out of the host | ADR-0013, Sysbox/Kata/Firecracker/gVisor |
| 2.4 | WASM isn't airtight | **Fuel/epoch + memory limits**; capability-gated host functions; minimal WIT surface; out-of-process worker for native | **Extism**/wazero/Wasmtime, ADR-0009 |
| 2.5 | Frontend plugins run untrusted code in-context | **Hardened JS / SES** Compartments per plugin + **signing + SRI + CSP**; **ShadowRealm/iframe** for the untrusted tier | **SES/LavaMoat/Endo**, cosign, ADR-0010 + **ADR-0016** |
| 2.6 | UI-as-data injection | Allow-list component refs; **schema-validate props**; no arbitrary HTML/expressions; sign/validate shared documents | JSON Schema, ADR-0012 |
| 2.7 | WebRTC IP leak / TURN abuse | **Time-limited TURN credentials**; ICE relay policy; mask relay IP; rotate creds | **coturn** REST API |
| 2.8 | Identity, multi-tenancy, tokens | Real IdP + OIDC; **offline-attenuable capability tokens**; strict tenant isolation checks | **Ory/Keycloak**, **Biscuit** (ADR-0015) |
| 2.9 | Supply chain & abuse platform | **Sign + verify** all plugin/container artifacts; SBOM; npm provenance + lockfiles; default-deny egress + quotas + audit | **Sigstore/cosign**, SES/LavaMoat |

## The hard ones, in detail

### Frontend plugins (the open gap — LIMITATIONS §2.5)
Curated Module Federation (ADR-0010) runs plugin code in the app context, so curation alone is *trust the
publisher*. We close most of the gap **without abandoning federation** by adding defense-in-depth — the
exact approach **MetaMask** uses to confine its **Snaps** plugins:

1. **Hardened JavaScript (SES).** `lockdown()` freezes intrinsics; each plugin runs in its own
   **Compartment** with only explicitly granted capabilities (no ambient `fetch`, `localStorage`, DOM, or
   the GraphQL token). Tooling: **LavaMoat**/**Endo**.
2. **Signing + integrity.** Plugins are **cosign**-signed and loaded under **Subresource Integrity**; the
   loader verifies signature + hash before executing.
3. **Capability bridge only.** A plugin reaches privileged data solely through the user-scoped GraphQL
   client handed to its Compartment — never by reaching into host globals. Strict **CSP** as backstop.
4. **Untrusted tier.** Anything not first-party runs in a **ShadowRealm** or sandboxed `<iframe>` +
   postMessage, with no change to the contract.

This makes a malicious/compromised plugin's blast radius ≈ its granted capabilities, not the whole UI.
See **[ADR-0016](adr/0016-harden-frontend-plugins-ses.md)**.

### Capability / permission tokens (LIMITATIONS §2.8, ADR-0009)
The Android-style permission manifest is realized with **Biscuit tokens**: public-key-signed,
**offline-attenuable** capability tokens carrying a Datalog policy. Properties that fit exactly:
- A token can be **attenuated** (narrowed) by its holder with no server round-trip — e.g. the backend
  hands a plugin a token scoped to only the permissions the user granted, and can further narrow it
  per-request.
- Any component knowing the public key verifies it **offline** — `ResourceManager`, the provisioning API,
  and sandboxes all check the same token without a central session lookup.
- Revocation lists + short TTLs bound the damage of a leaked token.

See **[ADR-0015](adr/0015-capability-tokens-biscuit.md)**.

### Backend blast-radius (LIMITATIONS §2.1)
The backend calls a **least-privilege provisioning API** (ADR-0013), never a raw socket. That API:
- accepts only "run *approved image* with *this sandbox profile*, *these quotas*, *this egress policy*";
- runs workloads under **Sysbox** (default) or **Kata/gVisor** (untrusted), modelled on **Google Agent
  Sandbox**'s declarative pod API;
- authenticates the backend with **SPIFFE** identity, so a stolen backend credential can't issue
  arbitrary container commands.

### GraphQL hardening (LIMITATIONS §2.2)
Phased, per current best practice: depth limiting + timeouts (day 1) → **complexity/cost analysis**
(`gqlgen` + `query-cost-analysis`) → field-level cost + resource-based rate limiting → **persisted/trusted
documents** and introspection disabled in production. Authorization stays **default-deny** in resolvers
via directives (ADR-0007), with tests asserting every field is covered.

## Residual risks we accept (for now)
- **Side-channel** (Spectre-class) reads across the WASM/sandbox boundary — mitigated by runtime hardening,
  not eliminated.
- **GPU driver attack surface** when passing through hardware encode/decode.
- **Accessibility** of remote app surfaces (a usability, not a breach, limit — LIMITATIONS §1.4).
- **Native-client supply chain** (CEF builds, OS packages) — signed releases + reproducible builds reduce
  but don't remove it.

## Sources
- Hardened JavaScript / SES (MetaMask Snaps, LavaMoat): <https://hardenedjs.org/> · <https://lavamoat.github.io/>
- Biscuit tokens: <https://www.biscuitsec.org/> · <https://github.com/eclipse-biscuit/biscuit>
- gqlgen complexity + GraphQL security: <https://gqlgen.com/reference/complexity/> · <https://cheatsheetseries.owasp.org/cheatsheets/GraphQL_Cheat_Sheet.html>
- Sysbox: <https://github.com/nestybox/sysbox> · Kata/Firecracker/gVisor comparison: <https://northflank.com/blog/kata-containers-vs-firecracker-vs-gvisor>
- Google Agent Sandbox (CNCF): <https://github.com/kubernetes-sigs/agent-sandbox>
- coturn TURN REST API (time-limited creds): <https://github.com/coturn/coturn/wiki/turnserver>
- Extism: <https://extism.org/> · wazero: <https://github.com/tetratelabs/wazero>
- Sigstore/cosign: <https://www.sigstore.dev/>
