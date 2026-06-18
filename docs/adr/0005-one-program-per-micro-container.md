# ADR-0005 — One program per micro-container

- Status: Accepted
- Date: 2026-06-18

## Context

The project runs programs — including **untrusted user modules** — and streams them to the browser.
The original design imagined modules loaded with an **auth token used on every API request to identify
the module and its rights**. We need an isolation and identity model for those programs.

## Decision

Each program runs in its **own single-purpose micro-container** with a headless Wayland compositor
(ADR-0002). Each module/plugin is issued a **capability token** (carried forward from the original README
idea) presented on every core API call to identify it and scope its rights.

> **Isolation tier — updated by [ADR-0013](0013-strong-isolation-by-default.md).** Because user programs
> are untrusted, the **default** sandbox is now **microVM / gVisor / Kata**-class, not namespace-only
> rootless containers. Rootless + seccomp + dropped capabilities + no host networking is the floor;
> plain rootless is an explicit, logged downgrade for trusted images only.

## Alternatives considered

- **Shared desktop/container for many apps:** simpler, but apps share a blast radius and (under X11)
  could snoop each other. Rejected.
- **One container per program, namespaces only (chosen baseline):** good isolation, low overhead.
- **gVisor/Kata per program:** strongest isolation; higher overhead and some syscall-compat cost.
  Offered as opt-in, not the default.

## Consequences

- Clear blast-radius boundary and lifecycle per app; failures don't cascade.
- Capability tokens give the core a consistent identity/authorization model for plugins.
- Per-app containers multiply image/resource management work — handled by the host backend abstraction
  (ADR-0006) and `ResourceManager`.
