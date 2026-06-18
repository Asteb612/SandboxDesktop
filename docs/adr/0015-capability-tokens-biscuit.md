# ADR-0015 — Capability tokens via Biscuit

- Status: Accepted
- Date: 2026-06-18
- Refines: [ADR-0009](0009-backend-plugin-security-capability-model.md) (the "capability token")

## Context

ADR-0009 issues each plugin a scoped, revocable **capability token** representing its Android-style
granted permissions, checked on every privileged action by `ResourceManager` — and the provisioning API
and sandboxes must check the same grant. We need a concrete token format. A plain opaque session token
needs a central lookup on every check; a signed JWT carries claims but cannot be **narrowed** by a holder
without re-minting at the issuer.

## Decision

Represent capability/permission grants as **Biscuit tokens** (Eclipse Biscuit):

- **Public-key signed, verified offline.** `ResourceManager`, the provisioning API, and sandboxes verify
  the same token with the public key — no central session round-trip per check.
- **Offline attenuation.** A holder can derive a *more restricted* token without contacting the issuer:
  the backend mints a token scoped to the user's granted permissions, then attenuates it further
  per-request (e.g. "this call may read only this path") before passing it down. Authority only ever
  shrinks along the chain — a natural fit for capability security and least privilege.
- **Datalog policy.** Permissions, checks, and request facts are expressed in Biscuit's Datalog variant,
  so the manifest's declared permissions map directly onto token checks.
- **Bounded blast radius.** Short TTLs + a revocation list limit damage from a leaked token.

## Alternatives considered

- **Opaque token + central store:** simple, but every check is a lookup and a coupling point; no holder
  attenuation. Rejected for the hot path.
- **Signed JWT:** offline-verifiable, but not attenuable by holders — every narrowing means a round-trip
  to the issuer. Usable for single-hop, but Biscuit covers both. (Hybrid: JWT for single-hop, Biscuit for
  delegation chains, is a known pattern if needed.)
- **Macaroons:** attenuable via caveats, but HMAC-shared-secret verification rather than public-key.
  Biscuit's public-key verification suits multiple independent verifiers (backend, provisioner, sandbox).
- **Biscuit (chosen).**

## Consequences

- One token type works across all verifiers with no shared session state; least privilege is enforced by
  construction (attenuation only narrows).
- New dependency + a Datalog policy surface to design and test carefully (an over-broad policy is still
  over-broad).
- Revocation still needs infrastructure (revocation list / short TTL); offline verification doesn't
  revoke by itself.

## References

- Biscuit: <https://www.biscuitsec.org/> · <https://github.com/eclipse-biscuit/biscuit>
