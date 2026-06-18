# ADR-0009 — Backend plugins: isolated dynamic modules with Android-style permissions

- Status: Accepted
- Date: 2026-06-18

## Context

Backend plugins extend the privileged Go backend, so they are the highest-risk extension point and must
be **very secure**. Requirements: plugins are **dynamic libraries the backend loads in isolation**; each
plugin **declares the authorizations it requires** (Android-style); and a plugin can do **only** what it
was granted.

## Decision

- **Capability-based, zero ambient authority.** A plugin begins with no access to filesystem, network,
  devices, or GraphQL operations. It receives only explicitly granted capabilities.
- **Isolated dynamic-library mechanism = WASM.** A plugin is a dynamically-loaded **WASM Component Model
  / WASI** module that the backend loads via an **embedded Wasmtime runtime**. This is a genuine "dynamic
  library loaded in isolation": memory-isolated from the host, capability-gated filesystem/network, typed
  interfaces via WIT.
- **Native in-process loading is rejected.** Go `plugin`/`dlopen` `.so` modules share the host address
  space — a fault or exploit compromises the whole backend. Where native code cannot target WASM, run it
  as an **out-of-process sandboxed worker over RPC** (hashicorp/go-plugin style), outside the host's
  address space.
- **Android-style declared permissions.** Each plugin ships a **permission manifest** enumerating
  required authorizations (paths, hosts, devices, GraphQL operations). `ModuleManager` validates it, the
  user grants it at install, and the plugin receives a scoped, **revocable capability token**. Ungranted
  permissions do not exist for that plugin.
- **Brokered access only.** Every privileged action flows through `ResourceManager`, the single
  chokepoint, which enforces the granted permissions, applies resource limits, and audits.
- **Programs ≠ plugins.** User programs/apps run as per-app Wayland containers (ADR-0005); plugins extend
  the backend and use the isolated-module model above.

## Alternatives considered

- **Native in-process `.so` (Go `plugin`):** dynamic and fast, but **no isolation** and notoriously
  brittle (toolchain/version lockstep). Rejected — incompatible with "in isolation" and "very secure."
- **Containers for every backend plugin:** strong isolation but heavy for small logic extensions and not
  really a "dynamic library." Kept only for GUI/app *programs*, not logic plugins.
- **WASM via embedded Wasmtime (chosen):** dynamic, in-isolation, capability-secure, polyglot.

## Consequences

- A plugin fault or exploit is contained to its sandbox, not the privileged backend.
- The permission manifest gives users an Android-like, auditable consent surface; tokens are revocable.
- WASM constrains plugins (no arbitrary syscalls, WASI-only host functions); the out-of-process worker
  path is the escape hatch for code that needs more.

## References

- WebAssembly Component Model: <https://component-model.bytecodealliance.org/>
- WASI: <https://wasi.dev/>
- Wasmtime security: <https://docs.wasmtime.dev/security.html>
- hashicorp/go-plugin (out-of-process plugins over RPC): <https://github.com/hashicorp/go-plugin>
