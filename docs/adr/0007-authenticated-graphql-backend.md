# ADR-0007 — Authenticated GraphQL backend as the privileged layer

- Status: Accepted
- Date: 2026-06-18
- Refines: [ADR-0003](0003-go-core-over-python-flask.md) (API contract)

## Context

The project should behave like a normal web application: an **authenticated user** calls a backend, and
the **backend** is the component with system access. The Round-1 design left the API as an ad-hoc
"WebSocket events + thin REST" surface. We need one coherent, typed, authenticated contract that carries
both control operations and real-time events, and that manages access rights itself.

## Decision

The Go backend exposes a single **GraphQL API** (gqlgen):

- **Queries / mutations** over HTTPS for control (list/launch/stop apps, save layout, manage plugins).
- **Subscriptions** over WebSocket (`graphql-transport-ws`) for real-time events (app ready/exited,
  stream offers, focus). WebRTC SDP/ICE for app media is exchanged through mutations/subscriptions; media
  itself stays out of band (browser ↔ container).
- **Authentication** on every entry: tokens verified on HTTP requests and in the **WebSocket init
  payload**; the authenticated user is injected into the resolver context. Identity is pluggable —
  built-in accounts to start, **OIDC**-ready.
- **Access rights are managed internally by GraphQL.** Authorization lives in the backend: declarative
  **schema directives** (`@auth`, `@hasPermission`) plus per-resolver checks against the user in context.
  Clients and plugins never make access decisions.
- The backend is the **only** component with system access; all privileged work is brokered through
  `ResourceManager` under scoped capabilities (see ADR-0009).

## Alternatives considered

- **REST + ad-hoc WebSocket (Round-1 sketch):** two contracts, no typing, awkward real-time. Rejected.
- **gRPC-web:** strong typing and streaming, but a heavier browser story and no query flexibility for a
  data-driven, per-user UI. Rejected for the client-facing API.
- **GraphQL (chosen):** one typed schema for queries, mutations, and subscriptions; mature Go support
  (gqlgen) for subscription auth and directive-based authorization; a natural fit for fetching a
  per-user UI document.

## Consequences

- A single authenticated, typed contract for control + events; the per-user UI document (ADR-0012) is
  just another query.
- Authorization is centralized and auditable in the backend, not scattered or client-trusted.
- Subscriptions require managing live WebSocket connections (a channel/goroutine per subscription) —
  acceptable and idiomatic in Go.
