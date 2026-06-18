# ADR-0006 — Local and remote hosts are interchangeable

- Status: Accepted
- Date: 2026-06-18

## Context

The goal states programs run "on some micro container locally or distant." A personal machine and a
remote/cloud host should both be first-class targets, and the UI/core should not care which one runs a
given program.

## Decision

Define a **single host-backend interface** in the Go core, with interchangeable implementations:

- **Local:** Podman/Docker socket.
- **Remote:** SSH / Kubernetes / HTTP API.

Both are designed from day one; the core selects a backend per app launch and brokers the stream
identically regardless of location.

## Alternatives considered

- **Local-first, remote later:** simplest, but bakes in local assumptions that are costly to undo.
  Rejected given equal-priority requirement.
- **Remote/cloud-first (Selkies's native home):** strong for remote, awkward for the personal-machine
  case. Rejected.
- **Both equally, abstracted (chosen):** one interface, two backends, uniform stream brokering.

## Consequences

- WebRTC brokering and the event API are location-agnostic; media flows browser ↔ container directly in
  both cases.
- Slightly more upfront design (a real abstraction, not a shortcut), repaid by not rewriting later.
- Remote backends add concerns (auth, network egress, TURN for WebRTC) the interface must accommodate.
