# ADR-0003 — Go core over Python/Flask

- Status: Accepted
- Date: 2026-06-18
- Note: the choice of **Go** stands. The **API contract** described below (“WebSocket-first event API +
  thin REST”) is **superseded by [ADR-0007](0007-authenticated-graphql-backend.md)**, which makes the
  authenticated **GraphQL** API the single contract (queries/mutations + subscriptions). The plugin
  model below is refined by [ADR-0009](0009-backend-plugin-security-capability-model.md) (isolated
  dynamic modules, not in-process sidecars).

## Context

The original core was **Python + Flask**, exposing a **REST** API to plugins and the UI. The core's
real job is now: orchestrate container lifecycles across local/remote hosts, broker WebRTC sessions,
and push **real-time events** (app launched/ready/exited, focus, resize) to the UI. REST request/
response and polling are a poor fit for that, and Python is a poor fit for the latency-sensitive,
highly concurrent control plane.

## Decision

Build the core/orchestrator in **Go**: a single binary exposing a **WebSocket-first** event API plus a
thin REST/HTTP surface for CRUD. Concurrency via goroutines (one per session). Plugins remain **Python
sidecars** (see ADR-0005).

## Alternatives considered

- **Keep Flask + REST (+ SSE/polling):** simplest continuity, but weak for bidirectional real-time
  events and concurrent session handling. Rejected.
- **Rust core:** excellent performance and aligns with Selkies's Rust components, but more
  implementation friction than needed for the control plane; the hot media path lives in the
  compositor/encoder, not the orchestrator. Rejected for the core (may still appear downstream).
- **Go (chosen):** strong concurrency, native WebSocket libraries, trivial single-binary deployment
  that matches container orchestration, good Podman/Docker/Kubernetes client ecosystem.

## Consequences

- WebSocket-first API carries WM/stream events naturally; goroutine-per-session scales cleanly.
- Single static binary simplifies deployment alongside containers.
- Python keeps its strengths where they matter — the plugin SDK and system access — as sidecars.
