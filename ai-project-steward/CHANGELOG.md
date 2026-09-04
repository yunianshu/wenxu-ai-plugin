# Changelog

All notable changes to AI Project Steward are documented here.

## [Unreleased]

### Added

- `release_artifacts.py scaffold`: generates stack-aware deployment script templates (package/backup/restore/start/stop/upgrade) for exactly the missing files when a repository has no packaging files, records a user-confirmed initial version into `VERSION`, and reports remaining `TODO(project)` markers. `bundle` now scaffolds missing scripts automatically and flags them in its result.
- Versioned tar.gz deployment packaging with a single top-level directory, stack detection, checksums, and package/backup/restore/start/stop/upgrade script contracts.
- Archify-compatible diagram workspaces with typed JSON sources, validated HTML outputs, and receipts.
- Root `CHANGELOG.md` creation and synchronization for managed projects.
- Synchronization that supplements missing baseline documentation.

### Changed

- Release package versions are now resolved from the project's authoritative version file or build manifest; conflicting versions block packaging.
- Architecture and flow diagrams now use the `tt-a1i/archify` model instead of Mermaid as the primary format.

### Fixed

- ZCode hook startup now uses the cross-compatible `CLAUDE_PLUGIN_ROOT` path variable instead of Codex-only `PLUGIN_ROOT`, with a native ZCode plugin manifest included.
