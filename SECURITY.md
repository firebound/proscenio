# Security Policy

## Supported versions

Proscenio is pre-1.0. Only the latest release line receives security fixes;
during the beta, that is the most recent `0.9.x-beta` tag and `main`.

| Version        | Supported |
| -------------- | --------- |
| latest `0.9.x` | yes       |
| older betas    | no        |

## Reporting a vulnerability

Report privately. Do not open a public issue for a security problem.

Preferred: GitHub private vulnerability reporting. Open the repository's
**Security** tab and choose **Report a vulnerability**. This keeps the report
private until a fix ships and lets a coordinated advisory be drafted in place.

Include what you have: affected component (Blender add-on, Godot importer, or
Photoshop UXP plugin), version or commit, reproduction steps, and the impact
you observed.

Expect an initial acknowledgement within a few days. Because Proscenio is a
desktop content-pipeline tool with no hosted service, there is no production
deployment to patch; fixes ship in the next tagged release and are noted in
`CHANGELOG.md`.

## Scope notes

- The three app bundles run inside their host (Blender, Godot, Photoshop) with
  that host's permissions. The Photoshop UXP plugin requests
  `localFileSystem: fullAccess`; treat reports about file paths it reads or
  writes as in scope.
- The `.proscenio` and PSD-manifest files are validated against the schemas in
  `packages/models/schemas/`. Parser or validation bypasses that let a crafted
  file escape those bounds are in scope.
- Build and CI tooling (dev-only dependencies, the release workflow) is in
  scope for supply-chain reports even though it does not ship to users.
