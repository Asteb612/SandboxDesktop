# ADR-0010 — Frontend plugins via curated Module Federation

- Status: Accepted
- Date: 2026-06-18

## Context

Plugins must be able to **change the interface** — contribute or replace UI (Component-tier and
Interface-tier overrides, see ADR-0011). The question is how plugin UI loads and how much it is trusted.

## Decision

Frontend plugins load via **curated Module Federation** (Vite, `@originjs/vite-plugin-federation`). They
run in the app context and may share the Pinia store via an interface contract.

Because federated code runs in-context, the **trust gate is the security boundary**:

- **Curation + signing.** Plugins are reviewed and **signed**; the loader verifies them and uses
  **Subresource Integrity** on the fetched modules.
- **Stable plugin API contract.** Plugins interact through a defined contract (registry registration,
  typed events, the user-scoped GraphQL client), not by reaching into host internals.
- **CSP defense-in-depth.** A strict Content-Security-Policy limits what plugin code can load/connect to;
  privileged data only ever arrives through the **user-scoped GraphQL** API (where authz is enforced
  internally, ADR-0007).

A future **untrusted tier** can run third-party UI in a **sandboxed `<iframe>` + postMessage capability
bridge** (the Figma model) without changing the contract.

## Alternatives considered

- **Sandboxed iframe + postMessage for all plugins:** strongest isolation, but blocks the rich,
  Pinia-sharing first-party integration the project wants now. Deferred to the untrusted tier.
- **Build-time-only plugins (recompile the app):** simplest and safe, but not dynamic — users could not
  add/change UI at runtime. Rejected.
- **Curated Module Federation (chosen):** dynamic runtime loading + rich integration, with curation/
  signing/SRI/CSP as the security boundary.

## Consequences

- Rich first-party UI plugins with shared state and runtime loading.
- Security depends on the curation/signing pipeline — it must be real (review, key management, SRI), not
  nominal.
- A clear upgrade path to an untrusted tier (iframe sandbox) if third-party plugins are later allowed.

## References

- Vite Module Federation: <https://github.com/originjs/vite-plugin-federation>
- Figma plugin security model: <https://www.figma.com/blog/how-we-built-the-figma-plugin-system/>
