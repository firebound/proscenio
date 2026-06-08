# Blender addon preferences

Status: **scope sketched, not started**. Successor to spec 022 (UI restructure). 022 introduces a minimal `ProscenioAddonPreferences` carrying a single `debug_mode` boolean (so the IA can debug-gate the Diagnostics panel and the Debug Pipeline subpanel). This spec grows that into the full preferences surface.

Third spec of the `apps/blender` UI/UX review series (019 naming, 022 structure, 023 help/docs/i18n, 024 preferences). Order between 023 and 024 is flexible; both depend on 022.

## Problem

The addon has no real preferences surface. Global, user-level settings that should not live per-`.blend` (the verbosity of the report log, the debug toggle, any future cross-tool defaults) currently have nowhere to live. 022 lands the `debug_mode` bool out of necessity; everything else has no home.

## Scope (sketch)

- **Info-log level.** A `debug / errors / info` enum that wires into the shared report helper (`core/_shared/report`) so the user controls console verbosity. Today every operator reports at one fixed level.
- **Debug mode.** Promote and own the `debug_mode` boolean 022 introduced (the Diagnostics panel + Debug Pipeline subpanel gate on it). Keep the same property so 022's gating keeps working; this spec just expands the surrounding preferences.
- **Any cross-tool global default** that surfaces by the time this lands (for example, the docs site base URL from spec 023, if it is made configurable rather than a constant).

## Decisions to lock (when promoted)

- Whether `debug_mode` stays a bare bool or becomes part of a broader "developer options" group.
- How the log-level enum maps onto the report helper's call sites (a single gate in `report`, or per-call levels).
- Whether the preferences carry any per-project overrides (likely not - scene PG already covers per-`.blend` state).

## Non-goals

- The contextual-panel-hiding toggle - cut in 022 (panels warn instead of hiding; no preference).
- Any panel/structure change - spec 022.
- The help/doc/i18n system - spec 023.

## Related

- [`../022-blender-ui-restructure/STUDY.md`](../022-blender-ui-restructure/STUDY.md): introduces the minimal `ProscenioAddonPreferences` + `debug_mode` this spec expands (decision D11).
- [`../021-blender-ui-audit/DESIGN-NOTES.md`](../021-blender-ui-audit/DESIGN-NOTES.md): the preferences decisions (log level + debug; contextual-hide toggle cut).
