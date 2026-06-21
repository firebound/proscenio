# Bugs found during manual testing

Reproducible bugs whose fix is **not yet applied** - the defect still reproduces. Each cites a reproducer + suspect + affected file, and promotes into a PR fix or a dedicated spec.

Bugs whose fix already shipped and only await a GUI confirmation are walkable items in the QA Companion checklist ([`tools/qa-companion/checklist/`](../tools/qa-companion/checklist/)) - the locked owner of the manual-test surface (see [decisions.md](decisions.md)). This file is exclusively still-broken behavior. Distinct from [backlog-ui-feedback.md](backlog-ui-feedback.md) (polish, not behavior).

## No currently-open bugs

The 2026-06-20 backlog-drain wave routed the prior entries into specs (see [`_index.md`](_index.md)):

- The doll-roundtrip re-measure waiver was not a current defect, so it moved to [`gated.md`](gated.md); it fires before the first public release tag.

New bugs found during manual testing land here. Lead with the symptom (see the bug-report style in [`.ai/conventions/docs.md`](../.ai/conventions/docs.md)), then the suspect and the affected file.
