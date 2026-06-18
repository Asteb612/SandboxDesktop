# ADR-0013 — Strong isolation by default; broker the container socket

- Status: Accepted
- Date: 2026-06-18
- Hardens: [ADR-0005](0005-one-program-per-micro-container.md),
  [ADR-0006](0006-local-and-remote-hosts-interchangeable.md)
- Addresses: [LIMITATIONS.md](../LIMITATIONS.md) §2.1, §2.3

## Context

The whole point of the system is to run **untrusted programs**. Two earlier choices were too weak for
that threat model:

1. **ADR-0005** made namespace-only **rootless containers the default** and treated gVisor/Kata as
   *opt-in*. That means the *secure* mode was the exception, while the default boundary (a shared kernel)
   is escapable via kernel bugs — exactly the workload we said is untrusted.
2. **ADR-0006** let the host backend speak to a raw **Podman/Docker socket**. Access to that socket is
   effectively **root on the host**, so any backend bug or confused-deputy escalates to full host
   takeover. The backend is already the single most privileged component (LIMITATIONS §2.1); handing it
   the raw socket maximizes blast radius.

## Decision

1. **Strong isolation is the default for user programs.** Each program runs in a **microVM / gVisor /
   Kata**-class sandbox by default, not namespace-only containers. Rootless + dropped capabilities +
   seccomp/AppArmor + no host networking is the *floor*, applied underneath. Plain rootless containers
   become an explicit, logged downgrade for trusted/first-party images only.
2. **The backend never holds the raw container socket.** Host backends expose a **narrow, least-privilege
   provisioning API** (a small daemon/service that accepts only "run this approved image with this
   sandbox profile, these limits, this network policy" and nothing else). The Go backend calls that API;
   it cannot issue arbitrary container/socket commands. This holds for both local and remote
   implementations (ADR-0006).
3. **Per-user quotas and egress control are part of the contract.** The provisioning API enforces hard
   per-user limits (max concurrent sandboxes, CPU/memory/GPU/time) and a **default-deny egress firewall**
   per sandbox; a program reaches only what its capabilities allow.

## Alternatives considered

- **Keep rootless-by-default, gVisor opt-in (ADR-0005 status quo):** lower overhead, but the default
  boundary is too weak for untrusted code. Rejected.
- **Full VM per app:** strongest, but heavy and slow to start; microVMs (Firecracker/Kata) get most of
  the benefit with fast boot. microVM/gVisor chosen as the default tier.
- **Backend holds the socket but "is careful":** rejected — a single bug = root; not a boundary.

## Consequences

- Higher per-app overhead (microVM/gVisor cost) and some syscall-compat edge cases — accepted as the
  price of running untrusted code safely. Trusted images may opt down to plain rootless.
- The provisioning API is a new component to build and harden, but it shrinks the backend's blast radius
  from "root on host" to "request an approved sandbox".
- GPU passthrough for hardware encode/accel still widens the in-sandbox attack surface; pair with the
  strongest available isolation tier and keep encode off the host where possible.

## References

- gVisor: <https://gvisor.dev/>
- Kata Containers: <https://katacontainers.io/>
- Firecracker microVMs: <https://firecracker-microvm.github.io/>
