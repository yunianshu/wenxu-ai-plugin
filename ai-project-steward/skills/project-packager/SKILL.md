---
name: project-packager
description: 构建项目发布版本，产出带单一顶层版本目录以及 package/backup/restore/start/stop/upgrade 脚本契约的可部署 tar.gz 包。当实现必须以可下载、可安装、可升级或可回滚的发布产物收尾时使用。Build project releases and generate deployable tar.gz packages with one top-level version directory plus package, backup, restore, start, stop, and upgrade shell scripts. Use when implementation must end with a downloadable, installable, upgradeable, or rollback-capable release.
---

# Project Packager

Produce the project's real release artifact, not an arbitrary archive of caches and source directories.

Run the helper when useful:

```text
python3 "$PLUGIN_ROOT/scripts/release_artifacts.py" detect --root <repo>
python3 "$PLUGIN_ROOT/scripts/release_artifacts.py" version --root <repo>
python3 "$PLUGIN_ROOT/scripts/release_artifacts.py" scaffold --root <repo> [--version <user-confirmed-initial-version>]
python3 "$PLUGIN_ROOT/scripts/release_artifacts.py" collect --root <repo> --artifact '<verified-output-glob>'
python3 "$PLUGIN_ROOT/scripts/release_artifacts.py" bundle --root <repo> --name <project> --include '<package-file-glob>'
python3 "$PLUGIN_ROOT/scripts/release_artifacts.py" audit --root <repo>
```

Read [packaging-guidance.md](references/packaging-guidance.md) and [deployment-scripts.md](references/deployment-scripts.md) before creating scripts or a release package.

## Package workflow

1. Read `AGENTS.md`, `README.md`, build manifests, lockfiles, CI/release workflows, and `docs/ai/verification.md`.
2. Run `detect`. Treat its plans as candidates; prefer the repository's documented or CI-proven release command.
3. Resolve the version from the project's authoritative version source. Prefer root `VERSION`, then the primary build manifest (`versionName`, `pubspec.yaml`, `package.json`, `pom.xml`, `Cargo.toml`, or `pyproject.toml`). Never invent or independently increment a version. If multiple sources disagree, stop and report every conflicting source. If the project declares no version anywhere, agree an initial version with the user first, then record it via `scaffold --version <confirmed>` (or directly in the primary manifest) — still never pick a number yourself.
4. Generate or update repository-specific `package.sh`, `backup.sh`, `restore.sh`, `start.sh`, `stop.sh`, and `upgrade.sh`, plus Windows one-click `start.bat` and `stop.bat` for starting and stopping the local service on Windows hosts. When any of them is missing, run `scaffold` first: it generates stack-aware script templates for exactly the missing files (never overwriting existing ones) and reports the remaining `TODO(project)` markers. Then specialize every template for the actual process manager, database, storage, health check, ownership, and paths. `bundle` also scaffolds missing scripts automatically, but a package containing scaffolded templates must still be reviewed before release. Do not emit generic scripts that ignore the actual process manager, database, storage, health check, ownership, or paths.
5. Run shell syntax checks and safe dry-runs where supported. Exercise backup and restore against disposable data; never test restore against production data.
6. Run the smallest required verification, then the official release build.
7. Assemble `<project>-v<version>-<YYYYMMDDHHMMSS>/` and create a same-named `.tar.gz`. The archive must contain exactly one top-level directory. Include runtime resources, migrations, example configuration, VERSION, scripts, and checksums; exclude mutable production data.
8. Run `audit` and inspect the archive listing. Report commands, package path, archive SHA-256, signing status, health-check status, and anything not verified.

## Rules

- Never package secrets, signing keys, local environment files, databases, user data, logs, IDE state, caches, or dependency directories.
- `scaffold` output is a starting point, never a finished release: resolve every `TODO(project)` marker (service manager, database, health endpoint, ownership, paths) against repository evidence before packaging. It never overwrites existing scripts and never invents a version on its own.
- Preserve native formats: APK/AAB for Android, IPA/archive for iOS, JAR/WAR for JVM, executable for Go/Rust, and the deployable frontend bundle for web projects.
- Do not claim a debug build is production-ready. Clearly label unsigned, debug, simulator-only, or environment-specific outputs.
- Use `git archive` only when the user explicitly wants source code or the project has no executable/deployable release format.
- Container images require a confirmed image name and version. Report the immutable digest when available.
- Do not overwrite unrelated existing artifacts; use versioned names when collisions are possible.
- The package directory, tar.gz filename, bundled `VERSION`, and manifest version must all equal the detected project version. A CLI `--version` value is only an assertion and must fail when it differs from the project.
- `upgrade.sh` runs from the extracted new-version directory. It must discover the currently installed directory from explicit configuration or a stable symlink, back up current data, stop the old service, replace immutable resources atomically, run compatible migrations, preserve configuration/data, start the new version, and verify health. On failure, restore the previous version and restart it.
- Backup archives must contain a manifest and never include themselves. Restore must validate the archive, refuse ambiguous targets, and require explicit confirmation for destructive replacement unless invoked by the controlled rollback path.

## Completion

Return clickable artifact links when the environment supports them. State target, version, build type, signing status, checksum verification, and any real-device or deployment check not performed.
