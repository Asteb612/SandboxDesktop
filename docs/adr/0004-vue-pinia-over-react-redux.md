# ADR-0004 — Vue + Pinia over React/Redux

- Status: Accepted
- Date: 2026-06-18

## Context

The original UI was **React + Redux**, with Redux justified by "complex UI component interaction." The
UI is now a **streaming workspace**: it launches apps, arranges their video/canvas surfaces in panes/
tabs, and hosts plugin UIs. Its state is essentially a set of **sessions + app instances + layout** —
not the flat global store that Redux's boilerplate is built for.

## Decision

Build the UI with **Vue 3** (single-file components, Composition API) and **Pinia** for state.

## Alternatives considered

- **React + Redux:** heavy boilerplate for the state shape we actually have; Redux was over-spec'd for
  this. Rejected (per project direction).
- **React + Zustand/Jotai:** lighter than Redux, but the project direction is Vue.
- **Svelte/SolidJS:** very light/fast, but a smaller ecosystem for this use case and not the chosen
  direction.
- **Vue 3 + Pinia (chosen):** reactive SFCs fit a live, surface-driven workspace; Pinia gives simple,
  typed stores sized to sessions + layout.

## Consequences

- State stays close to the domain (sessions/instances/layout) without reducer ceremony.
- Vue's reactivity drives live updates from core WebSocket events into panes cleanly.
- Rendered by the native CEF client (ADR-0014); built with Vite to static assets the client loads.
