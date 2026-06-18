# ADR-0011 — Three-level customization with WordPress-style overrides

- Status: Accepted
- Date: 2026-06-18

## Context

The frontend must be highly customizable and **different per user**, and plugins must be able to change
it. The requirement is explicitly layered into **three levels — Theme → Interface → Components** — each
with a **defined interface** that can be **overloaded**, in the spirit of WordPress (child themes, the
template hierarchy, and pluggable functions/blocks).

## Decision

Define three customization levels, each a stable contract, resolved by an override chain.

| Level | Controls | Defined interface | Overload mechanism (WordPress analogue) |
|-------|----------|-------------------|------------------------------------------|
| **1 · Theme** | Look & feel (color, spacing, type) | A named set of **design tokens** (CSS custom properties) + global styles | A theme extends/overrides another's tokens (child theme overrides parent) |
| **2 · Interface** | Which regions/panels exist and their arrangement | A **layout schema** — named slots/regions + the per-user layout document (ADR-0012) | A theme/plugin ships an Interface template; a more specific provider overrides it (template hierarchy) |
| **3 · Component** | The implementation of an individual widget | A **component contract** — props/slots/events schema + themeable `::part()`s | Any provider re-registers a component id with its own implementation behind the same contract (pluggable functions / block variations) |

- **Override resolution — most specific wins:** for every token, slot, and component id the system
  resolves a provider in priority order **per-user/per-instance → enabled plugins → active theme →
  built-in default**. Because each level has a stable contract, overrides are drop-in: replacing one
  component does not affect the rest of the UI.
- **Theme tier** is implemented with **design tokens as CSS custom properties** consumed by components
  built on **Web Components Shadow DOM**. Tokens pierce the shadow boundary for theming; **`::part()`**
  exposes specific internals for structural overrides. The component author decides what is themeable — a
  safe public styling contract.
- **Interface and Component tiers** are realized by the UI-as-data model and component registry in
  ADR-0012; plugins (ADR-0010) contribute at the Interface and Component tiers by registering templates
  and components.

## Alternatives considered

- **Single flat "theme" with CSS overrides only:** easy, but cannot express layout templates or swap
  component implementations. Rejected — too shallow for the requirement.
- **Per-component ad-hoc props, no formal contracts:** quick, but overrides become fragile and
  un-composable. Rejected.
- **Three contract'd tiers with an override chain (chosen):** matches the WordPress model the user asked
  for and keeps overrides safe and composable.

## Consequences

- Customization is predictable and composable; a plugin or theme can override exactly one tier without
  side effects.
- Each tier needs a versioned contract and a documented resolution order — real design work, paid back
  in extensibility.
- Style isolation (Shadow DOM) keeps theme/component overrides from leaking across the UI.

## References

- CSS Shadow Parts (`::part()`): <https://developer.mozilla.org/en-US/docs/Web/CSS/::part>
- Design tokens / CSS custom properties theming: <https://developer.mozilla.org/en-US/docs/Web/CSS/--*>
