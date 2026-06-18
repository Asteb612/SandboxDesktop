# ADR-0016 — Harden frontend plugins with Hardened JavaScript (SES)

- Status: Accepted
- Date: 2026-06-18
- Hardens: [ADR-0010](0010-frontend-plugins-module-federation.md)
- Addresses: [LIMITATIONS.md](../LIMITATIONS.md) §2.5

## Context

ADR-0010 loads frontend plugins via curated **Module Federation**, which runs plugin code in the app
context. LIMITATIONS §2.5 calls this the weakest part of the "very secure" claim: curation + signing
verify *integrity, not behavior*, so a signed-but-malicious or later-compromised plugin runs with full DOM
and same-origin privileges (it could read the GraphQL/session token, act as the user, keylog). We want to
keep federation's rich first-party integration **and** contain misbehavior.

## Decision

Confine every frontend plugin with **Hardened JavaScript (SES)** — the model MetaMask uses for its
**Snaps** plugins — as defense-in-depth on top of curation:

1. **Lockdown + Compartments.** Call `lockdown()` to freeze intrinsics; run each plugin in its own SES
   **Compartment** with only **explicitly granted capabilities** in scope — no ambient `fetch`,
   `localStorage`, cookies, DOM, or the raw GraphQL token.
2. **Capability bridge.** A plugin receives a narrow, user-scoped API object (e.g. a GraphQL client bound
   to its Biscuit-attenuated grant, ADR-0015) and the registry-registration hooks — nothing else.
3. **Signing + integrity.** Plugins are **cosign**-signed and loaded under **Subresource Integrity**;
   the loader verifies signature + hash before execution. Strict **CSP** as a backstop.
4. **Untrusted tier.** Non-first-party plugins run in a **ShadowRealm** or sandboxed `<iframe>` +
   postMessage, using the same capability bridge — no contract change.

Tooling: **SES/Endo** + **LavaMoat** (build-time supply-chain confinement).

## Alternatives considered

- **Curation + signing only (ADR-0010 as-is):** trust-the-publisher; no behavioral containment. Kept as
  the baseline but insufficient alone.
- **iframe sandbox for *all* plugins:** strongest isolation, but loses the in-context, Pinia-sharing
  first-party integration the project wants. Reserved for the untrusted tier.
- **SES hardening of in-context plugins (chosen):** keeps federation's integration while reducing a bad
  plugin's blast radius to its granted capabilities; proven at scale by MetaMask Snaps.

## Consequences

- A malicious/compromised first-party plugin can do ≈ only what its capabilities allow, not anything the
  UI can.
- Plugins must be authored against the SES subset (no reliance on frozen-then-mutated globals); the
  capability bridge + registry contract must be designed deliberately.
- Side-channels and bugs in the bridge remain residual risks (SECURITY.md); SES raises the bar, it is not
  absolute.

## References

- Hardened JavaScript / SES: <https://hardenedjs.org/>
- LavaMoat (and MetaMask Snaps confinement): <https://lavamoat.github.io/>
- ShadowRealm: <https://github.com/tc39/proposal-shadowrealm>
