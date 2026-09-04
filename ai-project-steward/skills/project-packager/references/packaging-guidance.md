# Packaging guidance

## Evidence priority

1. Release workflow or CI configuration that currently succeeds.
2. Verified commands in README, AGENTS, or development documentation.
3. Build manifests and standard toolchain conventions.
4. A user-confirmed command or target.

## Common outputs

| Project | Typical command | Typical artifact |
| --- | --- | --- |
| Android Gradle | `gradlew assembleRelease` or `bundleRelease` | APK or AAB under module build outputs |
| Flutter | `flutter build apk --release` or `appbundle` | APK or AAB under Flutter build outputs |
| Spring Boot/Gradle | `gradlew bootJar` | executable JAR |
| Maven | `mvn package` | JAR or WAR under target |
| Node/Web | repository build script | deployable dist/build directory archive |
| Rust | `cargo build --release` | target/release binary |
| Go | repository build command | platform executable |

The table supplies discovery hints only. Never replace a repository-specific release pipeline with a guessed command.

For service projects, the primary handoff is a versioned tar.gz deployment bundle with one top-level directory. Native APK, AAB, JAR, WAR, frontend bundles, and binaries become inputs to that deployment bundle when applicable.
