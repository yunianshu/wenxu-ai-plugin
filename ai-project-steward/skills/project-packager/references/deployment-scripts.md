# Deployment script contract

Generate scripts for the repository's actual deployment model. All scripts use POSIX shell where practical, start with `set -Eeuo pipefail`, resolve their own directory without depending on the caller's working directory, quote paths, log major actions, and fail with a non-zero status.

## Required package layout

```text
<project>-v<version>-<YYYYMMDDHHMMSS>/
├── bin/ or application runtime files
├── migrations/                 # only when the project has migrations
├── web/                        # only when the project has web assets
├── package.sh
├── backup.sh
├── restore.sh
├── start.sh
├── stop.sh
├── upgrade.sh
├── VERSION
├── manifest.json
└── .env.example                # never a real secret-bearing .env
```

The tar.gz contains exactly this single top-level directory. Optional Dockerfile, Compose, nginx, status, restart, and log helpers are included only when the project uses them.

## Version source

Read the version from the project's existing authoritative source. Use a root VERSION file when the project declares it authoritative; otherwise use the primary build manifest such as Android `versionName`, Flutter `pubspec.yaml`, Node `package.json`, Maven `pom.xml`, Cargo.toml, or pyproject.toml. Never use the packaging time, Git commit count, branch name, or an AI-selected number as the semantic version. The timestamp is only the final filename suffix. Stop when version sources disagree.

## Script responsibilities

| Script | Contract |
| --- | --- |
| `package.sh` | Builds verified runtime artifacts, stages a clean version directory, writes VERSION and checksums, rejects secrets and mutable data, creates tar.gz, then checks its single-root layout. |
| `backup.sh` | Quiesces or consistently snapshots configured databases/uploads/configuration, writes timestamp and manifest, checks free space, and produces a checksummed backup. |
| `restore.sh` | Validates checksum/version/target, protects the current state with a pre-restore backup, restores atomically where possible, fixes ownership, and verifies service health. |
| `start.sh` | Validates configuration and prerequisites, starts through the real service manager, waits with a bounded timeout, and verifies readiness/health rather than only process existence. |
| `stop.sh` | Stops gracefully, waits with a timeout, escalates only when configured, and remains idempotent when already stopped. |
| `upgrade.sh` | Runs from the extracted new-version directory; locks against concurrent upgrades, validates package/version, backs up, stops old version, preserves mutable data/config, switches immutable resources atomically, migrates, starts, checks health, and rolls back on failure. |

## Upgrade model

Prefer versioned immutable directories plus a stable `current` symlink:

```text
<install-root>/
├── current -> releases/<new-version>
├── releases/<old-version>/
├── releases/<new-version>/
├── shared/config/
├── shared/data/
└── backups/
```

Do not replace the directory from which the old service is actively running in place. Keep at least the immediately previous known-good release until the new health check passes. Database rollback is not automatically safe: use backward-compatible migrations or an explicit, tested database restore path.

## Required review

- Validate with `sh -n` or `bash -n` according to the declared interpreter and run ShellCheck when available.
- Test paths containing spaces, repeated start/stop, missing configuration, failed health checks, insufficient disk, interrupted upgrade, and rollback.
- Redact secrets from command output and logs.
- Never infer production paths, credentials, system users, ports, or service names when repository evidence does not establish them.
