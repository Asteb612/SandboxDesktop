# ADR-0012 — Per-user editable UI as data

- Status: Accepted
- Date: 2026-06-18

## Context

Each user needs their **own** interface, editable at runtime (the Interface and Component tiers of
ADR-0011), without writing code. We need a representation the shell can render and an editor can mutate,
persisted per user.

## Decision

Represent the interface as **data**:

- **Layout document.** Each user's interface is a **serializable document** — a tree of `slot → component
  ref + props + bound theme tokens + geometry`. The Vue shell renders it dynamically via `<component
  :is>`. Nothing in the shell is hardcoded; it renders whatever the resolved document says.
- **Component registry.** Every placeable widget — host components, theme-provided components, and
  **federated plugin components** (ADR-0010) — registers under a **component contract** (ADR-0011) with a
  **props schema** the editor uses to render configuration controls.
- **Edit mode.** Users rearrange/resize/add/remove panels via drag-drop (Gridstack/Syncfusion-style),
  restyle via theme tokens, and place any registered component. **No code/logic authoring** (a future
  low-code tier could layer on later).
- **Per-user persistence.** The user's selected theme, layout document, and enabled plugins/overrides are
  keyed to the authenticated user and stored via `ConfigManager`. On login the backend returns them
  (a GraphQL query, ADR-0007) and the shell renders that user's resolved interface — a **different
  interface per user**.

## Alternatives considered

- **Hardcoded layouts + a few preset themes (personalization only):** simplest, but cannot satisfy
  "the full UI is editable." Rejected.
- **Full low-code builder (user-authored logic/data binding):** powerful but a much larger scope and
  attack surface. Deferred.
- **UI-as-data, layout + theme + registry components (chosen):** fully editable composition without code,
  cleanly persisted and rendered.

## Consequences

- The interface is portable, diff-able, and shareable; per-user UIs are just stored documents.
- The editor is schema-driven, so any registered component is configurable without bespoke editor code.
- The document needs a versioned schema + migration story as components/contracts evolve.

## References

- Gridstack.js (drag-drop dashboard layout): <https://gridstackjs.com/>
- Vue dynamic components (`<component :is>`): <https://vuejs.org/guide/essentials/component-basics.html#dynamic-components>
